#!/bin/bash

# Copy environment file
cp ./compose.env ../oci_env/compose.env

cd ../oci_env || exit

# Activate the virtual environment
source venv/bin/activate

# Install packages
pip3 install -e client
pip install pulp-smash

# Tear down existing services and volumes
oci-env compose down --volumes

# Build images and start services
oci-env compose build
oci-env compose up

# Run database migrations (commented out)

# oci-env compose exec pulp django-admin makemigrations

# oci-env compose exec pulp django-admin migrate

# Example to show how to access API with authentication (commented out)
# curl -u admin:password http://localhost:5001/pulp/api/v3/status/ | jq '.'