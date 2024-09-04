.PHONY: bootstrap-server run-tests

bootstrap-server:
	./run.sh

dev-sync-cran: bootstrap-server
	./scripts/cleanup_and_recreate_dummy_resources.sh

dev-run-tests: bootstrap-server
	./scripts/run_tests.sh

dev-download-r-package: dev-sync-cran
	./scripts/download_r_package.sh

dev-upload-r-package: bootstrap-server
	./scripts/upload_r_package.sh

oci-env-setup:
	./scripts/oci_env_setup.sh