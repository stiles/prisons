"""
New York state prison data scraper for DOCCS facilities.
"""

import requests
import pandas as pd
import re
import time
import os
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse


class NewYorkScraper:
    """Scraper for New York Department of Corrections and Community Supervision (DOCCS) facilities."""
    
    def __init__(self):
        self.headers = {
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36',
        }
        
        self.base_url = 'https://doccs.ny.gov'
        self.facilities_url = 'https://doccs.ny.gov/facilities'

    def get_total_pages(self):
        """Determine the total number of pages in the facility list"""
        try:
            response = requests.get(self.facilities_url, headers=self.headers, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for pagination links with page= parameter
            page_links = soup.find_all('a', href=True)
            page_numbers = []
            
            for link in page_links:
                href = link.get('href', '')
                if 'page=' in href:
                    # Extract page number from URL like ?page=4
                    import re
                    match = re.search(r'page=(\d+)', href)
                    if match:
                        page_numbers.append(int(match.group(1)))
            
            if page_numbers:
                # DOCCS uses 0-based pagination, so max page + 1 = total pages
                max_page = max(page_numbers)
                return max_page + 1
            
            # If no pagination found, assume single page
            return 1
            
        except Exception as e:
            print(f"Error determining total pages: {e}")
            return 1

    def scrape_facility_list_page(self, page_num=1):
        """Scrape facility URLs from a single page"""
        try:
            url = f"{self.facilities_url}?page={page_num}"
            response = requests.get(url, headers=self.headers, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            facility_urls = []
            
            # Find all facility rows
            facility_rows = soup.find_all('div', class_='views-row')
            
            for row in facility_rows:
                # Find the facility link
                article = row.find('article')
                if article:
                    # Get the facility URL from the about attribute or find the link
                    facility_path = article.get('about')
                    if not facility_path:
                        # Try to find the link in the article
                        link = article.find('a', href=True)
                        if link:
                            facility_path = link['href']
                    
                    if facility_path:
                        facility_url = urljoin(self.base_url, facility_path)
                        facility_urls.append(facility_url)
            
            print(f"Found {len(facility_urls)} facilities on page {page_num}")
            return facility_urls
            
        except Exception as e:
            print(f"Error scraping page {page_num}: {e}")
            return []

    def scrape_all_facility_urls(self):
        """Scrape facility URLs from all pages"""
        print("Discovering New York DOCCS facilities...")
        
        total_pages = self.get_total_pages()
        print(f"Found {total_pages} pages to scrape")
        
        all_facility_urls = []
        
        for page_num in range(0, total_pages):  # 0-based pagination
            print(f"Scraping page {page_num+1}/{total_pages}...")
            page_urls = self.scrape_facility_list_page(page_num)
            all_facility_urls.extend(page_urls)
            
            # Rate limiting between pages
            time.sleep(1)
        
        print(f"Total facilities discovered: {len(all_facility_urls)}")
        return all_facility_urls

    def parse_address(self, address_div):
        """Parse structured address from the facility page"""
        if not address_div:
            return {}
        
        address_p = address_div.find('p', class_='address')
        if not address_p:
            return {}
        
        # Extract address components
        address_line1 = address_p.find('span', class_='address-line1')
        address_line2 = address_p.find('span', class_='address-line2')
        locality = address_p.find('span', class_='locality')
        admin_area = address_p.find('span', class_='administrative-area')
        postal_code = address_p.find('span', class_='postal-code')
        country = address_p.find('span', class_='country')
        
        return {
            'address_line1': address_line1.get_text(strip=True) if address_line1 else None,
            'address_line2': address_line2.get_text(strip=True) if address_line2 else None,
            'city': locality.get_text(strip=True) if locality else None,
            'state': admin_area.get_text(strip=True) if admin_area else None,
            'zip_code': postal_code.get_text(strip=True) if postal_code else None,
            'country': country.get_text(strip=True) if country else None
        }

    def scrape_facility_details(self, facility_url):
        """Scrape detailed information from a single facility page"""
        try:
            response = requests.get(facility_url, headers=self.headers, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            facility_data = {
                'facility_url': facility_url,
                'jurisdiction': 'New York',
                'agency': 'DOCCS'
            }
            
            # Extract facility name
            title_block = soup.find('div', class_='hero-location-title-block')
            if title_block:
                h1 = title_block.find('h1')
                if h1:
                    facility_data['name'] = h1.get_text(strip=True)
            
            # Extract counties served
            counties_section = soup.find('div', class_='location-counties-section')
            if counties_section:
                counties_div = counties_section.find('div', class_='location-counties')
                if counties_div:
                    facility_data['counties_served'] = counties_div.get_text(strip=True)
            
            # Extract address
            address_field = soup.find('div', class_='location-address-field')
            if address_field:
                address_div = address_field.find('div', class_='location-address')
                address_info = self.parse_address(address_div)
                facility_data.update(address_info)
            
            # Extract phone number
            phone_field = soup.find('div', class_='location-phone')
            if phone_field:
                phone_link = phone_field.find('a', class_='phone-number')
                if phone_link:
                    facility_data['phone'] = phone_link.get_text(strip=True)
            
            # Extract overview information (superintendent, security level, etc.)
            # Look for overview section by h2 text or section attributes
            overview_section = None
            
            # Method 1: Find section with h2 containing "Overview"
            h2_elements = soup.find_all('h2')
            for h2 in h2_elements:
                if h2.get('id') == 'overview' or 'overview' in h2.get_text().lower():
                    overview_section = h2.find_parent('section')
                    break
            
            # Method 2: Find section with toc-para class
            if not overview_section:
                overview_section = soup.find('section', class_='toc-para')
            
            if overview_section:
                wysiwyg_div = overview_section.find('div', class_='wysiwyg--field-webny-wysiwyg-body')
                if wysiwyg_div:
                    # Extract superintendent
                    superintendent_h4 = wysiwyg_div.find('h4')
                    if superintendent_h4 and 'Superintendent:' in superintendent_h4.get_text():
                        superintendent_text = superintendent_h4.get_text(strip=True)
                        facility_data['superintendent'] = superintendent_text.replace('Superintendent:', '').strip()
                    
                    # Extract facility description
                    description_p = wysiwyg_div.find('p')
                    if description_p:
                        description = description_p.get_text(strip=True)
                        facility_data['description'] = description
                        
                        # Extract security level from description
                        if 'maximum security' in description.lower():
                            facility_data['security_level'] = 'Maximum'
                        elif 'medium security' in description.lower():
                            facility_data['security_level'] = 'Medium'
                        elif 'minimum security' in description.lower():
                            facility_data['security_level'] = 'Minimum'
                        
                        # Extract gender from description
                        if 'for males' in description.lower():
                            facility_data['gender'] = 'Male'
                        elif 'for females' in description.lower():
                            facility_data['gender'] = 'Female'
            
            return facility_data
            
        except Exception as e:
            print(f"Error scraping facility details from {facility_url}: {e}")
            return None

    def geocode_address(self, address_line1, address_line2, city, state, zip_code):
        """Geocode a New York facility address using multiple methods"""
        # Construct full address
        address_parts = []
        if address_line1:
            address_parts.append(address_line1)
        if address_line2 and 'P.O. Box' not in address_line2:  # Skip PO Box for geocoding
            address_parts.append(address_line2)
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
            
            # Validate coordinates are in New York bounds (roughly)
            if 40.5 <= lat <= 45.0 and -79.8 <= lng <= -71.8:
                return lat, lng
            else:
                print(f"Warning: Google coordinates outside New York bounds for {full_address}")
        
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
            
            # Validate coordinates are in New York bounds
            if 40.5 <= lat <= 45.0 and -79.8 <= lng <= -71.8:
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
            
            # Validate coordinates are in New York bounds
            if 40.5 <= lat <= 45.0 and -79.8 <= lng <= -71.8:
                return lat, lng
        
        return None, None

    def add_coordinates_to_facilities(self, df):
        """Add coordinates to facilities by geocoding their addresses"""
        if df.empty:
            return df
        
        print("Geocoding New York facility addresses...")
        
        latitudes = []
        longitudes = []
        
        for idx, row in df.iterrows():
            print(f"Geocoding {idx+1}/{len(df)}: {row['name']}")
            
            lat, lng = self.geocode_address(
                row.get('address_line1'),
                row.get('address_line2'),
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
        """Scrape all New York prison data"""
        print("Starting New York prison data collection...")
        
        # Get all facility URLs
        facility_urls = self.scrape_all_facility_urls()
        
        if not facility_urls:
            print("No New York facilities found.")
            return pd.DataFrame()
        
        # Scrape details for each facility
        facilities = []
        failed_urls = []
        
        print(f"\nScraping details for {len(facility_urls)} facilities...")
        
        for i, url in enumerate(facility_urls, 1):
            print(f"Scraping {i}/{len(facility_urls)}: {url}")
            
            facility_data = self.scrape_facility_details(url)
            
            if facility_data:
                facilities.append(facility_data)
            else:
                failed_urls.append(url)
            
            # Rate limiting between requests
            time.sleep(0.5)
        
        if not facilities:
            print("No facility data was successfully scraped.")
            return pd.DataFrame()
        
        # Create DataFrame
        df = pd.DataFrame(facilities)
        
        # Add coordinates by geocoding addresses
        df = self.add_coordinates_to_facilities(df)
        
        print(f"\nSuccessfully collected data for {len(df)} New York facilities")
        
        if failed_urls:
            print(f"Failed to scrape {len(failed_urls)} facilities")
        
        # Show facility distribution by county
        if 'counties_served' in df.columns:
            print(f"\nFacilities by county:")
            print(df['counties_served'].value_counts().head(10))
        
        # Show security levels
        if 'security_level' in df.columns:
            print(f"\nSecurity levels:")
            print(df['security_level'].value_counts())
        
        # Show geocoding success rate
        geocoded_facilities = df.dropna(subset=['latitude', 'longitude'])
        print(f"\nGeocoding results: {len(geocoded_facilities)}/{len(df)} facilities have coordinates")
        
        return df
