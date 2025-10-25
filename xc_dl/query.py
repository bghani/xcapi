"""
Query builder for the Xeno-canto API v3.

This module provides a fluent interface for constructing search queries
using all supported Xeno-canto API search tags.
"""

from typing import List, Optional


class QueryBuilder:
    """
    Builder class for constructing Xeno-canto API search queries.
    
    Supports all API v3 search tags including taxonomic filters, geographic
    filters, recording quality, dates, and metadata fields.
    
    Example:
        >>> query = QueryBuilder().genus("Larus").species("fuscus").quality("A").build()
        >>> print(query)
        gen:Larus sp:fuscus q:A
    """
    
    def __init__(self):
        """Initialize an empty query builder."""
        self._tags = []
    
    def _add_tag(self, tag: str, value: str, quote: bool = False) -> 'QueryBuilder':
        """
        Add a tag to the query.
        
        Args:
            tag: The search tag name (e.g., 'gen', 'sp', 'cnt')
            value: The value for the tag
            quote: Whether to quote the value (for multi-word values)
        
        Returns:
            Self for method chaining
        """
        if value:
            if quote or ' ' in value:
                self._tags.append(f'{tag}:"{value}"')
            else:
                self._tags.append(f'{tag}:{value}')
        return self
    
    def genus(self, genus: str) -> 'QueryBuilder':
        """Filter by genus name."""
        return self._add_tag('gen', genus)
    
    def species(self, species: str) -> 'QueryBuilder':
        """Filter by species name (specific epithet or full species name)."""
        return self._add_tag('sp', species, quote=True)
    
    def subspecies(self, subspecies: str) -> 'QueryBuilder':
        """Filter by subspecies name."""
        return self._add_tag('ssp', subspecies, quote=True)
    
    def family(self, family: str) -> 'QueryBuilder':
        """Filter by family name."""
        return self._add_tag('fam', family)
    
    def group(self, group: str) -> 'QueryBuilder':
        """
        Filter by taxonomic group.
        
        Args:
            group: One of 'birds', 'grasshoppers', 'bats'
        """
        return self._add_tag('grp', group)
    
    def english_name(self, name: str) -> 'QueryBuilder':
        """Filter by English common name."""
        return self._add_tag('en', name, quote=True)
    
    def recordist(self, name: str) -> 'QueryBuilder':
        """Filter by recordist name."""
        return self._add_tag('rec', name, quote=True)
    
    def country(self, country: str) -> 'QueryBuilder':
        """Filter by country name."""
        return self._add_tag('cnt', country, quote=True)
    
    def location(self, location: str) -> 'QueryBuilder':
        """Filter by locality name."""
        return self._add_tag('loc', location, quote=True)
    
    def area(self, area: str) -> 'QueryBuilder':
        """
        Filter by continent or region.
        
        Args:
            area: e.g., 'africa', 'asia', 'europe', 'north america', etc.
        """
        return self._add_tag('area', area, quote=True)
    
    def bounding_box(self, lat_min: float, lon_min: float, lat_max: float, lon_max: float) -> 'QueryBuilder':
        """
        Filter by geographic bounding box.
        
        Args:
            lat_min: Minimum latitude
            lon_min: Minimum longitude
            lat_max: Maximum latitude
            lon_max: Maximum longitude
        """
        box_value = f"{lat_min},{lon_min},{lat_max},{lon_max}"
        return self._add_tag('box', box_value)
    
    def quality(self, quality: str) -> 'QueryBuilder':
        """
        Filter by quality rating.
        
        Args:
            quality: One of 'A', 'B', 'C', 'D', 'E', 'no score'
                    Can also use operators like 'A', '>B', etc.
        """
        return self._add_tag('q', quality)
    
    def sound_type(self, sound_type: str) -> 'QueryBuilder':
        """
        Filter by sound type.
        
        Args:
            sound_type: e.g., 'song', 'call', 'drumming', 'alarm call', etc.
        """
        return self._add_tag('type', sound_type, quote=True)
    
    def sex(self, sex: str) -> 'QueryBuilder':
        """
        Filter by sex of the recorded animal.
        
        Args:
            sex: e.g., 'male', 'female', 'uncertain'
        """
        return self._add_tag('sex', sex)
    
    def life_stage(self, stage: str) -> 'QueryBuilder':
        """
        Filter by life stage.
        
        Args:
            stage: e.g., 'adult', 'juvenile', 'subadult', etc.
        """
        return self._add_tag('stage', stage)
    
    def method(self, method: str) -> 'QueryBuilder':
        """
        Filter by recording method.
        
        Args:
            method: e.g., 'field recording', 'in the hand', etc.
        """
        return self._add_tag('method', method, quote=True)
    
    def length(self, length: str) -> 'QueryBuilder':
        """
        Filter by recording length.
        
        Args:
            length: e.g., '10-20', '<30', '>60' (in seconds)
        """
        return self._add_tag('len', length, quote=True)
    
    def year(self, year: str) -> 'QueryBuilder':
        """
        Filter by recording year.
        
        Args:
            year: e.g., '2020', '2015-2020', '>2018'
        """
        return self._add_tag('year', year)
    
    def month(self, month: str) -> 'QueryBuilder':
        """
        Filter by recording month.
        
        Args:
            month: e.g., '1', '6', '1-3' (1=January, 12=December)
        """
        return self._add_tag('month', month)
    
    def since(self, days: int) -> 'QueryBuilder':
        """
        Filter by recordings uploaded in the last N days.
        
        Args:
            days: Number of days to look back
        """
        return self._add_tag('since', str(days))
    
    def license(self, license_type: str) -> 'QueryBuilder':
        """
        Filter by license type.
        
        Args:
            license_type: e.g., 'cc', 'cc-by', 'cc-by-sa', etc.
        """
        return self._add_tag('lic', license_type)
    
    def also(self, species: str) -> 'QueryBuilder':
        """Filter by background species."""
        return self._add_tag('also', species, quote=True)
    
    def animal_seen(self, seen: bool) -> 'QueryBuilder':
        """Filter by whether the animal was seen."""
        value = 'yes' if seen else 'no'
        return self._add_tag('animal-seen', value)
    
    def playback_used(self, used: bool) -> 'QueryBuilder':
        """Filter by whether playback was used."""
        value = 'yes' if used else 'no'
        return self._add_tag('playback-used', value)
    
    def time_of_day(self, time: str) -> 'QueryBuilder':
        """
        Filter by time of day.
        
        Args:
            time: Time in format 'HH:MM' or range like '06:00-12:00'
        """
        return self._add_tag('time', time, quote=True)
    
    def altitude(self, altitude: str) -> 'QueryBuilder':
        """
        Filter by altitude in meters.
        
        Args:
            altitude: e.g., '100-500', '<1000', '>2000'
        """
        return self._add_tag('alt', altitude, quote=True)
    
    def latitude(self, latitude: str) -> 'QueryBuilder':
        """
        Filter by latitude.
        
        Args:
            latitude: e.g., '40-45', '>50'
        """
        return self._add_tag('lat', latitude, quote=True)
    
    def longitude(self, longitude: str) -> 'QueryBuilder':
        """
        Filter by longitude.
        
        Args:
            longitude: e.g., '-10-0', '<-100'
        """
        return self._add_tag('lon', longitude, quote=True)
    
    def number_in_group(self, number: str) -> 'QueryBuilder':
        """
        Filter by number of individuals in the recording.
        
        Args:
            number: e.g., '1', '2-5', '>10'
        """
        return self._add_tag('nr', number)
    
    def catalogue_number(self, number: str) -> 'QueryBuilder':
        """
        Filter by catalogue number.
        
        Args:
            number: e.g., '12345', '>100000'
        """
        return self._add_tag('catnr', number)
    
    def temperature(self, temp: str) -> 'QueryBuilder':
        """
        Filter by temperature during recording.
        
        Args:
            temp: e.g., '20-30', '<10', '>25'
        """
        return self._add_tag('temp', temp)
    
    def registration_number(self, regnr: str) -> 'QueryBuilder':
        """
        Filter by specimen registration number.
        
        Args:
            regnr: Registration number when specimen was collected
        """
        return self._add_tag('regnr', regnr, quote=True)
    
    def automatic_recording(self, is_auto: str) -> 'QueryBuilder':
        """
        Filter by whether recording was automatic (non-supervised).
        
        Args:
            is_auto: 'yes', 'no', or 'unknown'
        """
        return self._add_tag('auto', is_auto)
    
    def device(self, device: str) -> 'QueryBuilder':
        """
        Filter by recording device used.
        
        Args:
            device: Name or model of recording device
        """
        return self._add_tag('dvc', device, quote=True)
    
    def microphone(self, microphone: str) -> 'QueryBuilder':
        """
        Filter by microphone used.
        
        Args:
            microphone: Name or model of microphone
        """
        return self._add_tag('mic', microphone, quote=True)
    
    def sample_rate(self, rate: str) -> 'QueryBuilder':
        """
        Filter by sample rate.
        
        Args:
            rate: e.g., '44100', '48000', '>44100'
        """
        return self._add_tag('smp', rate)
    
    def remarks(self, remarks: str) -> 'QueryBuilder':
        """
        Filter by remarks text.
        
        Args:
            remarks: Search in recordist's remarks field
        """
        return self._add_tag('rmk', remarks, quote=True)
    
    def build(self) -> str:
        """
        Build and return the final query string.
        
        Returns:
            A query string suitable for the Xeno-canto API
        """
        return ' '.join(self._tags) if self._tags else ''
    
    def __str__(self) -> str:
        """Return the query string."""
        return self.build()
