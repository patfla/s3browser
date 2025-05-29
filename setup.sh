# Update and install system dependencies
sudo apt update
sudo apt install -y python3-pip python3-setuptools git zip unzip openjdk-21-jdk


# Optional but recommended: create and activate a virtual environment
python3 -m venv buildozer-env
source buildozer-env/bin/activate
pip install cython setuptools python-for-android kivy boto3 botocore jmespath idna charset_normalizer certifi,openssl python-dateutil s3transfer plyer

# Install Buildozer using pip
pip install --upgrade pip
# pip install --no-index --find-links deps/buildozer-1.5.0-py3-none-any.whl
pip install buildozer

