#!/bin/bash

ENV_NAME="myenv"
REQUIRED_PACKAGES=("tk" "pandas" "PyPDF2")
LAUNCH_SCRIPT="./LAUNCH.sh"  # Path to the LAUNCH.sh script

# Initialize Conda in your script
eval "$(conda shell.bash hook)"

# Function to check if a package is installed in the environment
is_package_installed() {
    package=$1
    conda list -n "$ENV_NAME" | grep -q "^$package\s"
    return $?
}

# Ensure Mamba is installed
if ! command -v mamba &> /dev/null; then
    echo "Mamba is not installed. Installing Mamba..."
    conda install mamba -n base -c conda-forge -y
else
    echo "Mamba is already installed."
fi

# Create the environment if it doesn't exist
if ! conda info --envs | grep -q "^$ENV_NAME\s"; then
    echo "Creating environment $ENV_NAME."
    mamba create -n "$ENV_NAME" python=3.12 -y
else
    echo "Environment $ENV_NAME already exists."d
fi

# Activate the environment
echo "Activating environment $ENV_NAME."
conda activate "$ENV_NAME"

# Install necessary packages only if they are not already installed
for package in "${REQUIRED_PACKAGES[@]}"; do
    if ! is_package_installed "$package"; then
        echo "Installing $package..."
        mamba install -n "$ENV_NAME" "$package" -y
    else
        echo "$package is already installed."
    fi
done

# Call the LAUNCH.sh script to execute gui.py
if [ -x "$LAUNCH_SCRIPT" ]; then
    echo "Launching the application..."
    "$LAUNCH_SCRIPT"
else
    echo "Error: Launch script ($LAUNCH_SCRIPT) not found or not executable."
fi
