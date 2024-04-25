#!/bin/bash

cd ../oci_env || exit
source venv/bin/activate
pip3 install -e client



oci-env compose down --volumes
# 4. build the images and do basic setup
oci-env compose build
oci-env compose up
oci-env generate-client -i pulp_r

# # 5. start the service
# oci-env compose up

# # 6. run the tests
# # the -i (install) flag is required only for the first run
# oci-env test -i -p pulp_r functional