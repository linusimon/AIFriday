#!/bin/bash
echo "Setting up Intelligent Task Routing Backend..."

# Required Python version
REQUIRED_VERSION="3.12"
TARGET_VERSION="3.12.13"

# Function to check Python version
check_python_version() {
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
        MAJOR_MINOR=$(echo $PYTHON_VERSION | cut -d. -f1,2)
        
        if [ "$MAJOR_MINOR" == "$REQUIRED_VERSION" ]; then
            echo "✓ Found compatible Python version: $PYTHON_VERSION"
            return 0
        fi
    fi
    return 1
}

# Function to install Python using pyenv
install_python_with_pyenv() {
    echo "Attempting to install Python $TARGET_VERSION using pyenv..."
    
    if ! command -v pyenv &> /dev/null; then
        echo "pyenv is not installed. Installing pyenv..."
        echo "Visit: https://github.com/pyenv/pyenv#installation"
        echo ""
        echo "Quick install (Linux/macOS):"
        echo "curl https://pyenv.run | bash"
        echo ""
        read -p "Press Enter after installing pyenv, or Ctrl+C to exit..."
        
        if ! command -v pyenv &> /dev/null; then
            echo "❌ pyenv still not found. Please install manually."
            return 1
        fi
    fi
    
    echo "Installing Python $TARGET_VERSION with pyenv..."
    pyenv install $TARGET_VERSION
    pyenv local $TARGET_VERSION
    
    # Reload pyenv
    eval "$(pyenv init --path)"
    eval "$(pyenv init -)"
    
    return 0
}

# Check for compatible Python version
if ! check_python_version; then
    echo "⚠ Python $REQUIRED_VERSION not found."
    echo "Current Python version: $(python3 --version 2>&1 || echo 'Not found')"
    echo ""
    
    read -p "Would you like to install Python $TARGET_VERSION using pyenv? (y/n): " -n 1 -r
    echo ""
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        install_python_with_pyenv
        
        if ! check_python_version; then
            echo "❌ Failed to install Python $TARGET_VERSION"
            echo "Please install Python $REQUIRED_VERSION manually and run this script again."
            exit 1
        fi
    else
        echo "⚠ Warning: Continuing with current Python version may cause compatibility issues."
        read -p "Press Enter to continue anyway, or Ctrl+C to exit..."
    fi
fi

# Determine which Python to use
if command -v pyenv &> /dev/null && [ -f ".python-version" ]; then
    PYTHON_CMD="python"
else
    PYTHON_CMD="python3"
fi

echo "Using Python: $($PYTHON_CMD --version)"
echo ""

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    $PYTHON_CMD -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
$PYTHON_CMD -m pip install --upgrade pip

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Create necessary directories
mkdir -p uploads
mkdir -p faiss_index
mkdir -p data

echo ""
echo "Setup complete!"
echo ""
echo "Next steps:"
echo "1. Update .env file with your API keys"
echo "2. Run ./start.sh to start the server"
echo ""
read -p "Press Enter to continue..."
