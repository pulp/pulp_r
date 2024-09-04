#!/bin/bash

set -e

# Check if podman is available in the user's path
if command -v podman &> /dev/null
then
    echo "Warning: The openapi-generator images used in pulp-openapi-generator might only be compiled for x86_64."
    echo "Please ensure that podman is set up to run amd64 (x86_64) containers, or temporarily remove it from your path."
    echo "The pulp-openapi-generator script defaults to podman if it's available."
    echo
fi

# Check if the required directories exist in the parent directory
if [ ! -d "../oci_env" ]; then
    echo "Cloning oci_env repository..."
    git clone https://github.com/pulp/oci_env.git ../oci_env
fi

if [ ! -d "../pulp-openapi-generator" ]; then
    echo "Cloning pulp-openapi-generator repository..."
    git clone https://github.com/pulp/pulp-openapi-generator.git ../pulp-openapi-generator
fi

# Copy environment file
cp ./compose.env ../oci_env/compose.env
cd ../oci_env || exit

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate the virtual environment
source venv/bin/activate

# Install packages
pip3 install -e client
pip install pulp-smash

# Tear down existing services and volumes
oci-env compose down

# Build images and start services
oci-env compose build
oci-env compose up

# Run database migrations (commented out)
# oci-env compose exec pulp django-admin makemigrations
# oci-env compose exec pulp django-admin migrate

# Example to show how to access API with authentication (commented out)
# curl -u admin:password http://localhost:8000/pulp/api/v3/status/ | jq '.'

# Create new remote
# curl -u admin:password -X POST "http://localhost:8000/pulp/api/v3/remotes/r/r/" \
#      -H "Content-Type: application/json" \
#      -d '{
#            "name": "CRAN Remote",
#            "url": "https://cran.r-project.org/src/contrib/PACKAGES.gz",
#            "policy": "on_demand"
#          }'


# Create new repository
# curl -u admin:password -X POST "http://localhost:8000/pulp/api/v3/repositories/r/r/" \
#      -H "Content-Type: application/json" \
#      -d '{
#            "name": "CRAN Repository",
#            "description": "Repository for CRAN packages"
#          }'


# Sync repository
# curl -u admin:password -X POST "http://localhost:8000/pulp/api/v3/repositories/r/r/<repository-href>/sync/" \
#      -H "Content-Type: application/json" \
#      -d '{
#            "remote": "/pulp/api/v3/remotes/r/r/<remote-href>/",
#            "mirror": true
#          }'

# Create a publication from the synced repository version
# curl -u admin:password -X POST "http://localhost:8000/pulp/api/v3/publications/r/r/" \
# -H "Content-Type: application/json" \
# -d '{ "repository_version": "/pulp/api/v3/repositories/r/r/<repository-href>/versions/1/" }'

# Create a distribution from the publication
# curl -u admin:password -X POST "http://localhost:8000/pulp/api/v3/distributions/r/r/" \
# -H "Content-Type: application/json" \
# -d '{
#       "name": "CRAN Distribution",
#       "base_path": "r/src/contrib",
#       "publication": "/pulp/api/v3/publications/r/r/<publication-href>/"
#     }'