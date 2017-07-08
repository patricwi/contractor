# -*- coding: utf-8 -*-

"""The app."""

from os import path
from locale import setlocale, LC_TIME

from flask import (Flask, render_template, send_file, redirect, url_for,
                   session, request)

from contractor.tex import render_tex
from contractor.soapclient import Importer
from contractor.api_auth import api_auth, protected
from contractor.yearly_settings import YearlySettingsForm, load_yearly_settings

app = Flask('contractor')
app.config.from_object('config')

# If directories have not been defined, use '.cache' in current working dir
app.config.setdefault('STORAGE_DIR', path.abspath('./.cache'))
app.config.setdefault('SETTINGS_DIR', path.abspath('./.cache'))

# Set locale to ensure correct weekday format
app.config.setdefault('LOCALE', 'de_CH.utf-8')
setlocale(LC_TIME, app.config['LOCALE'])

# Get CRM connection
CRM = Importer(app.config['SOAP_USERNAME'], app.config['SOAP_PASSWORD'])

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
    output_format = request.args.get('output', None)
    if output_format in ["mail", "email", "tex"]:
        session['output_format'] = format

    # Form for yearly settings
    settings_form = YearlySettingsForm()

    # Safe new data if valid
    settings_form.validate_and_save()

    return render_template('main.html',
                           user=session['logged_in'],
                           output_format=session.get('output_format', 'mail'),
                           settings_form=settings_form,
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

    # Get yearly settings
    yearly = load_yearly_settings()

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

        # Storage (from config)
        output_dir=app.config['STORAGE_DIR']
    )

    return send_file(filepath, as_attachment=True)
