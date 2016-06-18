"""Setup script."""

import os
from locale import setlocale, LC_TIME
from hashlib import md5
from base64 import b64encode
from ruamel import yaml
import click

# Find the directory where the script is placed
app_root = os.path.dirname(os.path.realpath(__file__))


@click.command()
@click.option('--soapuser',
              prompt="Enter the soap username",
              default="soap")
@click.option('--soappass',
              prompt="Enter the soap password (plain, NOT md5 hashed)")
@click.option('--storage-dir',
              prompt="Enter the directory for contract storage",
              default=os.path.join(app_root, "contracts"))
@click.option('--settings-dir',
              prompt="Enter the directory for yearly settings",
              default=app_root)
@click.option('--locale',
              prompt="Enter the locale to use. Must be a locale that exists "
                     "on the system and uses german weekdays.",
              default="de_CH.utf-8")
def init(soapuser, soappass, storage_dir, settings_dir, locale):
    """Create user config and directories needed.

    Args:
        soapuser (str): User for soap login, defaults to 'soap'
        soappass (str): Password for soap login
        storage_dir (str): Dir to store contracts etc.
        settings_dir (str): Dir to store yearly settings.
        locale_setting (str): The locale setting. Must use german weekdays,
            otherwise contracts will not be rendered properly
    """
    # Check locale
    click.echo('Checking locale...')
    setlocale(LC_TIME, locale)

    # Generate secret key and encode the bytes
    click.echo('Generate secret key...')
    key = b64encode(os.urandom(256)).decode('utf_8')

    # Create config dict and save as json
    click.echo('Save settings to config.yml...')
    config = {
        'SOAP_USERNAME': soapuser,
        'SOAP_PASSWORD': md5(soappass.encode('UTF-8')).hexdigest(),
        'STORAGE_DIR': storage_dir,
        'SETTINGS_DIR': settings_dir,
        'SECRET_KEY': key,
        'LOCALE': locale
    }

    config_file = os.path.join(app_root, 'config.yml')

    with open(config_file, 'w') as f:
        # setting default_flow_style to False will make the file more readable
        yaml.dump(config, f, default_flow_style=False)

    # Set up directories for app data and output storage
    click.echo("Creating directories...")
    for directory in storage_dir, settings_dir:
        os.makedirs(directory, exist_ok=True)

    click.echo("Done!")

if __name__ == '__main__':
    init()
