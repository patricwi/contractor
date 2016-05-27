# -*- coding: utf-8 -*-

"""The app."""

import os
import shutil
import json
import logging
from datetime import datetime
from locale import setlocale, LC_TIME

from flask import (Flask, render_template, send_file, redirect, url_for,
                   session, request)
from flask_wtf import Form
from wtforms import StringField, IntegerField, FormField, DateField

from contractor.tex import render_tex
from contractor.soapclient import CRMImporter
from contractor.api_auth import api_auth, protected

# Set locale to ensure german weekdays
setlocale(LC_TIME, "de_CH.UTF-8")
dateformat = "%d.%m.%Y"


app = Flask('contractor')

app.config.from_pyfile('config.py')

if not app.debug and app.config.get('ENABLE_LOG', False):
    logpath = os.path.join(app.config['LOG_DIR'],
                           'flask.log')
    file_handler = logging.FileHandler(logpath)
    file_handler.setLevel(app.config['LOGLEVEL'])
    app.logger.addHandler(file_handler)

app.config['DESCRIPTIONS'] = {
    'html': {
        # booth descriptions for html
        # small booths
        'sA1': 'small, cat A, one day',
        'sA2': 'small, cat A, two days',
        'sB1': 'small, cat B, one day',
        'sB2': 'small, cat B, two days',
        # big booths,
        'bA1': 'big, cat A, one day',
        'bA2': 'big, cat A, two days',
        'bB1': 'big, cat B, one day',
        'bB2': 'big, cat B, two days',
        # startops,
        'su1': r'\startupone',
        'su2': r'\startuptwo'
    }
}

app.config['YEARLY_SETTINGS'] = {
    'fairtitle': 'AMIV Kontakt.16',
    'president': 'Alexander Ens',
    'sender': 'Pascal Gutzwiller',

    # Fair days,
    'days': {
        'first': datetime.strptime('18.10.2016', dateformat).date(),
        'second': datetime.strptime('19.10.2016', dateformat).date(),
    },

    # Prices, all in francs
    'prices': {
        'sA1': '1100',
        'sA2': '2800',
        'sB1': '850',
        'sB2': '2600',
        'bA1': '2200',
        'bA2': '4800',
        'bB1': '1800',
        'bB2': '4400',
        'su1': '300',
        'su2': '750',
        'media': '850',
        'business': '1500',
        'first': '2500',
    },
}


class PricesSubForm(Form):
    """Form for prices, will be part of main form."""

    # small
    sA1 = IntegerField(render_kw={'placeholder': '1234'})
    sA2 = IntegerField(render_kw={'placeholder': '1234'})
    sB1 = IntegerField(render_kw={'placeholder': '1234'})
    sB2 = IntegerField(render_kw={'placeholder': '1234'})

    # big
    bA1 = IntegerField(render_kw={'placeholder': '1234'})
    bA2 = IntegerField(render_kw={'placeholder': '1234'})
    bB1 = IntegerField(render_kw={'placeholder': '1234'})
    bB2 = IntegerField(render_kw={'placeholder': '1234'})

    # startup
    su1 = IntegerField(render_kw={'placeholder': '1234'})
    su2 = IntegerField(render_kw={'placeholder': '1234'})

    # packets
    first = IntegerField(render_kw={'placeholder': '1234'})
    business = IntegerField(render_kw={'placeholder': '1234'})
    media = IntegerField(render_kw={'placeholder': '1234'})


class DaysSubForm(Form):
    """Form for days, will be part of main form."""

    first = DateField(format=dateformat,
                      render_kw={'placeholder': 'dd.mm.yyyy'})
    second = DateField(format=dateformat,
                       render_kw={'placeholder': 'dd.mm.yyyy'})


class YearlySettingsForm(Form):
    """Form to change yearly settings for the fair."""

    fairtitle = StringField('fairtitle',
                            render_kw={'placeholder': 'Kontakt.YY'})
    president = StringField('president',
                            render_kw={'placeholder': 'firstname lastname'})
    sender = StringField('sender',
                         render_kw={'placeholder': 'firstname lastname'})

    prices = FormField(PricesSubForm)
    days = FormField(DaysSubForm)


# Set up directories for app data and output storage
for directory in [app.config['STORAGE_DIR'], app.config['DATA_DIR']]:
    if not os.path.exists(directory):
        os.makedirs(directory)

# Get CRM connection
CRM = CRMImporter(app)

# Get Auth
app.register_blueprint(api_auth)
app.config['APIAUTH_LANDING_PAGE'] = 'main'
app.config['APIAUTH_URL'] = 'https://nicco.io/amiv/'


# Import companies
def _storagepath(name):
        return os.path.join(app.config['DATA_DIR'], name)


def _refresh_companies():
    """Get new companies and clear out old contracts."""
    (letterdata, errors) = CRM.get_contract_data()

    app.config['LETTERDATA'] = letterdata
    app.config['ERRORS'] = errors

    # Store
    with open(_storagepath('letterdata.json'), 'w') as f:
        json.dump(letterdata, f)

    with open(_storagepath('errors.json'), 'w') as f:
        json.dump(errors, f)

    # Remove everything in storage and recreate dir
    shutil.rmtree(app.config['STORAGE_DIR'])
    os.mkdir(app.config['STORAGE_DIR'])

# Load on startup
try:
    with open(_storagepath('letterdata.json'), 'r') as f:
        app.config['LETTERDATA'] = json.load(f)
    with open(_storagepath('errors.json'), 'r') as f:
        app.config['ERRORS'] = json.load(f)
except OSError:
    _refresh_companies()


# Routes

@app.route('/', methods=['GET', 'POST'])
@protected
def main():
    """Main view.

    Includes output format and yearly settings.
    """
    # Check if output format is specified
    format = request.args.get('output', None)
    if format in ["mail", "email", "tex"]:
        session['output_format'] = format

    # Form for yearly settings
    settings_form = YearlySettingsForm(**app.config['YEARLY_SETTINGS'])

    return render_template('main.html',
                           user=session['logged_in'],
                           output_format=session.get('output_format', 'mail'),
                           settings_form=settings_form,
                           descriptions=app.config['DESCRIPTIONS']['html'],
                           companies=app.config['LETTERDATA'],
                           errors=app.config['ERRORS'])


@app.route('/refresh')
@protected
def refresh():
    """Get companies again."""
    _refresh_companies()

    return redirect(url_for('main'))


@app.route('/contracts')
@app.route('/contracts/<int:id>')
@protected
def send_contracts(id=None):
    """Contract creation."""
    if id is None:
        selection = app.config['LETTERDATA']
    else:
        selection = [app.config['LETTERDATA'][id]]

    # Get output format, mail is default
    output = session.get("output_format", "mail")

    # Check if only tex is requested
    return_tex = (output == "tex")

    # Check if output format is email -> only single contract
    contract_only = (output == "email")

    yearly = app.config['YEARLY_SETTINGS']

    filepath = render_tex(
        # Data
        letterdata=selection,

        # Yearly settings
        fairtitle=yearly['fairtitle'],
        president=yearly['president'],
        sender=yearly['sender'],
        days=yearly['days'],
        prices=yearly['prices'],

        # Output options
        contract_only=contract_only,
        return_tex=return_tex,

        # Tex source and storage
        texpath=app.config['TEX_DIR'],
        output_dir=app.config['STORAGE_DIR']
    )

    return send_file(filepath, as_attachment=True)

if __name__ == "__main__":
    app.run()
