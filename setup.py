"""Setup configuration for Green Needle audio transcription system."""

from setuptools import setup, find_packages
import os

# Read the README file
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Read requirements
def read_requirements(filename):
    with open(filename, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip() and not line.startswith("#")]

# Get version
exec(open("src/green_needle/version.py").read())

setup(
    name="green-needle",
    version=__version__,
    author="Green Needle Team",
    author_email="support@greenneedle.io",
    description="High-quality local audio transcription using OpenAI Whisper",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/green-needle",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Multimedia :: Sound/Audio :: Speech",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    python_requires=">=3.8",
    install_requires=read_requirements("requirements.txt"),
    extras_require={
        "dev": read_requirements("requirements-dev.txt"),
        "gpu": ["torch>=2.0.0", "torchvision", "torchaudio"],
    },
    entry_points={
        "console_scripts": [
            "green-needle=green_needle.cli:main",
        ],
    },
    include_package_data=True,
    package_data={
        "green_needle": ["config/*.yaml", "templates/*"],
    },
)