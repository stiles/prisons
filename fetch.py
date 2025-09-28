"""
Unified prison data scraper for multiple jurisdictions.

Supports federal prisons (BOP) and state prisons (starting with California).
"""

import argparse
import os
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
from scrapers import FederalScraper, CaliforniaScraper, NewYorkScraper, TexasScraper, IllinoisScraper, FloridaScraper


def export_data(df, jurisdiction, output_dir):
    """Export data to multiple formats"""
    if df.empty:
        print(f"No data to export for {jurisdiction}")
        return
    
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    base_filename = f"{jurisdiction.lower()}_prisons"
    
    # Export to JSON
    json_path = os.path.join(output_dir, f"{base_filename}.json")
    df.to_json(json_path, orient='records', indent=2)
    print(f"Exported to: {json_path}")
    
    # Export to CSV
    csv_path = os.path.join(output_dir, f"{base_filename}.csv")
    df.to_csv(csv_path, index=False)
    print(f"Exported to: {csv_path}")
    
    # Export to GeoJSON (only facilities with valid coordinates)
    if 'latitude' in df.columns and 'longitude' in df.columns:
        geo_df = df.dropna(subset=['latitude', 'longitude'])
        if not geo_df.empty:
            try:
                geometry = [Point(xy) for xy in zip(geo_df.longitude, geo_df.latitude)]
                gdf = gpd.GeoDataFrame(geo_df, geometry=geometry, crs='EPSG:4326')
                geojson_path = os.path.join(output_dir, f"{base_filename}.geojson")
                gdf.to_file(geojson_path, driver='GeoJSON')
                print(f"Exported to: {geojson_path}")
                print(f"Facilities with coordinates: {len(geo_df)}/{len(df)}")
            except Exception as e:
                print(f"Error creating GeoJSON for {jurisdiction}: {e}")
        else:
            print(f"No facilities with coordinates found for {jurisdiction}")


def scrape_federal():
    """Scrape federal prison data"""
    scraper = FederalScraper()
    df = scraper.scrape_all()
    
    if not df.empty:
        export_data(df, 'federal', 'data/federal')
        return df
    return pd.DataFrame()


def scrape_california():
    """Scrape California state prison data"""
    scraper = CaliforniaScraper()
    df = scraper.scrape_all()
    
    if not df.empty:
        export_data(df, 'california', 'data/california')
        return df
    return pd.DataFrame()


def scrape_texas():
    """Scrape Texas state prison data"""
    scraper = TexasScraper()
    df = scraper.scrape_all()
    
    if not df.empty:
        export_data(df, 'texas', 'data/texas')
        return df
    return pd.DataFrame()


def scrape_new_york():
    """Scrape New York state prison data"""
    scraper = NewYorkScraper()
    df = scraper.scrape_all()
    
    if not df.empty:
        export_data(df, 'new_york', 'data/new_york')
        return df
    return pd.DataFrame()


def scrape_illinois():
    """Scrape Illinois state prison data"""
    scraper = IllinoisScraper()
    df = scraper.scrape_all()
    
    if not df.empty:
        export_data(df, 'illinois', 'data/illinois')
        return df
    return pd.DataFrame()


def scrape_florida():
    """Scrape Florida state prison data"""
    scraper = FloridaScraper()
    df = scraper.scrape_all()
    
    if not df.empty:
        export_data(df, 'florida', 'data/florida')
        return df
    return pd.DataFrame()


def main():
    """Main function to orchestrate prison data collection"""
    parser = argparse.ArgumentParser(description='Scrape prison data from multiple jurisdictions')
    parser.add_argument('--states', 
                       default='federal', 
                       help='Comma-separated list of jurisdictions to scrape (federal,california,texas,new_york,illinois,florida)')
    parser.add_argument('--output-dir', 
                       default='data', 
                       help='Base output directory for data files')
    
    args = parser.parse_args()
    
    # Parse requested jurisdictions
    requested_states = [state.strip().lower() for state in args.states.split(',')]
    
    # Available scrapers
    scrapers = {
        'federal': scrape_federal,
        'california': scrape_california,
        'texas': scrape_texas,
        'new_york': scrape_new_york,
        'illinois': scrape_illinois,
        'florida': scrape_florida
    }
    
    print("Prison Data Scraper")
    print("=" * 50)
    print(f"Requested jurisdictions: {', '.join(requested_states)}")
    print(f"Output directory: {args.output_dir}")
    print()
    
    results = {}
    
    for state in requested_states:
        if state in scrapers:
            print(f"\n{'='*20} {state.upper()} {'='*20}")
            try:
                df = scrapers[state]()
                results[state] = df
                
                if not df.empty:
                    print(f"✓ Successfully collected {len(df)} {state} facilities")
                else:
                    print(f"✗ No data collected for {state}")
                    
            except Exception as e:
                print(f"✗ Error scraping {state}: {e}")
                results[state] = pd.DataFrame()
        else:
            print(f"✗ Unknown jurisdiction: {state}")
            print(f"Available options: {', '.join(scrapers.keys())}")
    
    # Summary
    print(f"\n{'='*20} SUMMARY {'='*20}")
    total_facilities = 0
    for state, df in results.items():
        count = len(df) if not df.empty else 0
        total_facilities += count
        status = "✓" if count > 0 else "✗"
        print(f"{status} {state.capitalize()}: {count} facilities")
    
    print(f"\nTotal facilities collected: {total_facilities}")
    
    if total_facilities > 0:
        print(f"\nData exported to: {args.output_dir}/")
        print("Available formats: JSON, CSV, GeoJSON (where coordinates available)")


if __name__ == "__main__":
    main()
