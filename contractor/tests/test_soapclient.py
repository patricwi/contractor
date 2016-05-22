# -*- coding: utf-8 -*-

"""Simple tests to check basic functionality of the CRM connection.

We have no way of verifying imported data, but we will assert all we can:

* Are the necessary config values set?
* Can the connector establish a connection?
* Can the import be done without crashing? Are some companies imported?
"""

from unittest import TestCase
from app import app
from contractor.soapclient import CRMImporter


class CRMTest(TestCase):
    """CRM test class."""

    def test_config(self):
        """Check app config."""
        self.assertIn('SOAP_URL', app.config)
        self.assertIn('SOAP_APPNAME', app.config)
        self.assertIn('SOAP_USERNAME', app.config)
        self.assertIn('SOAP_PASSWORD', app.config)

    def test_soap_server_reachable(self):
        """Try to create a connector.

        Raises exception if server is not available.
        """
        CRMImporter(app)

    def test_import(self):
        """Call the import function.

        Check if anything is imported.
        """
        conn = CRMImporter(app)

        (companies, errors) = conn.get_contract_data()

        self.assertTrue(len(companies) > 0)
