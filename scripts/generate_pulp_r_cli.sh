#!/bin/bash

set -e

# The openapi generator expects the PULP_API to be on port 24817
export PULP_API="http://localhost:24817"
export PULP_API_ROOT="/pulp/"
export COMPONENT="core" # or "pulp_r"

# Backup the original compose.yml
cp compose.yml compose.yml.bak

# Trap to ensure we always revert the compose change
trap 'mv compose.yml.bak compose.yml' EXIT

# Modify the compose.yml file to use the correct port
awk '{gsub(/"8080:80"/,"\"24817:80\""); print}' compose.yml.bak > compose.yml

# Start the Pulp server
docker compose up -d

# Function to check if Pulp is ready
is_pulp_ready() {
    curl -s -f ${PULP_API}/pulp/api/v3/status/ > /dev/null
}

# Wait for Pulp to be ready
echo "Waiting for Pulp to be ready..."
while ! is_pulp_ready; do
    sleep 5
done

echo "::group::BINDINGS"

# Clone the pulp-openapi-generator repository if it doesn't exist
if [ ! -d "../pulp-openapi-generator" ]; then
    git clone https://github.com/pulp/pulp-openapi-generator.git ../pulp-openapi-generator
fi

# Change to the pulp-openapi-generator directory
cd ../pulp-openapi-generator
git fetch origin main
git pull origin main

# Create a temporary Python virtual environment
python -m venv temp_venv
source temp_venv/bin/activate

# Install required packages
pip install packaging

echo "Generating the Python bindings for ${COMPONENT}"

# Generate the Python bindings for the component
./generate.sh ${COMPONENT} python

# Create a clean directory for the generated client
rm -rf "../pulp_r/${COMPONENT}_client"
mkdir -p "../pulp_r/${COMPONENT}_client"

# Copy the generated client to the new directory
cp -R "${COMPONENT}-client/"* "../pulp_r/${COMPONENT}_client/"

echo "${COMPONENT} CLI has been generated and copied to the pulp_r/${COMPONENT}_client directory."

# Change to the client directory
cd "../pulp_r/${COMPONENT}_client"

# Install the generated client package
pip install -e .

echo "${COMPONENT} CLI package has been installed."

# Provide instructions for using the new CLI
echo "You can now use the ${COMPONENT} CLI. Here are some example commands:"
echo "python -m pulpcore.client.${COMPONENT}.api_client --help"
echo "python -m pulpcore.client.${COMPONENT}.api_client list_repositories"

# Change back to the original directory
cd ../../pulp_r

# Stop the Pulp server
docker compose down

# Clean up any leftover containers or volumes
docker compose down -v

echo "Cleanup completed."