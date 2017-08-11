FROM notspecial/amivtex

# Ensure the de_CH.utf-8 locale exists, needed for weekday mapping
RUN apt-get update && apt-get install -y locales && \
    locale-gen de_CH.UTF-8 && \
    rm -rf /var/lib/apt/lists/*

# Install uwsgi (build tools are required)
RUN apt-get update && apt-get install -y build-essential && \
    pip install uwsgi && \
    rm -rf /var/lib/apt/lists/* && \
    apt-get purge -y --auto-remove build-essential

COPY requirements.txt /requirements.txt
RUN pip install -r requirements.txt

COPY contractor /contractor
COPY app.py /app.py

# Environment variable for config, use path for docker secrets as default
ENV CONTRACTOR_CONFIG=/run/secrets/contractor_config

# Run uwsgi to serve the app on port 80
EXPOSE 80
CMD ["uwsgi", \
"--http", "0.0.0.0:80", \
# More efficient usage of resources
"--processes", "4", \
# Otherwise uwsig will crash with bytesio
"--wsgi-disable-file-wrapper", \
# Exit if app cannot be started, e.g. if config is missing
"--need-app", \
# Allows accessing the app at / as well as /contractor
"--manage-script-name", \
"--mount", "/contractor=app:app"]
