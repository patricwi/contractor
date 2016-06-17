# -*- coding: utf-8 -*-

"""Provide login via amivapi."""

from functools import wraps
import requests

from flask import (Blueprint, redirect, url_for, session,
                   render_template, current_app)

from flask_wtf import Form
from wtforms import StringField, PasswordField
from wtforms.validators import DataRequired

api_auth = Blueprint('api_auth', __name__)
"""The blueprint used for the endpoints."""


class LoginForm(Form):
    """Form for api login data."""

    user = StringField('user',
                       validators=[DataRequired()],
                       render_kw={'placeholder': 'nethz'})
    password = PasswordField('password',
                             validators=[DataRequired()],
                             render_kw={'placeholder': 'password'})


@api_auth.route('/login', methods=['GET', 'POST'])
def login():
    """Log in and redirect or present login view."""
    form = LoginForm()
    login_error = False
    api_error = False

    # Helper
    _logged_in = redirect('/')

    if session.get('logged_in', False):
        # Already logged in
        return _logged_in

    if form.validate_on_submit():
        # Login with amivpi
        apiurl = current_app.config['AMIVAPI_URL']

        data = {
            'user': form.user.data,
            'password': form.password.data}

        response = requests.post(apiurl + 'sessions', data=data)

        if response.status_code == 201:
            id = response.json()['user_id']
            token = response.json()['token']

            # Use requests session to get username
            s = requests.Session()
            s.auth = (token, '')
            user = s.get(apiurl + 'users/%s' % id).json()

            session['logged_in'] = user['firstname'] + " " + user['lastname']

            # Success! Redirect
            return _logged_in
        elif response.status_code in [401, 500]:
            # TODO (Alex): right now the api crashes with wrong credentials,
            # change this as soon as api is fixed
            # Wrong credentials
            login_error = True
        else:
            # AMIVAPI is unreachable
            api_error = True

    return render_template('login.html', login_form=form,
                           api_error=api_error, login_error=login_error)


@api_auth.route('/logout')
def logout():
    """Log out."""
    session.pop('logged_in', None)
    return redirect(url_for('api_auth.login'))


def protected(func):
    """Decorator to require auth."""
    @wraps(func)
    def protected_view(*args, **kwargs):
        if session.get('logged_in', False):
            return func(*args, **kwargs)
        else:
            return redirect(url_for('api_auth.login'))

    return protected_view
