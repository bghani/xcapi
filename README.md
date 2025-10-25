# xc-dl: Xeno-canto Downloader

A Python package for downloading wildlife recordings from the [Xeno-canto](https://xeno-canto.org) API.

## Features

- **Comprehensive search**: Support for all Xeno-canto API v3 search tags
  - Taxonomic: genus, species, subspecies, family, group, English name
  - Geographic: country, location, area, bounding box, latitude, longitude, altitude
  - Quality: rating, sound type, sex, life stage, recording method
  - Temporal: year, month, upload date, time of day
  - Metadata: recordist, length, license, equipment (device, microphone), sample rate, temperature, and more
- **Automatic pagination**: Handles large result sets seamlessly
- **Organized downloads**: Creates per-species folders with standardized naming
- **Metadata export**: Saves detailed CSV files with recording information
- **CLI and programmatic**: Use as a command-line tool or import as a Python library

## Installation

```bash
uv pip install -e .
```

## Usage

### Command Line

Download all Orthoptera recordings from Europe:

```bash
xc-dl --grp Orthoptera --area europe --output_dir ./data
```

Download high-quality bird songs from Spain:

```bash
xc-dl --grp birds --cnt Spain --type song --q A --output_dir ./recordings
```

Filter by altitude and time of day:

```bash
xc-dl --grp birds --alt 1000-2000 --time "06:00-09:00" --output_dir ./alpine
```

Search by recording equipment and sample rate:

```bash
xc-dl --grp birds --mic "Sennheiser" --smp ">44100" --q A --output_dir ./hifi
```

### Python API

```python
from xc_dl.query import QueryBuilder
from xc_dl.client import XenoCantoClient
from xc_dl.downloader import Downloader

# Build a query
query = QueryBuilder().group("birds").country("Spain").quality("A").build()

# Fetch recordings
client = XenoCantoClient(api_key="your-api-key")
recordings = client.search(query)

# Download
downloader = Downloader(output_dir="./data")
downloader.download_recordings(recordings)
```

## API Key

You need a Xeno-canto API key to use this package. Register at [xeno-canto.org](https://xeno-canto.org) and verify your email to get your key from your [account page](https://xeno-canto.org/account).

Set your API key as an environment variable:

```bash
export XENO_CANTO_API_KEY="your-api-key"
```

## License

MIT
