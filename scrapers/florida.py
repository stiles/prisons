"""
Florida state prison data scraper for FDC facilities.
"""

import requests
import pandas as pd
import re
import json
import time
import os
from bs4 import BeautifulSoup
from urllib.parse import urljoin


class FloridaScraper:
    """Scraper for Florida Department of Corrections (FDC) facilities."""
    
    def __init__(self):
        self.headers = {
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36',
        }
        
        self.base_url = 'https://fdc.myflorida.com'
        self.api_url = 'https://fdc-media.ccplatform.net/api/page/data/institution_office/?contentType=institutions&locationId=3831'
        self.facilities_list_url = 'https://www.fdc.myflorida.com/institutions/institutions-list'

    def _parse_address(self, address_text):
        """Parse address text into structured components"""
        if not address_text:
            return {
                'street_address': None,
                'city': None,
                'state': 'FL',
                'zip_code': None
            }
        
        # Address format: "630 Opportunity Lane Havana, Florida 32333"
        # Split by comma to separate street/city from state/zip
        parts = address_text.split(',')
        if len(parts) >= 2:
            # First part contains street address and city
            street_city = parts[0].strip()
            # Last part contains state and zip
            state_zip = parts[-1].strip()
            
            # Extract state and zip from last part
            state_zip_match = re.search(r'([A-Za-z\s]+)\s+(\d{5}(?:-\d{4})?)', state_zip)
            state = 'FL'
            zip_code = None
            if state_zip_match:
                state = 'FL'  # We know it's Florida
                zip_code = state_zip_match.group(2)
            
            # Split street address and city
            # Assume last word before comma is city
            street_city_parts = street_city.split()
            if len(street_city_parts) >= 2:
                city = street_city_parts[-1]
                street_address = ' '.join(street_city_parts[:-1])
            else:
                city = None
                street_address = street_city
            
            return {
                'street_address': street_address,
                'city': city,
                'state': state,
                'zip_code': zip_code
            }
        
        # Fallback: treat entire string as street address
        return {
            'street_address': address_text,
            'city': None,
            'state': 'FL',
            'zip_code': None
        }

    def _extract_facility_data(self, soup):
        """Extract facility data from individual facility page"""
        data = {
            'warden': None,
            'capacity': None,
            'gender': None,
            'phone': None,
            'fax': None,
            'chaplain_phone': None,
            'warden_email': None,
            'general_email': None,
            'contact_name': None,
            'recruiter_email': None,
            'contact_phone': None,
            'hours': None,
            'programs': []
        }
        
        # Extract data from Next.js page data
        script_tag = soup.find('script', {'id': '__NEXT_DATA__'})
        if script_tag:
            try:
                page_data = json.loads(script_tag.string)
                facility_data = page_data.get('props', {}).get('pageProps', {}).get('pageData', {})
                
                if facility_data:
                    data['warden'] = facility_data.get('warden')
                    data['phone'] = facility_data.get('institutionPhone')
                    data['fax'] = facility_data.get('institutionFax')
                    data['chaplain_phone'] = facility_data.get('chaplainPhone')
                    data['warden_email'] = facility_data.get('wardenEmail')
                    data['general_email'] = facility_data.get('generalEmail')
                    data['contact_name'] = facility_data.get('contactName')
                    data['recruiter_email'] = facility_data.get('recruiterEmail')
                    data['contact_phone'] = facility_data.get('contactPhone')
                    data['hours'] = facility_data.get('hours')
                    
                    # Extract capacity and gender from description HTML
                    description = facility_data.get('description', {}).get('html5', '')
                    if description:
                        soup_desc = BeautifulSoup(description, 'html.parser')
                        
                        # Look for capacity in table
                        capacity_cell = soup_desc.find('td', string='Capacity')
                        if capacity_cell:
                            capacity_value = capacity_cell.find_next_sibling('td')
                            if capacity_value:
                                try:
                                    data['capacity'] = int(capacity_value.get_text(strip=True))
                                except ValueError:
                                    pass
                        
                        # Look for gender in table
                        gender_cell = soup_desc.find('td', string='Population Gender')
                        if gender_cell:
                            gender_value = gender_cell.find_next_sibling('td')
                            if gender_value:
                                data['gender'] = gender_value.get_text(strip=True)
                        
                        # Extract programs
                        programs = []
                        
                        # Academic Programs
                        academic_header = soup_desc.find('h3', string='Academic Programs')
                        if academic_header:
                            program_list = academic_header.find_next('ul')
                            if program_list:
                                for li in program_list.find_all('li'):
                                    programs.append(f"Academic: {li.get_text(strip=True)}")
                        
                        # Vocational Programs
                        vocational_header = soup_desc.find('h3', string='Vocational Programs')
                        if vocational_header:
                            program_list = vocational_header.find_next('ul')
                            if program_list:
                                for li in program_list.find_all('li'):
                                    programs.append(f"Vocational: {li.get_text(strip=True)}")
                        
                        # Betterment Programs
                        betterment_header = soup_desc.find('h3', string='Betterment Programs')
                        if betterment_header:
                            program_list = betterment_header.find_next('ul')
                            if program_list:
                                for li in program_list.find_all('li'):
                                    programs.append(f"Betterment: {li.get_text(strip=True)}")
                        
                        # Substance Use Programs
                        substance_header = soup_desc.find('h3', string='Substance Use Programs')
                        if substance_header:
                            program_list = substance_header.find_next('ul')
                            if program_list:
                                for li in program_list.find_all('li'):
                                    programs.append(f"Substance Use: {li.get_text(strip=True)}")
                        
                        # Re-Entry Programs
                        reentry_header = soup_desc.find('h3', string='Re-Entry Programs')
                        if reentry_header:
                            program_list = reentry_header.find_next('ul')
                            if program_list:
                                for li in program_list.find_all('li'):
                                    programs.append(f"Re-Entry: {li.get_text(strip=True)}")
                        
                        # Chaplaincy Services
                        chaplaincy_header = soup_desc.find('h3', string='Chaplaincy Services')
                        if chaplaincy_header:
                            program_list = chaplaincy_header.find_next('ul')
                            if program_list:
                                for li in program_list.find_all('li'):
                                    programs.append(f"Chaplaincy: {li.get_text(strip=True)}")
                        
                        data['programs'] = programs
                        
            except (json.JSONDecodeError, KeyError) as e:
                print(f"  Error parsing page data: {e}")
        
        return data

    def scrape_facility_list(self):
        """Scrape the list of facilities from FDC API"""
        print("Fetching Florida prison facility list from API...")
        
        try:
            response = requests.get(self.api_url, headers=self.headers, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            
            if not isinstance(data, list):
                print("Error: API response is not a list")
                return []
            
            facilities = []
            for item in data:
                if isinstance(item, dict) and 'name' in item and 'url' in item:
                    # Parse address
                    address_info = self._parse_address(item.get('address', ''))
                    
                    facilities.append({
                        'name': item['name'],
                        'facility_url': item['url'],
                        'county': item.get('county'),
                        'office': item.get('office'),
                        **address_info
                    })
            
            print(f"Found {len(facilities)} Florida facilities")
            return facilities
            
        except Exception as e:
            print(f"Error fetching Florida facility list: {e}")
            return []

    def scrape_facility_details(self, facility_url):
        """Scrape detailed information from individual facility page"""
        try:
            response = requests.get(facility_url, headers=self.headers, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract facility data
            facility_data = self._extract_facility_data(soup)
            
            return facility_data
            
        except Exception as e:
            print(f"Error scraping facility details from {facility_url}: {e}")
            return {}

    def geocode_address(self, address_components):
        """Geocode facility address using multiple services"""
        if not address_components.get('street_address') or not address_components.get('city'):
            return None, None
        
        # Construct full address
        address_parts = []
        if address_components.get('street_address'):
            address_parts.append(address_components['street_address'])
        if address_components.get('city'):
            address_parts.append(address_components['city'])
        if address_components.get('state'):
            address_parts.append(address_components['state'])
        if address_components.get('zip_code'):
            address_parts.append(address_components['zip_code'])
        
        full_address = ', '.join(address_parts)
        
        # Try Google Maps API first if available
        google_api_key = os.environ.get('GOOGLE_MAPS_API_KEY')
        if google_api_key:
            try:
                geocode_url = f"https://maps.googleapis.com/maps/api/geocode/json"
                params = {
                    'address': full_address,
                    'key': google_api_key
                }
                
                response = requests.get(geocode_url, params=params, timeout=10)
                response.raise_for_status()
                data = response.json()
                
                if data['status'] == 'OK' and data['results']:
                    location = data['results'][0]['geometry']['location']
                    print(f"  ✓ Geocoded with Google Maps: {full_address}")
                    time.sleep(0.1)  # Rate limiting
                    return location['lat'], location['lng']
                    
            except Exception as e:
                print(f"  Google Maps geocoding failed: {e}")
        
        # Fallback to Nominatim
        try:
            nominatim_url = "https://nominatim.openstreetmap.org/search"
            params = {
                'q': full_address,
                'format': 'json',
                'limit': 1,
                'countrycodes': 'us'
            }
            
            response = requests.get(nominatim_url, params=params, 
                                  headers={'User-Agent': 'PrisonDataScraper/1.0'}, 
                                  timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data:
                print(f"  ✓ Geocoded with Nominatim: {full_address}")
                time.sleep(1)  # Rate limiting for free service
                return float(data[0]['lat']), float(data[0]['lon'])
                
        except Exception as e:
            print(f"  Nominatim geocoding failed: {e}")
        
        # Fallback to Photon
        try:
            photon_url = "https://photon.komoot.io/api/"
            params = {
                'q': full_address,
                'limit': 1
            }
            
            response = requests.get(photon_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data.get('features'):
                coords = data['features'][0]['geometry']['coordinates']
                print(f"  ✓ Geocoded with Photon: {full_address}")
                time.sleep(1)  # Rate limiting
                return coords[1], coords[0]  # Photon returns [lon, lat]
                
        except Exception as e:
            print(f"  Photon geocoding failed: {e}")
        
        print(f"  ✗ Failed to geocode: {full_address}")
        return None, None

    def scrape_all(self):
        """Scrape all Florida prison facility data"""
        print("Starting Florida Department of Corrections (FDC) scraper...")
        
        # Get facility list
        facilities = self.scrape_facility_list()
        if not facilities:
            return pd.DataFrame()
        
        all_facilities = []
        
        for i, facility in enumerate(facilities, 1):
            print(f"\n[{i}/{len(facilities)}] Processing: {facility['name']}")
            
            # Get detailed facility information
            details = self.scrape_facility_details(facility['facility_url'])
            
            # Geocode the facility
            lat, lon = self.geocode_address(facility)
            
            # Combine all data
            facility_data = {
                'name': facility['name'],
                'jurisdiction': 'Florida',
                'agency': 'Florida Department of Corrections (FDC)',
                'facility_url': facility['facility_url'],
                'street_address': facility.get('street_address'),
                'city': facility.get('city'),
                'state': facility.get('state', 'FL'),
                'zip_code': facility.get('zip_code'),
                'county': facility.get('county'),
                'office': facility.get('office'),
                'latitude': lat,
                'longitude': lon,
                'warden': details.get('warden'),
                'capacity': details.get('capacity'),
                'gender': details.get('gender'),
                'phone': details.get('phone'),
                'fax': details.get('fax'),
                'chaplain_phone': details.get('chaplain_phone'),
                'warden_email': details.get('warden_email'),
                'general_email': details.get('general_email'),
                'contact_name': details.get('contact_name'),
                'recruiter_email': details.get('recruiter_email'),
                'contact_phone': details.get('contact_phone'),
                'hours': details.get('hours'),
                'programs': '; '.join(details.get('programs', []))
            }
            
            all_facilities.append(facility_data)
            
            # Rate limiting
            time.sleep(1)
        
        df = pd.DataFrame(all_facilities)
        
        # Validate coordinates are within Florida bounds
        if not df.empty:
            # Florida approximate bounds: 24.4°N to 31.0°N, 80.0°W to 87.6°W
            valid_coords = df[
                (df['latitude'].between(24.0, 31.5)) & 
                (df['longitude'].between(-88.0, -79.5))
            ]
            
            invalid_coords = df[
                ~((df['latitude'].between(24.0, 31.5)) & 
                  (df['longitude'].between(-88.0, -79.5))) &
                df['latitude'].notna() & df['longitude'].notna()
            ]
            
            if not invalid_coords.empty:
                print(f"\nWarning: {len(invalid_coords)} facilities have coordinates outside Florida bounds:")
                for _, facility in invalid_coords.iterrows():
                    print(f"  - {facility['name']}: {facility['latitude']}, {facility['longitude']}")
        
        print(f"\n✓ Successfully scraped {len(df)} Florida facilities")
        geocoded_count = df[df['latitude'].notna()].shape[0]
        print(f"✓ Geocoded {geocoded_count}/{len(df)} facilities ({geocoded_count/len(df)*100:.1f}%)")
        
        return df
