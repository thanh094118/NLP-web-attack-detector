#!/bin/bash

echo "Setting up project environment..."

echo "Checking Python environment..."
if command -v python3 &> /dev/null; then
    PYTHON_BIN="python3"
elif command -v python &> /dev/null; then
    PYTHON_BIN="python"
else
    echo "Python not found. Please install Python 3.11+ first."
    exit 1
fi

PYTHON_VERSION=$($PYTHON_BIN -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
PYTHON_MAJOR=$($PYTHON_BIN -c "import sys; print(sys.version_info.major)")
PYTHON_MINOR=$($PYTHON_BIN -c "import sys; print(sys.version_info.minor)")
if [ "$PYTHON_MAJOR" -lt 3 ] || { [ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 11 ]; }; then
    echo "Python $PYTHON_VERSION detected. This project requires Python >= 3.11."
    exit 1
fi
echo "Using $PYTHON_BIN (Python $PYTHON_VERSION)"

mkdir -p data

cd data

echo ""
echo "Downloading dataset from Google Drive..."
echo "Folder: SR-BH 2020 Dataset"
echo ""

FOLDER_ID="1CyGzbLDo3qDNyGOoOESy3cgebxyQKK4D"

download_with_gdown() {
    if ! command -v gdown &> /dev/null; then
        echo "gdown not found. Installing gdown..."
        $PYTHON_BIN -m pip install gdown
    fi
    
    echo "Downloading folder using gdown..."
    gdown --folder "https://drive.google.com/drive/folders/${FOLDER_ID}" -O .
}

download_with_python_gdown() {
    $PYTHON_BIN -c "
import gdown
import os

folder_id = '${FOLDER_ID}'
url = f'https://drive.google.com/drive/folders/{folder_id}'
gdown.download_folder(url, quiet=False, use_cookies=False)
" 2>/dev/null
}

if command -v gdown &> /dev/null; then
    download_with_gdown
elif $PYTHON_BIN -c "import gdown" 2>/dev/null; then
    download_with_python_gdown
else
    echo "Installing gdown..."
    $PYTHON_BIN -m pip install gdown -q
    download_with_gdown
fi

if [ $? -eq 0 ]; then
    echo ""
    echo "Dataset downloaded successfully to ./data/"
else
    echo ""
    echo "Download failed. Trying alternative method..."
    echo "Please manually download from:"
    echo "https://drive.google.com/drive/folders/${FOLDER_ID}"
    echo "and place contents in ./data/ folder"
fi

cd ..

echo ""
echo "=========================================="
echo "Installing Python dependencies..."
echo "=========================================="

if [ -f "requirements.txt" ]; then
    echo "Found requirements.txt"

    $PYTHON_BIN -m pip install -r requirements.txt
    
    if [ $? -eq 0 ]; then
        echo ""
        echo "Dependencies installed successfully"
    else
        echo ""
        echo "Failed to install dependencies"
    fi
else
    echo "requirements.txt not found in current directory"
    echo "Please create requirements.txt with necessary packages"
fi

echo ""
echo "=========================================="
echo "Setup complete!"
echo "=========================================="
echo ""
echo "Data location: ./data/"
echo ""
echo "To verify:"
echo "  ls -la ./data/"
echo ""
