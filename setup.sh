# Optional but recommended: create and activate a virtual environment
python3 -m venv buildozer-env
source buildozer-env/bin/activate

# Update and install system dependencies
sudo apt update
sudo apt install -y python3-pip python3-setuptools git zip unzip openjdk-11-jdk

# Install Buildozer using pip
pip install --upgrade pip
pip install buildozer

