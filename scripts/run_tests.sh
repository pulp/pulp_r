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
oci-env compose up -d

# Wait for the database connection to establish
while true; do
    result=$(curl -s http://localhost:5001/pulp/api/v3/status/ | jq -r .database_connection.connected)
    echo "Server Response - database connected: $result"
    if [ "$result" = "true" ]; then
        break
    fi
    sleep 5
done
# Remove podman from path before running these commands
oci-env generate-client -i pulpcore
oci-env generate-client -i pulp_r

# Run functional tests for the pulp_python plugin
oci-env test -ip pulp_r functional

# Example to show how to access API with authentication (commented out)
# curl -u admin:password http://localhost:5001/pulp/api/v3/status/ | jq '.'

# oci-env generate-client -i
# oci-env generate-client -i pulpcore
# oci-env generate-client pulp_r

# Run unit tests (commented out)
# oci-env test -i -p pulp_r unit

# Run functional tests (commented out)
# oci-env test -i -p pulp_r functional
