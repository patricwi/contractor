# -*- coding: utf-8 -*-

"""Tests for the tex creation.

Note: This will test creation for input combination, so it can take a while!

We can not check if the pdfs are correctly created, but we can assert the
following:

* All contract and output combinations work without crashing (smoke testing)
* There will be a file created in the end
* There will be exactly one file (cleanup works)

This test must be run from the same directory where the "amivtex" directory is!
"""

from unittest import TestCase
from tempfile import TemporaryDirectory
import os
from subprocess import CalledProcessError
from pprint import pformat
from itertools import count, chain
from datetime import datetime as dt

from contractor.tex import render_tex
from contractor.choices import BoothChoice, PacketChoice


class TEXTest(TestCase):
    """Tess class for tex tests."""

    output_formats = ["mail", "email", "tex"]

    def _data(self):
        """Get all different combinations for companies.

        TODO: Maybe some of this can be arranged nicer.
        """
        # Booth choice
        for booth in BoothChoice:

            # days
            if booth.days == 1:
                daychoice = ['first', 'second']
            else:
                daychoice = ['both']

            for days in daychoice:
                # packets (they are exclusive since first includes business)
                for (business, first) in [(PacketChoice.business, None),
                                          (None, PacketChoice.first),
                                          (None, None)]:
                    for media in [PacketChoice.media, None]:
                        # Companycountry can either be empty (Switzerland)
                        # Or will be specified (all other countries)
                        for companycountry in ['', 'Faraway']:
                            yield {
                                # Data without distinct choices.
                                # Adding some umlauts to be sure that
                                # wont crash anything
                                # Although we have no way to check if they are
                                # displayed correctly
                                'amivrepresentative': 'Pablö',

                                'companyrepresentative': 'Sr. Senior',
                                'companyname': 'Täst Inc.',
                                'companyaddress': "l'Teststrüüt 5",
                                'companycity': "1234 Testingtàn",

                                'companycountry': companycountry,

                                # booth and day
                                'boothchoice': booth,
                                'days': days,

                                # packets
                                'media': media,
                                'business': business,
                                'first': first,
                            }

    def _loop_create_contract_combinations(self, data):
        """Try to create all contracts at once (in all output formats).

        Assert that exactly one file is created.

        Args:
            data (list): companydata to create contract for
        """
        counter = count()

        # Loop through format
        for format in self.output_formats:
            contract_only = (format == "email")
            return_tex = (format == "tex")

            # Create a new temp dir every round so no
            # Data gets carried over
            with TemporaryDirectory(prefix="contractor") as dir:
                render_tex(
                    letterdata=data,
                    texpath="./amivtex",
                    output_dir=dir,
                    contract_only=contract_only,
                    return_tex=return_tex,
                    fairtitle="Superfair",
                    president="El Presidente",
                    sender="Herr Handlanger",
                    # Generate prices for all choicesin a loop with
                    # Counter as a price
                    prices={
                        choice.name: next(counter) for choice in chain(
                            BoothChoice, PacketChoice)
                    },
                    days={
                        'first': dt(2016, 10, 18),
                        'second': dt(2016, 10, 19),
                    },
                )

                # Only one file (pdf or tex) is created in the end
                n_files = len(os.listdir(dir))
                self.assertTrue(n_files == 1)

    def test_create_all(self):
        """Try to create all contracts at once (in all output formats)."""
        # All companies
        try:
            self._loop_create_contract_combinations([i for i in self._data()])
        except CalledProcessError:
            msg = ("Render tex failed for creation of all contracts.")
            raise Exception(msg)

    def test_create_single(self):
        """Try to create all contracts separately (in all output formats)."""
        for company in self._data():
            try:
                self._loop_create_contract_combinations([company])
            except CalledProcessError:
                msg = ("Rendering tex failed for this data:\n" +
                       pformat(company))
                raise Exception(msg)
