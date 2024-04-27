#!/bin/bash

cp ./compose.env ../oci_env/compose.env
cd ../oci_env || exit
source venv/bin/activate
pip3 install -e client
pip install pulp-smash



oci-env compose down --volumes
# 4. build the images and do basic setup
oci-env compose build
oci-env compose up -d

while true; do
    result=$(curl -s http://localhost:5001/pulp/api/v3/status/ | jq -r .database_connection.connected)
    echo "Server Response - database connected: $result"
    if [ "$result" = "true" ]; then
        break
    fi
    sleep 5
done

oci-env test -ip pulp_r functional

# By default the API will be served from http://localhost:5001/pulp/api/v3/. You can login with admin/password by default. E.g.:
# curl -u admin:password http://localhost:5001/pulp/api/v3/status/ | jq '.'

# python scripts/query_server.py

# oci-env generate-client -i
# oci-env generate-client -i pulpcore
# oci-env generate-client pulp_r


# 6. run the tests

# Unit: oci-env test -i -p pulp_r unit

# Functional: oci-env test -i -p pulp_r functional