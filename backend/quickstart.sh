#!/bin/bash

# LegalGPT API Quick Start Script

echo "=================================="
echo "LegalGPT API - Quick Start"
echo "=================================="
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found!"
    echo "Creating .env from .env.example..."
    cp .env.example .env
    echo "✓ .env file created"
    echo ""
    echo "⚠️  IMPORTANT: Please edit .env file and add:"
    echo "   - DATABASE_URL (PostgreSQL connection)"
    echo "   - ANTHROPIC_API_KEY (your Anthropic API key)"
    echo "   - SECRET_KEY (generate a secure secret)"
    echo ""
    echo "Press Enter after updating .env file..."
    read
fi

echo "Step 1: Installing dependencies..."
uv sync
echo "✓ Dependencies installed"
echo ""

echo "Step 2: Initializing database..."
uv run python init_db.py
echo "✓ Database initialized"
echo ""

echo "Step 3: Populating vector database with sample documents..."
uv run python populate_vectordb.py
echo "✓ Vector database populated"
echo ""

echo "=================================="
echo "Setup Complete!"
echo "=================================="
echo ""
echo "To start the API server, run:"
echo "  uv run uvicorn main:app --reload"
echo ""
echo "API will be available at:"
echo "  - http://localhost:8000"
echo "  - Docs: http://localhost:8000/docs"
echo ""
echo "Default credentials:"
echo "  Username: demo"
echo "  Password: demo123"
echo ""
