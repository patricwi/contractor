# -*- coding: utf-8 -*-

"""Create the xelatex files."""

from jinja2 import Environment, PackageLoader
from datetime import datetime as dt
from werkzeug.utils import secure_filename
import subprocess
import os

# Create the jinja env
texenv = Environment(loader=PackageLoader('contractor', 'tex_templates'))
texenv.block_start_string = '((*'
texenv.block_end_string = '*))'
texenv.variable_start_string = '((('
texenv.variable_end_string = ')))'
texenv.comment_start_string = '((='
texenv.comment_end_string = '=))'

template = texenv.get_template("kontakt_contract_template.tex")


def render_tex(president,
               sender,
               prices,
               letterdata,
               texpath='.',
               output_dir='.',
               return_tex=False):
    """Render the template and return the filename.

    If return_tex is true, the raw tex will be returned and nothing rendered
    """
    rendered = template.render(texpath=texpath,
                               president=president,
                               sender=sender,
                               prices=prices,
                               letterdata=letterdata)

    basename = 'contracts_' + dt.utcnow().strftime('%Y')

    # If a single contract is requested, add the company name to the filename
    if len(letterdata) == 1:
        basename += '_' + secure_filename(letterdata[0]['companyname'])

    filename = os.path.join(output_dir, basename)

    texname = filename + '.tex'

    with open(texname, 'w') as f:
        f.write(rendered)

    if return_tex:
        return texname
    else:
        commands = ["xelatex",
                    "-output-directory", output_dir,
                    "-interaction=batchmode", texname]

        # sic! needs to be run twice to insert references
        # Check call ensures status code 0
        subprocess.check_call(commands)
        subprocess.check_call(commands)

        # Clean up
        # for ending in ['.tex', '.aux', '.log']:
        #     os.remove('%s%s' % (filename, ending))

        return basename + '.pdf'
