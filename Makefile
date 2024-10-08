.PHONY: bootstrap-server run-tests

bootstrap-server:
	./run.sh

dev-sync-cran: bootstrap-server
	./scripts/cleanup_and_recreate_dummy_resources.sh

dev-run-tests: bootstrap-server
	./scripts/run_tests.sh

dev-run-performance-tests: bootstrap-server
	./scripts/run_tests.sh

dev-download-r-package: dev-sync-cran
	./scripts/download_r_package.sh

dev-upload-r-package: bootstrap-server
	./scripts/upload_r_package.sh

generate-pulp-r-cli:
	./scripts/generate_pulp_r_cli.sh

oci-env-setup:
	./scripts/oci_env_setup.sh

test-customizable-syncs:
	./scripts/test_customizable_syncs.sh