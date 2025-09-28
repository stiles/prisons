"""
Texas state prison data scraper for TDCJ facilities.
"""

import requests
import pandas as pd
import re
import time
import os
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import urllib3

# Disable SSL warnings for sites with certificate issues
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class TexasScraper:
    """Scraper for Texas Department of Criminal Justice (TDCJ) facilities."""
    
    def __init__(self):
        self.headers = {
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36',
        }
        
        self.base_url = 'https://www.tdcj.texas.gov'
        self.unit_directory_url = 'https://www.tdcj.texas.gov/unit_directory/index.html'

    def scrape_unit_directory_table(self):
        """Scrape the main unit directory table to get basic facility info and URLs"""
        try:
            response = requests.get(self.unit_directory_url, headers=self.headers, timeout=15, verify=False)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find the unit directory table
            table = soup.find('table', class_='tdcj_table')
            if not table:
                print("Error: Could not find unit directory table")
                return pd.DataFrame()
            
            facilities = []
            rows = table.find('tbody').find_all('tr')[1:]  # Skip header row
            
            for row in rows:
                cells = row.find_all('td')
                if len(cells) >= 8:
                    # Extract basic info from table
                    name_cell = cells[0]
                    unit_name = name_cell.get_text(strip=True)
                    
                    # Get facility detail URL
                    facility_url = None
                    link = name_cell.find('a')
                    if link and link.get('href'):
                        facility_url = urljoin(self.base_url + '/unit_directory/', link.get('href'))
                    
                    facility_data = {
                        'name': unit_name,
                        'unit_code': cells[1].get_text(strip=True),
                        'operator': cells[2].get_text(strip=True),
                        'gender': cells[3].get_text(strip=True),
                        'facility_type': cells[4].get_text(strip=True),
                        'region': cells[5].get_text(strip=True),
                        'city': cells[6].get_text(strip=True),
                        'county': cells[7].get_text(strip=True),
                        'facility_url': facility_url,
                        'jurisdiction': 'Texas',
                        'agency': 'TDCJ'
                    }
                    
                    facilities.append(facility_data)
            
            df = pd.DataFrame(facilities)
            print(f"Successfully scraped {len(df)} Texas facilities from unit directory table")
            return df
            
        except Exception as e:
            print(f"Error scraping unit directory table: {e}")
            return pd.DataFrame()

    def parse_facility_details(self, soup):
        """Parse detailed information from a facility page"""
        details = {}
        
        # Extract warden information
        warden_p = soup.find('p')
        if warden_p and 'Senior Warden:' in warden_p.get_text():
            warden_text = warden_p.get_text(strip=True)
            warden_match = re.search(r'Senior Warden:\s*(.+)', warden_text)
            if warden_match:
                details['senior_warden'] = warden_match.group(1).strip()
        
        # Find all paragraphs with bold labels
        paragraphs = soup.find_all('p')
        
        for p in paragraphs:
            text = p.get_text()
            
            # Extract various facility details using regex patterns
            patterns = {
                'unit_full_name': r'Unit Full Name:\s*(.+)',
                'family_liaison': r'Family Liaison Coordinator:\s*(.+)',
                'date_established': r'Date Unit Established or On Line:\s*(.+)',
                'total_employees': r'Total Employees:\s*(\d+)',
                'security_employees': r'Security Employees:\s*(\d+)',
                'non_security_employees': r'Non-Security Employees:\s*(\d+)',
                'windham_employees': r'Windham Education Employees:\s*(\d+)',
                'medical_employees': r'Contract Medical and Mental Health Employees:\s*(.+)',
                'capacity': r'Capacity:\s*([\d,]+)',
                'custody_levels': r'Custody Levels Housed:\s*(.+)',
                'acreage': r'Approximate Acreage:\s*(.+)',
                'agricultural_ops': r'Agricultural Operations:\s*(.+)',
                'manufacturing_ops': r'Manufacturing and Logistics Op\.:\s*(.+)',
                'facility_ops': r'Facility Operations:\s*(.+)',
                'additional_ops': r'Additional Operations:\s*(.+)',
                'medical_capabilities': r'Medical Capabilities:\s*(.+)',
                'educational_programs': r'Educational Programs:\s*(.+)',
                'additional_programs': r'Additional Programs/Services:\s*(.+)',
                'community_work': r'Community Work Projects:\s*(.+)',
                'volunteer_initiatives': r'Volunteer Initiatives:\s*(.+)'
            }
            
            for key, pattern in patterns.items():
                match = re.search(pattern, text)
                if match:
                    details[key] = match.group(1).strip()
        
        # Extract address and phone from the structured sections
        address_divs = soup.find_all('div', class_='div_50_left')
        for div in address_divs:
            text = div.get_text()
            
            # Extract address
            if 'Address:' in text:
                address_lines = text.split('\n')[1:]  # Skip "Address:" line
                address_lines = [line.strip() for line in address_lines if line.strip()]
                if len(address_lines) >= 3:
                    details['street_address'] = address_lines[1]  # Skip unit name
                    # Parse city, state, zip from last line
                    city_state_zip = address_lines[-1]
                    match = re.match(r'^(.+),\s*([A-Z]{2})\s+(\d{5}(?:-\d{4})?)$', city_state_zip)
                    if match:
                        details['parsed_city'] = match.group(1).strip()
                        details['state'] = match.group(2)
                        details['zip_code'] = match.group(3)
            
            # Extract phone
            phone_match = re.search(r'Phone:\s*\((\d{3})\)\s*(\d{3})-(\d{4})', text)
            if phone_match:
                details['phone'] = f"({phone_match.group(1)}) {phone_match.group(2)}-{phone_match.group(3)}"
            
            # Extract location description
            location_match = re.search(r'Location:\s*(.+)', text)
            if location_match:
                details['location_description'] = location_match.group(1).strip()
        
        return details

    def scrape_facility_details(self, facility_url):
        """Scrape detailed information from a single facility page"""
        if not facility_url:
            return {}
        
        try:
            response = requests.get(facility_url, headers=self.headers, timeout=15, verify=False)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Parse facility details
            details = self.parse_facility_details(soup)
            
            return details
            
        except Exception as e:
            print(f"Error scraping facility details from {facility_url}: {e}")
            return {}

    def geocode_address(self, street_address, city, state, zip_code):
        """Geocode a Texas facility address using multiple methods"""
        # Construct full address
        address_parts = []
        if street_address:
            address_parts.append(street_address)
        if city:
            address_parts.append(city)
        if state:
            address_parts.append(state)
        if zip_code:
            address_parts.append(zip_code)
        
        full_address = ', '.join(address_parts)
        
        # Try multiple geocoding services (Google first if API key available)
        methods = []
        
        # Add Google geocoding if API key is available
        if os.getenv('GOOGLE_MAPS_API_KEY'):
            methods.append(self._geocode_with_google)
        
        # Add fallback methods
        methods.extend([
            self._geocode_with_nominatim,
            self._geocode_with_photon,
        ])
        
        for method in methods:
            try:
                lat, lng = method(full_address)
                if lat is not None and lng is not None:
                    return lat, lng
            except Exception as e:
                print(f"Geocoding method failed for {full_address}: {e}")
                continue
        
        print(f"All geocoding methods failed for: {full_address}")
        return None, None

    def _geocode_with_google(self, full_address):
        """Try geocoding with Google Maps Geocoding API"""
        api_key = os.getenv('GOOGLE_MAPS_API_KEY')
        if not api_key:
            return None, None
        
        url = 'https://maps.googleapis.com/maps/api/geocode/json'
        params = {
            'address': full_address,
            'key': api_key,
            'region': 'us'  # Bias results to US
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if data['status'] == 'OK' and data['results']:
            result = data['results'][0]
            location = result['geometry']['location']
            lat = float(location['lat'])
            lng = float(location['lng'])
            
            # Validate coordinates are in Texas bounds (roughly)
            if 25.8 <= lat <= 36.5 and -106.6 <= lng <= -93.5:
                return lat, lng
            else:
                print(f"Warning: Google coordinates outside Texas bounds for {full_address}")
        
        return None, None

    def _geocode_with_nominatim(self, full_address):
        """Try geocoding with Nominatim"""
        url = 'https://nominatim.openstreetmap.org/search'
        params = {
            'q': full_address,
            'format': 'json',
            'limit': 1,
            'countrycodes': 'us'
        }
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        
        results = response.json()
        
        if results:
            result = results[0]
            lat = float(result['lat'])
            lng = float(result['lon'])
            
            # Validate coordinates are in Texas bounds
            if 25.8 <= lat <= 36.5 and -106.6 <= lng <= -93.5:
                return lat, lng
        
        return None, None

    def _geocode_with_photon(self, full_address):
        """Try geocoding with Photon (alternative OSM-based service)"""
        url = 'https://photon.komoot.io/api/'
        params = {
            'q': full_address,
            'limit': 1,
            'osm_tag': 'place'
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if data.get('features'):
            feature = data['features'][0]
            coords = feature['geometry']['coordinates']
            lng, lat = coords[0], coords[1]  # GeoJSON format is [lng, lat]
            
            # Validate coordinates are in Texas bounds
            if 25.8 <= lat <= 36.5 and -106.6 <= lng <= -93.5:
                return lat, lng
        
        return None, None

    def add_coordinates_to_facilities(self, df):
        """Add coordinates to facilities by geocoding their addresses"""
        if df.empty:
            return df
        
        print("Geocoding Texas facility addresses...")
        
        latitudes = []
        longitudes = []
        
        for idx, row in df.iterrows():
            print(f"Geocoding {idx+1}/{len(df)}: {row['name']}")
            
            # Use parsed city if available, otherwise fall back to table city
            city = row.get('parsed_city') or row.get('city')
            
            lat, lng = self.geocode_address(
                row.get('street_address'),
                city,
                row.get('state', 'TX'),
                row.get('zip_code')
            )
            
            latitudes.append(lat)
            longitudes.append(lng)
            
            # Rate limiting - be respectful to the geocoding service
            # Use shorter delay for Google API (higher rate limits)
            if os.getenv('GOOGLE_MAPS_API_KEY'):
                time.sleep(0.1)  # Google allows higher rate limits
            else:
                time.sleep(1)    # Be more conservative with free services
        
        df['latitude'] = latitudes
        df['longitude'] = longitudes
        
        # Count successful geocodes
        successful_geocodes = df.dropna(subset=['latitude', 'longitude'])
        print(f"Successfully geocoded {len(successful_geocodes)}/{len(df)} facilities")
        
        return df

    def scrape_all(self):
        """Scrape all Texas prison data"""
        print("Starting Texas prison data collection...")
        
        # Get basic facility info from unit directory table
        facilities_df = self.scrape_unit_directory_table()
        
        if facilities_df.empty:
            print("No Texas facilities found in unit directory.")
            return pd.DataFrame()
        
        # Scrape detailed information for each facility
        print(f"\nScraping detailed information for {len(facilities_df)} facilities...")
        
        detailed_facilities = []
        failed_urls = []
        
        for idx, row in facilities_df.iterrows():
            print(f"Scraping details {idx+1}/{len(facilities_df)}: {row['name']}")
            
            # Start with basic info from table
            facility_data = row.to_dict()
            
            # Add detailed info from facility page
            if row['facility_url']:
                details = self.scrape_facility_details(row['facility_url'])
                facility_data.update(details)
            else:
                failed_urls.append(row['name'])
            
            detailed_facilities.append(facility_data)
            
            # Rate limiting between requests
            time.sleep(0.5)
        
        # Create DataFrame with all data
        df = pd.DataFrame(detailed_facilities)
        
        # Add coordinates by geocoding addresses
        df = self.add_coordinates_to_facilities(df)
        
        print(f"\nSuccessfully collected data for {len(df)} Texas facilities")
        
        if failed_urls:
            print(f"Failed to get detailed info for {len(failed_urls)} facilities")
        
        # Show facility distribution by region
        if 'region' in df.columns:
            print(f"\nFacilities by region:")
            print(df['region'].value_counts())
        
        # Show facility types
        if 'facility_type' in df.columns:
            print(f"\nFacility types:")
            print(df['facility_type'].value_counts())
        
        # Show capacity statistics
        if 'capacity' in df.columns:
            capacity_df = df[df['capacity'].notna()]
            if not capacity_df.empty:
                capacity_df['capacity'] = pd.to_numeric(capacity_df['capacity'], errors='coerce')
                total_capacity = capacity_df['capacity'].sum()
                print(f"\nTotal system capacity: {total_capacity:,} inmates")
                print(f"Average facility capacity: {capacity_df['capacity'].mean():.0f} inmates")
        
        # Show geocoding success rate
        geocoded_facilities = df.dropna(subset=['latitude', 'longitude'])
        print(f"\nGeocoding results: {len(geocoded_facilities)}/{len(df)} facilities have coordinates")
        
        return df
