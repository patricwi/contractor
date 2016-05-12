# -*- coding: utf-8 -*-

"""The app."""

from flask import (Flask, render_template, send_file, redirect,
                   url_for)
from flask.ext.basicauth import BasicAuth

from contractor.tex import render_tex
from contractor.soapclient import CRMImporter
import os
import shutil
import json

app = Flask('contractor')

app.config.from_pyfile('config.py')

# Auth
basic_auth = BasicAuth(app)

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
su1 = "Startup-Stand, ein Messetag",
su2 = "Startup-Stand, zwei Messetage",

app.config['TEX_SETTINGS'] = {
    # booth descriotions
    # small booths
    'sA1': sA1,
    'sA2': sA2,
    'sB1': sB1,
    'sB2': sB2,
    # big booths,
    'bA1': bA1,
    'bA2': bA2,
    'bB1': bB1,
    'bB2': bB2,
    # startops,
    'su1': su1,
    'su2': su2,

    'president': 'Alexander Ens',
    'sender': 'Pascal Gutzwiller',

    # Fair days,
    'day_one': 'Dienstag, 18.10.',
    'day_two': 'Mittwoch, 19.10.',

    # Prices, all in francs
    'prices': {
        'booths': {
            sA1: '1100',
            sA2: '2800',
            sB1: '850',
            sB2: '2600',
            bA1: '2200',
            bA2: '4800',
            bB1: '1800',
            bB2: '4400',
            su1: '300',
            su2: '750',
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


@app.route('/')
def main():
    """Main view."""
    return render_template('main.html', companies=app.config['LETTERDATA'])


@app.route('/refresh')
def refresh():
    """Get companies again."""
    _refresh_companies()

    return redirect(url_for('main'))


@app.route('/contracts')
@app.route('/contracts/<int:id>')
def send_contracts(id=None):
    """Contract creation."""
    if id is None:
        selection = app.config['LETTERDATA']
    else:
        selection = [app.config['LETTERDATA'][id]]

    pdfname = render_tex(app.config['TEX_SETTINGS']['president'],
                         app.config['TEX_SETTINGS']['sender'],
                         app.config['TEX_SETTINGS']['prices'],
                         selection,
                         texpath=app.config['TEX_DIR'],
                         output_dir=app.config['STORAGE_DIR'])

    path = os.path.join(app.config['STORAGE_DIR'], pdfname)

    print(path)

    return send_file(path, as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True)
