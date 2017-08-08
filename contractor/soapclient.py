# -*- coding: utf-8 -*-

"""Provide a connector to the AMIV sugarcrm."""

from amivcrm import AMIVCRM

from .choices import BoothChoice, PacketChoice

# Fields needed
FIELDS = [
    'id',
    'name',
    'assigned_user_name',
    'shipping_address_street',
    'shipping_address_street_2',
    'shipping_address_street_3',
    'shipping_address_street_4',
    'shipping_address_city',
    'shipping_address_state',
    'shipping_address_postalcode',
    'shipping_address_country',
    'tag1_c',
    'tag2_c',
    'tischgroesse_c',
    'packet_c',
    'mediapaket_c',
    'kategorie_c',
    'kontaktinfo_c'
]


class Importer(AMIVCRM):
    """Wrapper around CRM class to provide some data parsing."""

    def __init__(self, *args, **kwargs):
        super(Importer, self).__init__(*args, **kwargs)

    def _parse_response(self, response):
        """Parse data for the template.

        Args:
            response (dict): soap response as a dict

        Returns:
            dict: Data formatted for contract creation.
        """
        # Because of the way the amiv letter works, street and city must not be
        # None
        missing = [field for field in ['shipping_address_street',
                                       'shipping_address_postalcode',
                                       'shipping_address_city']
                   if response[field] is None]

        if len(missing) > 0:
            raise Exception("The following fields are missing: " +
                            ', '.join(missing))

        # Basic fields
        letterdata = {
            'id': response['id'],
            'amivrepresentative': response['assigned_user_name'],
            'companyname': response['name'],
            'companyaddress': response['shipping_address_street'],
            'companycity': ("%s %s" % (response['shipping_address_postalcode'],
                                       response['shipping_address_city'])),
        }

        # Get packets
        letterdata['media'] = (
            PacketChoice.media
            if response['mediapaket_c'] == "mediaPaket" else None)

        letterdata['business'] = (
            PacketChoice.business
            if response['packet_c'] == "business" else None)

        letterdata['first'] = (
            PacketChoice.first
            if response['packet_c'] == "first" else None)

        # Include country only if its not "Schweiz" and is specified
        country = response.get('shipping_address_country', "Schweiz")
        if country in ["Schweiz", None]:
            letterdata['companycountry'] = ""
        else:
            letterdata['companycountry'] = response['shipping_address_country']

        # Get fair days
        if (response['tag1_c'] == '1') and (response['tag2_c'] == '1'):
            # Both days
            n_days = 2
            letterdata['days'] = "both"
        else:
            # only one day
            n_days = 1

            # Check which day to print correct date on contract
            if response['tag1_c'] == '1':
                letterdata['days'] = "first"
            if response['tag2_c'] == '1':
                letterdata['days'] = "second"

        # Get booth choice
        # The field 'tischgroesse_c' is weirdly formatted.
        # 'kein' == small both
        # 'ein' == big booth
        # 'zwei' == startup
        if response['tischgroesse_c'] == 'kein':
            boothsize = "startup"
        elif response['tischgroesse_c'] == 'ein':
            boothsize = "small"
        elif response['tischgroesse_c'] == 'zwei':
            boothsize = "big"
        else:
            raise ValueError("Unrecognized value for 'tischgroesse_c': " +
                             response['tischgroesse_c'])

        # Get kategory, map katA to A etc
        mapping = {"kat" + letter: letter for letter in ['A', 'B', 'C']}
        category = mapping[response['kategorie_c']]

        # With size, category and days we can get the right choice
        letterdata['boothchoice'] = BoothChoice((boothsize, category, n_days))

        # Get person that did the fair signup:
        # Always at the beginning of the "kontaktinfo_c" field.
        # TODO (Alex): This seems a little hacked to me. As soon as we have a
        #   proper way to identify the main contact we should switch
        try:
            name = ''.join(response['kontaktinfo_c'].split(',')[0:2])
        except Exception:
            raise ValueError("Company representative could not be imported "
                             "from field 'kontaktinfo_c': with content "
                             "'%s'" % response.get('kontaktinfo_c', None))

        letterdata['companyrepresentative'] = name

        return letterdata

    def get_company(self, company_id):
        """Get data for a single company by id."""
        response = self.getentry("Accounts", company_id, select_fields=FIELDS)

        return self._parse_response(response)

    def get_companies(self):
        """Get the data from soap to fill in the template.

        Returns:
            tuple (list, dict): The list contains all succesfully imported
                company data.
                The dictionary contains all errors and has the schema:
                companyname: reason for error.
        """
        response = self.get("Accounts",
                            query="accounts_cstm.messeteilnahme_c = 1",
                            order_by="accounts.name",
                            select_fields=FIELDS)

        # Parse data to fit template and collect errors
        data = []
        errors = {}

        for company in response:
            try:
                parsed = self._parse_response(company)
            except Exception as e:
                errors[company['name']] = str(e)
            else:
                data.append(parsed)

        return (data, errors)
