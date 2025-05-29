#!/bin/bash
set -e

# Install system dependencies
sudo apt update
sudo apt install -y python3-pip python3-setuptools python3-venv git zip unzip wget openjdk-21-jdk

# Create and activate a virtual environment for Buildozer
# python3 -m venv buildozer-env
source buildozer-env/bin/activate
pip install --upgrade pip

# Install Buildozer and python-for-android
pip install buildozer python-for-android

# Trigger Buildozer so it downloads the Android SDK/NDK r25b and API 30
# as specified in buildozer.spec
buildozer android p4a -- --help
