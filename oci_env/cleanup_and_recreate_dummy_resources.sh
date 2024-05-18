#!/bin/bash

set -e

# Credentials
USERNAME="admin"
PASSWORD="password"
BASE_URL="http://localhost:5001/pulp/api/v3"

# Function to delete a resource
delete_resource() {
    local resource_url=$1
    response=$(curl -u $USERNAME:$PASSWORD -X DELETE "$resource_url")
    echo "Deleted $resource_url: $response"
}

# Function to get all distributions
get_distributions() {
    curl -u $USERNAME:$PASSWORD -X GET "$BASE_URL/distributions/r/r/"
}

# Function to get all remotes
get_remotes() {
    curl -u $USERNAME:$PASSWORD -X GET "$BASE_URL/remotes/r/r/"
}

# Function to get all repositories
get_repositories() {
    curl -u $USERNAME:$PASSWORD -X GET "$BASE_URL/repositories/r/r/"
}

# Function to get all publications
get_publications() {
    curl -u $USERNAME:$PASSWORD -X GET "$BASE_URL/publications/r/r/"
}

# Get and delete all distributions
distributions=$(get_distributions | jq -r '.results[].pulp_href')
for dist in $distributions; do
    delete_resource "$BASE_URL$dist"
done

# Get and delete all remotes
remotes=$(get_remotes | jq -r '.results[].pulp_href')
for remote in $remotes; do
    delete_resource "$BASE_URL$remote"
done

# Get and delete all repositories
repositories=$(get_repositories | jq -r '.results[].pulp_href')
for repo in $repositories; do
    delete_resource "$BASE_URL$repo"
done

# Get and delete all publications
publications=$(get_publications | jq -r '.results[].pulp_href')
for pub in $publications; do
    delete_resource "$BASE_URL$pub"
done

# Wait for deletions to complete
sleep 10

# Create new remote
remote_response=$(curl -u $USERNAME:$PASSWORD -X POST "$BASE_URL/remotes/r/r/" \
     -H "Content-Type: application/json" \
     -d '{
           "name": "CRAN Remote",
           "url": "https://cran.r-project.org/src/contrib/PACKAGES.gz",
           "policy": "on_demand"
         }')

remote_href=$(echo $remote_response | jq -r '.pulp_href')
echo "Created remote: $remote_href"

# Create new repository
repo_response=$(curl -u $USERNAME:$PASSWORD -X POST "$BASE_URL/repositories/r/r/" \
     -H "Content-Type: application/json" \
     -d '{
           "name": "CRAN Repository",
           "description": "Repository for CRAN packages"
         }')

repo_href=$(echo $repo_response | jq -r '.pulp_href')
echo "Created repository: $repo_href"

# Sync repository
sync_response=$(curl -u $USERNAME:$PASSWORD -X POST "$BASE_URL/repositories/r/r/${repo_href}/sync/" \
     -H "Content-Type: application/json" \
     -d "{
           \"remote\": \"$remote_href\",
           \"mirror\": true
         }")

sync_task=$(echo $sync_response | jq -r '.task')
echo "Started sync task: $sync_task"

# Wait for sync to complete
sync_status=""
while [[ "$sync_status" != "completed" ]]; do
    sync_status=$(curl -u $USERNAME:$PASSWORD -X GET "$BASE_URL$sync_task" | jq -r '.state')
    echo "Sync status: $sync_status"
    sleep 5
done

# Create a publication from the synced repository version
pub_response=$(curl -u $USERNAME:$PASSWORD -X POST "$BASE_URL/publications/r/r/" \
-H "Content-Type: application/json" \
-d "{
      \"repository_version\": \"${repo_href}/versions/1/\"
    }")

pub_href=$(echo $pub_response | jq -r '.pulp_href')
echo "Created publication: $pub_href"

pub_task=$(echo $pub_response | jq -r '.task')
echo "Started publication task: $pub_task"

# Wait for publication to complete
pub_status=""
while [[ "$pub_status" != "completed" ]]; do
    pub_status=$(curl -u $USERNAME:$PASSWORD -X GET "$BASE_URL$pub_task" | jq -r '.state')
    echo "Publication status: $pub_status"
    sleep 5
done

# Create a distribution from the publication
dist_response=$(curl -u $USERNAME:$PASSWORD -X POST "$BASE_URL/distributions/r/r/" \
-H "Content-Type: application/json" \
-d "{
      \"name\": \"CRAN Distribution\",
      \"base_path\": \"r/src/contrib\",
      \"publication\": \"$pub_href\"
    }")

echo "Distribution creation response: $dist_response"
