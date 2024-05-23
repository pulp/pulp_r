# Pulp R Content Plugin

Welcome to the Pulp R Content Plugin repository! This plugin extends the functionality of the Pulp platform to support managing and distributing R packages.

## Getting Started

To get started with the Pulp R Content Plugin, follow these steps:

1. Clone the repository:
   ```
   git clone git@github.com:pulp/pulp_r.git
   ```

2. Change into the project directory:
   ```
   cd pulp_r
   ```

3. Bootstrap the server by executing the `bootstrap_server.sh` script:
   ```
   ./oci_env/bootstrap_server.sh
   ```
   This script will set up the necessary environment and bring up the Pulp server.

4. (Optional) If you want to create a local cran distribution, in another session, you can run the `cleanup_and_recreate_dummy_resources.sh` script:
   ```
   ./oci_env/cleanup_and_recreate_dummy_resources.sh
   ```
   This script will create a local distribution of CRAN packages and sync it to the Pulp server.

5. (Optional) After the distribution is created, you can download a sample package from your local distribution using the `download_r_package.sh` script:
   ```
   ./oci_env/download_r_package.sh
   ```
   This script will download a sample package from the local distribution.

### Compose Configuration

The `compose.env` file in the root directory contains the configuration for the Pulp server. Here's a brief explanation of the settings:

```
COMPOSE_PROFILE=pulp_container_base
```
This setting specifies the profiles to use for the Pulp server. In this case, we're using the `pulp_container_base` profile.

```
DEV_SOURCE_PATH=pulpcore:pulp_r
```
The `DEV_SOURCE_PATH` setting is a colon-separated list of Python dependencies to include from the source.


```
DJANGO_SUPERUSER_USERNAME=admin
DJANGO_SUPERUSER_PASSWORD=password
```
These settings define the credentials for the Django admin user that gets created during startup.

```
API_HOST=localhost
API_PORT=5001
API_PROTOCOL=http
DOCS_PORT=12345

```
These settings configure the host, port, and protocol used for the Pulp content origin API.

### Running Tests

To run tests for the Pulp R Content Plugin, use the `run_tests.sh` script located in the `oci_env` directory:

```
./oci_env/run_tests.sh
```

This script will execute the test suite and provide you with the test results.

## Contributing

We welcome contributions to the Pulp R Content Plugin! If you find any issues or have suggestions for improvements, please open an issue or submit a pull request on the GitHub repository.

Happy packaging with Pulp R!