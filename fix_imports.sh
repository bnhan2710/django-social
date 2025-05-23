#!/bin/bash

# Script to fix problematic imports in Django models
echo "════════════════════════════════════════════"
echo "🔧 Django Import Fix Script"
echo "════════════════════════════════════════════"

# Check if models.py exists
if [ ! -f "core/models.py" ]; then
    echo "❌ Error: core/models.py not found!"
    exit 1
fi

# Create backup of models.py
echo "📝 Creating backup of models.py..."
cp core/models.py core/models.py.bak
echo "✅ Backup created at core/models.py.bak"

# Fix turtle import
echo "🔍 Checking for problematic imports..."
if grep -q "from turtle import" core/models.py; then
    echo "⚠️ Found problematic 'turtle' import in models.py"
    
    # Replace the problematic import
    sed -i 's/from turtle import update/# Removed problematic import: from turtle import update/' core/models.py
    
    # Check if we need to add a replacement import
    if grep -q "update(" core/models.py; then
        echo "⚠️ Found usage of 'update' function, adding Django equivalent import..."
        # Add Django's update import at the top of the file after the existing imports
        sed -i '1,10s/^import/from django.db.models import update_or_create\nimport/' core/models.py
        # Replace any update() calls with update_or_create() if needed
        sed -i 's/update(/update_or_create(/g' core/models.py
    fi
    
    echo "✅ Fixed turtle import in models.py"
else
    echo "✅ No problematic 'turtle' imports found"
fi

# Check for other common problematic imports
echo "🔍 Checking for other problematic imports..."

# Check for tkinter
if grep -q "import tkinter" core/models.py || grep -q "from tkinter" core/models.py; then
    echo "⚠️ Found tkinter import in models.py. This will cause issues on servers without GUI."
    sed -i 's/import tkinter/# Removed problematic import: import tkinter/' core/models.py
    sed -i 's/from tkinter/# Removed problematic import: from tkinter/' core/models.py
    echo "✅ Fixed tkinter import in models.py"
fi

# Check for pygame
if grep -q "import pygame" core/models.py || grep -q "from pygame" core/models.py; then
    echo "⚠️ Found pygame import in models.py. This will cause issues on servers."
    sed -i 's/import pygame/# Removed problematic import: import pygame/' core/models.py
    sed -i 's/from pygame/# Removed problematic import: from pygame/' core/models.py
    echo "✅ Fixed pygame import in models.py"
fi

echo "════════════════════════════════════════════"
echo "✅ Import checking and fixing complete!"
echo "════════════════════════════════════════════"
echo "📝 If you need to restore the original file, use:"
echo "   cp core/models.py.bak core/models.py"
echo "════════════════════════════════════════════" 