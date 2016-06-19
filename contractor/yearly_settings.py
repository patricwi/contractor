# -*- coding: utf-8 -*-

"""Yearly adjustable settings.

Provides a Yearly Settings Form that will handle saving and loading data to/
from the disk.

The settings are saved using yaml (instead of json), since it can handle
date objects without additional parsing.

This file provides basically two things:

1. The `YearlySettingsForm` class
2. The `get_yearly_settings` function to load the data easily

"""

from ruamel import yaml
from datetime import datetime as dt
from itertools import chain

from flask_wtf import Form
from wtforms import StringField, TextAreaField, FormField
from wtforms.validators import InputRequired
from wtforms.fields.html5 import IntegerField, DateField

from .choices import BoothChoice, PacketChoice

# Date format that works well with html5 date input field
DATEFORMAT = "%Y-%m-%d"
DATEPLACEHOLDER = "yyyy-mm-dd"

# Defaults for yearly settings, from the 2016 fair
# This is just for convenience. With those defaults we never have to deal with
# missing yearly data
DEFAULT_YEARLY_SETTINGS = {
    'fairtitle': 'AMIV Kontakt.16',
    'president': 'Alexander Ens',
    'sender': 'Pascal Gutzwiller\nQuästor Kommission Kontakt',

    # Fair days,
    'days': {
        'first': dt(2016, 10, 18),
        'second': dt(2016, 10, 19),
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


def load_yearly_settings():
    """Get yearly settings from defaults and file.

    First import defaults from app_config.

    Then try to load the yearly_settings.yml file and update data if this works
    """
    settings = DEFAULT_YEARLY_SETTINGS

    try:
        with open('yearly_settings.yml', 'r') as f:
            settings.update(yaml.load(f))
    except OSError:
        # No updates from file
        pass

    return settings


class _PriceField(IntegerField):
    """Special field that can be recognized in the templated for formatting."""

    pass


class _PricesSubForm(Form):
    """Form for prices, will be part of main form.

    Empty form so far, we will add the attributes in a loop since they are
    many and all look the same.
    """

    pass

# Iterate over enum. While they can be used as dict keys, we can't use them
# as attribute name. So we use the name field of the enum as field name
for choice in chain(BoothChoice, PacketChoice):
    setattr(_PricesSubForm,
            choice.name,
            _PriceField(label=str(choice),
                        validators=[InputRequired()],
                        render_kw={'placeholder': '1234'}))


class _DaysSubForm(Form):
    """Form for days, will be part of main form."""

    first = DateField(label='First Day of Fair',
                      format=DATEFORMAT,
                      validators=[InputRequired()],
                      render_kw={'placeholder': DATEPLACEHOLDER})
    second = DateField(label='Second Day of Fair',
                       format=DATEFORMAT,
                       validators=[InputRequired()],
                       render_kw={'placeholder': DATEPLACEHOLDER})


class YearlySettingsForm(Form):
    """Form to change yearly settings for the fair.

    Auto loads defaults unless told not to.
    Also provides a `validate_and_save` method that will save yearly
    settings to a file if the form is valid.
    """

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

    prices = FormField(_PricesSubForm)
    days = FormField(_DaysSubForm)

    def __init__(self, auto=True, *args, **kwargs):
        """Load defaults unless told not to."""
        # Autoloader will get general defaults from settings and overwrite from
        # yearly_settings file if fould
        if auto:
            defaults = load_yearly_settings()
        else:
            defaults = {}

        # User provided defaults, if any
        defaults.update(kwargs)

        super().__init__(*args, **defaults)

    def validate_and_save(self):
        """Save settings to file if valid.

        Uses Flask-WTFs validate_on_submit to determine if the request is
        POST and data is valid.
        """
        if self.validate_on_submit():
            with open('yearly_settings.yml', 'w') as f:
                # setting default_flow_style to False will make the file more
                # readable
                yaml.dump(self.data, f, default_flow_style=False)
