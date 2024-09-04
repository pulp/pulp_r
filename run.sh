#!/bin/bash
set -e


cleanup() {
    echo "Cleaning up..."
    rm -rf "$temp_dir"
    docker compose down
}

trap cleanup SIGINT SIGTERM

docker compose down

docker compose up --build -d

is_pulp_ready() {
    curl -s -f http://localhost:8080/pulp/api/v3/status/ > /dev/null
}

# Stream logs from all containers
docker compose logs -f &

echo "Waiting for Pulp to be ready..."
while ! is_pulp_ready; do
    sleep 5
done

# Create a temporary directory for the Python virtual environment
temp_dir=$(mktemp -d)

docker compose exec -it pulp bash -c 'pulpcore-manager reset-admin-password --password password'

# Set up CRAN server and sync packages
./oci_env/cleanup_and_recreate_dummy_resources.sh

# Clean up
cleanup
