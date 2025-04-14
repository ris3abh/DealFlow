from setuptools import setup, find_packages

setup(
    name="dealflow",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "camel-ai[all]==0.2.44",
        "python-dotenv",
        "requests",
    ],
    author="Rishabh Sharma",
    author_email="rishabh.sharma@spinutech.com",
    description="A sales agent framework built on CAMEL",
    keywords="ai, sales, agent, camel",
    python_requires=">=3.12",
)