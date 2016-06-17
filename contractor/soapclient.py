# -*- coding: utf-8 -*-

"""Provide a connector to the AMIV sugarcrm.

sugarcrm provides a SOAP and a REST api. At the time this tool was written
the REST api was unfortunately not available. Therefore SOAP is used.

The python library suds is used, more exactly the fork by (jurko)
[https://bitbucket.org/jurko/suds].

Information for the AMIV side can be found in the (wiki)
[intern.amiv.ethz.ch/wiki/SugarCRM#SOAP]. Although written for php the
procedures can be copied without to much trouble.


This file provides two classes, the first being a more generic wrapper for the
amiv crm soap, the second being basically a wrapper around the first tailored
to the contractor flask app.

If you want to write your own python app using crm, you'll be all set copying
the first class. Should it be used a lot it might be worth considering to move
the connector to it's own project.

In the wiki you will notice that the password in php is `md5('somestring')`.
To get the python equivalent of this, you need:

```
from hashlib import md5
password = md5(b'somestring').hexdigest()

```
Note: This is python 3.5. In earlier versions the import is different.
    Furthermore notice that md5 requires the string as binary, so don't
    forget the `b` prefix.
"""

from suds.client import Client
from contextlib import contextmanager
import html


class AMIVCRMConnector(object):
    """The connector class.

    If you want to implement your own app you can just copy this class.
    In the (wiki)[intern.amiv.ethz.ch/wiki/SugarCRM#SOAP] you will find the
    url, appname, username and password.

    You can use the session context to easily manage the connection.

    Example usage:

    ```
    crm = AMIVCRMConnector(...)
    with crm.session():
        crm.get_full_entry_list(...)
    ```

    Args:
        url (str): CRM url
        appname (str): the soap appname
        username (str): the soap username
        password (str): the soap password
    """

    def __init__(self, url, appname, username, password):
        """Init."""
        self.client = Client(url)
        self.session_id = None
        self.appname = appname
        self.username = username
        self.password = password

    def login(self):
        """Login.

        Args:
            username (str): sugarcrm soap username
            password (str): sugarcrm soap password, md5 hashed
        """
        auth = {'user_name': self.username,
                'password': self.password}

        self.session_id = self.client.service.login(auth, self.appname).id

    def check_session(self):
        """Raise exception if session is missing."""
        if self.session_id is None:
            raise RuntimeError("No session, you need to log in!")

    def logout(self):
        """Logout."""
        self.check_session()

        self.client.service.logout(self.session_id)
        self.session_id = None

    @contextmanager
    def session(self):
        """Session context.

        Use in a with statement. Login will be performed on entering and
        logout on leaving the block

        Args:
            username (str): sugarcrm soap username
            password (str): sugarcrm soap password, md5 hashed
        """
        self.login()
        yield
        self.logout()

    def _safe_str(self, item):
        """Escape strings.

        First of all if its a string it is actually a suds Text class.
        In some environments this seems not to play along well with unicode.
        (Although it is a subclass of str)

        Therefore explicitly cast it to a str and unescape html chars.

        Possible improvement: Check if soap returns anything else but strings.
        If not, the if statement might be scraped.

        Args:
            item: The object to make safe. Changed only if subclass of str.
        """
        if isinstance(item, str):
            return html.unescape(str(item))
        else:
            return item

    def parse(self, response):
        """Turn results into list of dicts."""
        return ([{item.name: self._safe_str(item.value)
                for item in entry.name_value_list}
                for entry in response.entry_list])

    def get_full_entry_list(self, module_name="", query="", order_by="",
                            select_fields=[]):
        """Get list of all entries.

        Because the server ignores the 'max_results' parameter,
        we need this workaround.

        Args:
            module_name (str): crm module
            query (str): SQL query string
            order_by (str): SQL order by string
            select_fields (list): fields the crm should return

        Returns:
            list: list of dictionaries with result data
        """
        self.check_session()

        results = []

        # Collect results
        offset = 0
        while True:
            response = self.client.service.get_entry_list(
                session=self.session_id,
                module_name=module_name,
                query=query,
                order_by=order_by,
                offset=offset,
                select_fields=select_fields)
            # Check if end is reached
            if response.result_count == 0:
                break
            else:
                results += self.parse(response)
                offset = response.next_offset

        return results


class CRMImporter(object):
    """Handling connection and parsing of soap data.

    This class is specific for the kontakt contract app.

    Args:
        app (Flask): The flask object.
    """

    def __init__(self, app=None):
        """Init."""
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        """Init app.

        Read soap settings and get data.

        Args:
            app (Flask): The flask object.
        """
        try:
            url = app.config['SOAP_URL']
            appname = app.config['SOAP_APPNAME']
            username = app.config['SOAP_USERNAME']
            password = app.config['SOAP_PASSWORD']
        except:
            # In python 3, this will "reraise" - the old stacktrace won't
            # be lost
            raise Exception("SOAP login data missing. "
                            "Call setup.py to create.")

        self.client = AMIVCRMConnector(url, appname, username, password)

        # Get initial data
        self.refresh()

    def refresh(self):
        """Connect to CRM and refresh company data."""
        (self.data, self.errors) = self._get_contract_data()

    def _parse_company_response(self, response):
        """Parse data for the template.

        Args:
            response (dict): soap response as a dict

        Returns:
            dict: Data formatted for contract creation.
        """
        # Parse straighforward fields
        letterdata = {
            'amivrepresentative': response['assigned_user_name'],
            'companyname': response['name'],
            'companyaddress': response['shipping_address_street'],
            'companycity': ("%s %s" % (response['shipping_address_postalcode'],
                                       response['shipping_address_city'])),
            'media': response['mediapaket_c'] == "mediaPaket",
            'business': response['packet_c'] == "business",
            'first': response['packet_c'] == "first"
        }

        # Include country only if its not "Schweiz" and is specified
        if response.get('shipping_address_country', "Schweiz") == "Schweiz":
            letterdata['companycountry'] = ""
        else:
            letterdata['companycountry'] = response['shipping_address_country']

        # Get fair days
        if (response['tag1_c'] == '1') and (response['tag2_c'] == '1'):
            # Both days
            twodays = True
            letterdata['days'] = "both"
        else:
            # only one day, which one?
            twodays = False
            if (response['tag1_c'] == '1'):
                letterdata['days'] = "first"
            if (response['tag2_c'] == '1'):
                letterdata['days'] = "second"

        # Specify two helper functions to determine booth
        def is_small_booth():
            """Check if booth is small.

            The field 'tischgroesse_c' is weirdly formatted.

            a value of 'kein' means small both,
            a value of 'ein' means big booth.
            """
            if response['tischgroesse_c'] == 'kein':
                return True
            elif response['tischgroesse_c'] == 'ein':
                return False
            else:
                raise ValueError("Unrecognized value for 'tischgroesse_c': " +
                                 response['tischgroesse_c'])

        def get_booth_choice():
            """Get booth choice.

            katA is category A,
            katB is category B,
            katC means startup
            """
            if response['kategorie_c'] == 'katA':
                if is_small_booth():
                    if twodays:
                        # Small booth, kat A, 2 days
                        return 'sA2'
                    else:
                        # Small booth, kat A, 1 day
                        return 'sA1'
                else:
                    if twodays:
                        # Big booth, kat A, 2 days
                        return 'bA2'
                    else:
                        # Big booth, kat A, 1 day
                        return 'bA1'
            elif response['kategorie_c'] == 'katB':
                if is_small_booth():
                    if twodays:
                        # Small booth, kat B, 2 days
                        return 'sB2'
                    else:
                        # Small booth, kat B, 1 day
                        return 'sB1'
                else:
                    if twodays:
                        # Big booth, kat B, 2 days
                        return 'bB2'
                    else:
                        # Big booth, kat B, 1 day
                        return 'bB1'
            elif response['kategorie_c'] == 'katC':
                # katC means startup, only day info required
                if twodays:
                    # Startup, two days
                    return 'su2'
                else:
                    # Startup, one day
                    return 'su1'
            else:
                raise ValueError("Unrecognized value for 'kategorie_c' " +
                                 response['kategorie_c'])

        # Get booth choice and boothinfo
        letterdata['boothchoice'] = get_booth_choice()

        try:
            if is_small_booth():
                letterdata['boothinfo'] = 'small'
            else:
                letterdata['boothinfo'] = 'big'
        except ValueError:
            # Exception is raised for startups, no booth info
            letterdata['boothinfo'] = ''

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

    def _get_contract_data(self):
        """Get the data from soap to fill in the template.

        Returns:
            tuple (list, dict): The list contains all succesfully imported
                companies formatted for the latex template.
                The dictionary contains all errors and has the schema:
                companyname: reason for error.
        """
        # Fields needed

        fields = [
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

        # Get data
        with self.client.session():
            results = self.client.get_full_entry_list(
                module_name="Accounts",
                query="accounts_cstm.messeteilnahme_c = 1",
                order_by="accounts.name",
                select_fields=fields)

        # Parse data to fit template and collect errors
        data = []
        errors = {}

        for company in results:
            try:
                parsed = self._parse_company_response(company)
            except Exception as e:
                errors[company['name']] = str(e)
            else:
                data.append(parsed)

        return (data, errors)
