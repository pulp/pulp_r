#!/bin/bash

set -e

# The openapi generator expects the PULP_API to be on port 24817
export PULP_API="http://localhost:24817"
export PULP_API_ROOT="/pulp/"
export COMPONENT="r"

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

# Reset admin password
docker compose exec -it pulp bash -c 'pulpcore-manager reset-admin-password --password password'

echo "Admin password has been reset to 'password'"

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
./generate.sh pulp_${COMPONENT} python

# Create a clean directory for the generated client
rm -rf "../pulp_r/${COMPONENT}_client"
mkdir -p "../pulp_r/${COMPONENT}_client"

# Copy the generated client to the new directory
cp -R "pulp_${COMPONENT}-client/"* "../pulp_r/${COMPONENT}_client/"

echo "${COMPONENT} CLI has been generated and copied to the pulp_r/${COMPONENT}_client directory."

# Change to the client directory
cd "../pulp_r/${COMPONENT}_client"

# Install the generated client package
pip install -e .

echo "${COMPONENT} CLI package has been installed."

# Provide instructions for using the new CLI
echo "You can now use the ${COMPONENT} CLI. Here are some example commands:"
echo "python -c 'from pulpcore.client.pulp_r import api_client; print(api_client.__doc__)'"
echo "python -c 'from pulpcore.client.pulp_r import RepositoriesRApi; print(RepositoriesRApi.__doc__)'"

# Change back to the original directory
cd ../../pulp_r

echo "CLI generation completed successfully."

# Example usage of the pulp_r CLI
echo "Example usage of the pulp_r CLI:"

# Activate the virtual environment
source ../pulp-openapi-generator/temp_venv/bin/activate

# Print API client documentation
python -c 'from pulpcore.client.pulp_r import api_client; print(api_client.__doc__)'

# Print RepositoriesRApi documentation
python -c 'from pulpcore.client.pulp_r import RepositoriesRApi; print(RepositoriesRApi.__doc__)'

# Example of creating a repository using the CLI
echo "Creating a dummy repository using the CLI:"
python -c '
from pulpcore.client.pulp_r import ApiClient, Configuration, RepositoriesRApi
from pulpcore.client.pulp_r.models import RRRepository

config = Configuration(host="http://localhost:24817")
config.username = "admin"
config.password = "password"
client = ApiClient(configuration=config)
api_instance = RepositoriesRApi(client)

try:
    repo = RRRepository(name="CLI Dummy Repository", description="Created via CLI")
    result = api_instance.create(repo)
    print(f"Created repository: {result.pulp_href}")
except Exception as e:
    print(f"An error occurred: {e}")
'

# Demonstrate CLI usage
echo "Demonstrating CLI usage:"
python -c '
from pulpcore.client.pulp_r import ApiClient, Configuration, RepositoriesRApi

config = Configuration(host="http://localhost:24817")
config.username = "admin"
config.password = "password"
client = ApiClient(configuration=config)
api_instance = RepositoriesRApi(client)

# List repositories
print("Listing repositories:")
repositories = api_instance.list()
for repo in repositories.results:
    print(f"Repository: {repo.name}, HREF: {repo.pulp_href}")
'

# Demonstrate CLI command
echo "Demonstrating actual CLI command:"
pulp r repository list

# Deactivate the virtual environment
deactivate

# Instructions for uploading to PyPI
echo "To upload the CLI package to PyPI, follow these steps:"
echo "1. Ensure you have an account on PyPI (https://pypi.org)"
echo "2. Install twine: pip install twine"
echo "3. Navigate to the r_client directory: cd r_client"
echo "4. Build the distribution: python setup.py sdist bdist_wheel"
echo "5. Upload to PyPI: twine upload dist/*"

echo "To use the CLI commands:"
echo "1. Install the package: pip install pulp-r-client"
echo "2. Use commands like:"
echo "   pulp r repository list"
echo "   pulp r repository create --name my_repo"
echo "   pulp r repository update --name my_repo --description 'Updated description'"
echo "   pulp r repository destroy --name my_repo"

# Stop the Pulp server
docker compose down

# Clean up any leftover containers or volumes
docker compose down -v

echo "Cleanup completed."