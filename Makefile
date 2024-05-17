.PHONY: bootstrap-server run-tests

bootstrap-server:
	./oci_env/bootstrap_server.sh

run-tests:
	./oci_env/run_tests.sh

oci-env-pulp-exec:
	cd ../oci_env && source venv/bin/activate && oci-env compose exec pulp bash