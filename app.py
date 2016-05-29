# -*- coding: utf-8 -*-

"""The app."""

import os
import shutil
import yaml
import logging
from datetime import datetime
from locale import setlocale, LC_TIME

from flask import (Flask, render_template, send_file, redirect, url_for,
                   session, request)
from flask_wtf import Form
from wtforms import StringField, TextAreaField, FormField
from wtforms.validators import InputRequired
from wtforms.fields.html5 import IntegerField, DateField

from contractor.tex import render_tex
from contractor.soapclient import CRMImporter
from contractor.api_auth import api_auth, protected

# Set locale to ensure german weekdays
setlocale(LC_TIME, "de_CH.UTF-8")
dateformat = "%Y-%m-%d"
dateplaceholder = "yyyy-mm-dd"


app = Flask('contractor')

app.config.from_pyfile('config.py')

if 'LOG_DIR' in app.config:
    logpath = os.path.join(app.config['LOG_DIR'],
                           'flask.log')
    file_handler = logging.FileHandler(logpath)
    file_handler.setLevel(app.config['LOGLEVEL'])
    app.logger.addHandler(file_handler)

# All different options in neat order (used to create form)
choices = ['sA1', 'sA2', 'sB1', 'sB2',
           'bA1', 'bA2', 'bB1', 'bB2',
           'su1', 'su2',
           'media', 'business', 'first']

# Additional fulltext
fulltext = {
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
    # startups,
    'su1': 'start-up, one day',
    'su2': 'start-up, two days',
    # packets
    'media': 'media packet',
    'business': 'business packet',
    'first': 'first packet'
}

app.config['YEARLY_SETTINGS'] = {
    'fairtitle': 'AMIV Kontakt.16',
    'president': 'Alexander Ens',
    'sender': 'Pascal Gutzwiller\nQuästor Kommission Kontakt',

    # Fair days,
    'days': {
        'first': datetime.strptime('18.10.2016', "%d.%m.%Y").date(),
        'second': datetime.strptime('19.10.2016', "%d.%m.%Y").date(),
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


class PriceField(IntegerField):
    """Special field that can be recognized in the templated for formatting."""

    pass


class PricesSubForm(Form):
    """Form for prices, will be part of main form.

    Empty form so far, we will add the attributes in a loop since they are
    many and all look the same.
    """

    pass

for shortname in choices:
    setattr(PricesSubForm,
            shortname,
            PriceField(label=fulltext[shortname],
                       validators=[InputRequired()],
                       render_kw={'placeholder': '1234'}))


class DaysSubForm(Form):
    """Form for days, will be part of main form."""

    first = DateField(label='First Day of Fair',
                      format=dateformat,
                      validators=[InputRequired()],
                      render_kw={'placeholder': dateplaceholder})
    second = DateField(label='Second Day of Fair',
                       format=dateformat,
                       validators=[InputRequired()],
                       render_kw={'placeholder': dateplaceholder})


class YearlySettingsForm(Form):
    """Form to change yearly settings for the fair."""

    fairtitle = StringField(label='Title of Fair',
                            validators=[InputRequired()],
                            render_kw={'placeholder': 'Kontakt.YY'})
    president = StringField(label='President',
                            validators=[InputRequired()],
                            description='The president of the Kontakt '
                                        'Kommission',
                            render_kw={'placeholder': 'Firstname Lastname'})
    sender = TextAreaField(label='Sender',
                           validators=[InputRequired()],
                           description='Sender of contract letters, usually '
                                       'the president or treasurer. You can '
                                       'use several lines to add title etc.',
                           render_kw={
                               'placeholder': 'Firstname Lastname\n'
                                              '(Additional info, if any)'})

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
def _datapath(name):
        return os.path.join(app.config['DATA_DIR'], name)


def _refresh_companies():
    """Get new companies and clear out old contracts."""
    (letterdata, errors) = CRM.get_contract_data()

    app.config['LETTERDATA'] = letterdata
    app.config['ERRORS'] = errors

    # Store
    with open(_datapath('letterdata.yml'), 'w') as f:
        yaml.dump(letterdata, f)

    with open(_datapath('errors.yml'), 'w') as f:
        yaml.dump(errors, f)

    # Remove everything in storage (finished contracts) and recreate dir
    shutil.rmtree(app.config['STORAGE_DIR'])
    os.mkdir(app.config['STORAGE_DIR'])

# Load on startup
try:
    with open(_datapath('letterdata.yml'), 'r') as f:
        app.config['LETTERDATA'] = yaml.load(f)
    with open(_datapath('errors.yml'), 'r') as f:
        app.config['ERRORS'] = yaml.load(f)
except OSError:
    _refresh_companies()

# if there are any yearly settings saved, overwrite defaults
try:
    with open(_datapath('yearly_settings.yml'), 'r') as f:
        app.config['YEARLY_SETTINGS'] = yaml.load(f)
except OSError:
    # Keep defaults
    pass


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

    if settings_form.validate_on_submit():
        print("yehaa")
        # Adjust settings and save them to file
        app.config['YEARLY_SETTINGS'] = settings_form.data
        with open(_datapath('yearly_settings.yml'), 'w') as f:
            yaml.dump(app.config['YEARLY_SETTINGS'], f)

    return render_template('main.html',
                           user=session['logged_in'],
                           output_format=session.get('output_format', 'mail'),
                           settings_form=settings_form,
                           descriptions=fulltext,
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
