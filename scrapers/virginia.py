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

class VirginiaScraper:
    """Scraper for Virginia Department of Corrections facilities."""
    
    def __init__(self):
        self.base_url = "https://www.vadoc.virginia.gov"
        self.facilities_url = "https://www.vadoc.virginia.gov/facilities-and-offices"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
    
    def scrape_facilities(self) -> List[Dict]:
        """
        Scrape all Virginia correctional facilities.
        
        Returns:
            List of facility dictionaries with details and coordinates
        """
        logger.info("Starting Virginia facilities scrape...")
        
        # Get facility data from main page
        facilities = self.get_facilities_from_main_page()
        
        if not facilities:
            logger.error("Failed to get facility data from main page")
            return []
        
        logger.info(f"Found {len(facilities)} facilities on main page")
        
        # Process each facility for geocoding
        processed_facilities = []
        for i, facility in enumerate(facilities, 1):
            try:
                logger.info(f"Processing facility {i}/{len(facilities)}: {facility['name']}")
                
                # Geocode the address if we have one
                if facility.get('street_address') and facility.get('city'):
                    coords = self.geocode_address(facility)
                    if coords:
                        facility['latitude'], facility['longitude'] = coords
                
                processed_facilities.append(facility)
                
                # Rate limiting - be respectful
                time.sleep(0.2)
                
            except Exception as e:
                logger.error(f"Error processing {facility.get('name', 'Unknown')}: {e}")
                processed_facilities.append(facility)  # Add anyway without coordinates
                continue
        
        logger.info(f"Successfully processed {len(processed_facilities)} facilities")
        return processed_facilities
    
    def get_facilities_from_main_page(self) -> List[Dict]:
        """Extract facility information from the main facilities page."""
        try:
            response = self.session.get(self.facilities_url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            facilities = []
            
            # Get all text content and split into lines for processing
            text_content = soup.get_text()
            lines = [line.strip() for line in text_content.split('\n') if line.strip()]
            
            # Find facility blocks by looking for patterns
            facility_blocks = self.extract_facility_blocks(lines)
            
            for block in facility_blocks:
                facility_data = self.parse_facility_block(block)
                if facility_data:
                    facilities.append(facility_data)
            
            # Also extract facilities from the dropdown menu
            dropdown_facilities = self.extract_dropdown_facilities(soup)
            
            # Merge dropdown facilities with main page facilities
            facilities = self.merge_facility_data(facilities, dropdown_facilities)
            
            return facilities
            
        except Exception as e:
            logger.error(f"Error getting facilities from main page: {e}")
            return []
    
    def extract_facility_blocks(self, lines: List[str]) -> List[List[str]]:
        """Extract facility information blocks from the page text."""
        facility_blocks = []
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # Look for facility names (containing 'Correctional', 'Prison', 'Center', etc.)
            if self.is_facility_name(line):
                current_block = [line]
                
                # Look ahead for facility information
                j = i + 1
                while j < len(lines) and j < i + 15:  # Look ahead max 15 lines
                    next_line = lines[j].strip()
                    
                    # Stop if we hit another facility name
                    if self.is_facility_name(next_line):
                        break
                    
                    # Include non-empty lines that contain facility info
                    if next_line and (
                        self.is_facility_info(next_line) or
                        re.search(r'[A-Za-z\s]+,\s*VA\s*\d{5}', next_line) or  # City, state, zip
                        re.search(r'\d{5}', next_line) or  # Just zip code
                        'superintendent' in next_line.lower() or
                        'warden' in next_line.lower()
                    ):
                        current_block.append(next_line)
                    
                    j += 1
                
                if len(current_block) > 1:  # Only add if we found additional info
                    facility_blocks.append(current_block)
                
                i = j - 1  # Continue from where we left off
            
            i += 1
        
        return facility_blocks
    
    def is_facility_name(self, line: str) -> bool:
        """Check if a line looks like a facility name."""
        facility_keywords = [
            'correctional center', 'correctional unit', 'correctional complex',
            'state prison', 'detention center', 'work center', 'diversion center',
            'reception center', 'classification center', 'treatment center'
        ]
        
        line_lower = line.lower()
        return any(keyword in line_lower for keyword in facility_keywords)
    
    def is_facility_info(self, line: str) -> bool:
        """Check if a line contains facility information (address, phone, etc.)."""
        # Address patterns
        if re.search(r'\d+.*(?:road|street|ave|avenue|drive|dr|blvd|boulevard|lane|ln|way|court|ct|highway|hwy)', line, re.IGNORECASE):
            return True
        
        # City, state, zip patterns (with or without zip)
        if re.search(r'[A-Za-z\s]+,\s*VA(?:\s*\d{5})?', line):
            return True
        
        # Just zip code
        if re.match(r'^\d{5}$', line):
            return True
        
        # Phone patterns
        if re.search(r'\(\d{3}\)\s*\d{3}-\d{4}', line):
            return True
        
        # Other facility info
        if any(keyword in line.lower() for keyword in ['phone:', 'fax:', 'warden:', 'superintendent:']):
            return True
        
        return False
    
    def parse_facility_block(self, block: List[str]) -> Optional[Dict]:
        """Parse a facility information block into structured data."""
        if not block:
            return None
        
        facility = {
            'name': block[0].strip(),
            'state': 'Virginia',
            'agency': 'Virginia Department of Corrections (VADOC)'
        }
        
        # Join all lines to handle multi-line addresses
        full_text = ' '.join(block[1:])
        
        # Parse the rest of the block for address, phone, etc.
        for i, line in enumerate(block[1:]):
            line = line.strip()
            
            # Parse street address
            if re.search(r'\d+.*(?:road|street|ave|avenue|drive|dr|blvd|boulevard|lane|ln|way|court|ct|highway|hwy)', line, re.IGNORECASE):
                facility['street_address'] = line
            
            # Parse city, state, zip (could be on same line or next line)
            city_match = re.search(r'([A-Za-z\s]+),\s*VA\s*(\d{5})', line)
            if city_match:
                facility['city'] = city_match.group(1).strip()
                facility['zip_code'] = city_match.group(2)
            elif re.match(r'^[A-Za-z\s]+,\s*VA$', line):
                # City and state on one line, zip might be next
                city_state = line.split(',')[0].strip()
                facility['city'] = city_state
                # Look for zip on next line
                if i + 2 < len(block) and re.match(r'^\d{5}$', block[i + 2].strip()):
                    facility['zip_code'] = block[i + 2].strip()
            elif re.match(r'^\d{5}$', line):
                # Just a zip code, city might be on previous line
                facility['zip_code'] = line
                if i > 0:
                    prev_line = block[i].strip()  # Previous line (i is 0-based in this loop)
                    if ',' in prev_line and 'VA' in prev_line:
                        city_match = re.search(r'([A-Za-z\s]+),\s*VA', prev_line)
                        if city_match:
                            facility['city'] = city_match.group(1).strip()
            
            # Parse phone
            phone_match = re.search(r'\((\d{3})\)\s*(\d{3})-(\d{4})', line)
            if phone_match:
                facility['phone'] = f"({phone_match.group(1)}) {phone_match.group(2)}-{phone_match.group(3)}"
            
            # Parse warden/superintendent (could include name)
            if any(title in line.lower() for title in ['warden', 'superintendent']):
                # Extract name if it's in the format "Name, Title" or "Title: Name"
                if ':' in line:
                    warden_match = re.search(r'(?:warden|superintendent):\s*(.+)', line, re.IGNORECASE)
                    if warden_match:
                        facility['warden'] = warden_match.group(1).strip()
                elif ',' in line:
                    # Format might be "John Doe, Superintendent"
                    name_match = re.search(r'([^,]+),\s*(?:warden|superintendent)', line, re.IGNORECASE)
                    if name_match:
                        facility['warden'] = name_match.group(1).strip()
                else:
                    # Just the name followed by title
                    warden_match = re.search(r'(.+?)\s+(?:warden|superintendent)', line, re.IGNORECASE)
                    if warden_match:
                        facility['warden'] = warden_match.group(1).strip()
        
        # Determine facility type based on name
        facility['facility_type'] = self.determine_facility_type(facility['name'])
        
        return facility
    
    def extract_dropdown_facilities(self, soup: BeautifulSoup) -> List[str]:
        """Extract facility names from the dropdown menu."""
        dropdown_facilities = []
        
        try:
            # Look for the facilities dropdown menu
            dropdown = soup.find('ul', id='facilities-submenu')
            if dropdown:
                # Find all links in the dropdown
                facility_links = dropdown.find_all('a', href='#')
                
                for link in facility_links:
                    facility_name = link.get_text().strip()
                    if self.is_facility_name(facility_name):
                        dropdown_facilities.append(facility_name)
            
        except Exception as e:
            logger.warning(f"Error extracting dropdown facilities: {e}")
        
        return dropdown_facilities
    
    def merge_facility_data(self, main_facilities: List[Dict], dropdown_names: List[str]) -> List[Dict]:
        """Merge facility data from main page with dropdown facility names."""
        # Create a set of names from main facilities for quick lookup
        main_names = {self.normalize_facility_name(f['name']) for f in main_facilities}
        
        # Add any dropdown facilities that aren't in the main list
        for dropdown_name in dropdown_names:
            normalized_dropdown = self.normalize_facility_name(dropdown_name)
            
            if normalized_dropdown not in main_names:
                # Create a basic facility entry
                facility = {
                    'name': dropdown_name,
                    'state': 'Virginia',
                    'agency': 'Virginia Department of Corrections (VADOC)',
                    'facility_type': self.determine_facility_type(dropdown_name)
                }
                main_facilities.append(facility)
        
        return main_facilities
    
    def normalize_facility_name(self, name: str) -> str:
        """Normalize facility name for comparison."""
        return re.sub(r'[^\w\s]', '', name.lower()).strip()
    
    def determine_facility_type(self, name: str) -> str:
        """Determine facility type based on name."""
        name_lower = name.lower()
        
        if 'state prison' in name_lower:
            return 'State Prison'
        elif 'correctional center' in name_lower:
            return 'Correctional Center'
        elif 'correctional unit' in name_lower:
            return 'Correctional Unit'
        elif 'correctional complex' in name_lower:
            return 'Correctional Complex'
        elif 'detention center' in name_lower:
            return 'Detention Center'
        elif 'work center' in name_lower:
            return 'Work Center'
        elif 'diversion center' in name_lower:
            return 'Diversion Center'
        elif 'reception' in name_lower and 'classification' in name_lower:
            return 'Reception & Classification Center'
        elif 'treatment center' in name_lower:
            return 'Treatment Center'
        else:
            return 'Correctional Facility'
    
    def geocode_address(self, facility: Dict) -> Optional[Tuple[float, float]]:
        """Geocode facility address to get coordinates."""
        try:
            # Build full address
            address_parts = []
            
            if facility.get('street_address'):
                address_parts.append(facility['street_address'])
            
            if facility.get('city'):
                address_parts.append(f"{facility['city']}, VA")
            
            if facility.get('zip_code'):
                address_parts.append(facility['zip_code'])
            
            if not address_parts:
                return None
            
            full_address = ', '.join(address_parts)
            logger.info(f"Geocoding: {full_address}")
            
            # Try geocoding with multiple services
            coords = self.try_geocoding_services(full_address)
            if coords:
                logger.info(f"Successfully geocoded {facility.get('name', 'Unknown')}: {coords}")
                return coords
            else:
                logger.warning(f"Failed to geocode {facility.get('name', 'Unknown')}: {full_address}")
                return None
            
        except Exception as e:
            logger.warning(f"Error geocoding address: {e}")
            return None
    
    def try_geocoding_services(self, address: str) -> Optional[Tuple[float, float]]:
        """Try multiple geocoding services to get coordinates."""
        import os
        
        # Try Google Maps API if available
        google_api_key = os.getenv('GOOGLE_MAPS_API_KEY')
        if google_api_key:
            coords = self.geocode_google(address, google_api_key)
            if coords:
                return coords
            time.sleep(0.1)  # Rate limiting
        
        # Try Nominatim (OpenStreetMap)
        coords = self.geocode_nominatim(address)
        if coords:
            return coords
        time.sleep(1)  # Rate limiting for free service
        
        # Try Photon (another free service)
        coords = self.geocode_photon(address)
        if coords:
            return coords
        
        return None
    
    def geocode_google(self, address: str, api_key: str) -> Optional[Tuple[float, float]]:
        """Geocode using Google Maps API."""
        try:
            import urllib.parse
            encoded_address = urllib.parse.quote(address)
            url = f"https://maps.googleapis.com/maps/api/geocode/json?address={encoded_address}&key={api_key}"
            
            response = self.session.get(url)
            response.raise_for_status()
            data = response.json()
            
            if data['status'] == 'OK' and data['results']:
                location = data['results'][0]['geometry']['location']
                return (location['lat'], location['lng'])
                
        except Exception as e:
            logger.debug(f"Google geocoding failed: {e}")
        
        return None
    
    def geocode_nominatim(self, address: str) -> Optional[Tuple[float, float]]:
        """Geocode using Nominatim (OpenStreetMap)."""
        try:
            import urllib.parse
            encoded_address = urllib.parse.quote(address)
            url = f"https://nominatim.openstreetmap.org/search?q={encoded_address}&format=json&limit=1"
            
            headers = {'User-Agent': 'Prison Data Scraper (educational research)'}
            response = self.session.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            
            if data:
                return (float(data[0]['lat']), float(data[0]['lon']))
                
        except Exception as e:
            logger.debug(f"Nominatim geocoding failed: {e}")
        
        return None
    
    def geocode_photon(self, address: str) -> Optional[Tuple[float, float]]:
        """Geocode using Photon API."""
        try:
            import urllib.parse
            encoded_address = urllib.parse.quote(address)
            url = f"https://photon.komoot.io/api/?q={encoded_address}&limit=1"
            
            response = self.session.get(url)
            response.raise_for_status()
            data = response.json()
            
            if data.get('features'):
                coords = data['features'][0]['geometry']['coordinates']
                return (coords[1], coords[0])  # Photon returns [lon, lat]
                
        except Exception as e:
            logger.debug(f"Photon geocoding failed: {e}")
        
        return None


def main():
    """Main function for testing the scraper."""
    scraper = VirginiaScraper()
    facilities = scraper.scrape_facilities()
    
    print(f"Found {len(facilities)} Virginia correctional facilities:")
    for facility in facilities[:10]:  # Show first 10
        print(f"- {facility['name']}")
        if facility.get('facility_type'):
            print(f"  Type: {facility['facility_type']}")
        if facility.get('street_address'):
            print(f"  Address: {facility['street_address']}")
        if facility.get('city'):
            print(f"  City: {facility['city']}, VA {facility.get('zip_code', '')}")
        if facility.get('phone'):
            print(f"  Phone: {facility['phone']}")
        if facility.get('latitude'):
            print(f"  Coordinates: {facility['latitude']}, {facility['longitude']}")
        print()

if __name__ == "__main__":
    main()
