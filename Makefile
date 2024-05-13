.PHONY: bootstrap-server run-tests

bootstrap-server:
	./oci_env/bootstrap_server.sh

run-tests:
	./oci_env/run_tests.sh