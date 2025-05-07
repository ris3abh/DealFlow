#!/usr/bin/env python
from setuptools import setup, find_packages

# Read requirements
with open('requirements.txt', 'r') as f:
    requirements = f.read().splitlines()

# Read README for long description
with open('README.md', 'r') as f:
    long_description = f.read()

setup(
    name="dealflow",
    version="0.1.0",  # Will be updated by bumpversion
    description="An advanced sales agent framework built on CAMEL",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Spinutech - Rishabh Sharma",
    author_email="rishabh.sharma@spinutech.com",
    url="https://bsstfs.visualstudio.com/DefaultCollection/DealFlow/_git/DealFlow",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    include_package_data=True,
    install_requires=requirements,
    python_requires=">=3.12",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.12",
    ],
    keywords="sales, ai, camel, llm, agents",
)