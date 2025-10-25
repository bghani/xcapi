"""
Downloader for Xeno-canto recordings.

Handles downloading audio files, organizing them into folders, and saving metadata.
"""

import csv
import os
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
    
    def download_recordings(
        self,
        recordings: List[Dict],
        verbose: bool = False,
        skip_existing: bool = True
    ) -> Dict[str, int]:
        """
        Download a list of recordings.
        
        Organizes files into species folders and creates metadata CSV files.
        
        Args:
            recordings: List of recording dictionaries from XenoCantoClient
            verbose: Whether to print progress information
            skip_existing: Skip files that already exist
        
        Returns:
            Dictionary with download statistics (downloaded, skipped, failed)
        """
        stats = {
            'downloaded': 0,
            'skipped': 0,
            'failed': 0
        }
        
        if not recordings:
            if verbose:
                print("No recordings to download.")
            return stats
        
        for i, recording in enumerate(recordings, 1):
            if verbose:
                species_name = f"{recording.get('gen', 'Unknown')} {recording.get('sp', 'unknown')}"
                print(f"[{i}/{len(recordings)}] Processing {species_name} (ID: {recording.get('id', '?')})")
            
            try:
                downloaded = self._download_recording(recording, skip_existing, verbose)
                if downloaded:
                    stats['downloaded'] += 1
                else:
                    stats['skipped'] += 1
            except Exception as e:
                stats['failed'] += 1
                if verbose:
                    print(f"  ERROR: {str(e)}")
        
        self._save_metadata(recordings)
        
        if verbose:
            print(f"\nDownload complete:")
            print(f"  Downloaded: {stats['downloaded']}")
            print(f"  Skipped: {stats['skipped']}")
            print(f"  Failed: {stats['failed']}")
        
        return stats
    
    def _download_recording(
        self,
        recording: Dict,
        skip_existing: bool,
        verbose: bool
    ) -> bool:
        """
        Download a single recording.
        
        Args:
            recording: Recording dictionary
            skip_existing: Skip if file exists
            verbose: Print progress
        
        Returns:
            True if downloaded, False if skipped
        """
        species_folder = self._get_species_folder(recording)
        species_folder.mkdir(parents=True, exist_ok=True)
        
        file_url = recording.get('file', '')
        if not file_url:
            raise ValueError("No file URL found in recording")
        
        if not file_url.startswith('http'):
            file_url = 'https:' + file_url
        
        file_name = recording.get('file-name', f"XC{recording.get('id', 'unknown')}.mp3")
        
        file_name = self._sanitize_filename(file_name)
        
        output_path = species_folder / file_name
        
        if skip_existing and output_path.exists():
            if verbose:
                print(f"  Skipped (already exists)")
            return False
        
        response = requests.get(file_url, stream=True, timeout=60)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        
        with open(output_path, 'wb') as f:
            downloaded = 0
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
        
        if verbose:
            size_mb = downloaded / (1024 * 1024)
            print(f"  Downloaded {file_name} ({size_mb:.2f} MB)")
        
        return True
    
    def _get_species_folder(self, recording: Dict) -> Path:
        """
        Get the folder path for a species.
        
        Creates folders like: output_dir/Genus_species/
        
        Args:
            recording: Recording dictionary
        
        Returns:
            Path to species folder
        """
        genus = recording.get('gen', 'Unknown').strip()
        species = recording.get('sp', 'unknown').strip()
        
        folder_name = f"{genus}_{species}"
        folder_name = self._sanitize_filename(folder_name)
        
        return self.output_dir / folder_name
    
    def _sanitize_filename(self, filename: str) -> str:
        """
        Sanitize a filename to remove problematic characters.
        
        Args:
            filename: Original filename
        
        Returns:
            Sanitized filename
        """
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        
        filename = filename.strip('. ')
        
        return filename
    
    def _save_metadata(self, recordings: List[Dict]):
        """
        Save metadata for all recordings to a CSV file.
        
        Args:
            recordings: List of recording dictionaries
        """
        if not recordings:
            return
        
        metadata_file = self.output_dir / 'metadata.csv'
        
        fieldnames = [
            'id', 'gen', 'sp', 'ssp', 'grp', 'en', 'rec', 'cnt', 'loc',
            'lat', 'lng', 'alt', 'type', 'sex', 'stage', 'method',
            'url', 'file', 'file-name', 'lic', 'q', 'length', 'time',
            'date', 'uploaded', 'rmk', 'animal-seen', 'playback-used',
            'temp', 'regnr', 'auto', 'dvc', 'mic', 'smp'
        ]
        
        with open(metadata_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
            writer.writeheader()
            
            for recording in recordings:
                row = {k: recording.get(k, '') for k in fieldnames}
                
                if 'also' in recording and isinstance(recording['also'], list):
                    row['also'] = '; '.join(recording['also'])
                
                writer.writerow(row)
        
        print(f"Metadata saved to {metadata_file}")
    
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
