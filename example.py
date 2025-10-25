#!/usr/bin/env python3
"""
Example usage of the xc-dl package programmatically.

This demonstrates how to use xc-dl as a Python library.
"""

from xc_dl.query import QueryBuilder
from xc_dl.client import XenoCantoClient
from xc_dl.downloader import Downloader
import os


def main():
    print("=" * 60)
    print("xc-dl: Xeno-canto Downloader - Example Usage")
    print("=" * 60)
    print()
    
    print("1. Building a query...")
    query = QueryBuilder() \
        .group("birds") \
        .country("Spain") \
        .quality("A") \
        .build()
    
    print(f"   Query: {query}")
    print()
    
    api_key = os.getenv('XENO_CANTO_API_KEY')
    
    if not api_key:
        print("⚠ API Key not found!")
        print()
        print("To use xc-dl, you need a Xeno-canto API key:")
        print("1. Register at https://xeno-canto.org")
        print("2. Verify your email")
        print("3. Get your API key from https://xeno-canto.org/account")
        print("4. Set it as an environment variable:")
        print("   export XENO_CANTO_API_KEY='your-key-here'")
        print()
        print("For now, here's how the package would work:")
        print()
        print("2. Initialize the client...")
        print("   client = XenoCantoClient(api_key='your-key')")
        print()
        print("3. Search for recordings...")
        print("   recordings = client.search(query, max_results=10)")
        print()
        print("4. Download recordings...")
        print("   downloader = Downloader(output_dir='./data')")
        print("   downloader.download_recordings(recordings, verbose=True)")
        print()
        return
    
    try:
        print("2. Initializing client...")
        with XenoCantoClient(api_key=api_key) as client:
            print("   ✓ Client initialized")
            print()
            
            print("3. Fetching metadata (not downloading yet)...")
            metadata = client.get_metadata(query, verbose=True)
            print()
            
            print("4. To download recordings, you can use:")
            print("   xc-dl --grp birds --cnt Spain --q A --max_results 5")
            print()
            
    except Exception as e:
        print(f"   Error: {e}")
        print()


if __name__ == "__main__":
    main()
