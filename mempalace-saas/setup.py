from setuptools import setup, find_packages

setup(
    name="mempalace-cli",
    version="0.1.0",
    packages=find_packages(),
    install_requires=["mcp>=0.1.0"],
    entry_points={
        "console_scripts": [
            "mempalace=mempalace_cli.main:main",
        ],
    },
    author="Your Name",
    description="A secure universal CLI wrapper for the Mempalace SaaS",
    python_requires=">=3.6",
)
