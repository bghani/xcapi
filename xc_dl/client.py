"""
API client for the Xeno-canto API v3.

Handles HTTP requests, pagination, error handling, and response parsing.
"""

import os
import time
from typing import Dict, List, Optional
import requests


class XenoCantoClient:
    """
    Client for interacting with the Xeno-canto API v3.
    
    Handles authentication, pagination, rate limiting, and error responses.
    
    Example:
        >>> client = XenoCantoClient(api_key="your-key")
        >>> results = client.search("gen:Larus sp:fuscus")
        >>> print(f"Found {len(results)} recordings")
    """
    
    API_ENDPOINT = "https://xeno-canto.org/api/3/recordings"
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the Xeno-canto API client.
        
        Args:
            api_key: Your Xeno-canto API key. If not provided, will try to
                    read from XENO_CANTO_API_KEY environment variable.
        
        Raises:
            ValueError: If no API key is provided or found in environment
        """
        self.api_key = api_key or os.getenv('XENO_CANTO_API_KEY')
        if not self.api_key:
            raise ValueError(
                "API key is required. Provide it as an argument or set "
                "XENO_CANTO_API_KEY environment variable."
            )
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'xc-dl/0.1.0 (Python; requests)'
        })
    
    def search(
        self,
        query: str,
        per_page: int = 100,
        max_results: Optional[int] = None,
        verbose: bool = False
    ) -> List[Dict]:
        """
        Search for recordings matching the given query.
        
        Automatically handles pagination to retrieve all matching results.
        
        Args:
            query: A search query string (use QueryBuilder to construct)
            per_page: Number of results per page (50-500, default 100)
            max_results: Maximum number of results to retrieve (None for all)
            verbose: Whether to print progress information
        
        Returns:
            A list of recording dictionaries
        
        Raises:
            requests.exceptions.RequestException: If API request fails
            ValueError: If query is empty or invalid parameters
        """
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")
        
        if not (50 <= per_page <= 500):
            raise ValueError("per_page must be between 50 and 500")
        
        all_recordings = []
        page = 1
        
        while True:
            if verbose:
                print(f"Fetching page {page}...")
            
            response_data = self._fetch_page(query, page, per_page)
            
            recordings = response_data.get('recordings', [])
            all_recordings.extend(recordings)
            
            if verbose:
                num_total = response_data.get('numRecordings', '?')
                print(f"  Retrieved {len(all_recordings)}/{num_total} recordings")
            
            if max_results and len(all_recordings) >= max_results:
                all_recordings = all_recordings[:max_results]
                break
            
            current_page = response_data.get('page', page)
            total_pages = response_data.get('numPages', 1)
            
            if current_page >= total_pages:
                break
            
            page += 1
            
            time.sleep(0.1)
        
        return all_recordings
    
    def _fetch_page(self, query: str, page: int, per_page: int) -> Dict:
        """
        Fetch a single page of results.
        
        Args:
            query: Search query string
            page: Page number (1-indexed)
            per_page: Results per page
        
        Returns:
            JSON response as a dictionary
        
        Raises:
            requests.exceptions.RequestException: If request fails
            RuntimeError: If API returns an error response
        """
        params = {
            'query': query,
            'key': self.api_key,
            'page': page,
            'per_page': per_page
        }
        
        try:
            response = self.session.get(self.API_ENDPOINT, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            if 'error' in data:
                error_info = data['error']
                raise RuntimeError(
                    f"API error [{error_info.get('code', 'unknown')}]: "
                    f"{error_info.get('message', 'Unknown error')}"
                )
            
            return data
            
        except requests.exceptions.Timeout:
            raise RuntimeError("Request timed out. Please try again.")
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Request failed: {str(e)}")
    
    def get_metadata(self, query: str, verbose: bool = False) -> Dict:
        """
        Get metadata about search results without fetching all recordings.
        
        Args:
            query: Search query string
            verbose: Whether to print information
        
        Returns:
            Dictionary with numRecordings, numSpecies, and numPages
        """
        response_data = self._fetch_page(query, page=1, per_page=1)
        
        metadata = {
            'numRecordings': response_data.get('numRecordings', 0),
            'numSpecies': response_data.get('numSpecies', 0),
            'numPages': response_data.get('numPages', 0)
        }
        
        if verbose:
            print(f"Query: {query}")
            print(f"Found {metadata['numRecordings']} recordings from {metadata['numSpecies']} species")
        
        return metadata
    
    def close(self):
        """Close the HTTP session."""
        self.session.close()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
