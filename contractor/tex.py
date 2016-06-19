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

Important note on date output:

The filter will use the %A option in date formatting. This will set the week-
day depending on the locale. So make sure to actually set the locale to
something german so it fits the rest of the contract. Example:

>>> import locale
>>> locale.setlocale(locale.LC_TIME, "de_CH.UTF-8")

Done! (This is not done automatically since available locales are not
guaranteed)


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


# Add additional filters
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

texenv.filters.update({
    # Escaping for tex, short name because used often
    'l': escape_tex,

    # Escape newline
    'newline': lambda x: x.replace('\n', r'\\'),

    # Filters to parse date, including short one to list dates nicely
    # Format: Dienstag, 18.10.2016
    'fulldate': lambda date: dt.strftime(date, "%A, %d.%m.%Y"),
    # Format: Dienstag, 18.
    'shortdate': lambda date: dt.strftime(date, "%A, %d.")
})


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
        str: filename (including path) to output
    """
    # We need to make sure the tex path ends in a slash, use os.path for that
    texpath = os.path.join(texpath, '')

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
        # Capture output with PIPE (just to keep console clean)
        # Check true requires status code 0
        subprocess.run(commands, stdout=subprocess.PIPE, check=True)
        subprocess.run(commands, stdout=subprocess.PIPE, check=True)

        # Clean up
        for ending in ['.tex', '.aux', '.log']:
            os.remove('%s%s' % (filename, ending))

        return filename + '.pdf'
