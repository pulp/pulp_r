#!/bin/bash

set -e

# Credentials
USERNAME="admin"
PASSWORD="password"
BASE_URL_V3="http://localhost:8080/pulp/api/v3"
BASE_URL_HOST="http://localhost:8080"

# Function to delete a resource
delete_resource() {
    local resource_url=$1
    local delete_url="$BASE_URL_HOST$resource_url"
    echo "Deleting $delete_url"
    curl -u $USERNAME:$PASSWORD -X DELETE "$delete_url"
}

# Function to get all distributions
get_distributions() {
    curl -u $USERNAME:$PASSWORD -X GET "$BASE_URL_V3/distributions/r/r/"
}

# Function to get all remotes
get_remotes() {
    curl -u $USERNAME:$PASSWORD -X GET "$BASE_URL_V3/remotes/r/r/"
}

# Function to get all repositories
get_repositories() {
    curl -u $USERNAME:$PASSWORD -X GET "$BASE_URL_V3/repositories/r/r/"
}

# Function to get all publications
get_publications() {
    curl -u $USERNAME:$PASSWORD -X GET "$BASE_URL_V3/publications/r/r/"
}

# Get and delete all distributions
distributions=$(get_distributions | jq -r '.results[].pulp_href')
for dist in $distributions; do
    delete_resource "$dist"
done

# Get and delete all remotes
remotes=$(get_remotes | jq -r '.results[].pulp_href')
for remote in $remotes; do
    delete_resource "$remote"
done

# Get and delete all repositories
repositories=$(get_repositories | jq -r '.results[].pulp_href')
for repo in $repositories; do
    delete_resource "$repo"
done

# Get and delete all publications
publications=$(get_publications | jq -r '.results[].pulp_href')
for pub in $publications; do
    delete_resource "$pub"
done

# Wait for deletions to complete
sleep 10

# Create new remote
remote_response=$(curl -u $USERNAME:$PASSWORD -X POST "$BASE_URL_V3/remotes/r/r/" \
    -H "Content-Type: application/json" \
    -d '{
          "name": "CRAN Remote",
          "url": "https://cran.r-project.org/src/contrib/PACKAGES.gz",
          "policy": "on_demand"
        }')
remote_href=$(echo $remote_response | jq -r '.pulp_href')
echo "Created remote: $remote_href"

# Create new repository
repo_response=$(curl -u $USERNAME:$PASSWORD -X POST "$BASE_URL_V3/repositories/r/r/" \
    -H "Content-Type: application/json" \
    -d '{
          "name": "CRAN Repository",
          "description": "Repository for CRAN packages"
        }')
repo_href=$(echo $repo_response | jq -r '.pulp_href')
echo "Created repository: $repo_href"

# Sync repository
sync_response=$(curl -u $USERNAME:$PASSWORD -X POST "${BASE_URL_HOST}${repo_href}sync/" \
    -H "Content-Type: application/json" \
    -d "{
          \"remote\": \"$remote_href\",
          \"mirror\": true
        }")
sync_task=$(echo $sync_response | jq -r '.task')
echo "Started sync task: $BASE_URL_HOST$sync_task"

# Wait for sync to complete
sync_status=""
while [[ "$sync_status" != "completed" ]]; do
    sync_status=$(curl -u $USERNAME:$PASSWORD -X GET "$BASE_URL_HOST$sync_task" | jq -r '.state')
    echo "Sync status: $sync_status"
    sleep 5
done

# Create a publication from the synced repository version
pub_response=$(curl -u $USERNAME:$PASSWORD -X POST "$BASE_URL_V3/publications/r/r/" \
    -H "Content-Type: application/json" \
    -d "{
          \"repository_version\": \"${repo_href}versions/1/\"
        }")
pub_task_href=$(echo $pub_response | jq -r '.task')
echo "Started publication task: $BASE_URL_HOST$pub_task_href"

# Wait for publication to complete
pub_status=""
while [[ "$pub_status" != "completed" ]]; do
    pub_status=$(curl -u $USERNAME:$PASSWORD -X GET "$BASE_URL_HOST$pub_task_href" | jq -r '.state')
    echo "Publication status: $pub_status"
    sleep 5
done

# Extract the publication href from the task response
pub_href=$(curl -u $USERNAME:$PASSWORD -X GET "$BASE_URL_HOST$pub_task_href" | jq -r '.created_resources[0]')
echo "Created publication: $pub_href"

# Create a distribution from the publication
dist_response=$(curl -u $USERNAME:$PASSWORD -X POST "$BASE_URL_V3/distributions/r/r/" \
    -H "Content-Type: application/json" \
    -d "{
          \"name\": \"CRAN Distribution\",
          \"base_path\": \"r/src/contrib\",
          \"publication\": \"$pub_href\"
        }")
distribution_task_href=$(echo $dist_response | jq -r '.task')

# Wait for distribution to complete
distribution_status=""
while [[ "$distribution_status" != "completed" ]]; do
    distribution_status=$(curl -u $USERNAME:$PASSWORD -X GET "$BASE_URL_HOST$distribution_task_href" | jq -r '.state')
    echo "Distribution status: $distribution_status"
    sleep 5
done

# Extract the distribution href from the task response
distribution_href=$(curl -u $USERNAME:$PASSWORD -X GET "$BASE_URL_HOST$distribution_task_href" | jq -r '.created_resources[0]')
echo "Created distribution: $distribution_href"

# Get distribution details
curl -u $USERNAME:$PASSWORD -X GET "$BASE_URL_HOST$distribution_href"