"""
Command-line interface for xcapi.

Provides a comprehensive CLI for searching and downloading Xeno-canto recordings.
"""

import argparse
import os
import sys
from xcapi.query import QueryBuilder
from xcapi.client import XenoCantoClient
from xcapi.downloader import Downloader


def main():
    """Main entry point for the xcapi CLI."""
    parser = argparse.ArgumentParser(
        description='Download animal sound recordings from Xeno-canto',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Download Orthoptera from Europe
  xcapi --grp Orthoptera --area europe --output_dir ./data
  
  # Download high-quality bird songs from Spain
  xcapi --grp birds --cnt Spain --type song --q A
  
  # Download recordings of a specific species
  xcapi --gen Larus --sp fuscus --output_dir ./gulls
  
  # Download recent recordings from last 30 days
  xcapi --grp birds --since 30
  
Environment Variables:
  XENO_CANTO_API_KEY   Your Xeno-canto API key (required)
        """
    )
    
    parser.add_argument(
        '--api_key',
        help='Xeno-canto API key (or set XENO_CANTO_API_KEY env variable)'
    )
    
    parser.add_argument(
        '--output_dir',
        default='./xc_downloads',
        help='Output directory for downloads (default: ./xc_downloads)'
    )
    
    parser.add_argument(
        '--max_results',
        type=int,
        help='Maximum number of recordings to download'
    )
    
    parser.add_argument(
        '--per_page',
        type=int,
        default=100,
        help='Results per page (50-500, default: 100)'
    )
    
    parser.add_argument(
        '--skip_existing',
        action='store_true',
        default=True,
        help='Skip already downloaded files (default: True)'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Print detailed progress information'
    )
    
    parser.add_argument(
        '--metadata_only',
        action='store_true',
        help='Fetch metadata only without downloading audio files'
    )
    
    tax_group = parser.add_argument_group('Taxonomic filters')
    tax_group.add_argument('--gen', '--genus', help='Genus name (e.g., Corvus)')
    tax_group.add_argument('--sp', '--species', help='Species name (e.g., "Pica pica"). To perform a search for a species name that has multiple words, you must enclose the words in double quotes.')
    tax_group.add_argument('--ssp', '--subspecies', help='Subspecies name. To perform a search for a subspecies name that has multiple words, you must enclose the words in double quotes.')
    tax_group.add_argument('--en', '--english', help='English common name (e.g., "Common blackbird"). To perform a search for a common name that has multiple words, you must enclose the words in double quotes.')
    tax_group.add_argument('--fam', '--family', help='Family name. To perform a search for a family name that has multiple words, you must enclose the words in double quotes.')
    tax_group.add_argument('--grp', '--group', help='Taxonomic group (e.g., birds, grasshoppers, bats). To perform a search for a taxonomic group that has multiple words, you must enclose the words in double quotes (e.g., --grp "land mammals").')
    

    geo_group = parser.add_argument_group('Geographic filters')
    geo_group.add_argument('--cnt', '--country', help='Country name (e.g., Germany). To perform a search for a country that has multiple words, you must enclose the words in double quotes (e.g., --cnt "Costa Rica")')
    geo_group.add_argument('--loc', '--location', help='Locality or site name (e.g., tambopata). To perform a search for a location that has multiple words, you must enclose the words in double quotes (e.g., --loc "New Delhi")')
    geo_group.add_argument('--area', help='Continent or region (e.g., Europe, Asia, Africa)')
    geo_group.add_argument('--box', help='Bounding box as lat_min,lon_min,lat_max,lon_max')
    geo_group.add_argument('--lat', '--latitude', help='Latitude or range (e.g., 40-45, ">50"). Quotes are required in most shells for < or >.')
    geo_group.add_argument('--lon', '--longitude', help='Longitude or range (e.g., -10-0, "<-100"). Quotes are required in most shells for < or >.')
    geo_group.add_argument('--alt', '--altitude', help='Altitude in meters (e.g., 100-500, "<1000"). Quotes are required in most shells for < or >.')

    quality_group = parser.add_argument_group('Quality and type filters')
    quality_group.add_argument(
        '--q', '--quality',
        help='Recording quality rating (A–E). Supports operators like A, ">B" or "<C". '
            'Quotes are required in most shells for < or >, e.g. --q ">B".'
    )
    quality_group.add_argument('--type', help='Sound type (e.g., song, call, alarm, etc.)')
    quality_group.add_argument('--sex', help='Sex (male, female, uncertain)')
    quality_group.add_argument('--stage', help='Life stage (adult, juvenile, etc.)')
    quality_group.add_argument('--method', help='Recording method')

    time_group = parser.add_argument_group('Time filters')
    time_group.add_argument('--year', help='Year or range (e.g., 2020, 2015-2020). Quotes are required in most shells for < or > (e.g., --year ">2020").')
    time_group.add_argument('--month', help='Month or range (e.g., 6, 1-7). Quotes are required in most shells for < or > (e.g., --month "<5")')
    time_group.add_argument('--since', type=int, help='Recordings uploaded since YYYY-MM-DD (e.g., 2012-11-09) or since last N days (e.g., 2, 3)')
    time_group.add_argument('--time', help='Time of day or range (e.g., 06:00, 06:00-12:00)')

    other_group = parser.add_argument_group('Other filters')
    other_group.add_argument('--rec', '--recordist', help='Recordist name (e.g., "Raziya"). To perform a search for a location that has multiple words, you must enclose the words in double quotes (e.g., "Raziya Qadri") ')
    other_group.add_argument(
        '--len', '--length',
        help='Recording length in seconds (e.g., 10, 20, 10-20, "<30", ">60"). '
            'Ranges and comparison operators are supported. Quotes are required in most shells for < or >.'
    )
    other_group.add_argument('--lic', '--license', help='License type (e.g., CC-BY, CC0)')
    other_group.add_argument('--also', help='Background species name. To perform a search for a background species name that has multiple words, you must enclose the words in double quotes.')
    other_group.add_argument('--animal_seen', choices=['yes', 'no'],
                            help='Was the animal seen? (yes/no)')
    other_group.add_argument('--playback_used', choices=['yes', 'no'],
                            help='Was playback used? (yes/no)')

    metadata_group = parser.add_argument_group('Recording metadata filters')
    metadata_group.add_argument(
        '--nr', '--number',
        help='Number of individuals (e.g., 1, 2-5, ">10"). Quotes are required in most shells for < or >.'
    )
    metadata_group.add_argument(
        '--catnr', help='Catalogue number (e.g., 12345, ">100000", 5000-10000). Quotes are required in most shells for < or >.'
    )
    metadata_group.add_argument(
        '--temp', '--temperature',
        help='Temperature in °C (e.g., 20-30, "<10", ">35"). Quotes are required in most shells for < or >.'
    )
    metadata_group.add_argument('--regnr', help='Specimen registration number')
    metadata_group.add_argument(
        '--auto', '--automatic', choices=['yes', 'no', 'unknown'],
        help='Automatic (non-supervised) recording'
    )
    metadata_group.add_argument('--dvc', '--device', help='Recording device (e.g., "Zoom F3").  To perform a search for a recording device that has multiple words, you must enclose the words in double quotes.')
    metadata_group.add_argument('--mic', '--microphone', help='Microphone model. To perform a search for a microphone model that has multiple words, you must enclose the words in double quotes.')
    metadata_group.add_argument('--smp', '--sample_rate',
                                help='Sample rate or a range in Hz (e.g., 44100, 44100-100000, ">44100"). Quotes are required in most shells for < or >.')
    metadata_group.add_argument('--rmk', '--remarks', help='Search in remarks field text')
        
    args = parser.parse_args()
    
    try:
        query = build_query_from_args(args)
        
        if not query:
            parser.error("No search filters specified. Use --help for available options.")
        
        if args.verbose:
            print(f"Query: {query}\n")
        
        api_key = args.api_key or os.getenv('XENO_CANTO_API_KEY')
        if not api_key:
            print("ERROR: API key required. Set XENO_CANTO_API_KEY environment variable or use --api_key", file=sys.stderr)
            sys.exit(1)
        
        with XenoCantoClient(api_key=api_key) as client:
            print("Searching for recordings...")
            recordings = client.search(
                query=query,
                per_page=args.per_page,
                max_results=args.max_results,
                verbose=args.verbose
            )
            
            if not recordings:
                print("No recordings found matching the query.")
                return
            
            print(f"\nFound {len(recordings)} recordings.")
            
            downloader = Downloader(output_dir=args.output_dir)
            
            if args.metadata_only:
                print(f"Saving metadata to: {downloader.output_dir}\n")
                downloader.save_metadata_only(recordings, verbose=True)
                print("\n✓ Metadata saved! Use without --metadata_only to download audio files.")
                return
            
            print(f"Downloading to: {downloader.output_dir}\n")
            
            stats = downloader.download_recordings(
                recordings=recordings,
                verbose=args.verbose,
                skip_existing=args.skip_existing
            )
            
            print("\n✓ Download complete!")
            
    except KeyboardInterrupt:
        print("\n\nDownload interrupted by user.", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"\nERROR: {str(e)}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


def build_query_from_args(args) -> str:
    """
    Build a query string from command-line arguments.
    
    Args:
        args: Parsed command-line arguments
    
    Returns:
        Query string for the Xeno-canto API
    """
    builder = QueryBuilder()
    
    if args.gen:
        builder.genus(args.gen)
    if args.sp:
        builder.species(args.sp)
    if args.ssp:
        builder.subspecies(args.ssp)
    if args.fam:
        builder.family(args.fam)
    if args.grp:
        builder.group(args.grp)
    if args.en:
        builder.english_name(args.en)
    
    if args.cnt:
        builder.country(args.cnt)
    if args.loc:
        builder.location(args.loc)
    if args.area:
        builder.area(args.area)
    if args.box:
        try:
            coords = [float(x.strip()) for x in args.box.split(',')]
            if len(coords) != 4:
                raise ValueError("Box must have 4 coordinates")
            builder.bounding_box(*coords)
        except ValueError as e:
            raise ValueError(f"Invalid bounding box format: {e}")
    if args.lat:
        builder.latitude(args.lat)
    if args.lon:
        builder.longitude(args.lon)
    if args.alt:
        builder.altitude(args.alt)
    
    if args.q:
        builder.quality(args.q)
    if args.type:
        builder.sound_type(args.type)
    if args.sex:
        builder.sex(args.sex)
    if args.stage:
        builder.life_stage(args.stage)
    if args.method:
        builder.method(args.method)
    
    if args.year:
        builder.year(args.year)
    if args.month:
        builder.month(args.month)
    if args.since:
        builder.since(args.since)
    if args.time:
        builder.time_of_day(args.time)
    
    if args.rec:
        builder.recordist(args.rec)
    if getattr(args, 'len', None):
        builder.length(args.len)
    if args.lic:
        builder.license(args.lic)
    if args.also:
        builder.also(args.also)
    if args.animal_seen:
        builder.animal_seen(args.animal_seen == 'yes')
    if args.playback_used:
        builder.playback_used(args.playback_used == 'yes')
    
    if args.nr:
        builder.number_in_group(args.nr)
    if args.catnr:
        builder.catalogue_number(args.catnr)
    if args.temp:
        builder.temperature(args.temp)
    if args.regnr:
        builder.registration_number(args.regnr)
    if args.auto:
        builder.automatic_recording(args.auto)
    if args.dvc:
        builder.device(args.dvc)
    if args.mic:
        builder.microphone(args.mic)
    if args.smp:
        builder.sample_rate(args.smp)
    if args.rmk:
        builder.remarks(args.rmk)
    
    return builder.build()


if __name__ == '__main__':
    main()
