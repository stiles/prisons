#!/usr/bin/env python3

import requests
import re
from bs4 import BeautifulSoup
from typing import Dict, List, Optional, Tuple
import logging
import time
import urllib3

# Suppress SSL warnings for sites with certificate issues
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MarylandScraper:
    """Scraper for Maryland Department of Public Safety and Correctional Services facilities."""
    
    def __init__(self):
        self.base_url = "https://www.dpscs.state.md.us"
        self.facilities_url = "https://www.dpscs.state.md.us/locations/prisons.shtml"
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
        Scrape all Maryland correctional facilities.
        
        Returns:
            List of facility dictionaries with details and coordinates
        """
        logger.info("Starting Maryland facilities scrape...")
        
        # Get facility URLs from the main directory
        facility_urls = self.get_facility_urls()
        
        if not facility_urls:
            logger.error("Failed to get facility URLs")
            return []
        
        logger.info(f"Found {len(facility_urls)} facility URLs")
        
        # Process each facility
        facilities = []
        for i, (name, url) in enumerate(facility_urls, 1):
            try:
                logger.info(f"Processing facility {i}/{len(facility_urls)}: {name}")
                
                facility = self.scrape_facility_details(name, url)
                if facility:
                    facilities.append(facility)
                
                # Rate limiting - be respectful
                time.sleep(0.3)
                
            except Exception as e:
                logger.error(f"Error processing {name}: {e}")
                continue
        
        logger.info(f"Successfully processed {len(facilities)} facilities")
        return facilities
    
    def get_facility_urls(self) -> List[Tuple[str, str]]:
        """Extract facility URLs from the main directory."""
        try:
            response = self.session.get(self.facilities_url, verify=False)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            facility_urls = []
            
            # Find the sectionNavGroup3 div that contains the facility links
            nav_group = soup.find('div', id='sectionNavGroup3')
            if nav_group:
                links = nav_group.find_all('a', class_='nav-link')
                for link in links:
                    name = link.get_text().strip()
                    url = link.get('href')
                    
                    if url:
                        # Convert relative URL to absolute
                        if url.startswith('../'):
                            url = self.base_url + '/locations/' + url.split('/')[-1]
                        elif not url.startswith('http'):
                            url = self.base_url + url
                        
                        facility_urls.append((name, url))
            
            return facility_urls
            
        except Exception as e:
            logger.error(f"Error getting facility URLs: {e}")
            return []
    
    def scrape_facility_details(self, name: str, url: str) -> Optional[Dict]:
        """Scrape detailed information from individual facility page."""
        try:
            response = self.session.get(url, verify=False)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            facility = {
                'name': name,
                'state': 'Maryland',
                'agency': 'Maryland Department of Public Safety and Correctional Services (DPSCS)',
                'detail_url': url
            }
            
            # Extract facility type
            facility['facility_type'] = self.determine_facility_type(name)
            
            # Extract contact and facility info from the left_redbox div
            contact_info = self.extract_contact_info(soup)
            facility.update(contact_info)
            
            # Try to geocode the address
            if facility.get('street_address') and facility.get('city'):
                coordinates = self.geocode_address(facility)
                facility.update(coordinates)
            
            return facility
            
        except Exception as e:
            logger.warning(f"Error scraping facility details for {name}: {e}")
            return None
    
    def extract_contact_info(self, soup: BeautifulSoup) -> Dict:
        """Extract contact and facility information from the left_redbox div."""
        contact_info = {}
        
        try:
            # Find the left_redbox div that contains contact information
            redbox = soup.find('div', class_='left_redbox')
            if redbox:
                # Get all text content
                text_content = redbox.get_text()
                
                # Extract address information
                address_info = self.parse_contact_text(text_content)
                contact_info.update(address_info)
                
                # Extract staff information
                staff_info = self.extract_staff_info(text_content)
                contact_info.update(staff_info)
                
                # Extract facility details
                facility_details = self.extract_facility_details(text_content)
                contact_info.update(facility_details)
                
        except Exception as e:
            logger.warning(f"Error extracting contact info: {e}")
        
        return contact_info
    
    def parse_contact_text(self, text: str) -> Dict:
        """Parse contact information from the text content."""
        contact_info = {}
        
        try:
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            
            # Look for address pattern
            for i, line in enumerate(lines):
                # Look for street address (contains numbers and street indicators)
                if re.search(r'\d+.*(?:Avenue|Street|Road|Drive|Boulevard|Lane|Way|Court|Place|Ave|St|Rd|Dr|Blvd|Ln|Ct|Pl)', line, re.IGNORECASE):
                    contact_info['street_address'] = line
                    
                    # Next line should be city, state, zip
                    if i + 1 < len(lines):
                        city_line = lines[i + 1]
                        city_info = self.parse_city_state_zip(city_line)
                        contact_info.update(city_info)
                    break
            
            # Extract phone number
            phone_match = re.search(r'Phone:\s*\((\d{3})\)\s*(\d{3})-(\d{4})', text)
            if phone_match:
                contact_info['phone'] = f"({phone_match.group(1)}) {phone_match.group(2)}-{phone_match.group(3)}"
            
            # Extract fax number
            fax_match = re.search(r'Fax:\s*\((\d{3})\)\s*(\d{3})-(\d{4})', text)
            if fax_match:
                contact_info['fax'] = f"({fax_match.group(1)}) {fax_match.group(2)}-{fax_match.group(3)}"
                
        except Exception as e:
            logger.warning(f"Error parsing contact text: {e}")
        
        return contact_info
    
    def parse_city_state_zip(self, city_line: str) -> Dict:
        """Parse city, state, and ZIP code from city line."""
        city_info = {}
        
        try:
            # Pattern: "City, State ZIP"
            match = re.match(r'^(.+?),\s*([A-Z]{2})\s+(\d{5}(?:-\d{4})?)$', city_line.strip())
            if match:
                city_info['city'] = match.group(1).strip()
                city_info['zip_code'] = match.group(3)
            else:
                # Fallback: try to extract what we can
                if ',' in city_line:
                    parts = city_line.split(',')
                    city_info['city'] = parts[0].strip()
                    
                    # Look for ZIP in the rest
                    rest = ' '.join(parts[1:])
                    zip_match = re.search(r'(\d{5}(?:-\d{4})?)', rest)
                    if zip_match:
                        city_info['zip_code'] = zip_match.group(1)
                        
        except Exception as e:
            logger.warning(f"Error parsing city/state/zip: {e}")
        
        return city_info
    
    def extract_staff_info(self, text: str) -> Dict:
        """Extract staff information from the text content."""
        staff_info = {}
        
        try:
            # Extract warden information
            warden_patterns = [
                r'(?:Acting\s+)?Warden[:\s]*\n*([^\n]+)',
                r'Warden[:\s]*([^\n]+)',
            ]
            
            for pattern in warden_patterns:
                match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
                if match:
                    warden_name = match.group(1).strip()
                    if warden_name and warden_name != 'Warden':
                        staff_info['warden'] = warden_name
                        break
            
            # Extract assistant warden
            assistant_match = re.search(r'Assistant\s+Warden[:\s]*\n*([^\n]+)', text, re.IGNORECASE | re.MULTILINE)
            if assistant_match:
                assistant_name = assistant_match.group(1).strip()
                if assistant_name:
                    staff_info['assistant_warden'] = assistant_name
            
            # Extract facility administrator
            admin_match = re.search(r'Facility\s+Administrator[:\s]*\n*([^\n]+)', text, re.IGNORECASE | re.MULTILINE)
            if admin_match:
                admin_name = admin_match.group(1).strip()
                if admin_name:
                    staff_info['facility_administrator'] = admin_name
                    
        except Exception as e:
            logger.warning(f"Error extracting staff info: {e}")
        
        return staff_info
    
    def extract_facility_details(self, text: str) -> Dict:
        """Extract facility details like security level and year opened."""
        facility_details = {}
        
        try:
            # Extract security level
            security_match = re.search(r'Security\s+Level[:\s]*\n*([^\n]+)', text, re.IGNORECASE | re.MULTILINE)
            if security_match:
                security_level = security_match.group(1).strip()
                if security_level:
                    facility_details['security_level'] = security_level
            
            # Extract year opened
            year_match = re.search(r'Year\s+Opened[:\s]*\n*(\d{4})', text, re.IGNORECASE | re.MULTILINE)
            if year_match:
                year_opened = year_match.group(1).strip()
                if year_opened:
                    facility_details['year_opened'] = int(year_opened)
                    
        except Exception as e:
            logger.warning(f"Error extracting facility details: {e}")
        
        return facility_details
    
    def determine_facility_type(self, name: str) -> str:
        """Determine facility type based on name."""
        name_lower = name.lower()
        
        if 'correctional center' in name_lower:
            return 'Correctional Center'
        elif 'correctional facility' in name_lower:
            return 'Correctional Facility'
        elif 'correctional institution' in name_lower:
            return 'Correctional Institution'
        elif 'training center' in name_lower:
            return 'Training Center'
        elif 'women' in name_lower:
            return 'Women\'s Institution'
        elif 'institution' in name_lower:
            return 'Institution'
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
            address_parts.append('Maryland')
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
    scraper = MarylandScraper()
    facilities = scraper.scrape_facilities()
    
    print(f"Found {len(facilities)} Maryland correctional facilities:")
    for facility in facilities[:10]:  # Show first 10
        print(f"- {facility['name']}")
        if facility.get('facility_type'):
            print(f"  Type: {facility['facility_type']}")
        if facility.get('security_level'):
            print(f"  Security: {facility['security_level']}")
        if facility.get('warden'):
            print(f"  Warden: {facility['warden']}")
        if facility.get('street_address'):
            print(f"  Address: {facility['street_address']}")
        if facility.get('city'):
            print(f"  City: {facility['city']}, MD {facility.get('zip_code', '')}")
        if facility.get('phone'):
            print(f"  Phone: {facility['phone']}")
        if facility.get('year_opened'):
            print(f"  Opened: {facility['year_opened']}")
        if facility.get('latitude'):
            print(f"  Coordinates: {facility['latitude']}, {facility['longitude']}")
        print()

if __name__ == "__main__":
    main()
