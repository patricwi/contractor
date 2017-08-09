# -*- coding: utf-8 -*-

"""Provide login via amivapi."""

from functools import wraps
import requests
from requests.compat import urljoin

from flask import (Blueprint, redirect, url_for, make_response,
                   render_template, current_app, request, g)

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField
from wtforms.validators import DataRequired

COOKIE = 'amivapi_token'

api_auth = Blueprint('api_auth', __name__)
"""The blueprint used for the endpoints."""


class LoginForm(FlaskForm):
    """Form for api login data."""
    class Meta:
        # CSRF protection not needed here. This way we don't require a secret
        csrf = False

    user = StringField('user',
                       validators=[DataRequired()],
                       render_kw={'placeholder': 'nethz'})
    password = PasswordField('password',
                             validators=[DataRequired()],
                             render_kw={'placeholder': 'password'})


@api_auth.route('/login', methods=['GET', 'POST'])
def login():
    """Log in and redirect or present login view."""
    # CSRF is disabled because its not providing any protection here
    # This way we don't require a secret key
    form = LoginForm()
    login_error = api_error = False

    # Helper, redirect to url specified in query or root of app
    _login_response = make_response(redirect(request.script_root))

    if _get_session():
        # Already logged in
        return _login_response

    if form.validate_on_submit():
        # Login with amivpi
        data = {
            'username': form.user.data,
            'password': form.password.data}

        try:
            response = requests.post(_sessions_url(), data=data)

            if response.status_code == 201:
                # Successful login!
                token = response.json()['token']
                _login_response.set_cookie(COOKIE, token)
                return _login_response
            elif response.status_code in range(400, 500):
                # Some input was wrong
                login_error = True
            else:
                # AMIVAPI is unreachable
                api_error = True
        except (requests.ConnectionError, requests.Timeout):
            api_error = True

    return render_template('login.html',
                           login_form=form,
                           api_error=api_error,
                           login_error=login_error)


@api_auth.route('/logout')
def logout():
    """Log out by removing cookie and deleting token from amivapi."""
    login_data = _get_session()
    if login_data:
        (_id, _etag, token) = login_data
        h = {'Authorization': token, 'If-Match': _etag}
        delete_url = "%s/%s" % (_sessions_url(), _id)
        # Don't catch exceptions, let logout fail if something goes wrong
        requests.delete(delete_url, headers=h)

    response = make_response(redirect(url_for('.login')))
    response.set_cookie(COOKIE, expires=0)
    return response


def protected(func):
    """Decorator to require auth."""
    @wraps(func)
    def protected_view(*args, **kwargs):
        if _get_session():
            return func(*args, **kwargs)
        else:
            return redirect(url_for('api_auth.login'))

    return protected_view


def _sessions_url():
    return urljoin(current_app.config['AMIVAPI_URL'], 'sessions')


def _get_session():
    """Return (session id, etag, token) if logged in, None otherwise.

    Token will be taken from cookies.
    g.username will be set to full name of user.
    """
    token = request.cookies.get(COOKIE)

    if token:
        h = {'Authorization': token}
        p = {'where': '{"token": "%s"}' % token, 'embedded': '{"user": 1}'}

        try:
            response = requests.get(_sessions_url(), headers=h, params=p)
            if response.status_code == 200:
                session = response.json()['_items'][0]
                user = session['user']
                g.username = " ".join((user['firstname'], user['lastname']))
                return (session['_id'], session['_etag'], token)
        except (requests.ConnectionError, requests.Timeout):
            pass
