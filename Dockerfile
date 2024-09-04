ARG FROM_TAG="3.55.1"

FROM pulp/pulp-ci-centos9:${FROM_TAG}

ARG FROM_TAG
ARG PULP_PYTHON_VERSION="3.12.1"

# Unlike Pulp-minimal (Single Process), pulp-ci-centos (Multi Process) does not come pre-installed with Pulp Python Plugin
RUN pip3 install --upgrade \
    git+https://github.com/pulp/pulp_python@${PULP_PYTHON_VERSION} \
    httpx && \
    rm -rf /root/.cache/pip

# Install development dependencies
RUN pip3 install --upgrade pip setuptools wheel

# Install pulp_r in editable mode
COPY . /app/pulp_r
WORKDIR /app/pulp_r
RUN pip3 install -e .

# Create necessary directories and generate encryption key
RUN mkdir -p /etc/pulp/certs && \
    openssl rand -base64 32 > /etc/pulp/certs/database_fields.symmetric.key && \
    chmod 640 /etc/pulp/certs/database_fields.symmetric.key && \
    chown root:pulp /etc/pulp/certs/database_fields.symmetric.key

# Ensure the settings module is set and add /etc/pulp to PYTHONPATH
ENV DJANGO_SETTINGS_MODULE=pulpcore.app.settings

USER pulp:pulp

RUN PULP_STATIC_ROOT=/var/lib/operator/static/ PULP_CONTENT_ORIGIN=localhost \
    /usr/local/bin/pulpcore-manager collectstatic --clear --noinput --link

USER root:root

CMD ["/init"]