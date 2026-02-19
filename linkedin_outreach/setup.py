from setuptools import setup, find_packages

setup(
    name="linkedin-outreach",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "linkedin-api>=2.2.1",
        "jinja2>=3.1.0",
        "pyyaml>=6.0",
        "schedule>=1.2.0",
        "rich>=13.0.0",
        "click>=8.1.0",
        "faker>=22.0.0",
    ],
    entry_points={
        "console_scripts": [
            "linkedin-outreach=linkedin_outreach.cli:main",
        ],
    },
)
