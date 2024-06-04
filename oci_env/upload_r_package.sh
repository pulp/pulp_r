#!/bin/bash

set -e

# Credentials
USERNAME="admin"
PASSWORD="password"
BASE_URL_V3="http://localhost:5001/pulp/api/v3"
BASE_URL_HOST="http://localhost:5001"
DISTRIBUTION_BASE_PATH="r/tenantx/src/contrib"
CONTENT_INDEX_PATH="content/r/tenantx"
PACKAGE_CONTENT_URL="$BASE_URL_V3/$CONTENT_INDEX_PATH"

# Create a temporary directory for the dummy package
temp_dir=$(mktemp -d)
trap 'rm -rf "$temp_dir"' EXIT

# Generate a unique package name
package_name="dummy$(date +%s)$RANDOM"

# Function to create a dummy R package
create_dummy_package() {
    cd "$temp_dir"
    mkdir -p "$package_name"
    cd "$package_name"

    cat > DESCRIPTION <<EOL
Package: $package_name
Title: A Dummy R Package
Version: 0.1.0
Author: John Doe
Maintainer: John Doe <john.doe@example.com>
Description: This is a dummy R package created for testing purposes.
License: MIT
EOL

    mkdir -p R
    cat > R/dummy.R <<EOL
#' A dummy function
#'
#' This function prints a greeting message.
#'
#' @param name The name of the person to greet.
#'
#' @export
greet <- function(name) {
  message(paste("Hello,", name, "!"))
}
EOL

    R CMD build .
    cd "$temp_dir"
}

# Function to upload the package to Pulp
upload_package() {
    local package_file=$1
    local repo_href=$2

    response=$(curl -u $USERNAME:$PASSWORD -X POST "$BASE_URL_HOST$repo_href"upload_content/ \
        -H "Content-Type: multipart/form-data" \
        -F "file=@$package_file" \
        -F "relative_path=$package_name/${package_name}_0.1.0.tar.gz" \
        -F "url=http://example.com/$package_name/${package_name}_0.1.0.tar.gz" \
        -F "name=$package_name" \
        -F "version=0.1.0" \
        -F "priority=" \
        -F "summary=A Dummy R Package" \
        -F "description=This is a dummy R package created for testing purposes." \
        -F "license=MIT" \
        -F "md5sum=" \
        -F "path=" \
        -F "depends=[]" \
        -F "imports=[]" \
        -F "suggests=[]" \
        -F "requires=[]" \
        -F "needs_compilation=false" \
        -w "\n%{http_code}" )

    http_code=$(echo "$response" | tail -n1)
    response_body=$(echo "$response" | sed '$d')

    echo "Response: $response_body"

    if [[ "$http_code" -ge 200 && "$http_code" -lt 300 ]]; then
        echo "Upload successful."
    else
        echo "Upload failed with status code $http_code."
        exit 1
    fi
}

# Create a dummy R package
create_dummy_package
package_file="$temp_dir/$package_name/${package_name}_0.1.0.tar.gz"

# Generate a unique repository name by appending a timestamp
timestamp=$(date +%s)
repo_name="R Package Repository $timestamp"

# Create a new repository
repo_response=$(curl -u $USERNAME:$PASSWORD -X POST "$BASE_URL_V3/repositories/r/r/" \
    -H "Content-Type: application/json" \
    -d "{
          \"name\": \"$repo_name\",
          \"description\": \"Repository for R packages\"
        }")

if [[ $(echo $repo_response | jq -r '.pulp_href') == "null" ]]; then
    echo "Failed to create repository. Server response:"
    echo $repo_response
    exit 1
fi

repo_href=$(echo $repo_response | jq -r '.pulp_href')
echo "Created repository: $repo_href"

# Upload the package to the repository
upload_package $package_file $repo_href

# Extract the task href from the response
task_href=$(echo $response_body | jq -r '.task')

# Wait for the publication task to complete
task_status=""
while [[ "$task_status" != "completed" ]]; do
    task_status=$(curl -u $USERNAME:$PASSWORD -X GET "$BASE_URL_HOST$task_href" | jq -r '.state')
    echo "Task status: $task_status"
    sleep 5
done

# Extract the publication href from the task response
pub_href=$(curl -u $USERNAME:$PASSWORD -X GET "$BASE_URL_HOST$task_href" | jq -r '.created_resources[0]')
if [[ $pub_href == null ]]; then
    echo "Failed to retrieve the publication href."
    exit 1
fi
echo "Created publication: $pub_href"


# Check if a distribution with the same base_path already exists
existing_dist=$(curl -u $USERNAME:$PASSWORD -X GET "$BASE_URL_V3/distributions/r/r/?base_path=$DISTRIBUTION_BASE_PATH" | jq -r '.results[0].pulp_href')

if [[ $existing_dist != "null" ]]; then
    # Update the existing distribution
    dist_response=$(curl -u $USERNAME:$PASSWORD -X PATCH "$BASE_URL_HOST$existing_dist" \
        -H "Content-Type: application/json" \
        -d "{
              \"publication\": \"$pub_href\"
            }")
else
    # Create a new distribution
    dist_response=$(curl -u $USERNAME:$PASSWORD -X POST "$BASE_URL_V3/distributions/r/r/" \
        -H "Content-Type: application/json" \
        -d "{
              \"name\": \"CRAN Distribution tenantx\",
              \"base_path\": \"$DISTRIBUTION_BASE_PATH\",
              \"publication\": \"$pub_href\"
            }")
fi
distribution_task_href=$(echo $dist_response | jq -r '.task')
echo "Started distribution task: $BASE_URL_HOST$distribution_task_href"

# Wait for distribution to complete
distribution_status=""
while [[ "$distribution_status" != "completed" ]]; do
    task_response=$(curl -u $USERNAME:$PASSWORD -X GET "$BASE_URL_HOST$distribution_task_href")
    distribution_status=$(echo "$task_response" | jq -r '.state')
    echo "Distribution status: $distribution_status"
    echo "Task response: $task_response"
    sleep 5
done

# Extract the distribution href from the task response or use the existing_dist href
if [[ $existing_dist != "null" ]]; then
    distribution_href=$existing_dist
else
    distribution_href=$(echo "$task_response" | jq -r '.created_resources[0]')
fi

echo "Distribution href: $distribution_href"

if [[ "$distribution_href" == "null" ]]; then
    echo "Failed to retrieve the distribution href."
    exit 1
fi

echo "Created distribution: $distribution_href"

# Get distribution details
curl -u $USERNAME:$PASSWORD -X GET "$BASE_URL_HOST$distribution_href"

# Install the package from the Pulp repository
R -e "install.packages('$package_name', repos='$PACKAGE_CONTENT_URL')"

# Use the installed package
R -e "library($package_name); greet('Pulp')"
