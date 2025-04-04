"""
NMBS Train Data Package
A package for analyzing, visualizing, and serving NMBS (Belgian Railways) train data
"""

from setuptools import setup, find_packages

setup(
    name="nmbs_data",
    version="0.1.0",
    description="Tools for analyzing and visualizing NMBS (Belgian Railways) train data",
    author="Your Name",
    author_email="your.email@example.com",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "pandas>=1.3.0",
        "matplotlib>=3.4.0",
        "numpy>=1.20.0",
        "dash>=2.0.0",
        "plotly>=5.0.0",
        "folium>=0.12.0",
        "gtfs-realtime-bindings>=1.0.0",
        "protobuf>=3.20.0",
    ],
    python_requires=">=3.7",
    entry_points={
        "console_scripts": [
            "nmbs-data=nmbs_data.main:main",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
    ],
)