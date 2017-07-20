# Use Arch linux as base
# This is an easy way to get up-to- date TexLive
# If thats not needed the python image would suffice
FROM dock0/arch

# Set locale to something with utf-8 to avoid problems with files in python
ENV LANG=en_US.UTF-8

# Install python, tex (we also need latexextra) and uwsgi (requires gcc)
RUN pacman -Sy --noconfirm gcc \
    texlive-core texlive-bin texlive-latexextra \
    python python-pip
RUN pip install uwsgi


## TeX Setup

# Set HOME so we can use a local TEXMF tree for amivtex
ENV HOME /
COPY amivtex /texmf/tex/latex/amivtex

# Ensure the de_CH.utf-8 locale exists, needed for weekday mapping
RUN echo "de_CH.UTF-8 UTF-8" >> /etc/locale.gen ; locale-gen

## App Setup

COPY requirements.txt /requirements.txt
RUN pip install -r requirements.txt

COPY contractor /contractor
COPY app.py /app.py


## Configuration Files

# Environment variable for config, use path for docker secrets as default
ENV CONTRACTOR_CONFIG=/run/secrets/contractor_config


## Entrypoint and default command

# Expose port 80
EXPOSE 80

# Entrypoint script downloads non-public fonts at container start
COPY entrypoint.sh /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]

# Run uwsgi to serve the app
CMD ["uwsgi", \
"--http", "0.0.0.0:80", \
# More efficient usage of resources
"--processes", "4", \
# Otherwise uwsig will crash for bytesio
"--wsgi-disable-file-wrapper", \
# Allows accessing the app at / as well as /contractor
"--manage-script-name", \
"--mount", "/contractor=app:app"]
