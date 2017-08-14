# -*- coding: utf-8 -*-

"""The app."""

from os import getenv, getcwd, path
from datetime import datetime as dt
from io import BytesIO
from locale import setlocale, LC_TIME

from flask import (Flask, render_template, send_file, make_response, g)
from werkzeug import secure_filename
from jinjatex import Jinjatex
from jinja2 import PackageLoader, StrictUndefined

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


CRM = Importer(app.config['SOAP_USERNAME'], app.config['SOAP_PASSWORD'])

TEX = Jinjatex(tex_engine='xelatex',
               loader=PackageLoader('contractor', 'tex_templates'),
               undefined=StrictUndefined,
               trim_blocks=True)


TEX.env.filters.update({
    # Filters to parse date, including short one to list dates nicely
    # Format: Dienstag, 18.10.2016
    'fulldate': lambda date: dt.strftime(date, "%A, %d.%m.%Y"),
    # Format: Dienstag, 18.
    'shortdate': lambda date: dt.strftime(date, "%A, %d.")
})


# Get Auth
app.register_blueprint(api_auth)


def send(data):
    """Send data as file with headers to disable caching.

    We want the preview to be refreshed, so need to avoid browser caching.
    """
    try:
        filename = '%s.pdf' % g.get('company', 'contracts')
        response = make_response(send_file(BytesIO(data),
                                           mimetype='application/pdf',
                                           attachment_filename=filename,
                                           as_attachment=True,
                                           cache_timeout=0))
        response.headers['Content-Length'] = len(data)
    except TypeError:
        filename = '%s.tex' % g.get('company', 'source')
        response = make_response(send_file(BytesIO(data.encode()),
                                           mimetype='text/plain',
                                           attachment_filename=filename,
                                           as_attachment=True,
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
    (data, errors) = CRM.get_companies()

    return render_template('main.html',
                           user=g.username,
                           yearly=app.config['YEARLY_SETTINGS'],
                           companies=data,
                           errors=errors)


@app.route('/contracts/<output_format>')
@app.route('/contracts/<output_format>/<company_id>')
@protected
def send_contracts(output_format, company_id=None):
    """Contract creation."""
    if company_id is None:
        selection = CRM.get_companies()[0]  # select data of (data, errors)
    else:
        selection = [CRM.get_company(company_id)]
        g.company = secure_filename(selection[0]['companyname'])

    # Check if output format is email -> only single contract
    contract_only = (output_format == "email")

    # Get yearly settings
    yearly = app.config['YEARLY_SETTINGS']

    options = dict(
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
    )

    if (output_format == "tex"):
        return send(TEX.render_template('contract.tex', **options))
    else:
        return send(TEX.compile_template('contract.tex', **options))
