#!/bin/bash

set -e

# Credentials
USERNAME="admin"
PASSWORD="password"
BASE_URL_V3="http://localhost:5001/pulp/api/v3"
BASE_ULR_HOST="http://localhost:5001"
DISTRIBUTION_BASE_PATH="r/src/contrib"
PACKAGE_CONTENT_URL="$BASE_URL_V3/content/$DISTRIBUTION_BASE_PATH"

# Create a temporary directory for the dummy package
temp_dir=$(mktemp -d)
trap 'rm -rf "$temp_dir"' EXIT

# Function to create a dummy R package
create_dummy_package() {
    cd "$temp_dir"
    mkdir -p dummy_package
    cd dummy_package

    cat > DESCRIPTION <<EOL
Package: dummy
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

    curl -u $USERNAME:$PASSWORD -X POST "$BASE_ULR_HOST$repo_href"upload_content/ \
        -H "Content-Type: multipart/form-data" \
        -F "file=@$package_file"
}

# Function to publish the repository
publish_repository() {
    local repo_href=$1

    curl -u $USERNAME:$PASSWORD -X POST "$BASE_URL_V3/publications/r/r/" \
        -H "Content-Type: application/json" \
        -d "{\"repository\": \"$repo_href\"}"
}

# Function to create a distribution
create_distribution() {
    local pub_href=$1

    curl -u $USERNAME:$PASSWORD -X POST "$BASE_URL_V3/distributions/r/r/" \
        -H "Content-Type: application/json" \
        -d "{
              \"name\": \"R Package Distribution\",
              \"base_path\": \"$DISTRIBUTION_BASE_PATH\",
              \"publication\": \"$pub_href\"
            }"
}

# Create a dummy R package
create_dummy_package
package_file="$temp_dir/dummy_package/dummy_0.1.0.tar.gz"

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

# Publish the repository
pub_response=$(publish_repository "$repo_href")
pub_href=$(echo $pub_response | jq -r '.pulp_href')
echo "Published repository: $pub_href"

# Create a distribution
dist_response=$(create_distribution $pub_href)
dist_href=$(echo $dist_response | jq -r '.pulp_href')
echo "Created distribution: $dist_href"

# Install the package from the Pulp repository
R -e "install.packages('dummy', repos='$PACKAGE_CONTENT_URL')"

# Use the installed package
R -e "library(dummy); greet('Pulp')"