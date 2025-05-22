# Update package list and install dependencies

sudo apt update
sudo apt install -y wget build-essential libncursesw5-dev libssl-dev \
 libsqlite3-dev tk-dev libgdbm-dev libc6-dev libbz2-dev libffi-dev zlib1g-dev

# Download Python 3.11 source code

cd /usr/src
sudo wget https://www.python.org/ftp/python/3.11.8/Python-3.11.8.tgz
sudo tar xzf Python-3.11.8.tgz
cd Python-3.11.8

# Build and install

sudo ./configure --enable-optimizations
sudo make -j$(nproc)
sudo make altinstall

# Create virtual environment

python3 -m venv venv
source venv/bin/activate # Linux/macOS

pip3 freeze > requirements.txt

# Install dependencies

pip3 install -r requirements.txt

# Run the FastAPI server on EC2

source venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8000

chmod 400 RealEstateAIAgent-keypair.pem

# Transfer code to EC2:

scp -i RealEstateAIAgent-keypair.pem -r ./agent.py ec2-user@13.42.180.170:/home/ec2-user/realestateaiagent

uvicorn main:app --host 0.0.0.0 --port 8000
lsof -i :8000
