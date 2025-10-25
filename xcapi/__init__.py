"""
xcapi: A command-line and programmatic downloader for the Xeno-canto API.

This package provides tools to search, download, and organize wildlife recordings
from the Xeno-canto database (https://xeno-canto.org).
"""

__version__ = "0.1.0"
__author__ = "xcapi contributors"
__license__ = "MIT"

from xcapi.query import QueryBuilder
from xcapi.client import XenoCantoClient
from xcapi.downloader import Downloader

__all__ = ["QueryBuilder", "XenoCantoClient", "Downloader"]
