# xc-dl: Xeno-canto Downloader

## Overview

A professional Python package for downloading wildlife recordings from the Xeno-canto API (https://xeno-canto.org). Built with uv as the package manager, featuring comprehensive CLI and programmatic interfaces.

**Current State**: Fully functional package with all core features implemented.

## Recent Changes

- **2025-10-25**: Initial package creation
  - Created modular package structure with xc_dl/query.py, client.py, downloader.py, and cli.py
  - Implemented comprehensive query builder supporting all Xeno-canto API v3 search tags
  - Built robust API client with pagination and error handling
  - Created smart downloader with per-species folder organization and CSV metadata export
  - Configured full-featured CLI with argparse supporting all filters
  - Set up pyproject.toml for uv with MIT license and console script entrypoint
  - Installed dependencies and verified CLI functionality

## Project Architecture

### Package Structure
```
xc-dl/
├── xc_dl/
│   ├── __init__.py       # Package initialization and exports
│   ├── query.py          # QueryBuilder class for API queries
│   ├── client.py         # XenoCantoClient for API communication
│   ├── downloader.py     # Downloader for audio files and metadata
│   └── cli.py            # Command-line interface
├── pyproject.toml        # uv package configuration
├── example.py            # Programmatic usage example
├── README.md             # User documentation
└── .gitignore            # Python/project ignores
```

### Key Components

1. **QueryBuilder** (`xc_dl/query.py`)
   - Fluent interface for building search queries
   - Supports all API v3 tags: taxonomic (gen, sp, ssp, fam, grp), geographic (cnt, loc, area, box), quality (q, type, sex, stage), temporal (year, month, since), and metadata filters
   - Handles proper quoting for multi-word values

2. **XenoCantoClient** (`xc_dl/client.py`)
   - Handles API authentication and requests
   - Automatic pagination for large result sets
   - Rate-limit awareness with delays
   - Comprehensive error handling

3. **Downloader** (`xc_dl/downloader.py`)
   - Downloads recordings into per-species folders (Genus_species/)
   - Creates metadata.csv with full recording details
   - Skip existing files option
   - Progress tracking and statistics

4. **CLI** (`xc_dl/cli.py`)
   - Full argparse interface mirroring all API filters
   - Console script entrypoint: `xc-dl`
   - Detailed help and examples
   - Verbose mode for debugging

## User Preferences

- Package manager: uv (as specified)
- License: MIT
- Python version: >=3.8
- Code style: Clean, modular, well-documented with comprehensive docstrings

## Dependencies

- requests: HTTP client for API communication
- Standard library: csv, pathlib, argparse, os, time

## Usage

### Command Line
```bash
# Basic usage
xc-dl --grp Orthoptera --area europe --output_dir ./data

# High-quality bird songs from Spain
xc-dl --grp birds --cnt Spain --type song --q A

# Specific species
xc-dl --gen Larus --sp fuscus --output_dir ./gulls
```

### Python API
```python
from xc_dl import QueryBuilder, XenoCantoClient, Downloader

query = QueryBuilder().group("birds").country("Spain").quality("A").build()
client = XenoCantoClient(api_key="your-key")
recordings = client.search(query)
downloader = Downloader(output_dir="./data")
downloader.download_recordings(recordings, verbose=True)
```

## API Key Setup

Users need a Xeno-canto API key:
1. Register at https://xeno-canto.org
2. Verify email
3. Get key from https://xeno-canto.org/account
4. Set environment variable: `export XENO_CANTO_API_KEY='your-key'`

## Development Notes

- API endpoint: https://xeno-canto.org/api/3/recordings
- Results per page: 50-500 (default 100)
- Automatic pagination handles large datasets
- Downloads organized by species for easy management
- Metadata includes: location, quality, date, recordist, license, and more
