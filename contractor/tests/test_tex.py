# -*- coding: utf-8 -*-

"""Tests for the tex creation.

Note: This will test creation for every company, so it can take a while!

We can not check if the pdfs are correctly created, but we can assert the
following:

* All contract and output combinations work without crashing
* There will be a file created in the end
* There will be exactly one file (cleanup works)



"""

from unittest import TestCase
from tempfile import TemporaryDirectory
import os
from subprocess import CalledProcessError

from app import app
from contractor.tex import render_tex

TEX_DIR = app.config['TEX_DIR']  # Only thing needed from actual config


class TEXTest(TestCase):
    """Tess class for tex tests."""

    output_formats = ["mail", "email", "tex"]

    def _loop_create_contract_combinations(self, id=None):
        """Try to create all contracts at once (in all output formats).

        Assert that exactly one file is created.

        Args:
            id: the id to call send_contracts with
        """
        # Loop through format
        for format in self.output_formats:
            contract_only = (format == "email")
            return_tex = (format == "tex")

            # Create a new temp dir every round so no
            # Data gets carried over
            with TemporaryDirectory(prefix="contractor") as dir:
                if id is None:
                    selection = app.config['LETTERDATA']
                else:
                    selection = [app.config['LETTERDATA'][id]]

                try:
                    render_tex(
                        letterdata=selection,
                        texpath=TEX_DIR,
                        output_dir=dir,
                        contract_only=contract_only,
                        return_tex=return_tex,
                        fairtitle="Superfair",
                        president="El Presidente",
                        sender="Herr Handlanger",
                        prices={
                            'booths': {
                                'sA1': '1',
                                'sA2': '2',
                                'sB1': '3',
                                'sB2': '4',
                                'bA1': '5',
                                'bA2': '6',
                                'bB1': '7',
                                'bB2': '8',
                                'su1': '9',
                                'su2': '10',
                            },
                            'media': '11',
                            'business': '12',
                            'first': '13',
                        },
                        days={
                            'first': 'Someday',
                            'second': 'Other doy',
                            'both': 'All the days!'
                        }
                    )
                except CalledProcessError:
                    # Make sure directory still

                    # Add id to message for easier debugging
                    if id is None:
                        msg = ("Render tex failt for all contracts.")
                    else:
                        msg = ("Rendering tex failed for company: " +
                               str(id))
                    raise Exception(msg)

                # Only one file (pdf or tex) is created in the end
                n_files = len(os.listdir(dir))
                self.assertTrue(n_files == 1)

                # Clean up, remove temp dir
                # rmtree(dir)

    def test_create_all(self):
        """Try to create all contracts at once (in all output formats)."""
        # id is None -> all companies
        self._loop_create_contract_combinations(id=None)

    def test_create_single(self):
        """Try to create all contracts separately (in all output formats)."""
        for i in range(len(app.config['LETTERDATA'])):
            self._loop_create_contract_combinations(id=i)
