# -*- coding: utf-8 -*-

"""App settings."""

# All SOAP settings except password
SOAP_URL = "https://people.ee.ethz.ch/~amivkt/crm/service/v2/soap.php?wsdl"
SOAP_APPNAME = "AMIV Kontakt: Internal: Customer Relationship Management"
SOAP_USERNAME = "soap"

# URL for amivapi
AMIVAPI_URL = 'https://nicco.io/amiv/'

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
