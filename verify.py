#!/usr/bin/env python3
"""Simple verification script for Green Needle installation."""

import sys
import os

print("🔍 Verifying Green Needle installation...")
print("-" * 50)

# Check Python version
python_version = sys.version_info
print(f"Python version: {python_version.major}.{python_version.minor}.{python_version.micro}")
if python_version < (3, 8):
    print("❌ Python 3.8 or higher is required")
    sys.exit(1)
else:
    print("✅ Python version OK")

# Check file structure
files_to_check = [
    ("README.md", "Documentation"),
    ("requirements.txt", "Dependencies list"),
    ("setup.py", "Setup script"),
    ("src/green_needle/__init__.py", "Package init"),
    ("src/green_needle/transcriber.py", "Core module"),
]

all_good = True
for file_path, description in files_to_check:
    if os.path.exists(file_path):
        print(f"✅ {description}: {file_path}")
    else:
        print(f"❌ Missing {description}: {file_path}")
        all_good = False

# Check syntax of Python files
print("\n📝 Checking Python syntax...")
try:
    import py_compile
    src_files = []
    for root, dirs, files in os.walk('src'):
        for file in files:
            if file.endswith('.py'):
                src_files.append(os.path.join(root, file))
    
    errors = 0
    for file_path in src_files:
        try:
            py_compile.compile(file_path, doraise=True)
        except py_compile.PyCompileError:
            print(f"❌ Syntax error in {file_path}")
            errors += 1
            all_good = False
    
    if errors == 0:
        print(f"✅ All {len(src_files)} Python files have valid syntax")
except Exception as e:
    print(f"❌ Error checking syntax: {e}")
    all_good = False

print("\n" + "-" * 50)
if all_good:
    print("✅ Basic verification passed!")
    print("\nTo use Green Needle:")
    print("1. Install dependencies: pip install -r requirements.txt")
    print("2. Install package: pip install -e .")
    print("3. Run: green-needle --help")
else:
    print("❌ Verification failed. Please check the errors above.")
    sys.exit(1)