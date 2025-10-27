# xcapi: Xeno-canto API 

A Python package for downloading animal sounds from the [Xeno-canto](https://xeno-canto.org) API.

## Features

- **Comprehensive search**: Support for all [Xeno-canto API v3](https://xeno-canto.org/explore/api) search tags:
  - Taxonomic: genus, species, subspecies, family, group, English name
  - Geographic: country, location, area, bounding box, latitude, longitude, altitude
  - Quality: rating, sound type, sex, life stage, recording method
  - Temporal: year, month, upload date, time of day
  - Metadata: recordist, length, license, equipment (device, microphone), sample rate, temperature, and more
- **Operator and range support**: Use comparisons like <, >, and ranges (10-20) across supported fields.
- **Two easy ways to use it**: You can run searches directly from the command line (CLI) without writing any code, or use it inside your Python scripts (API) with a simple, chainable query builder.

## Installation

Install the package using pip:

```bash
pip install xenocanto-api
```
#### API Key Setup

Starting October 10, 2025 users need a Xeno-canto API key to download recordings from the Xeno-canto API:
1. Register at [https://xeno-canto.org](https://xeno-canto.org)
2. Verify email
3. Get key from [https://xeno-canto.org/account](https://xeno-canto.org/account)


## Usage (with examples)

The package can be used either as a CLI (Command Line Interface) for quick terminal-based commands, or as a Python API for programmatic access through the QueryBuilder, XenoCantoClient, and Downloader classes.

### Command Line (CLI)

Set your API key as an environment variable:

```bash
export XENO_CANTO_API_KEY="your-api-key"
```

Show all the available command-line options:

```bash
xcapi --help
```

Download all Grasshopper recordings and metadata from Europe:

```bash
xcapi --grp grasshoppers --area europe --output_dir ./data
```

Download high-quality bird songs and metadata from France:

```bash
xcapi --grp birds --cnt France --type song --q A --output_dir ./data
```

Download grasshopper recordings while filtering by recordist, altitude and year:

```bash
xcapi --grp grasshoppers --rec "Baudewijn Odé" --alt 1000-2000 --year ">2023" --output_dir ./data
```

Download frog sounds while filtering by sample rate and recording quality:

```bash
xcapi --grp frogs --smp ">44100" --q "<C" --output_dir ./data
```

Download just the metadata:

```bash
xcapi --grp frogs --smp ">44100" --q "<C" --output_dir ./data --metadata_only
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

# Download recordings and metadata
downloader = Downloader(output_dir="./data")
downloader.download_recordings(recordings)

# Download just the metadata
downloader = Downloader(output_dir="./data")
downloader._save_metadata(recordings)


```

In this way, you can chain multiple filters when building a query. Here is a list of all filters that can be used:

 <table>
<tr>
<td width="50%" valign="top">

#### **Taxonomic filters**
- `genus(genus_name)`
- `species(species_name)`
- `subspecies(subspecies_name)`
- `family(family_name)`
- `group(group_name)` – e.g. `"birds"`, `"grasshoppers"`, `"bats"`, `"land mammals"`, `"frogs"`
- `english_name(name)`

#### **Geographic filters**
- `country(country_name)`
- `location(location_name)`
- `area(region_name)` – e.g. `"Europe"`, `"Asia"`, `"Africa"`
- `bounding_box(lat_min, lon_min, lat_max, lon_max)`
- `latitude(range_or_operator)` – e.g. `"40-45"`, `">50"`
- `longitude(range_or_operator)` – e.g. `"-10-0"`, `"<-100"`
- `altitude(range_or_operator)` – e.g. `"100-500"`, `"<1000"`

#### **Quality and type filters**
- `quality(rating)` – one of `"A"`, `"B"`, `"C"`, `"D"`, `"E"`, or operators like `">B"`, `"<C"`
- `sound_type(type)` – e.g. `"song"`, `"call"`, `"drumming"`
- `sex(sex)` – e.g. `"male"`, `"female"`, `"uncertain"`
- `life_stage(stage)` – e.g. `"adult"`, `"juvenile"`
- `method(method)` – e.g. `"field recording"`

</td>
<td width="50%" valign="top">

#### **Temporal filters**
- `year(year_or_range)` – e.g. `"2020"`, `"2015-2020"`, `">2018"`
- `month(month_or_range)` – e.g. `"6"`, `"1-3"`
- `since(days)` – recordings uploaded in the last N days – e.g. `"2"`, `"5"` or since a date – e.g. `"2012-11-09"`.
- `time_of_day(time_or_range)` – e.g. `"06:00"`, `"06:00-12:00"`

#### **Other and metadata filters**
- `recordist(name)` – e.g. `"John Doe"`
- `length(length_or_range)` – e.g. `"10-20"`, `"<30"`, `">60"`
- `license(license_type)` – e.g. `"cc-by"`, `"cc0"`
- `also(species)` – background species
- `animal_seen(True/False)`
- `playback_used(True/False)`
- `number_in_group(value)` – e.g. `"1"`, `"2-5"`, `">10"`
- `catalogue_number(number)` – e.g. `"12345"`, `">100000"`
- `temperature(value)` – e.g. `"20-30"`, `"<10"`
- `registration_number(value)`
- `automatic_recording("yes"|"no"|"unknown")`
- `device(device_name)`
- `microphone(microphone_name)`
- `sample_rate(rate)` – e.g. `"44100"`, `">48000"`, `"44100-96000"`
- `remarks(text)`

</td>
</tr>
</table>
 

Visit [this page](https://xeno-canto.org/help/search#advanced) to get more detailed information on different search tags.







