"""
Downloader for Xeno-canto recordings.

Handles downloading audio files, organizing them into folders, and saving metadata.
"""

import csv
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import requests


class Downloader:
    """
    Downloads Xeno-canto recordings and organizes them with metadata.

    Creates a directory structure with per-species folders and saves
    comprehensive metadata to CSV files.

    Example:
        >>> downloader = Downloader(output_dir="./data")
        >>> downloader.download_recordings(recordings, verbose=True)
    """

    def __init__(self, output_dir: str = "./xc_downloads"):
        """
        Initialize the downloader.

        Args:
            output_dir: Base directory for downloads (default: ./xc_downloads)
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Public methods
    # ------------------------------------------------------------------

    def download_recordings(
        self,
        recordings: List[Dict],
        verbose: bool = False,
        redownload: bool = False
    ) -> Dict[str, int]:
        """
        Download a list of recordings.

        By default, skips recordings already present in xcapi_runs.json or,
        if that does not exist, bootstrapped from metadata.csv. Use
        redownload=True to ignore existing records and start completely fresh.

        Args:
            recordings: List of recording dictionaries from XenoCantoClient
            verbose: Whether to print progress information
            redownload: If True, re-download everything and overwrite existing records

        Returns:
            Dictionary with download statistics (downloaded, skipped, failed)
        """
        stats = {'downloaded': 0, 'skipped': 0, 'failed': 0}

        if not recordings:
            if verbose:
                print("No recordings to download.")
            return stats

        # Determine which IDs to skip
        existing_ids = set()
        if not redownload:
            existing_ids = self._load_existing_ids(verbose=verbose, allow_bootstrap=True)

        new_recordings = []

        for i, recording in enumerate(recordings, 1):
            rec_id = str(recording.get('id', ''))
            species_name = f"{recording.get('gen', 'Unknown')} {recording.get('sp', 'unknown')}"

            if rec_id in existing_ids:
                stats['skipped'] += 1
                if verbose:
                    print(f"[{i}/{len(recordings)}] Skipping {species_name} (ID: {rec_id}) — already downloaded")
                continue

            if verbose:
                print(f"[{i}/{len(recordings)}] Downloading {species_name} (ID: {rec_id})")

            try:
                self._download_recording(recording, verbose)
                stats['downloaded'] += 1
                new_recordings.append(recording)
            except Exception as e:
                stats['failed'] += 1
                if verbose:
                    print(f"  ERROR: {str(e)}")

        # Persist results
        if new_recordings:
            self._append_metadata(new_recordings, redownload=redownload)
            self._update_runs(new_recordings, redownload=redownload)
        elif redownload and not new_recordings:
            # redownload requested but nothing came back — still reset files
            self._append_metadata([], redownload=True)
            self._update_runs([], redownload=True)

        if verbose:
            print(f"\nDownload complete:")
            print(f"  Downloaded: {stats['downloaded']}")
            print(f"  Skipped:    {stats['skipped']}")
            print(f"  Failed:     {stats['failed']}")

        return stats

    def save_metadata_only(
        self,
        recordings: List[Dict],
        verbose: bool = False
    ) -> str:
        """
        Save only metadata for recordings not yet downloaded to metadata_only.csv.

        Computes the delta between what xeno-canto returned and what has already
        been downloaded (using xcapi_runs.json, or bootstrapped from metadata.csv).
        Overwrites metadata_only.csv fresh on every run.

        Does NOT modify metadata.csv or xcapi_runs.json.

        Args:
            recordings: List of recording dictionaries from XenoCantoClient
            verbose: Whether to print progress information

        Returns:
            Path to the saved metadata_only.csv file
        """
        if not recordings:
            if verbose:
                print("No recordings returned by query.")
            return ""

        # Load existing downloaded IDs (json first, then bootstrap from csv)
        existing_ids = self._load_existing_ids(
            verbose=verbose,
            allow_bootstrap=True,
            write_bootstrap=False
        )

        # Compute delta — only recordings not yet downloaded
        new_recordings = [
            r for r in recordings
            if str(r.get('id', '')) not in existing_ids
        ]

        n_total = len(recordings)
        n_new = len(new_recordings)
        n_skip = n_total - n_new

        if verbose:
            print(f"Query returned {n_total} recordings.")
            print(f"  Already downloaded: {n_skip}")
            print(f"  New (not yet downloaded): {n_new}")

        metadata_only_file = self.output_dir / 'metadata_only.csv'

        if n_new == 0:
            # Write an empty file with just the header so the user knows it ran
            self._write_csv(metadata_only_file, [], mode='w')
            if verbose:
                print("No new recordings to report. metadata_only.csv cleared.")
        else:
            self._write_csv(metadata_only_file, new_recordings, mode='w')
            if verbose:
                print(f"✓ metadata_only.csv written with {n_new} new recording(s) → {metadata_only_file}")

        return str(metadata_only_file)

    def get_download_info(self) -> Dict:
        """
        Get information about existing downloads.

        Returns:
            Dictionary with statistics about downloaded files
        """
        total_files = 0
        total_size = 0
        species_folders = []

        if not self.output_dir.exists():
            return {
                'total_files': 0,
                'total_size_mb': 0,
                'species_count': 0,
                'species_folders': []
            }

        for item in self.output_dir.iterdir():
            if item.is_dir():
                species_folders.append(item.name)
                for file in item.iterdir():
                    if file.is_file():
                        total_files += 1
                        total_size += file.stat().st_size

        return {
            'total_files': total_files,
            'total_size_mb': total_size / (1024 * 1024),
            'species_count': len(species_folders),
            'species_folders': sorted(species_folders)
        }

    # ------------------------------------------------------------------
    # ID tracking
    # ------------------------------------------------------------------

    def _load_existing_ids(
        self,
        verbose: bool = False,
        allow_bootstrap: bool = False,
        write_bootstrap: bool = True
    ) -> set:
        """
        Return the set of all previously downloaded recording IDs.

        Checks xcapi_runs.json first. If that does not exist and
        allow_bootstrap is True, falls back to reading metadata.csv.
        write_bootstrap controls whether the bootstrapped result is
        persisted to xcapi_runs.json — set to False for metadata-only
        runs so they never create or modify xcapi_runs.json.

        Args:
            verbose: Print status messages
            allow_bootstrap: Whether to bootstrap from metadata.csv if
                             xcapi_runs.json is missing
            write_bootstrap: Whether to persist the bootstrapped JSON to disk

        Returns:
            Set of recording IDs (strings)
        """
        runs_path = self.output_dir / 'xcapi_runs.json'
        metadata_path = self.output_dir / 'metadata.csv'

        # 1. JSON exists — use it directly
        if runs_path.exists():
            runs = json.loads(runs_path.read_text(encoding='utf-8'))
            all_ids = set(str(rid) for ids in runs.values() for rid in ids)
            if verbose:
                print(f"Found {len(all_ids)} previously downloaded IDs in xcapi_runs.json")
            return all_ids

        # 2. JSON missing but CSV exists and bootstrap is allowed
        if allow_bootstrap and metadata_path.exists():
            if verbose:
                print("xcapi_runs.json not found — bootstrapping from metadata.csv")
            ids = []
            with open(metadata_path, newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row.get('id'):
                        ids.append(str(row['id']))
            if write_bootstrap:
                runs = {"first_run_unknown_date": ids}
                runs_path.write_text(json.dumps(runs, indent=2), encoding='utf-8')
                if verbose:
                    print(f"Bootstrapped xcapi_runs.json with {len(ids)} IDs from metadata.csv")
            else:
                if verbose:
                    print(f"Found {len(ids)} previously downloaded IDs in metadata.csv")
            return set(ids)

        # 3. Nothing found
        if verbose:
            print("No previous download records found — downloading everything")
        return set()

    def _update_runs(self, recordings: List[Dict], redownload: bool = False):
        """
        Update xcapi_runs.json with newly downloaded recording IDs.

        Args:
            recordings: Newly downloaded recordings
            redownload: If True, overwrite runs file with just this run
        """
        runs_path = self.output_dir / 'xcapi_runs.json'
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
        new_ids = [str(r['id']) for r in recordings]

        if redownload:
            runs = {timestamp: new_ids}
        else:
            if runs_path.exists():
                runs = json.loads(runs_path.read_text(encoding='utf-8'))
            else:
                runs = {}
            runs[timestamp] = new_ids

        runs_path.write_text(json.dumps(runs, indent=2), encoding='utf-8')

    # ------------------------------------------------------------------
    # CSV helpers
    # ------------------------------------------------------------------

    FIELDNAMES = [
        'id', 'gen', 'sp', 'ssp', 'grp', 'en', 'rec', 'cnt', 'loc',
        'lat', 'lon', 'alt', 'type', 'sex', 'stage', 'method',
        'url', 'file', 'file-name', 'lic', 'q', 'length', 'time',
        'date', 'uploaded', 'rmk', 'animal-seen', 'playback-used',
        'temp', 'regnr', 'auto', 'dvc', 'mic', 'smp'
    ]

    def _write_csv(self, path: Path, recordings: List[Dict], mode: str = 'a'):
        """
        Write recordings to a CSV file.

        Args:
            path: Destination file path
            recordings: List of recording dictionaries
            mode: 'w' to overwrite, 'a' to append
        """
        file_exists = path.exists() and mode == 'a'

        with open(path, mode, newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(
                f, fieldnames=self.FIELDNAMES, extrasaction='ignore'
            )
            if not file_exists:
                writer.writeheader()
            for recording in recordings:
                row = {k: recording.get(k, '') for k in self.FIELDNAMES}
                if 'also' in recording and isinstance(recording['also'], list):
                    row['also'] = '; '.join(recording['also'])
                writer.writerow(row)

    def _append_metadata(self, recordings: List[Dict], redownload: bool = False):
        """
        Append new recording metadata to metadata.csv, or overwrite if redownload.

        Args:
            recordings: List of recording dictionaries
            redownload: If True, overwrite the file
        """
        metadata_file = self.output_dir / 'metadata.csv'
        mode = 'w' if redownload else 'a'
        self._write_csv(metadata_file, recordings, mode=mode)
        if recordings:
            print(f"Metadata saved to {metadata_file}")

    # ------------------------------------------------------------------
    # Download helpers
    # ------------------------------------------------------------------

    def _download_recording(self, recording: Dict, verbose: bool) -> None:
        """
        Download a single recording to its species folder.

        Args:
            recording: Recording dictionary
            verbose: Print progress
        """
        species_folder = self._get_species_folder(recording)
        species_folder.mkdir(parents=True, exist_ok=True)

        file_url = recording.get('file', '')
        if not file_url:
            raise ValueError("No file URL found in recording")

        if not file_url.startswith('http'):
            file_url = 'https:' + file_url

        file_name = recording.get(
            'file-name', f"XC{recording.get('id', 'unknown')}.mp3"
        )
        file_name = self._sanitize_filename(file_name)
        output_path = species_folder / file_name

        response = requests.get(file_url, stream=True, timeout=60)
        response.raise_for_status()

        with open(output_path, 'wb') as f:
            downloaded = 0
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)

        if verbose:
            size_mb = downloaded / (1024 * 1024)
            print(f"  ✓ {file_name} ({size_mb:.2f} MB)")

    def _get_species_folder(self, recording: Dict) -> Path:
        """
        Return the species subfolder path for a recording.

        Args:
            recording: Recording dictionary

        Returns:
            Path to species folder (e.g. output_dir/Turdus_merula/)
        """
        genus = recording.get('gen', 'Unknown').strip()
        species = recording.get('sp', 'unknown').strip()
        folder_name = self._sanitize_filename(f"{genus}_{species}")
        return self.output_dir / folder_name

    def _sanitize_filename(self, filename: str) -> str:
        """
        Remove characters that are invalid in file/folder names.

        Args:
            filename: Original filename

        Returns:
            Sanitized filename
        """
        for char in '<>:"/\\|?*':
            filename = filename.replace(char, '_')
        return filename.strip('. ')