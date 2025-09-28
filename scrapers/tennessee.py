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

class TennesseeScraper:
    """Scraper for Tennessee Department of Correction facilities."""
    
    def __init__(self):
        self.base_url = "https://www.tn.gov"
        self.facilities_url = "https://www.tn.gov/correction/state-prisons/state-prison-list.html"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0',
        })
    
    def scrape_facilities(self) -> List[Dict]:
        """
        Scrape all Tennessee correctional facilities.
        
        Returns:
            List of facility dictionaries with details and coordinates
        """
        logger.info("Starting Tennessee facilities scrape...")
        
        # Get facility URLs from the main directory page
        facility_urls = self.get_facility_urls()
        
        if not facility_urls:
            logger.error("Failed to get facility URLs from directory page")
            return []
        
        logger.info(f"Found {len(facility_urls)} facility URLs")
        
        # Scrape details from each facility page
        facilities = []
        for i, (name, url) in enumerate(facility_urls.items(), 1):
            try:
                logger.info(f"Processing facility {i}/{len(facility_urls)}: {name}")
                
                facility_data = self.scrape_facility_details(name, url)
                if facility_data:
                    facilities.append(facility_data)
                
                # Rate limiting - be respectful
                time.sleep(0.3)
                
            except Exception as e:
                logger.error(f"Error processing {name}: {e}")
                continue
        
        logger.info(f"Successfully processed {len(facilities)} facilities")
        return facilities
    
    def get_facility_urls(self) -> Dict[str, str]:
        """Extract facility URLs from the main directory page."""
        try:
            # Add retry logic for connection issues
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    response = self.session.get(self.facilities_url, timeout=30)
                    response.raise_for_status()
                    break
                except Exception as e:
                    logger.warning(f"Attempt {attempt + 1} failed: {e}")
                    if attempt == max_retries - 1:
                        raise
                    time.sleep(2)
            
            soup = BeautifulSoup(response.content, 'html.parser')
            facility_urls = {}
            
            # Find all facility links in the regional sections
            regional_sections = soup.find_all('div', class_='tn-rte')
            
            for section in regional_sections:
                # Look for facility links
                facility_links = section.find_all('a', href=True)
                
                for link in facility_links:
                    href = link.get('href')
                    if href and 'state-prison-list' in href and href != '/correction/state-prisons/state-prison-list.html':
                        facility_name = link.get_text().strip()
                        
                        # Clean up facility name (remove parenthetical info)
                        facility_name = re.sub(r'\s*\(formerly[^)]+\)', '', facility_name)
                        
                        # Construct full URL
                        if href.startswith('/'):
                            full_url = self.base_url + href
                        else:
                            full_url = href
                        
                        facility_urls[facility_name] = full_url
            
            return facility_urls
            
        except Exception as e:
            logger.error(f"Error getting facility URLs: {e}")
            return {}
    
    def scrape_facility_details(self, name: str, url: str) -> Optional[Dict]:
        """Scrape details from an individual facility page."""
        try:
            response = self.session.get(url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            facility = {
                'name': name,
                'state': 'Tennessee',
                'agency': 'Tennessee Department of Correction (TDOC)',
                'detail_url': url
            }
            
            # Extract warden and address information
            warden_info = self.extract_warden_info(soup)
            facility.update(warden_info)
            
            # Extract facility description/details
            description_info = self.extract_description_info(soup)
            facility.update(description_info)
            
            # Determine facility type
            facility['facility_type'] = self.determine_facility_type(name)
            
            # Geocode the address if we have one
            if facility.get('street_address') and facility.get('city'):
                coordinates = self.geocode_address(facility)
                facility.update(coordinates)
            
            return facility
            
        except Exception as e:
            logger.warning(f"Error scraping facility details for {name}: {e}")
            return None
    
    def extract_warden_info(self, soup: BeautifulSoup) -> Dict:
        """Extract warden and address information from facility page."""
        warden_info = {}
        
        try:
            # Look for warden information in textimage-text div
            text_sections = soup.find_all('div', class_='textimage-text')
            
            for section in text_sections:
                # Look for warden heading
                warden_heading = section.find('h2')
                if warden_heading and 'warden' in warden_heading.get_text().lower():
                    warden_text = warden_heading.get_text().strip()
                    # Extract warden name
                    warden_match = re.search(r'Warden\s+(.+)', warden_text)
                    if warden_match:
                        warden_info['warden'] = warden_match.group(1).strip()
                
                # Extract address information from paragraphs
                paragraphs = section.find_all('p')
                for p in paragraphs:
                    p_text = p.get_text().strip()
                    
                    # Look for address patterns
                    if self.looks_like_address(p_text):
                        address_info = self.parse_address_text(p_text)
                        warden_info.update(address_info)
                        break
                        
        except Exception as e:
            logger.warning(f"Error extracting warden info: {e}")
        
        return warden_info
    
    def looks_like_address(self, text: str) -> bool:
        """Check if text looks like an address block."""
        # Look for patterns that indicate address information
        address_patterns = [
            r'\d+\s+\w+.*(?:Drive|Street|Road|Avenue|Lane|Boulevard|Way|Circle|Court)',
            r'P\.O\.\s*Box\s*\d+',
            r'\w+,\s*Tennessee\s*\d{5}',
            r'\(\d{3}\)\s*\d{3}-\d{4}'
        ]
        
        for pattern in address_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False
    
    def parse_address_text(self, text: str) -> Dict:
        """Parse address information from text block."""
        address_info = {}
        
        try:
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            
            for line in lines:
                # Extract street address
                street_match = re.search(r'^(\d+\s+[\w\s]+(?:Drive|Street|Road|Avenue|Lane|Boulevard|Way|Circle|Court))', line, re.IGNORECASE)
                if street_match and not address_info.get('street_address'):
                    address_info['street_address'] = street_match.group(1).strip()
                
                # Extract city, state, zip
                city_state_zip_match = re.search(r'^([^,]+),\s*Tennessee\s*(\d{5}(?:-\d{4})?)', line, re.IGNORECASE)
                if city_state_zip_match:
                    address_info['city'] = city_state_zip_match.group(1).strip()
                    address_info['zip_code'] = city_state_zip_match.group(2).strip()
                
                # Extract phone number
                phone_match = re.search(r'\((\d{3})\)\s*(\d{3})-(\d{4})', line)
                if phone_match:
                    address_info['phone'] = f"({phone_match.group(1)}) {phone_match.group(2)}-{phone_match.group(3)}"
                
                # Extract county information
                county_match = re.search(r'\(([^)]+\s+County)\)', line)
                if county_match:
                    address_info['county'] = county_match.group(1).strip()
                
                # Extract P.O. Box for mailing
                po_box_match = re.search(r'P\.O\.\s*Box\s*(\d+)', line, re.IGNORECASE)
                if po_box_match:
                    address_info['mailing_address'] = f"P.O. Box {po_box_match.group(1)}"
                    
        except Exception as e:
            logger.warning(f"Error parsing address text: {e}")
        
        return address_info
    
    def extract_description_info(self, soup: BeautifulSoup) -> Dict:
        """Extract facility description and operational details."""
        description_info = {}
        
        try:
            # Look for facility description in main content
            content_sections = soup.find_all('div', class_='tn-rte')
            
            for section in content_sections:
                text_content = section.get_text()
                
                # Extract capacity information
                capacity_match = re.search(r'operating capacity of\s+([0-9,]+)', text_content, re.IGNORECASE)
                if capacity_match:
                    capacity_str = capacity_match.group(1).replace(',', '')
                    description_info['capacity'] = int(capacity_str)
                
                # Extract security level
                if 'maximum-security' in text_content.lower() or 'maximum security' in text_content.lower():
                    description_info['security_level'] = 'Maximum'
                elif 'medium-security' in text_content.lower() or 'medium security' in text_content.lower():
                    description_info['security_level'] = 'Medium'
                elif 'minimum-security' in text_content.lower() or 'minimum security' in text_content.lower():
                    description_info['security_level'] = 'Minimum'
                
                # Extract facility size/acreage
                acres_match = re.search(r'(\d+)\s+acres', text_content, re.IGNORECASE)
                if acres_match:
                    description_info['acres'] = int(acres_match.group(1))
                
                # Extract square footage
                sqft_match = re.search(r'([0-9,]+)\s+square feet', text_content, re.IGNORECASE)
                if sqft_match:
                    sqft_str = sqft_match.group(1).replace(',', '')
                    description_info['square_feet'] = int(sqft_str)
                
                # Extract staff count
                staff_match = re.search(r'approximately\s+([0-9,]+)\s+staff', text_content, re.IGNORECASE)
                if staff_match:
                    staff_str = staff_match.group(1).replace(',', '')
                    description_info['staff_count'] = int(staff_str)
                    
        except Exception as e:
            logger.warning(f"Error extracting description info: {e}")
        
        return description_info
    
    def determine_facility_type(self, name: str) -> str:
        """Determine facility type based on name."""
        name_lower = name.lower()
        
        if 'penitentiary' in name_lower:
            return 'State Penitentiary'
        elif 'correctional complex' in name_lower:
            return 'Correctional Complex'
        elif 'correctional facility' in name_lower:
            return 'Correctional Facility'
        elif 'correctional center' in name_lower:
            return 'Correctional Center'
        elif 'rehabilitation center' in name_lower:
            return 'Rehabilitation Center'
        elif 'transition center' in name_lower:
            return 'Transition Center'
        elif 'special needs' in name_lower:
            return 'Special Needs Facility'
        elif 'industrial complex' in name_lower:
            return 'Industrial Complex'
        elif 'therapeutic' in name_lower:
            return 'Therapeutic Facility'
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
            address_parts.append('Tennessee')
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
    scraper = TennesseeScraper()
    facilities = scraper.scrape_facilities()
    
    print(f"Found {len(facilities)} Tennessee correctional facilities:")
    for facility in facilities[:10]:  # Show first 10
        print(f"- {facility['name']}")
        if facility.get('facility_type'):
            print(f"  Type: {facility['facility_type']}")
        if facility.get('warden'):
            print(f"  Warden: {facility['warden']}")
        if facility.get('street_address'):
            print(f"  Address: {facility['street_address']}")
        if facility.get('city'):
            print(f"  City: {facility['city']}, TN {facility.get('zip_code', '')}")
        if facility.get('phone'):
            print(f"  Phone: {facility['phone']}")
        if facility.get('capacity'):
            print(f"  Capacity: {facility['capacity']}")
        if facility.get('security_level'):
            print(f"  Security Level: {facility['security_level']}")
        print()

if __name__ == "__main__":
    main()
