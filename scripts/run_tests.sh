#!/bin/bash

cd ../oci_env || exit
source venv/bin/activate
pip3 install -e client



oci-env compose down --volumes
# 4. build the images and do basic setup
oci-env compose build
oci-env compose up -d

pip install pulp-cli
BASE_ADDR="http://localhost:5001"
pulp config create --base-url $BASE_ADDR --no-verify-ssl --format json --verbose --username admin --password password --overwrite



# By default the API will be served from http://localhost:5001/pulp/api/v3/. You can login with admin/password by default. E.g.:
# curl -u admin:password http://localhost:5001/pulp/api/v3/status/ | jq '.'

# oci-env generate-client -i
# oci-env generate-client -i pulpcore
# oci-env generate-client pulp_r


# 6. run the tests

# Unit: oci-env test -i -p pulp_r unit

# Functional: oci-env test -i -p pulp_r functional