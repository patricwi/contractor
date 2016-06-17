# -*- coding: utf-8 -*-

"""The app."""

from locale import setlocale, LC_TIME
from ruamel import yaml

from flask import (Flask, render_template, send_file, redirect, url_for,
                   session, request)

from contractor.tex import render_tex
from contractor.soapclient import CRMImporter
from contractor.api_auth import api_auth, protected
from contractor.yearly_settings import YearlySettingsForm, get_yearly_settings

app = Flask('contractor')

app.config.from_object('contractor.settings')

# Load User config
try:
    with open('config.yml', 'r') as f:
        app.config.from_mapping(yaml.load(f))
except:
    raise("No config found! Use `python init.py` to create.")

# Set locale to ensure correct weekday format
setlocale(LC_TIME, app.config['LOCALE'])

# Get CRM connection
CRM = CRMImporter(app)

# Get Auth
app.register_blueprint(api_auth)


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
    settings_form = YearlySettingsForm()

    # Safe new data if valid
    settings_form.validate_and_save()

    return render_template('main.html',
                           user=session['logged_in'],
                           output_format=session.get('output_format', 'mail'),
                           settings_form=settings_form,
                           descriptions=app.config['FULLTEXT'],
                           companies=CRM.data,
                           errors=CRM.errors)


@app.route('/refresh')
@protected
def refresh():
    """Get companies again."""
    CRM.refresh()

    return redirect(url_for('main'))


@app.route('/contracts')
@app.route('/contracts/<int:id>')
@protected
def send_contracts(id=None):
    """Contract creation."""
    if id is None:
        selection = CRM.data
    else:
        selection = [CRM.data[id]]

    # Get output format, mail is default
    output = session.get("output_format", "mail")

    # Check if only tex is requested
    return_tex = (output == "tex")

    # Check if output format is email -> only single contract
    contract_only = (output == "email")

    # Create the yearly settings form. data will be autoloaded.
    yearly = get_yearly_settings()

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
