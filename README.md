# Contractor

Simple tool to create amiv job fair contracts from CRM data.

The interface itself is based mainly on [flask](flask.pocoo.org) and uses 
[bootstrap v4](v4-alpha.getbootstrap.com)

## Configuration

A config file with the SugarCRM
credentials is needed. Both username and password can be found in the
[AMIV Wiki](https://intern.amiv.ethz.ch/wiki/SugarCRM#SOAP).

Create the file, e.g. called `config.py`:

```python
SOAP_USERNAME = "..."
SOAP_PASSWORD = "..."
```

## Deployment with Docker

A docker image is available under `notspecial/contractor` in the docker hub.
Both the config file and a URL to access the (non-public) DINPro
fonts are needed to run it. The URL can also be found in the
[AMIV Wiki](https://wiki.amiv.ethz.ch/Corporate_Design#DINPro).
Put the URL into a file, e.g. called `font_url`, next to the config.

The most convenient way to pass the config and URL to the container is
using [Docker secrets](https://docs.docker.com/engine/swarm/secrets/#read-more-about-docker-secret-commands).

```bash
# Create secrets (read below if you want to name them differently)
docker secret create font_url font_url
docker secret create contractor_config config.py

# Create service (image will be pulled from docker hub)
# You can change the port from 300 to something else
docker service create \
    --name contractor \
    --secret contractor_config \
    --secret font_url \
    --publish 3000:8080 \
    notspecial/contractor

# Done! Check if everything works
curl 127.0.0.1:3000
```

The image assumes the files to be found at `/run/secrets/font_url` and
`/run/secrets/contractor_config`. Therefore, if you choose different
names for your secrets, set the environment
variables `CONTRACTOR_CONFIG` and `FONT_URL_FILE`
to the paths of your secrets (by default `/run/secrets/<secret_name>`).

## Development

For compilation of the tex files,
[amivtex](https://github.com/NotSpecial/amivtex) needs to be installed along
with the DINPro fonts. Take a look at the repository for instructions.

You need Python 3. The following commands create a virtual environment and
install dependencies:

```bash
# (If not yet done: clone and go into folder)
git clone https://github.com/NotSpecial/contractor
cd contractor

# Create and activate virtual environment
python -m venv env
source env/bin/activate

# Install dependencies
pip install -r requirements.txt

# Point app at config (optional, default is 'config.py' in current working dir)
export CONTRACTOR_CONFIG=...

# Start development server
export FLASK_APP=app.py
export FLASK_DEBUG=1
flask run
```

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
