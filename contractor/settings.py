# -*- coding: utf-8 -*-

"""App settings."""

from datetime import datetime as dt

# All SOAP settings except password
SOAP_URL = "https://people.ee.ethz.ch/~amivkt/crm/service/v2/soap.php?wsdl"
SOAP_APPNAME = "AMIV Kontakt: Internal: Customer Relationship Management"
SOAP_USERNAME = "soap"

# URL for amivapi
AMIVAPI_URL = 'https://nicco.io/amiv/'

# Folders
TEX_DIR = "/home/alex/amivtex/"

# All different options in neat order (used to create form)
CHOICES = ['sA1', 'sA2', 'sB1', 'sB2',
           'bA1', 'bA2', 'bB1', 'bB2',
           'su1', 'su2',
           'media', 'business', 'first']

# Additional fulltext for website formatting
FULLTEXT = {
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
    # startups,
    'su1': 'start-up, one day',
    'su2': 'start-up, two days',
    # packets
    'media': 'media packet',
    'business': 'business packet',
    'first': 'first packet'
}

# Defaults for yearly settings, from the 2016 fair
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
