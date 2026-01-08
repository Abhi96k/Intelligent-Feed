#!/bin/bash

# Intelligent Feed Frontend Setup Script
# This script sets up the development environment

set -e

echo "================================================"
echo "Intelligent Feed Frontend - Setup"
echo "================================================"
echo ""

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js 16+ first."
    echo "   Visit: https://nodejs.org/"
    exit 1
fi

# Check Node version
NODE_VERSION=$(node -v | cut -d'v' -f2 | cut -d'.' -f1)
if [ "$NODE_VERSION" -lt 16 ]; then
    echo "❌ Node.js version 16+ required. Current version: $(node -v)"
    exit 1
fi

echo "✓ Node.js $(node -v) detected"
echo "✓ npm $(npm -v) detected"
echo ""

# Check if backend is running
echo "Checking backend connectivity..."
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "✓ Backend is running on http://localhost:8000"
else
    echo "⚠️  Backend is not running on http://localhost:8000"
    echo "   The frontend will work, but API calls will fail until backend is started."
fi
echo ""

# Install dependencies
echo "Installing npm dependencies..."
echo "This may take a few minutes..."
npm install

if [ $? -eq 0 ]; then
    echo "✓ Dependencies installed successfully"
else
    echo "❌ Failed to install dependencies"
    exit 1
fi
echo ""

# Create .env.local if it doesn't exist
if [ ! -f .env.local ]; then
    echo "Creating .env.local file..."
    cat > .env.local << EOF
# Intelligent Feed Frontend Environment Variables
# Backend API URL (default uses Vite proxy)
VITE_API_BASE_URL=http://localhost:8000

# API timeout in milliseconds
VITE_API_TIMEOUT=30000

# Enable debug mode
VITE_ENABLE_DEBUG=true
EOF
    echo "✓ .env.local created"
else
    echo "✓ .env.local already exists"
fi
echo ""

echo "================================================"
echo "Setup Complete!"
echo "================================================"
echo ""
echo "Next steps:"
echo ""
echo "1. Ensure backend is running:"
echo "   → Check http://localhost:8000/health"
echo ""
echo "2. Start the development server:"
echo "   → npm run dev"
echo ""
echo "3. Open your browser:"
echo "   → http://localhost:3000"
echo ""
echo "4. Try asking a question like:"
echo "   → 'Why did revenue drop in Q3?'"
echo ""
echo "For more information, see:"
echo "  - QUICKSTART.md"
echo "  - README.md"
echo "  - DEVELOPMENT.md"
echo ""
echo "Happy coding! 🚀"
