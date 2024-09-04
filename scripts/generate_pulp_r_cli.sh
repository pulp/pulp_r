#!/bin/bash

set -e

# The openapi generator expects the PULP_API to be on port 24817 https://github.com/pulp/pulp-openapi-generator?tab=readme-ov-file#requirements
export PULP_API="http://localhost:24817"
export PULP_API_ROOT="/pulp/"

# Backup the original compose.yml
cp compose.yml compose.yml.bak

# Modify the compose.yml file to use the correct port
awk '{gsub(/"8080:80"/,"\"24817:80\""); print}' compose.yml.bak > compose.yml

# Start the Pulp server
docker compose up -d

# Function to check if Pulp is ready
is_pulp_ready() {
    curl -s -f "${PULP_URL}${PULP_API_ROOT}api/v3/status/" > /dev/null
}

# Wait for Pulp to be ready
echo "Waiting for Pulp to be ready..."
while ! is_pulp_ready; do
    sleep 5
done

# Clone the pulp-openapi-generator repository if it doesn't exist
if [ ! -d "../pulp-openapi-generator" ]; then
    git clone https://github.com/pulp/pulp-openapi-generator.git ../pulp-openapi-generator
fi

# Change to the pulp-openapi-generator directory
cd ../pulp-openapi-generator

# Generate the Python bindings for pulp_r
./generate.sh pulp_r python

# Move the generated client back to our project directory
mkdir -p ../pulp_r/pulp_r_client
mv pulp_r-client/* ../pulp_r/pulp_r_client/

echo "Pulp R CLI has been generated and moved to the pulp_r/pulp_r_client directory."

# Stop the Pulp server
cd ../pulp_r
docker compose down

# Restore the original compose.yml
mv compose.yml.bak compose.yml

echo "Compose file has been restored to its original state."

# Clean up any leftover containers or volumes
docker compose down -v

echo "Cleanup completed."