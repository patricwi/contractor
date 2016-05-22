# -*- coding: utf-8 -*-

r"""Create the xelatex files.

The jinja environment and filters are based on a [flask snippet]
(http://flask.pocoo.org/snippets/55/) by Clemens Kaposi.

Some adjustments were made:
* Environment made independent from flask
* New filter to convert '\n' to '\\'

The render_tex function takes care of filename and directory things.
It plugs everything into the template and can return either the .tex file or
start latex and return the .pdf (also removes all non .pdf files)
"""

from jinja2 import Environment, PackageLoader, StrictUndefined
from datetime import datetime as dt
from werkzeug.utils import secure_filename
import subprocess
import os
import re

# Create the jinja env
texenv = Environment(loader=PackageLoader('contractor', 'tex_templates'))
texenv.block_start_string = '((*'
texenv.block_end_string = '*))'
texenv.variable_start_string = '((('
texenv.variable_end_string = ')))'
texenv.comment_start_string = '((='
texenv.comment_end_string = '=))'
texenv.undefined = StrictUndefined
texenv.trim_blocks = True


# Filters to turn newlines into latex \\ and to escape characters

def escape_tex(value):
    """Regex for most tex relevant things."""
    subs = (
        (re.compile(r'\\'), r'\\textbackslash'),
        (re.compile(r'([{}_#%&$])'), r'\\\1'),
        (re.compile(r'~'), r'\~{}'),
        (re.compile(r'\^'), r'\^{}'),
        (re.compile(r'"'), r"''"),
        (re.compile(r'\.\.\.+'), r'\\ldots'),
    )

    newval = value
    for pattern, replacement in subs:
        newval = pattern.sub(replacement, newval)
    return newval

texenv.filters['newline'] = lambda x: x.replace('\n', r'\\')
texenv.filters['l'] = escape_tex  # short name because used much

template = texenv.get_template("kontakt_contract_template.tex")


def render_tex(fairtitle="",
               president="",
               sender="",
               prices={},
               days={},
               letterdata=[],
               texpath='.',
               output_dir='.',
               contract_only=False,
               return_tex=False):
    """Render the template and return the filename.

    If return_tex is true, the raw tex will be returned and nothing rendered.

    Args:
        fairtitle (str): The title of the fair, e.g. "Kontakt.16"
        president (str): Current contract president. He/She will need to sign
            the contracts
        sender (str): The sender of the contracts, usually president or
            treasurer
        prices (dict): Needs the keys 'booths', 'media', 'business', 'first'
            booths has to be another dict with keys matching the keys for
            boothchoice. The prices itself are strings without 'CHF', i.e.
            {'media': '1234'}
        days (dict): The keys must be 'first', 'second', 'both' with the
            correct day(s) and date(s) as values (str)
        letterdata (list): List of parsed companies
        texpath (str): path to the `amivtex` folder on the system
        contract_only (bool): Return only the contract or cover letter plus
            contract in duplicate if False
        return_tex: If true, return tex source instead of pdf.
        output_dir (str): path where results will be stored.

    Returns:
        str: Filename of created file
    """
    rendered = template.render(fairtitle=fairtitle,
                               texpath=texpath,
                               president=president,
                               sender=sender,
                               prices=prices,
                               days=days,
                               letterdata=letterdata,
                               contract_only=contract_only)

    basename = 'contracts_' + dt.utcnow().strftime('%Y')

    # If a single contract is requested, add the company name to the filename
    if len(letterdata) == 1:
        basename += '_' + secure_filename(letterdata[0]['companyname'])

    filename = os.path.join(output_dir, basename)

    texname = filename + '.tex'

    with open(texname, 'wb') as f:
        f.write(rendered.encode('utf-8'))

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
        for ending in ['.tex', '.aux', '.log']:
            os.remove('%s%s' % (filename, ending))

        return basename + '.pdf'
