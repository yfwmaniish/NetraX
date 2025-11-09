#!/bin/bash
# H4$HCR4CK$ AI-Powered Dark Web Leak Detection System Setup Script
# Author: H4$HCR4CK$ Team

set -e  # Exit on error

echo "🚀 H4$HCR4CK$ AI-Powered Dark Web Leak Detection System Setup"
echo "=============================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   print_error "Do not run this script as root!"
   exit 1
fi

# Step 1: Check system requirements
print_header "Checking System Requirements..."

# Check Python version
if command -v python3 &> /dev/null; then
    python_version=$(python3 --version 2>&1 | awk '{print $2}')
    print_status "Python 3 found: $python_version"
    
    # Check if Python version is >= 3.8
    python3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)" || {
        print_error "Python 3.8 or higher is required!"
        exit 1
    }
else
    print_error "Python 3 is not installed!"
    exit 1
fi

# Check pip
if command -v pip3 &> /dev/null; then
    print_status "pip3 found"
else
    print_error "pip3 is not installed!"
    exit 1
fi

# Step 2: Install system dependencies
print_header "Installing System Dependencies..."

# Check if we can install system packages
if command -v apt-get &> /dev/null; then
    print_status "Debian/Ubuntu system detected"
    
    # Update package list
    print_status "Updating package list..."
    sudo apt-get update -qq
    
    # Install Tesseract OCR
    if ! command -v tesseract &> /dev/null; then
        print_status "Installing Tesseract OCR..."
        sudo apt-get install -y tesseract-ocr tesseract-ocr-eng
    else
        print_status "Tesseract OCR already installed"
    fi
    
    # Install additional image processing libraries
    print_status "Installing image processing libraries..."
    sudo apt-get install -y libpoppler-cpp-dev poppler-utils
    
    # Install Tor and Privoxy (if not already installed)
    if ! command -v tor &> /dev/null; then
        print_status "Installing Tor..."
        sudo apt-get install -y tor
    else
        print_status "Tor already installed"
    fi
    
    if ! command -v privoxy &> /dev/null; then
        print_status "Installing Privoxy..."
        sudo apt-get install -y privoxy
    else
        print_status "Privoxy already installed"
    fi
    
elif command -v yum &> /dev/null; then
    print_status "Red Hat/CentOS system detected"
    print_warning "Please install the following packages manually:"
    echo "  - tesseract tesseract-langpack-eng"
    echo "  - poppler-cpp-devel poppler-utils"
    echo "  - tor privoxy"
    
elif command -v brew &> /dev/null; then
    print_status "macOS with Homebrew detected"
    
    # Install Tesseract
    if ! command -v tesseract &> /dev/null; then
        print_status "Installing Tesseract OCR..."
        brew install tesseract
    else
        print_status "Tesseract OCR already installed"
    fi
    
    # Install poppler for PDF processing
    brew install poppler
    
    # Install Tor and Privoxy
    if ! command -v tor &> /dev/null; then
        print_status "Installing Tor..."
        brew install tor
    fi
    
    if ! command -v privoxy &> /dev/null; then
        print_status "Installing Privoxy..."
        brew install privoxy
    fi
else
    print_warning "Unknown system. Please install the following manually:"
    echo "  - tesseract-ocr"
    echo "  - poppler-utils or poppler"
    echo "  - tor"
    echo "  - privoxy"
fi

# Step 3: Create virtual environment
print_header "Setting up Python Virtual Environment..."

if [ ! -d "venv" ]; then
    print_status "Creating virtual environment..."
    python3 -m venv venv
else
    print_status "Virtual environment already exists"
fi

# Activate virtual environment
print_status "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
print_status "Upgrading pip..."
pip install --upgrade pip

# Step 4: Install Python dependencies
print_header "Installing Python Dependencies..."

# Install requirements
if [ -f "requirements.txt" ]; then
    print_status "Installing dependencies from requirements.txt..."
    pip install -r requirements.txt
else
    print_error "requirements.txt not found!"
    exit 1
fi

# Install spaCy English model
print_status "Downloading spaCy English model..."
python -m spacy download en_core_web_sm

# Step 5: Setup configuration
print_header "Setting up Configuration..."

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        print_status "Creating .env file from template..."
        cp .env.example .env
        print_warning "Please edit .env file to add your Gemini API key and other settings!"
    else
        print_error ".env.example not found!"
    fi
else
    print_status ".env file already exists"
fi

# Create logs directory
if [ ! -d "logs" ]; then
    print_status "Creating logs directory..."
    mkdir logs
fi

# Step 6: Initialize database
print_header "Initializing Database..."

print_status "Setting up database..."
python3 -c "from database.models import initialize_database; initialize_database()"

# Step 7: Configure Tor and Privoxy
print_header "Configuring Tor and Privoxy..."

# Check if Privoxy configuration exists
if [ -f "/etc/privoxy/config" ]; then
    print_status "Privoxy configuration found"
    
    # Check if Tor forwarding is configured
    if ! grep -q "forward-socks5" /etc/privoxy/config; then
        print_warning "Privoxy may need configuration for Tor forwarding"
        print_status "Add this line to /etc/privoxy/config:"
        echo "forward-socks5 / 127.0.0.1:9050 ."
    fi
else
    print_warning "Privoxy configuration not found at /etc/privoxy/config"
fi

# Step 8: Run tests
print_header "Running System Tests..."

if [ -f "test_ai_system.py" ]; then
    print_status "Running AI system tests..."
    python3 test_ai_system.py
else
    print_warning "Test script not found, skipping tests"
fi

# Step 9: Final setup
print_header "Final Setup..."

# Make scripts executable
chmod +x launcher.sh
if [ -f "setup.sh" ]; then
    chmod +x setup.sh
fi

print_status "Setup completed successfully!"

echo ""
echo "=============================================================="
echo "🎉 H4$HCR4CK$ AI-Powered System Setup Complete!"
echo "=============================================================="
echo ""
print_status "Next Steps:"
echo "1. Edit .env file to add your Gemini API key:"
echo "   nano .env"
echo ""
echo "2. Start Tor and Privoxy services:"
echo "   sudo systemctl start tor"
echo "   sudo systemctl start privoxy"
echo ""
echo "3. Test the system:"
echo "   python3 test_ai_system.py"
echo ""
echo "4. Start the crawler:"
echo "   bash launcher.sh"
echo ""
print_warning "Important: Make sure to add your GEMINI_API_KEY to the .env file!"
print_status "Get your API key from: https://aistudio.google.com/app/apikey"
echo ""

# Deactivate virtual environment
deactivate
