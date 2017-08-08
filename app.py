# -*- coding: utf-8 -*-

"""The app."""

from os import getenv, getcwd, path
from io import BytesIO
from locale import setlocale, LC_TIME

from flask import (Flask, render_template, send_file,
                   session, make_response)

from contractor.tex import render_tex
from contractor.soapclient import Importer
from contractor.api_auth import api_auth, protected

app = Flask('contractor')
app.config.from_pyfile('settings.py')

# Try to load config specified by envvar, default to config.py in work dir
default_config = path.join(getcwd(), 'config.py')
config_file = getenv("CONTRACTOR_CONFIG", default_config)
app.config.from_pyfile(config_file)

# If directories have not been defined, use '.cache' in current working dir
app.config.setdefault('STORAGE_DIR', path.abspath('./.cache'))

# Set locale to ensure correct weekday format
app.config.setdefault('LOCALE', 'de_CH.utf-8')
setlocale(LC_TIME, app.config['LOCALE'])

# Get CRM connection
CRM = Importer(app.config['SOAP_USERNAME'], app.config['SOAP_PASSWORD'])

# Get Auth
app.register_blueprint(api_auth)


def send(data):
    """Send data as file with headers to disable caching.

    We want the preview to be refreshed, so need to avoid browser caching.
    """

    try:
        response = make_response(send_file(BytesIO(data),
                                           mimetype='application/pdf',
                                           cache_timeout=0))
        response.headers['Content-Length'] = len(data)
    except TypeError:
        response = make_response(send_file(BytesIO(data.encode()),
                                           mimetype='text/plain',
                                           cache_timeout=0))
        response.headers['Content-Length'] = len(data.encode())
    return response


# Routes

@app.route('/', methods=['GET', 'POST'])
@protected
def main():
    """Main view.

    Includes output format and yearly settings.
    """
    CRM.refresh()

    return render_template('main.html',
                           user=session['logged_in'],
                           yearly_settings=app.config['YEARLY_SETTINGS'],
                           companies=CRM.data,
                           errors=CRM.errors)


@app.route('/contracts/<output_format>')
@app.route('/contracts/<output_format>/<int:id>')
@protected
def send_contracts(output_format, id=None):
    """Contract creation."""
    if id is None:
        selection = CRM.data
    else:
        selection = [CRM.data[id]]

    # Check if only tex is requested
    return_tex = (output_format == "tex")

    # Check if output format is email -> only single contract
    contract_only = (output_format == "email")

    # Get yearly settings
    yearly = app.config['YEARLY_SETTINGS']

    compiled = render_tex(
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

    return send(compiled)
