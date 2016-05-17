# -*- coding: utf-8 -*-

"""The app."""

import os
import shutil
import json
import logging

from flask import (Flask, render_template, send_file, redirect, url_for,
                   session, request)

from contractor.tex import render_tex
from contractor.soapclient import CRMImporter
from contractor.api_auth import api_auth, protected

app = Flask('contractor')

app.config.from_pyfile('config.py')

if not app.debug and app.config.get('ENABLE_LOG', False):
    logpath = os.path.join(app.config['LOG_DIR'],
                           'flask.log')
    file_handler = logging.FileHandler(logpath)
    file_handler.setLevel(app.config['LOGLEVEL'])
    app.logger.addHandler(file_handler)

# Different Booth, category, day options
# small booths
sA1 = "Kleiner Stand, Kategorie A, ein Messetag"
sA2 = "Kleiner Stand, Kategorie A, zwei Messetage"
sB1 = "Kleiner Stand, Kategorie B, ein Messetag"
sB2 = "Kleiner Stand, Kategorie B, zwei Messetage"
# big booths,
bA1 = "Grosser Stand, Kategorie A, ein Messetag"
bA2 = "Grosser Stand, Kategorie A, zwei Messetage"
bB1 = "Grosser Stand, Kategorie B, ein Messetag"
bB2 = "Grosser Stand, Kategorie B, zwei Messetage"
# startops,
su1 = "Startup-Stand, ein Messetag"
su2 = "Startup-Stand, zwei Messetage"

app.config['DESCRIPTIONS'] = {
    'tex': {
        # booth descriptions, map to tex commands
        # small booths
        'sA1': r'\smallAone',
        'sA2': r'\smallAtwo',
        'sB1': r'\smallBone',
        'sB2': r'\smallBtwo',
        # big booths,
        'bA1': r'\bigAone',
        'bA2': r'\bigAtwo',
        'bB1': r'\bigBone',
        'bB2': r'\bigBtwo',
        # startops,
        'su1': r'\startupone',
        'su2': r'\startuptwo'
    },
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
        'first': 'Teilnahme Dienstag, 18.10.2016',
        'second': 'Teilname Mittwoch, 19.10.2016',
        'both': 'Teilnahme Dienstag, 18.10.2016 und Mittwoch 19.10.2016',
    },

    # Prices, all in francs
    'prices': {
        'booths': {
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
        },
        'media': '850',
        'business': '1500',
        'first': '2500',
    },
}

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
def _storagename(name):
        return os.path.join(app.config['DATA_DIR'], name)


def _refresh_companies():
    """Get new companies and clear out old contracts."""
    (letterdata, errors) = CRM.get_contract_data()

    app.config['LETTERDATA'] = letterdata
    app.config['ERRORS'] = errors

    # Store
    with open(_storagename('letterdata.json'), 'w') as f:
        json.dump(letterdata, f)

    with open(_storagename('errors.json'), 'w') as f:
        json.dump(errors, f)

    # Remove everything in storage and recreate dir
    shutil.rmtree(app.config['STORAGE_DIR'])
    os.mkdir(app.config['STORAGE_DIR'])

# Load on startup
try:
    with open(_storagename('letterdata.json'), 'r') as f:
        app.config['LETTERDATA'] = json.load(f)
    with open(_storagename('errors.json'), 'r') as f:
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

    return render_template('main.html',
                           user=session['logged_in'],
                           output_format=session.get('output_format', 'mail'),
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

    pdfname = render_tex(descriptions=app.config['DESCRIPTIONS']['tex'],
                         letterdata=selection,
                         texpath=app.config['TEX_DIR'],
                         output_dir=app.config['STORAGE_DIR'],
                         contract_only=contract_only,
                         return_tex=return_tex,
                         **app.config['YEARLY_SETTINGS'])

    path = os.path.join(app.config['STORAGE_DIR'], pdfname)

    return send_file(path, as_attachment=True)

if __name__ == "__main__":
    app.run()
