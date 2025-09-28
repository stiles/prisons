"""
California state prison data scraper for CDCR facilities.
"""

import requests
import pandas as pd
import re
import json
import time
import os
from bs4 import BeautifulSoup
from urllib.parse import urljoin


class CaliforniaScraper:
    """Scraper for California Department of Corrections and Rehabilitation (CDCR) facilities."""
    
    def __init__(self):
        self.headers = {
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36',
        }
        
        self.cdcr_table_url = 'https://www.cdcr.ca.gov/adult-operations/list-of-adult-institutions/'
        self.google_maps_url = 'https://www.google.com/maps/d/u/1/embed?mid=1NqorHuwhYG0wPQXZBn4uOHYJGbud1XY&ehbc=2E312F'

    def _parse_address(self, address_text):
        """Parse address text into structured components"""
        lines = [line.strip() for line in address_text.split('\n') if line.strip()]
        
        # Extract phone number (last line with parentheses)
        phone = None
        if lines and '(' in lines[-1] and ')' in lines[-1]:
            phone = lines[-1].strip()
            lines = lines[:-1]
        
        # Extract city, state, zip (second to last line)
        city, state, zip_code = None, 'CA', None
        if lines:
            city_state_zip = lines[-1].strip()
            # Match pattern like "City, CA 12345" or "City, CA 12345-1234"
            match = re.match(r'^(.+),\s*([A-Z]{2})\s+(\d{5}(?:-\d{4})?)$', city_state_zip)
            if match:
                city, state, zip_code = match.groups()
                lines = lines[:-1]
        
        # Remaining lines are street address
        street_address = '\n'.join(lines) if lines else None
        
        return {
            'street_address': street_address,
            'city': city,
            'state': state,
            'zip_code': zip_code,
            'phone': phone
        }

    def _extract_acronym(self, name_text):
        """Extract acronym from facility name"""
        # Look for text in parentheses
        match = re.search(r'\(([^)]+)\)', name_text)
        if match:
            return match.group(1)
        return None

    def scrape_cdcr_table(self):
        """Scrape facility data from CDCR table"""
        print("Fetching California prison data from CDCR table...")
        
        try:
            response = requests.get(self.cdcr_table_url, headers=self.headers, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find the table with prison data
            table = soup.find('table')
            if not table:
                print("Error: Could not find prison data table")
                return pd.DataFrame()
            
            facilities = []
            rows = table.find_all('tr')[1:]  # Skip header row
            
            for row in rows:
                cells = row.find_all('td')
                if len(cells) >= 3:
                    # Extract facility name and acronym
                    name_cell = cells[0].get_text(strip=True)
                    name = re.sub(r'\s*\([^)]*\)\s*', '', name_cell).strip()
                    acronym = self._extract_acronym(name_cell)
                    
                    # Extract address information
                    address_cell = cells[1].get_text('\n', strip=True)
                    address_info = self._parse_address(address_cell)
                    
                    # Extract facility page URL
                    facility_url = None
                    link = cells[2].find('a')
                    if link and link.get('href'):
                        facility_url = urljoin(self.cdcr_table_url, link.get('href'))
                    
                    facility_data = {
                        'name': name,
                        'acronym': acronym,
                        'street_address': address_info['street_address'],
                        'city': address_info['city'],
                        'state': address_info['state'],
                        'zip_code': address_info['zip_code'],
                        'phone': address_info['phone'],
                        'facility_url': facility_url,
                        'jurisdiction': 'California',
                        'agency': 'CDCR'
                    }
                    
                    facilities.append(facility_data)
            
            df = pd.DataFrame(facilities)
            print(f"Successfully scraped {len(df)} California facilities from CDCR table")
            return df
            
        except requests.exceptions.RequestException as e:
            print(f"Error fetching CDCR table: {e}")
            return pd.DataFrame()
        except Exception as e:
            print(f"Error parsing CDCR table: {e}")
            return pd.DataFrame()

    def scrape_google_maps_coordinates(self):
        """Scrape coordinates from Google My Maps embed"""
        print("Fetching coordinate data from Google Maps...")
        
        try:
            response = requests.get(self.google_maps_url, headers=self.headers, timeout=15)
            response.raise_for_status()
            
            content = response.text
            
            # Extract coordinate pairs and facility names
            facilities = []
            
            # Look for coordinate patterns (latitude, longitude pairs)
            coord_matches = re.findall(r'([-]?\d+\.\d{6,})', content)
            
            # Look for facility names in the content
            # We'll match against known California prison names
            known_prisons = [
                'Avenal State Prison', 'California Correctional Institution', 
                'California Health Care Facility', 'California Institution for Men',
                'California Institution for Women', 'California Men\'s Colony',
                'California Medical Facility', 'California Rehabilitation Center',
                'California State Prison, Corcoran', 'California State Prison, Los Angeles County',
                'California State Prison, Sacramento', 'California State Prison, Solano',
                'Calipatria State Prison', 'California State Prison, Centinela',
                'Central California Women\'s Facility', 'Correctional Training Facility',
                'Folsom State Prison', 'High Desert State Prison', 'Ironwood State Prison',
                'Kern Valley State Prison', 'Mule Creek State Prison', 'North Kern State Prison',
                'Pelican Bay State Prison', 'Pleasant Valley State Prison',
                'Richard J. Donovan Correctional Facility', 'Salinas Valley State Prison',
                'San Quentin Rehabilitation Center', 'Sierra Conservation Center',
                'Substance Abuse Treatment Facility', 'Valley State Prison', 'Wasco State Prison'
            ]
            
            # Convert coordinates to float and group into lat/lng pairs
            coords = []
            try:
                float_coords = [float(c) for c in coord_matches]
                # Group coordinates into pairs (assuming lat, lng order)
                for i in range(0, len(float_coords)-1, 2):
                    lat, lng = float_coords[i], float_coords[i+1]
                    # Basic validation for California coordinates
                    if 32 <= lat <= 42 and -125 <= lng <= -114:
                        coords.append((lat, lng))
            except ValueError:
                pass
            
            print(f"Found {len(coords)} potential coordinate pairs in California bounds")
            
            # For now, return empty DataFrame as we need more sophisticated parsing
            # to match coordinates with specific facilities
            print("Note: Coordinate extraction from Google Maps needs facility name matching")
            return pd.DataFrame()
            
        except requests.exceptions.RequestException as e:
            print(f"Error fetching Google Maps data: {e}")
            return pd.DataFrame()
        except Exception as e:
            print(f"Error parsing Google Maps data: {e}")
            return pd.DataFrame()

    def geocode_address(self, address, city, state, zip_code):
        """Geocode an address using multiple fallback methods"""
        # Clean and construct full address
        address_parts = []
        if address:
            # Clean up address formatting
            clean_address = address.replace('\n', ' ').strip()
            # Remove phone numbers from address
            clean_address = re.sub(r'\(\d{3}\)\s*\d{3}-\d{4}', '', clean_address).strip()
            if clean_address:
                address_parts.append(clean_address)
        if city:
            # Clean city name (remove newlines)
            clean_city = city.replace('\n', ' ').strip()
            if clean_city:
                address_parts.append(clean_city)
        if state:
            address_parts.append(state)
        if zip_code:
            address_parts.append(zip_code)
        
        full_address = ', '.join(address_parts)
        
        # Try manual fixes for known problematic addresses as final fallback
        # (Only used if all geocoding services fail)
        manual_coords = None
        
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
        
        # If all geocoding methods failed, try manual coordinates as last resort
        manual_coords = self._get_manual_coordinates(full_address, city)
        if manual_coords[0] is not None:
            return manual_coords
        
        print(f"All geocoding methods failed for: {full_address}")
        return None, None

    def _get_manual_coordinates(self, full_address, city):
        """Manual coordinates for facilities that are hard to geocode"""
        manual_coords = {
            # Known California prison coordinates (from research/maps)
            'Avenal': (36.0044, -120.1285),
            'Tehachapi': (35.1322, -118.4487),
            'Stockton': (37.9577, -121.2908),
            'Norco': (33.9306, -117.5486),
            'Soledad': (36.4247, -121.3263),
            'Ione': (38.3496, -120.9327),
            'San Diego': (32.7157, -117.1611),
            'Wasco': (35.5944, -119.3407)
        }
        
        # Try to match by city name
        if city and city.strip():
            clean_city = city.replace('\n', ' ').strip()
            for known_city, coords in manual_coords.items():
                if known_city.lower() in clean_city.lower():
                    print(f"Using manual coordinates for {clean_city}: {coords}")
                    return coords
        
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
            
            # Validate coordinates are in California bounds
            if 32 <= lat <= 42 and -125 <= lng <= -114:
                return lat, lng
            else:
                print(f"Warning: Google coordinates outside California bounds for {full_address}")
        
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
            
            # Validate coordinates are in California bounds
            if 32 <= lat <= 42 and -125 <= lng <= -114:
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
            
            # Validate coordinates are in California bounds
            if 32 <= lat <= 42 and -125 <= lng <= -114:
                return lat, lng
        
        return None, None

    def add_coordinates_to_facilities(self, df):
        """Add coordinates to facilities by geocoding their addresses"""
        if df.empty:
            return df
        
        print("Geocoding facility addresses...")
        
        latitudes = []
        longitudes = []
        
        for idx, row in df.iterrows():
            print(f"Geocoding {idx+1}/{len(df)}: {row['name']}")
            
            lat, lng = self.geocode_address(
                row.get('street_address'),
                row.get('city'), 
                row.get('state'),
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
        """Scrape all California prison data"""
        print("Starting California prison data collection...")
        
        # Get data from CDCR table
        cdcr_df = self.scrape_cdcr_table()
        
        if cdcr_df.empty:
            print("No California data was successfully fetched.")
            return pd.DataFrame()
        
        # Add coordinates by geocoding addresses
        cdcr_df = self.add_coordinates_to_facilities(cdcr_df)
        
        print(f"\nSuccessfully collected data for {len(cdcr_df)} California facilities")
        
        # Show facility distribution by city
        if 'city' in cdcr_df.columns:
            print(f"\nFacilities by city:")
            print(cdcr_df['city'].value_counts().head(10))
        
        # Show geocoding success rate
        geocoded_facilities = cdcr_df.dropna(subset=['latitude', 'longitude'])
        print(f"\nGeocoding results: {len(geocoded_facilities)}/{len(cdcr_df)} facilities have coordinates")
        
        return cdcr_df
