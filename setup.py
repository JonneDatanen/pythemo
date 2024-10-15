from setuptools import find_packages, setup

setup(
    name="pythemo",
    version="0.2.0",
    packages=find_packages(),
    install_requires=[
        "httpx",
    ],
    author="Your Name",
    author_email="your.email@example.com",
    description="A Python client for Themo smart thermostats",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    license="MIT",
)
