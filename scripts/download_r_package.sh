#!/bin/bash

set -e

# Function to install R on macOS
install_r_macos() {
    echo "Installing R on macOS..."

    # Install Homebrew if not installed
    if ! command -v brew &> /dev/null
    then
        echo "Homebrew not found. Installing Homebrew..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    fi

    # Install R
    brew install r

    echo "R installation completed."
}

# Function to install R on Debian-based systems
install_r_debian() {
    echo "Installing R on Debian-based system..."

    sudo apt-get update
    sudo apt-get install -y software-properties-common

    sudo apt-key adv --keyserver keyserver.ubuntu.com --recv-keys 51716619E084DAB9
    sudo add-apt-repository "deb https://cloud.r-project.org/bin/linux/ubuntu $(lsb_release -cs)-cran40/"

    sudo apt-get update
    sudo apt-get install -y r-base

    echo "R installation completed."
}

# Detect platform and install R accordingly
if [[ "$OSTYPE" == "darwin"* ]]; then
    install_r_macos
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    if [[ -f /etc/debian_version ]]; then
        install_r_debian
    else
        echo "Unsupported Linux distribution. Please install R manually."
        exit 1
    fi
else
    echo "Unsupported OS. Please install R manually."
    exit 1
fi

# Verify R installation
R --version

# Define the base URL for the CRAN Distribution
BASE_URL="http://localhost:8080/pulp/api/v3/content/r"

# The name of the R package to install
PACKAGE_NAME="ggplot2"

# R command to install the package from the specified repository
R_COMMAND="options(verbose = TRUE); tryCatch(
  {
    install.packages('${PACKAGE_NAME}', repos='${BASE_URL}')
  },
  error = function(e) {
    message(paste('Error installing package', '${PACKAGE_NAME}:', conditionMessage(e)))
  }
)"

# Run the R command
R --vanilla -e "${R_COMMAND}"

