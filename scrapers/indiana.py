#!/usr/bin/env python3

import requests
import re
from bs4 import BeautifulSoup
from typing import Dict, List, Optional, Tuple
import logging
import time

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class IndianaScraper:
    """Scraper for Indiana Department of Correction facilities."""
    
    def __init__(self):
        self.base_url = "https://www.in.gov"
        self.facilities_url = "https://www.in.gov/idoc/facilities/adult/"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
    
    def scrape_facilities(self) -> List[Dict]:
        """
        Scrape all Indiana correctional facilities.
        
        Returns:
            List of facility dictionaries with details and coordinates
        """
        logger.info("Starting Indiana facilities scrape...")
        
        # Get facility URLs from the main directory
        facility_urls = self.get_facility_urls()
        
        if not facility_urls:
            logger.error("Failed to get facility URLs")
            return []
        
        logger.info(f"Found {len(facility_urls)} facility URLs")
        
        # Process each facility
        facilities = []
        for i, (name, url, security_level, gender) in enumerate(facility_urls, 1):
            try:
                logger.info(f"Processing facility {i}/{len(facility_urls)}: {name}")
                
                facility = self.scrape_facility_details(name, url, security_level, gender)
                if facility:
                    facilities.append(facility)
                
                # Rate limiting - be respectful
                time.sleep(0.3)
                
            except Exception as e:
                logger.error(f"Error processing {name}: {e}")
                continue
        
        logger.info(f"Successfully processed {len(facilities)} facilities")
        return facilities
    
    def get_facility_urls(self) -> List[Tuple[str, str, str, str]]:
        """Extract facility URLs and basic info from the main directory."""
        try:
            response = self.session.get(self.facilities_url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            facility_urls = []
            
            # Find Adult Male section
            male_section = None
            for h3 in soup.find_all('h3'):
                if 'Adult Male' in h3.get_text():
                    male_section = h3
                    break
            
            if male_section:
                male_list = male_section.find_next('ul')
                if male_list:
                    for li in male_list.find_all('li'):
                        link = li.find('a')
                        if link:
                            name = link.get_text().strip()
                            url = link.get('href')
                            if url.startswith('/'):
                                url = self.base_url + url
                            
                            # Extract security level from text
                            security_text = li.get_text()
                            security_level = self.extract_security_level(security_text)
                            
                            facility_urls.append((name, url, security_level, 'Male'))
            
            # Find Adult Female section
            female_section = None
            for h3 in soup.find_all('h3'):
                if 'Adult Female' in h3.get_text():
                    female_section = h3
                    break
            
            if female_section:
                female_list = female_section.find_next('ul')
                if female_list:
                    for li in female_list.find_all('li'):
                        link = li.find('a')
                        if link:
                            name = link.get_text().strip()
                            url = link.get('href')
                            if url.startswith('/'):
                                url = self.base_url + url
                            
                            # Extract security level from text
                            security_text = li.get_text()
                            security_level = self.extract_security_level(security_text)
                            
                            facility_urls.append((name, url, security_level, 'Female'))
            
            return facility_urls
            
        except Exception as e:
            logger.error(f"Error getting facility URLs: {e}")
            return []
    
    def extract_security_level(self, text: str) -> str:
        """Extract security level from facility description text."""
        text_lower = text.lower()
        
        if 'maximum' in text_lower and 'medium' in text_lower and 'minimum' in text_lower:
            return 'Minimum, Medium & Maximum'
        elif 'maximum' in text_lower and 'medium' in text_lower:
            return 'Medium & Maximum'
        elif 'minimum' in text_lower and 'medium' in text_lower:
            return 'Minimum & Medium'
        elif 'minimum' in text_lower and 'maximum' in text_lower:
            return 'Minimum & Maximum'
        elif 'maximum' in text_lower:
            return 'Maximum'
        elif 'medium' in text_lower:
            return 'Medium'
        elif 'minimum' in text_lower:
            return 'Minimum'
        elif 're-entry' in text_lower:
            return 'Re-Entry'
        else:
            return 'Unknown'
    
    def scrape_facility_details(self, name: str, url: str, security_level: str, gender: str) -> Optional[Dict]:
        """Scrape detailed information from individual facility page."""
        try:
            response = self.session.get(url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            facility = {
                'name': name,
                'state': 'Indiana',
                'agency': 'Indiana Department of Correction (IDOC)',
                'security_level': security_level,
                'gender': gender,
                'detail_url': url
            }
            
            # Extract facility type
            facility['facility_type'] = self.determine_facility_type(name)
            
            # Extract address and contact info from the facility location section
            location_info = self.extract_location_info(soup)
            facility.update(location_info)
            
            # Try to geocode the address
            if facility.get('street_address') and facility.get('city'):
                coordinates = self.geocode_address(facility)
                facility.update(coordinates)
            
            return facility
            
        except Exception as e:
            logger.warning(f"Error scraping facility details for {name}: {e}")
            return None
    
    def extract_location_info(self, soup: BeautifulSoup) -> Dict:
        """Extract address and contact information from facility page."""
        location_info = {}
        
        try:
            # Look for the "Facility Physical Location" section
            location_section = soup.find('h3', string='Facility Physical Location')
            if location_section:
                # Get the next paragraph with address info
                address_p = location_section.find_next('p')
                if address_p:
                    address_text = address_p.get_text()
                    address_info = self.parse_address_text(address_text)
                    location_info.update(address_info)
                
                # Look for phone number in the same section
                phone_p = address_p.find_next('p') if address_p else None
                if phone_p and 'Phone' in phone_p.get_text():
                    phone_text = phone_p.get_text()
                    phone_match = re.search(r'\((\d{3})\)\s*(\d{3})-(\d{4})', phone_text)
                    if phone_match:
                        location_info['phone'] = f"({phone_match.group(1)}) {phone_match.group(2)}-{phone_match.group(3)}"
            
            # Also look for embedded Google Maps iframe for additional address validation
            iframe = soup.find('iframe', src=re.compile(r'google\.com/maps'))
            if iframe:
                src = iframe.get('src', '')
                # Extract address from Google Maps query parameter
                if 'q=' in src:
                    try:
                        import urllib.parse
                        parsed_url = urllib.parse.urlparse(src)
                        query_params = urllib.parse.parse_qs(parsed_url.query)
                        if 'q' in query_params:
                            maps_address = query_params['q'][0]
                            # Use this as a backup or validation
                            if not location_info.get('street_address'):
                                maps_info = self.parse_maps_address(maps_address)
                                location_info.update(maps_info)
                    except Exception as e:
                        logger.debug(f"Error parsing Google Maps address: {e}")
                        
        except Exception as e:
            logger.warning(f"Error extracting location info: {e}")
        
        return location_info
    
    def parse_address_text(self, address_text: str) -> Dict:
        """Parse address text into structured components."""
        address_info = {}
        
        try:
            lines = [line.strip() for line in address_text.split('\n') if line.strip()]
            
            if len(lines) >= 2:
                # First line should be facility name, second should be address
                if len(lines) >= 3:
                    # Format: Name \n Address \n City, State ZIP
                    address_info['street_address'] = lines[1]
                    city_state_zip = lines[2]
                else:
                    # Format: Name Address \n City, State ZIP
                    # Try to extract address from the first line after facility name
                    full_line = lines[1]
                    # Look for pattern like "21390 Old State Road 37, Branchville, IN 47514"
                    parts = full_line.split(', ')
                    if len(parts) >= 3:
                        address_info['street_address'] = parts[0]
                        city_state_zip = ', '.join(parts[1:])
                    else:
                        city_state_zip = full_line
                
                # Parse city, state, zip
                if 'city_state_zip' in locals():
                    city_info = self.parse_city_state_zip(city_state_zip)
                    address_info.update(city_info)
                    
        except Exception as e:
            logger.warning(f"Error parsing address text: {e}")
        
        return address_info
    
    def parse_maps_address(self, maps_address: str) -> Dict:
        """Parse address from Google Maps query parameter."""
        address_info = {}
        
        try:
            # Remove facility name if present
            if 'Correctional' in maps_address:
                # Find where the actual address starts
                parts = maps_address.split(' ')
                address_start = -1
                for i, part in enumerate(parts):
                    if re.match(r'\d+', part):  # Look for street number
                        address_start = i
                        break
                
                if address_start >= 0:
                    address_parts = parts[address_start:]
                    maps_address = ' '.join(address_parts)
            
            # Parse the address
            # Format should be like "21390 Old State Road 37, Branchville, IN 47514"
            parts = maps_address.split(', ')
            if len(parts) >= 3:
                address_info['street_address'] = parts[0]
                address_info['city'] = parts[1]
                
                # Parse state and zip from last part
                state_zip = parts[2].strip()
                state_zip_match = re.match(r'([A-Z]{2})\s+(\d{5}(?:-\d{4})?)', state_zip)
                if state_zip_match:
                    address_info['zip_code'] = state_zip_match.group(2)
                    
        except Exception as e:
            logger.warning(f"Error parsing maps address: {e}")
        
        return address_info
    
    def parse_city_state_zip(self, city_state_zip: str) -> Dict:
        """Parse city, state, and ZIP code from combined string."""
        city_info = {}
        
        try:
            # Pattern: "City, ST ZIP" or "City, ST ZIP-XXXX"
            match = re.match(r'^(.+?),\s*([A-Z]{2})\s+(\d{5}(?:-\d{4})?)$', city_state_zip.strip())
            if match:
                city_info['city'] = match.group(1).strip()
                city_info['zip_code'] = match.group(3)
            else:
                # Fallback: try to extract what we can
                parts = city_state_zip.split(',')
                if len(parts) >= 2:
                    city_info['city'] = parts[0].strip()
                    
                    # Look for ZIP in the last part
                    last_part = parts[-1].strip()
                    zip_match = re.search(r'(\d{5}(?:-\d{4})?)', last_part)
                    if zip_match:
                        city_info['zip_code'] = zip_match.group(1)
                        
        except Exception as e:
            logger.warning(f"Error parsing city/state/zip: {e}")
        
        return city_info
    
    def determine_facility_type(self, name: str) -> str:
        """Determine facility type based on name."""
        name_lower = name.lower()
        
        if 'correctional facility' in name_lower:
            return 'Correctional Facility'
        elif 'correctional center' in name_lower:
            return 'Correctional Center'
        elif 'state prison' in name_lower:
            return 'State Prison'
        elif 'women\'s prison' in name_lower:
            return 'Women\'s Prison'
        elif 're-entry center' in name_lower or 'reentry center' in name_lower:
            return 'Re-Entry Center'
        elif 'reception' in name_lower and 'diagnostic' in name_lower:
            return 'Reception Diagnostic Center'
        elif 'industrial facility' in name_lower:
            return 'Industrial Facility'
        else:
            return 'Correctional Facility'
    
    def geocode_address(self, facility: Dict) -> Dict:
        """Geocode facility address to get coordinates."""
        coordinates = {}
        
        try:
            # Construct full address
            address_parts = []
            if facility.get('street_address'):
                address_parts.append(facility['street_address'])
            if facility.get('city'):
                address_parts.append(facility['city'])
            address_parts.append('Indiana')
            if facility.get('zip_code'):
                address_parts.append(facility['zip_code'])
            
            full_address = ', '.join(address_parts)
            logger.info(f"Geocoding: {full_address}")
            
            # Try geocoding services in order of preference
            coords = self.try_geocoding_services(full_address)
            if coords:
                coordinates['latitude'] = coords[0]
                coordinates['longitude'] = coords[1]
                logger.info(f"✓ Geocoded: {coords[0]}, {coords[1]}")
            else:
                logger.warning(f"✗ Failed to geocode: {full_address}")
            
        except Exception as e:
            logger.warning(f"Error geocoding address: {e}")
        
        return coordinates
    
    def try_geocoding_services(self, address: str) -> Optional[Tuple[float, float]]:
        """Try multiple geocoding services in order of preference."""
        # Try Google Maps API first (if available)
        coords = self.geocode_google(address)
        if coords:
            return coords
        
        # Fallback to Nominatim
        time.sleep(1)  # Rate limiting for free service
        coords = self.geocode_nominatim(address)
        if coords:
            return coords
        
        # Fallback to Photon
        time.sleep(1)  # Rate limiting
        coords = self.geocode_photon(address)
        if coords:
            return coords
        
        return None
    
    def geocode_google(self, address: str) -> Optional[Tuple[float, float]]:
        """Geocode using Google Maps API."""
        try:
            import os
            api_key = os.getenv('GOOGLE_MAPS_API_KEY')
            if not api_key:
                return None
            
            url = "https://maps.googleapis.com/maps/api/geocode/json"
            params = {
                'address': address,
                'key': api_key
            }
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            if data['status'] == 'OK' and data['results']:
                location = data['results'][0]['geometry']['location']
                return (location['lat'], location['lng'])
                
        except Exception as e:
            logger.debug(f"Google geocoding failed: {e}")
        
        return None
    
    def geocode_nominatim(self, address: str) -> Optional[Tuple[float, float]]:
        """Geocode using OpenStreetMap Nominatim."""
        try:
            url = "https://nominatim.openstreetmap.org/search"
            params = {
                'q': address,
                'format': 'json',
                'limit': 1,
                'countrycodes': 'us'
            }
            
            headers = {
                'User-Agent': 'Prison Data Scraper (https://github.com/user/prisons)'
            }
            
            response = requests.get(url, params=params, headers=headers, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            if data:
                return (float(data[0]['lat']), float(data[0]['lon']))
                
        except Exception as e:
            logger.debug(f"Nominatim geocoding failed: {e}")
        
        return None
    
    def geocode_photon(self, address: str) -> Optional[Tuple[float, float]]:
        """Geocode using Photon geocoder."""
        try:
            url = "https://photon.komoot.io/api/"
            params = {
                'q': address,
                'limit': 1,
                'osm_tag': '!place:hamlet,village'
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            if data.get('features'):
                coords = data['features'][0]['geometry']['coordinates']
                return (coords[1], coords[0])  # Photon returns [lng, lat]
                
        except Exception as e:
            logger.debug(f"Photon geocoding failed: {e}")
        
        return None


def main():
    """Main function for testing the scraper."""
    scraper = IndianaScraper()
    facilities = scraper.scrape_facilities()
    
    print(f"Found {len(facilities)} Indiana correctional facilities:")
    for facility in facilities[:10]:  # Show first 10
        print(f"- {facility['name']}")
        if facility.get('facility_type'):
            print(f"  Type: {facility['facility_type']}")
        if facility.get('security_level'):
            print(f"  Security: {facility['security_level']}")
        if facility.get('gender'):
            print(f"  Gender: {facility['gender']}")
        if facility.get('street_address'):
            print(f"  Address: {facility['street_address']}")
        if facility.get('city'):
            print(f"  City: {facility['city']}, IN {facility.get('zip_code', '')}")
        if facility.get('phone'):
            print(f"  Phone: {facility['phone']}")
        if facility.get('latitude'):
            print(f"  Coordinates: {facility['latitude']}, {facility['longitude']}")
        print()

if __name__ == "__main__":
    main()
