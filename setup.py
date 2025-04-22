from setuptools import setup, find_packages

setup(
    packages=find_packages(where="src", exclude=["tests", "tests.*"]),
    package_dir={"": "src"}
)