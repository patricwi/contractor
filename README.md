# Contractor

Simple tool to create amiv kontakt contracts from CRM

This app uses the [suds fork by jurko](https://bitbucket.org/jurko/suds) to
connect to the AMIV sugarCRM with SOAP.

It this data to fill jinja2 templates which are then passed to latex.

*Important:* The amiv tex package needs a quite new version of latex, you can
run the tests to make sure everything compiles.

The interface itself is based on [flask](flask.pocoo.org) and uses 
[flask-wtforms](flask-wtf.readthedocs.org) and 
[bootstrap v4](v4-alpha.getbootstrap.com)

## Setup

Before you can run anything, you need to create a user config and storage
directories.

You can simply call

```
python init.py
```

and this will be taken care of. You also need to input a locale that works on 
your system. It is important that the locale provides german weekdays, or else
the contracts will look bad.

## Testing

There are some tests implemented, especially for tex creation and soap
connection. Use `py.test` to run them.

```
> pip install pytest
> py.test
```

The tests musst be run from the root directory (where the amivtex dir is) or 
the tex tests won't be able to find the .tex source.

*Beware:* The tex test tries a **lot** of choices and takes a lot of time to
finish!
