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

3. Bootstrap the server by executing the `run.sh` script:
   ```
   ./run.sh
   ```
   This script will set up the necessary environment and bring up the Pulp server.

4. (Optional) If you want to create a local cran distribution, in another session, you can run the `cleanup_and_recreate_dummy_resources.sh` script:
   ```
   ./scripts/cleanup_and_recreate_dummy_resources.sh
   ```
   This script will create a local distribution of CRAN packages and sync it to the Pulp server.

5. (Optional [ Note: Step 4 is required before calling this ]) After the distribution is created, you can download a sample package from your local distribution using the `download_r_package.sh` script:
   ```
   ./scripts/download_r_package.sh
   ```
   This script will download a sample package from the local distribution.

### Running Tests

To run tests for the Pulp R Content Plugin, use the `run_tests.sh` script located in the `scripts` directory:

```
./scripts/run_tests.sh
```

This script will execute the test suite and provide you with the test results.

## Contributing

We welcome contributions to the Pulp R Content Plugin! If you find any issues or have suggestions for improvements, please open an issue or submit a pull request on the GitHub repository.

Happy packaging with Pulp R!