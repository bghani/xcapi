# xcapi: Xeno-canto API 

A Python package for downloading animal sound recordings from the [Xeno-canto](https://xeno-canto.org) API.

## Features

- **Comprehensive search**: Support for all Xeno-canto API v3 search tags
  - Taxonomic: genus, species, subspecies, family, group, English name
  - Geographic: country, location, area, bounding box, latitude, longitude, altitude
  - Quality: rating, sound type, sex, life stage, recording method
  - Temporal: year, month, upload date, time of day
  - Metadata: recordist, length, license, equipment (device, microphone), sample rate, temperature, and more

## Installation

Step 1: Clone the repository

```bash
git clone https://github.com/bghani/xcapi.git
cd xcapi
```

Step 2: Install the package

```bash
pip install -e .
```

## Usage (with examples)


### Command Line


You need a Xeno-canto API key to use this package. Register at [xeno-canto.org](https://xeno-canto.org) and verify your email to get your key from your [account page](https://xeno-canto.org/account).

Set your API key as an environment variable:

```bash
export XENO_CANTO_API_KEY="your-api-key"
```

Show all the available command-line options:

```bash
xcapi --help
```

Download all Grasshopper recordings from Europe:

```bash
xcapi --grp grasshoppers --area europe --output_dir ./data
```

Download high-quality bird songs from Spain:

```bash
xcapi --grp birds --cnt Spain --type song --q A --output_dir ./data
```

Filter by altitude and time of day:

```bash
xcapi --grp birds --alt 1000-2000 --time "06:00-09:00" --output_dir ./data
```

Search by sample rate:

```bash
xcapi --grp birds --smp "44100" --q A --output_dir ./data
```


### Python API

```python
from xcapi.query import QueryBuilder
from xcapi.client import XenoCantoClient
from xcapi.downloader import Downloader

# Build a query
query = QueryBuilder().group("birds").country("Spain").quality("A").build()

# Fetch recordings
client = XenoCantoClient(api_key="your-api-key")
recordings = client.search(query)

# Download metadata
downloader = Downloader(output_dir="./data")
downloader._save_metadata(recordings)

# Download recordings and metadata
downloader = Downloader(output_dir="./data")
downloader.download_recordings(recordings)
```






