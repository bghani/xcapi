"""
xc-dl: A command-line and programmatic downloader for the Xeno-canto API.

This package provides tools to search, download, and organize wildlife recordings
from the Xeno-canto database (https://xeno-canto.org).
"""

__version__ = "0.1.0"
__author__ = "xc-dl contributors"
__license__ = "MIT"

from xc_dl.query import QueryBuilder
from xc_dl.client import XenoCantoClient
from xc_dl.downloader import Downloader

__all__ = ["QueryBuilder", "XenoCantoClient", "Downloader"]
