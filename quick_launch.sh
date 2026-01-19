#!/bin/bash

# Quick Launch Script for AI Gesture Control System
# This script runs stability tests and launches the application

echo "=================================================="
echo "   AI Gesture Control System - Quick Launch"
echo "=================================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo -e "${RED}✗ Virtual environment not found!${NC}"
    echo "Please run: python3 -m venv .venv"
    exit 1
fi

echo -e "${YELLOW}Running stability tests...${NC}"
echo ""

# Run stability tests
.venv/bin/python test_stability.py

# Check if tests passed
if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✓ All tests passed!${NC}"
    echo ""
    echo -e "${YELLOW}Launching Gesture Control System...${NC}"
    echo ""
    echo "Controls:"
    echo "  - Press '▶ Start Camera' to begin"
    echo "  - See GESTURE_CONTROLS.md for all gestures"
    echo "  - Adjust sensitivity/smoothing as needed"
    echo ""
    echo "To stop: Close the window or press Ctrl+C here"
    echo ""
    
    # Launch the application
    .venv/bin/python gesture_control_pro.py
else
    echo ""
    echo -e "${RED}✗ Tests failed! Please fix issues before launching.${NC}"
    echo ""
    echo "Check the error messages above for details."
    exit 1
fi
