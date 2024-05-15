#!/bin/bash

set -e

# Function to print messages with colors
print_message() {
    local type="$1"
    local message="$2"

    case $type in
        info)
            tput setaf 2  # Green
            ;;
        warn)
            tput setaf 3  # Yellow
            ;;
        error)
            tput setaf 1  # Red
            ;;
        *)
            tput setaf 7  # White
            ;;
    esac

    echo "$message"
    tput sgr0
}

# Clean up any existing Docker/Podman processes and logs
cleanup() {
    print_message info "Cleaning up Docker/Podman processes and logs..."
    docker-compose down --volumes --remove-orphans
    docker-compose logs > docker_logs.txt
    print_message info "Logs saved to docker_logs.txt"
}

# Trap EXIT to ensure cleanup happens
trap cleanup EXIT

# Check if podman is available in the user's path
if command -v podman &> /dev/null
then
    print_message warn "Warning: The openapi-generator images used in pulp-openapi-generator might only be compiled for x86_64."
    print_message warn "Please ensure that podman is set up to run amd64 (x86_64) containers, or temporarily remove it from your path."
    print_message warn "The pulp-openapi-generator script defaults to podman if it's available."
    echo
fi

# Check if the required directories exist in the parent directory
if [ ! -d "../oci_env" ]; then
    print_message info "Cloning oci_env repository..."
    git clone https://github.com/pulp/oci_env.git ../oci_env
fi

if [ ! -d "../pulp-openapi-generator" ]; then
    print_message info "Cloning pulp-openapi-generator repository..."
    git clone https://github.com/pulp/pulp-openapi-generator.git ../pulp-openapi-generator
fi

# Copy environment file
cp ./compose.env ../oci_env/compose.env
cd ../oci_env || exit

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    print_message info "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate the virtual environment
source venv/bin/activate

# Install packages
print_message info "Installing required packages..."
pip3 install -e client
pip install pulp-smash

# Tear down existing services and volumes
print_message info "Tearing down existing services and volumes..."
oci-env compose down --volumes

# Build images and start services
print_message info "Building images and starting services..."
oci-env compose build
oci-env compose up -d

# Tail logs from containers. This will follow the log output.
oci-env compose logs -f &

# Wait for the database connection to establish
print_message info "Waiting for the database connection to establish..."
while true; do
    result=$(curl -s http://localhost:5001/pulp/api/v3/status/ | jq -r .database_connection.connected)
    print_message info "Server Response - database connected: $result"
    if [ "$result" = "true" ]; then
        break
    fi
    sleep 5
done

# Remove podman from path before running these commands
PATH=$(echo $PATH | awk -F: '{$NF=""}1' OFS=:)

print_message info "Generating client for pulpcore..."
oci-env generate-client -i pulpcore

print_message info "Generating client for pulp_r..."
oci-env generate-client -i pulp_r

# Run functional tests for the pulp_python plugin
print_message info "Running functional tests for the pulp_r plugin..."
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