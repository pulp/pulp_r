#!/bin/bash

# Save the original PATH to restore later
ORIGINAL_PATH=$PATH

# Check if podman is available and get its path
if command -v podman >/dev/null; then
    PODMAN_PATH=$(dirname $(which podman))
    # Remove the directory containing 'podman' from the PATH
    export PATH=$(echo "$PATH" | tr ':' '\n' | grep -v "$PODMAN_PATH" | tr '\n' ':')
    echo "Podman found and temporarily disabled."
else
    echo "Podman not found, continuing without modification."
fi

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

oci-env generate-client -i pulpcore
oci-env generate-client pulp_r

# Run functional tests for the pulp_python plugin
oci-env test -ip pulp_python functional

# Example to show how to access API with authentication (commented out)
# curl -u admin:password http://localhost:5001/pulp/api/v3/status/ | jq '.'

# oci-env generate-client -i
# oci-env generate-client -i pulpcore
# oci-env generate-client pulp_r

# Run unit tests (commented out)
# oci-env test -i -p pulp_r unit

# Run functional tests (commented out)
# oci-env test -i -p pulp_r functional

# Restore the original PATH
export PATH=$ORIGINAL_PATH
echo "Original PATH restored."
