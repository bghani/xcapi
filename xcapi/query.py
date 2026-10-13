"""
Query builder for the Xeno-canto API v3.

This module provides a fluent interface for constructing search queries
using all supported Xeno-canto API search tags.
"""

from typing import List, Optional
import re

_INT_RANGE = re.compile(r"^(\d+)-(\d+)$")
_FLOAT_RANGE = re.compile(r"^(-?\d+(?:\.\d+)?)-(-?\d+(?:\.\d+)?)$")
_XC_NUMBER = re.compile(r"^\d+(-\d+)?$")


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
        self._lat_range = None
        self._lon_range = None
        self._has_box = False
    
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
        if not value:
            return self
        # Detect range pattern like 10-15 or 2020-2024 (numbers with dash)
        is_range = bool(re.match(r'^\d+(\-\d+)?$', value))

        # Should we quote it?
        if (
            not is_range and
            (quote or ' ' in value or value.startswith(('>', '<', '=')))
        ):
            if not (value.startswith('"') and value.endswith('"')):
                value = f'"{value}"'

        self._tags.append(f"{tag}:{value}")
        return self
    
    def _bounded_range(self, tag: str, value) -> 'QueryBuilder':
        """
        Xeno-canto ignores 'a-b' ranges for some tags and silently uses only
        the first value. Send such ranges as tag:">a-1" tag:"<b+1" instead
        (repeated tags are combined with AND by the API).
        """
        value = str(value).strip()
        m = _INT_RANGE.match(value)
        if m:
            lo, hi = int(m.group(1)), int(m.group(2))
            if lo > hi:
                raise ValueError(f"Invalid {tag} range {value!r}: start is greater than end")
            self._tags.append(f'{tag}:">{lo - 1}"')
            self._tags.append(f'{tag}:"<{hi + 1}"')
            return self
        return self._add_tag(tag, value)

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
            group: One of 'birds', 'grasshoppers', 'bats', 'land mammals', 'frogs', 'soundscape'
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
            area: one of 'africa', 'america', 'asia', 'australia', 'europe'
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
        self._has_box = True
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
            year: e.g., '2020', '>2018', '<2000', or a range '2015-2020'
        """
        return self._bounded_range('year', year)
    
    def month(self, month: str) -> 'QueryBuilder':
        """
        Filter by recording month.
        
        Args:
            month: e.g., '6', '>8', '<4', or a range '1-3' (1=January, 12=December)
        """
        return self._bounded_range('month', month)
    
    def since(self, days: int) -> 'QueryBuilder':
        """
        Filter by upload date.
        
        Args:
            days: Number of days to look back (e.g. 3), or a date
                  'YYYY-MM-DD' to get recordings uploaded since that date
        """
        return self._add_tag('since', str(days))
    
    def license(self, license_type: str) -> 'QueryBuilder':
        """
        Filter by license type.
        
        Args:
            license_type: Xeno-canto license code, e.g. 'BY', 'BY-NC', 'BY-SA',
                    'BY-NC-SA', 'BY-ND', 'BY-NC-ND', or 'PD' (public domain).
        """
        return self._add_tag('lic', license_type)
    
    def also(self, species: str) -> 'QueryBuilder':
        """Filter by background species."""
        return self._add_tag('also', species, quote=True)
    
    def id_questioned(self, questioned: bool) -> 'QueryBuilder':
        """emits id?:yes or id?:no"""
        value = 'yes' if questioned else 'no'
        return self._add_tag('id?', value)
    
    def animal_seen(self, seen: bool) -> 'QueryBuilder':
        """Filter by whether the animal was seen."""
        value = 'yes' if seen else 'no'
        return self._add_tag('seen', value)
    
    def playback_used(self, used: bool) -> 'QueryBuilder':
        """Filter by whether playback was used."""
        value = 'yes' if used else 'no'
        return self._add_tag('playback', value)
    
    def latitude(self, latitude: str) -> 'QueryBuilder':
        """
        Filter by latitude.
        
        Args:
            latitude: e.g., '52.1' (matches within 1 degree), '>66.5',
                      or a range '40-45' (sent as a bounding box)
        """
        m = _FLOAT_RANGE.match(str(latitude).strip())
        if m:
            self._lat_range = (m.group(1), m.group(2))
            return self
        return self._add_tag('lat', latitude, quote=True)
    
    def longitude(self, longitude: str) -> 'QueryBuilder':
        """
        Filter by longitude.
        
        Args:
            longitude: e.g., '4.9' (matches within 1 degree), '<-100',
                       or a range '-10-0' (sent as a bounding box)
        """
        m = _FLOAT_RANGE.match(str(longitude).strip())
        if m:
            self._lon_range = (m.group(1), m.group(2))
            return self
        return self._add_tag('lon', longitude, quote=True)
        
    
    def xc_number(self, number: str) -> 'QueryBuilder':
        """
        Filter by xeno-canto catalogue number.
        
        Args:
            number: an exact number ('76967') or a range ('88888-88890').
                    Xeno-canto does not support < or > for this tag.
        """
        number = str(number).strip()
        if not _XC_NUMBER.match(number):
            raise ValueError(
                f"xc_number must be an exact number or a range like '1-799999', got {number!r}. "
                "Xeno-canto does not support < or > for nr."
            )
        return self._add_tag('nr', number)
    
    def temperature(self, temp: str) -> 'QueryBuilder':
        """
        Filter by temperature during recording (grasshoppers only).
        
        Args:
            temp: e.g., '25' (25-26 °C), '>20', '<10', or a range '20-30'
        """
        return self._bounded_range('temp', temp)
    
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
            rate: e.g., '44100', '>48000', or a range '44100-96000'
        """
        return self._bounded_range('smp', rate)
    
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
        tags = list(self._tags)
        if self._lat_range or self._lon_range:
            if self._has_box:
                raise ValueError("Use either bounding_box() or a latitude/longitude range, not both.")
            la = self._lat_range or ('-90', '90')
            lo = self._lon_range or ('-180', '180')
            tags.append(f"box:{la[0]},{lo[0]},{la[1]},{lo[1]}")
        return ' '.join(tags)
    
    def __str__(self) -> str:
        """Return the query string."""
        return self.build()
    
    