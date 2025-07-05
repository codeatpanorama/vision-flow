#!/bin/bash

# Exit on error
set -e

echo "Updating conda environment 'vision-flow'..."

# Activate base conda environment to ensure conda commands work
#source ~/anaconda3/etc/profile.d/conda.sh || source ~/miniconda3/etc/profile.d/conda.sh

# Update using environment.yml
echo "Updating from environment.yml..."
conda env update -f environment.yml --prune

# Activate the environment
conda activate vision-flow

# Also update using pip for good measure
echo "Updating pip packages..."
pip install -r requirements.txt --upgrade

echo "Environment updated successfully!"
echo "Current package versions:"
pip list | grep -E "pdf2image|openai|pymongo|google-cloud-vision|python-dotenv" 