# -*- coding: utf-8 -*-

"""App settings."""

from datetime import datetime as dt

# URL for amivapi
AMIVAPI_URL = 'https://amiv-api.ethz.ch/'

# Yearly fair settings, move to CRM as soon as possible
YEARLY_SETTINGS = {
    'fairtitle': 'AMIV Kontakt.17',
    # president of kontakt team
    'president': 'Celina Rhonheimer',
    # Sender of Contracts, usually treasurer of kontakt team
    'sender': 'Patrick Wintermeyer\nQuästor Kommission Kontakt',

    # Fair days,
    'days': {
        'first': dt(2017, 10, 17),
        'second': dt(2017, 10, 18),
    },

    # Prices, all in francs
    'prices': {
        # Small
        'sA1': '1100',
        'sA2': '2400',
        'sB1': '850',
        'sB2': '2000',
        # Big
        'bA1': '2300',
        'bA2': '4800',
        'bB1': '1800',
        'bB2': '3800',
        # Startups
        'su1': '300',
        'su2': '750',
        # Pakets
        'media': '850',
        'business': '1500',
        'first': '2500',
    },
}
