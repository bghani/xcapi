# xcapi: Xeno-canto API

A Python package for downloading animal sound recordings from the [Xeno-canto](https://xeno-canto.org) API. Works with birds, grasshoppers, bats, frogs, and more.

No programming knowledge required — xcapi can be used entirely from the command line.

## Features

- **Comprehensive search**: Support for all [Xeno-canto API v3](https://xeno-canto.org/explore/api) search tags:
  - Taxonomic: genus, species, subspecies, family, group, English name
  - Geographic: country, location, area, bounding box, latitude, longitude, altitude
  - Quality: rating, sound type, sex, life stage, recording method
  - Temporal: year, month, upload date, time of day
  - Metadata: recordist, length, license, equipment (device, microphone), sample rate, temperature, and more
- **Operator and range support**: Use comparisons like `<`, `>`, and ranges (e.g. `10-20`) across supported fields.
- **Smart incremental downloads**: xcapi remembers what you have already downloaded and only fetches new recordings on repeat runs — no duplicate downloads, no wasted bandwidth.
- **Preview before downloading**: Use `--metadata_only` to see what a query would return and how many new recordings would be added, without downloading any audio.
- **Two easy ways to use it**: Run searches directly from the command line (CLI) without writing any code, or use it inside Python scripts with a simple, chainable query builder.

## Installation

```bash
pip install xenocanto-api
```

## API Key Setup

Starting October 10, 2025, a Xeno-canto API key is required to download recordings:

1. Register at [https://xeno-canto.org](https://xeno-canto.org)
2. Verify your email
3. Get your key from [https://xeno-canto.org/account](https://xeno-canto.org/account)

## Output Files

xcapi creates and manages the following files inside your `--output_dir`:

| File | Description |
|---|---|
| `metadata.csv` | Metadata for all downloaded recordings. Grows with each download run. Never overwritten unless `--redownload` is used. |
| `xcapi_runs.json` | Internal log of downloaded recording IDs, organised by timestamp. Used to skip already-downloaded recordings on future runs. As IDs are stored by download date, this file also serves as a download history that can be useful for tracking dataset growth over time or for reproducibility purposes. |
| `metadata_only.csv` | Created by `--metadata_only` runs. Contains only recordings not yet downloaded — a preview of what a real download would add. Overwritten fresh on each `--metadata_only` run. |

Audio files are saved into per-species subfolders inside `output_dir`, e.g. `output_dir/Turdus_merula/`.

> **Note**: `metadata.csv` and `xcapi_runs.json` are only updated by real download runs. Running `--metadata_only` never modifies them.

## Usage

### Command Line (CLI)

#### API key setup

**Option 1: Environment variable (recommended)**
```bash
export XENO_CANTO_API_KEY="your-api-key"
```

**Option 2: Pass it directly each time**
```bash
xcapi --api_key "your-api-key" --grp birds --cnt Spain
```

Show all available options:
```bash
xcapi --help
```

---

#### Downloading recordings

Download all grasshopper recordings from Europe:
```bash
xcapi --grp grasshoppers --area europe --output_dir ./data
```

Download high-quality bird songs from France:
```bash
xcapi --grp birds --cnt France --type song --q A --output_dir ./data
```

Download grasshopper recordings filtered by recordist, altitude, and year:
```bash
xcapi --grp grasshoppers --rec "Baudewijn Odé" --alt 1000-2000 --year ">2023" --output_dir ./data
```

Download frog sounds filtered by sample rate and quality:
```bash
xcapi --grp frogs --smp ">44100" --q "<C" --output_dir ./data
```

**Re-run the same command** — xcapi will automatically skip recordings already downloaded and only fetch new ones. Note that skipping only works when you point to the same `--output_dir` as a previous download, and that directory contains either `xcapi_runs.json` or `metadata.csv`:
```bash
xcapi --grp frogs --smp ">44100" --q "<C" --output_dir ./data
```

---

#### Previewing before downloading

Use `--metadata_only` to check what a query returns and how many recordings you don't have yet, without downloading any audio. Results are saved to `metadata_only.csv`:

```bash
xcapi --grp birds --cnt France --output_dir ./data --metadata_only
```

This is useful for estimating download size or checking for new additions before committing to a full download.

---

#### Re-downloading everything from scratch

Use `--redownload` to ignore previous download records and start completely fresh. This re-downloads all recordings and overwrites `metadata.csv` and `xcapi_runs.json`:

```bash
xcapi --grp birds --cnt France --output_dir ./data --redownload
```

---

### Python API

```python
from xcapi.query import QueryBuilder
from xcapi.client import XenoCantoClient
from xcapi.downloader import Downloader

# Set up client with your API key
client = XenoCantoClient(api_key="your-api-key")

# Alternatively, use a .env file to avoid passing the key each time:
# Create a file called .env in your working directory and add:
# XENO_CANTO_API_KEY=your-api-key
# Then simply run:
client = XenoCantoClient()

# Build a query
query = QueryBuilder().group("birds").country("Spain").quality("A").build()

# Fetch recording metadata from Xeno-canto
recordings = client.search(query)

# Download recordings
# xcapi will skip recordings already downloaded and only fetch new ones
downloader = Downloader(output_dir="./data")
downloader.download_recordings(recordings)

# Preview what's new without downloading audio
# Writes metadata_only.csv with recordings not yet downloaded
downloader.save_metadata_only(recordings)

# Re-download everything from scratch
downloader.download_recordings(recordings, redownload=True)
```

---

### Available query filters

You can chain multiple filters when building a query:

<table>
<tr>
<td width="50%" valign="top">

#### Taxonomic filters
- `genus(genus_name)`
- `species(species_name)`
- `subspecies(subspecies_name)`
- `family(family_name)`
- `group(group_name)` – e.g. `"birds"`, `"grasshoppers"`, `"bats"`, `"land mammals"`, `"frogs"`
- `english_name(name)`

#### Geographic filters
- `country(country_name)`
- `location(location_name)`
- `area(region_name)` – e.g. `"Europe"`, `"Asia"`, `"Africa"`
- `bounding_box(lat_min, lon_min, lat_max, lon_max)`
- `latitude(range_or_operator)` – e.g. `"40-45"`, `">50"`
- `longitude(range_or_operator)` – e.g. `"-10-0"`, `"<-100"`
- `altitude(range_or_operator)` – e.g. `"100-500"`, `"<1000"`

#### Quality and type filters
- `quality(rating)` – one of `"A"`, `"B"`, `"C"`, `"D"`, `"E"`, or operators like `">B"`, `"<C"`
- `sound_type(type)` – e.g. `"song"`, `"call"`, `"drumming"`
- `sex(sex)` – e.g. `"male"`, `"female"`
- `life_stage(stage)` – e.g. `"adult"`, `"juvenile"`
- `method(method)` – e.g. `"field recording"`

</td>
<td width="50%" valign="top">

#### Temporal filters
- `year(year_or_range)` – e.g. `"2020"`, `"2015-2020"`, `">2018"`
- `month(month_or_range)` – e.g. `"6"`, `"1-3"`
- `since(days)` – recordings uploaded in the last N days – e.g. `"2"`, `"5"` or since a date – e.g. `"2012-11-09"`
- `time_of_day(time_or_range)` – e.g. `"06:00"`, `"06:00-12:00"`

#### Other and metadata filters
- `recordist(name)` – e.g. `"Raziya Qadri"`
- `length(length_or_range)` – e.g. `"10-20"`, `"<30"`, `">60"`
- `license(license_type)` – e.g. `"cc-by"`, `"cc0"`
- `also(species)` – background species
- `animal_seen(True/False)`
- `playback_used(True/False)`
- `xc_number(value)` – e.g. `"76967"`, `"88888-88890"`, `">76967"`
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

Visit [this page](https://xeno-canto.org/help/search#advanced) for more detail on search tags.
