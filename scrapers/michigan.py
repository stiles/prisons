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

class MichiganScraper:
    """Scraper for Michigan Department of Corrections facilities."""
    
    def __init__(self):
        self.base_url = "https://www.michigan.gov"
        self.prisons_url = "https://www.michigan.gov/corrections/prisons"
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
        Scrape all Michigan correctional facilities.
        
        Returns:
            List of facility dictionaries with details and coordinates
        """
        logger.info("Starting Michigan facilities scrape...")
        
        # Get facility list from directory page
        facility_urls = self.get_facility_urls()
        if not facility_urls:
            logger.error("Failed to get facility URLs")
            return []
        
        logger.info(f"Found {len(facility_urls)} facility URLs")
        
        # Scrape each facility
        facilities = []
        for i, (name, url) in enumerate(facility_urls, 1):
            try:
                logger.info(f"Scraping facility {i}/{len(facility_urls)}: {name}")
                facility_data = self.scrape_facility_details(name, url)
                if facility_data:
                    facilities.append(facility_data)
                
                # Rate limiting - be respectful
                time.sleep(0.5)
                
            except Exception as e:
                logger.error(f"Error scraping {name}: {e}")
                continue
        
        logger.info(f"Successfully processed {len(facilities)} facilities")
        return facilities
    
    def get_facility_urls(self) -> List[Tuple[str, str]]:
        """Get list of facility names and URLs from the directory page."""
        try:
            response = self.session.get(self.prisons_url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find all facility links
            facility_links = soup.find_all('a', href=True)
            prison_links = [link for link in facility_links if '/corrections/prisons/' in link.get('href', '')]
            
            # Deduplicate and clean up
            seen_urls = set()
            facilities = []
            
            for link in prison_links:
                href = link.get('href')
                if href.startswith('/'):
                    full_url = self.base_url + href
                else:
                    full_url = href
                
                # Skip if we've already seen this URL
                if full_url in seen_urls:
                    continue
                seen_urls.add(full_url)
                
                # Get facility name from link text
                name = link.get_text().strip()
                
                # Skip if name is too generic or empty
                if not name or len(name) < 3 or name.lower() in ['directions', 'bing maps']:
                    continue
                
                # Clean up facility name
                name = self.clean_facility_name(name)
                if name:
                    facilities.append((name, full_url))
            
            return facilities
            
        except Exception as e:
            logger.error(f"Error getting facility URLs: {e}")
            return []
    
    def clean_facility_name(self, name: str) -> Optional[str]:
        """Clean and standardize facility names."""
        # Remove common prefixes that aren't part of the facility name
        prefixes_to_remove = [
            'Administration building at ',
            'Administration Building of ',
            'Aerial view of ',
            'View of ',
        ]
        
        for prefix in prefixes_to_remove:
            if name.startswith(prefix):
                name = name[len(prefix):]
        
        # Skip if it's just a description
        if any(word in name.lower() for word in ['administration', 'aerial', 'view', 'building']):
            return None
        
        return name.strip()
    
    def scrape_facility_details(self, name: str, url: str) -> Optional[Dict]:
        """Scrape detailed information from individual facility page."""
        try:
            response = self.session.get(url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Initialize facility data
            facility = {
                'name': name,
                'state': 'Michigan',
                'agency': 'Michigan Department of Corrections (MDOC)',
                'facility_url': url
            }
            
            # Get all text content for parsing
            all_text = soup.get_text()
            
            # Find the facility information section (usually starts with county name)
            facility_section = self.extract_facility_section(all_text, name)
            if not facility_section:
                logger.warning(f"No facility section found for {name}")
                return facility
            
            # Extract county information
            county_match = re.search(r'([A-Za-z\s]+County)', facility_section)
            if county_match:
                county_name = county_match.group(1).strip()
                # Clean up county name
                if county_name and not any(word in county_name.lower() for word in ['prisons', 'correctional']):
                    facility['county'] = county_name
            
            # Extract warden information
            warden_patterns = [
                r'(?:Acting\s+)?Warden\s+([^\n]+)',
                r'(?:Acting\s+)?Superintendent\s+([^\n]+)'
            ]
            
            for pattern in warden_patterns:
                match = re.search(pattern, facility_section, re.IGNORECASE)
                if match:
                    warden_name = match.group(1).strip()
                    # Clean up common artifacts
                    warden_name = re.sub(r'\s+', ' ', warden_name)
                    facility['warden'] = warden_name
                    break
            
            # Extract address information
            address_info = self.extract_address_from_section(facility_section)
            facility.update(address_info)
            
            # Extract phone number
            phone_patterns = [
                r'Telephone:\s*(\d{3}-\d{3}-\d{4})',
                r'Phone:\s*(\d{3}-\d{3}-\d{4})',
                r'(\d{3}-\d{3}-\d{4})'
            ]
            
            for pattern in phone_patterns:
                match = re.search(pattern, facility_section)
                if match:
                    facility['phone'] = match.group(1)
                    break
            
            # Extract opening year
            opened_match = re.search(r'Open:\s*(\d{4})', facility_section)
            if opened_match:
                facility['opened'] = int(opened_match.group(1))
            
            # Extract gender and age information
            gender_match = re.search(r'Gender/Age Limit:\s*([^\n]+)', facility_section)
            if gender_match:
                gender_info = gender_match.group(1).strip()
                facility['gender_age_limit'] = gender_info
                
                # Parse gender
                if 'male' in gender_info.lower() and 'female' not in gender_info.lower():
                    facility['gender'] = 'Male'
                elif 'female' in gender_info.lower():
                    facility['gender'] = 'Female'
            
            # Extract security level
            security_match = re.search(r'Security Level:\s*([^\n]+)', facility_section)
            if security_match:
                facility['security_level'] = security_match.group(1).strip()
            
            # Extract capacity if available
            capacity_patterns = [
                r'capacity[:\s]+(\d+)',
                r'houses?\s+(?:up\s+to\s+)?(\d+)\s+(?:inmates?|prisoners?)',
                r'(\d+)[-\s]bed'
            ]
            
            for pattern in capacity_patterns:
                match = re.search(pattern, facility_section, re.IGNORECASE)
                if match:
                    facility['capacity'] = int(match.group(1))
                    break
            
            # Geocode the address if we have one
            if facility.get('street_address') and facility.get('city'):
                coords = self.geocode_address(facility)
                if coords:
                    facility['latitude'], facility['longitude'] = coords
            
            return facility
            
        except Exception as e:
            logger.error(f"Error scraping facility details for {name}: {e}")
            return None
    
    def extract_facility_section(self, all_text: str, facility_name: str) -> str:
        """Extract the facility information section from the full page text."""
        try:
            # Look for the section that contains facility details
            # Usually starts with county name and contains warden info
            
            # Find patterns that indicate the start of facility info
            patterns = [
                r'([A-Za-z\s]+County.*?)(?=General|Programming|Security|\Z)',
                r'((?:Acting\s+)?Warden\s+[^\n]+.*?)(?=General|Programming|Security|\Z)',
                r'(\w+\s+County.*?)(?=General|Programming|Security|\Z)'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, all_text, re.DOTALL | re.IGNORECASE)
                if match:
                    section = match.group(1).strip()
                    # Make sure this section contains relevant info
                    if any(keyword in section.lower() for keyword in ['warden', 'superintendent', 'county', 'drive', 'street', 'road']):
                        return section
            
            # Fallback: look for any section with address-like content
            lines = all_text.split('\n')
            facility_lines = []
            found_start = False
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Look for county or warden as start indicators
                if re.search(r'(?:county|warden|superintendent)', line, re.IGNORECASE):
                    found_start = True
                    facility_lines.append(line)
                elif found_start:
                    # Stop at section headers
                    if line.lower() in ['general', 'programming', 'security']:
                        break
                    facility_lines.append(line)
                    
                    # Stop if we have enough content
                    if len(facility_lines) > 10:
                        break
            
            return '\n'.join(facility_lines)
            
        except Exception as e:
            logger.warning(f"Error extracting facility section: {e}")
            return ""
    
    def extract_address_from_section(self, section_text: str) -> Dict:
        """Extract address information from facility section text."""
        address_info = {}
        
        try:
            lines = section_text.split('\n')
            
            for i, line in enumerate(lines):
                line = line.strip()
                
                # Look for street address patterns
                if re.search(r'\d+\s+[A-Za-z\s]+(?:Street|St|Avenue|Ave|Road|Rd|Drive|Dr|Boulevard|Blvd|Lane|Ln|Way|Court|Ct|Highway|Hwy|Park|Industrial)', line, re.IGNORECASE):
                    address_info['street_address'] = line
                    
                    # Check next line for city, state, zip
                    if i + 1 < len(lines):
                        next_line = lines[i + 1].strip()
                        city_match = re.match(r'([^,]+),\s*MI\s+(\d{5})', next_line)
                        if city_match:
                            address_info['city'] = city_match.group(1).strip()
                            address_info['zip_code'] = city_match.group(2)
                    break
                        
        except Exception as e:
            logger.warning(f"Error extracting address from section: {e}")
        
        return address_info
    
    def extract_address_info(self, container) -> Dict:
        """Extract address information from facility page container."""
        address_info = {}
        
        try:
            # Look for address patterns in the HTML
            html_content = str(container)
            text_content = container.get_text()
            
            # Find address block (usually after warden name)
            address_patterns = [
                r'(?:Acting\s+)?(?:Warden|Superintendent)\s+[^<\n]+<br>\s*([^<\n]+)<br>\s*([^<\n]+)<br>',
                r'<strong>[^<]*(?:Warden|Superintendent)[^<]*</strong><br>\s*([^<\n]+)<br>\s*([^<\n]+)<br>'
            ]
            
            for pattern in address_patterns:
                match = re.search(pattern, html_content, re.IGNORECASE | re.DOTALL)
                if match:
                    street_address = match.group(1).strip()
                    city_state_zip = match.group(2).strip()
                    
                    # Clean up street address
                    street_address = re.sub(r'<[^>]+>', '', street_address).strip()
                    city_state_zip = re.sub(r'<[^>]+>', '', city_state_zip).strip()
                    
                    if street_address and not any(word in street_address.lower() for word in ['warden', 'superintendent', 'acting']):
                        address_info['street_address'] = street_address
                    
                    # Parse city, state, zip
                    city_match = re.match(r'([^,]+),\s*MI\s+(\d{5})', city_state_zip)
                    if city_match:
                        address_info['city'] = city_match.group(1).strip()
                        address_info['zip_code'] = city_match.group(2)
                    
                    break
            
            # If no address found with the above patterns, try simpler approach
            if not address_info.get('street_address'):
                # Look for lines that look like addresses
                lines = text_content.split('\n')
                for i, line in enumerate(lines):
                    line = line.strip()
                    
                    # Skip warden lines
                    if any(word in line.lower() for word in ['warden', 'superintendent', 'acting']):
                        continue
                    
                    # Look for street address patterns
                    if re.search(r'\d+\s+[A-Za-z\s]+(?:Street|St|Avenue|Ave|Road|Rd|Drive|Dr|Boulevard|Blvd|Lane|Ln|Way|Court|Ct|Highway|Hwy|Park|Industrial)', line, re.IGNORECASE):
                        address_info['street_address'] = line
                        
                        # Check next line for city, state, zip
                        if i + 1 < len(lines):
                            next_line = lines[i + 1].strip()
                            city_match = re.match(r'([^,]+),\s*MI\s+(\d{5})', next_line)
                            if city_match:
                                address_info['city'] = city_match.group(1).strip()
                                address_info['zip_code'] = city_match.group(2)
                        break
                        
        except Exception as e:
            logger.warning(f"Error extracting address info: {e}")
        
        return address_info
    
    def geocode_address(self, facility: Dict) -> Optional[Tuple[float, float]]:
        """Geocode facility address to get coordinates."""
        try:
            # Build full address
            address_parts = []
            
            if facility.get('street_address'):
                address_parts.append(facility['street_address'])
            
            if facility.get('city'):
                address_parts.append(f"{facility['city']}, MI")
            
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
    scraper = MichiganScraper()
    facilities = scraper.scrape_facilities()
    
    print(f"Found {len(facilities)} Michigan correctional facilities:")
    for facility in facilities[:5]:  # Show first 5
        print(f"- {facility['name']}")
        if facility.get('county'):
            print(f"  County: {facility['county']}")
        if facility.get('warden'):
            print(f"  Warden: {facility['warden']}")
        if facility.get('street_address'):
            print(f"  Address: {facility['street_address']}")
        if facility.get('city'):
            print(f"  City: {facility['city']}, MI {facility.get('zip_code', '')}")
        if facility.get('security_level'):
            print(f"  Security: {facility['security_level']}")
        print()

if __name__ == "__main__":
    main()
