#!/usr/bin/env python3

import requests
import csv
import re
from bs4 import BeautifulSoup
from typing import Dict, List, Optional, Tuple
import logging
import io

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NorthCarolinaScraper:
    """Scraper for North Carolina Department of Adult Correction facilities."""
    
    def __init__(self):
        self.base_url = "https://www.dac.nc.gov"
        self.csv_url = "https://www.dac.nc.gov/tablefield/export/paragraph/5189/field_map_data/en/0"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # Color code to facility type mapping based on legend
        self.color_types = {
            'Deep Purple': 'State Prison (Close/Medium/Minimum Security)',
            'Light Purple': 'State Prison (Medium Security)', 
            'Light Blue': 'Correctional Center (Minimum/Reentry)',
            'Blue': 'State Prison (Close Security)'
        }
    
    def scrape_facilities(self) -> List[Dict]:
        """
        Scrape all North Carolina correctional facilities.
        
        Returns:
            List of facility dictionaries with details and coordinates
        """
        logger.info("Starting North Carolina facilities scrape...")
        
        # Get CSV data
        csv_data = self.fetch_csv_data()
        if not csv_data:
            logger.error("Failed to fetch CSV data")
            return []
        
        # Parse facilities from CSV
        facilities = self.parse_csv_facilities(csv_data)
        logger.info(f"Found {len(facilities)} facilities in CSV")
        
        # Enhance with individual page data
        enhanced_facilities = []
        for facility in facilities:
            enhanced = self.enhance_facility_data(facility)
            if enhanced:
                enhanced_facilities.append(enhanced)
        
        logger.info(f"Successfully processed {len(enhanced_facilities)} facilities")
        return enhanced_facilities
    
    def fetch_csv_data(self) -> Optional[str]:
        """Fetch the CSV data from North Carolina's export endpoint."""
        try:
            response = self.session.get(self.csv_url)
            response.raise_for_status()
            return response.text
        except Exception as e:
            logger.error(f"Error fetching CSV data: {e}")
            return None
    
    def parse_csv_facilities(self, csv_content: str) -> List[Dict]:
        """Parse facility data from the CSV content."""
        facilities = []
        
        try:
            # Parse CSV
            csv_reader = csv.reader(io.StringIO(csv_content))
            header = next(csv_reader)  # Skip header row
            
            for row in csv_reader:
                if len(row) < 5:
                    continue
                
                row_id, county, title_html, url_path, color = row
                
                # Skip empty rows (counties without facilities)
                if not title_html.strip() or not url_path.strip():
                    continue
                
                # Parse facilities from HTML content
                facility_data = self.parse_facility_html(title_html, county, url_path, color)
                facilities.extend(facility_data)
                
        except Exception as e:
            logger.error(f"Error parsing CSV: {e}")
        
        return facilities
    
    def parse_facility_html(self, html_content: str, county: str, url_path: str, color: str) -> List[Dict]:
        """Parse facility information from HTML content in CSV."""
        facilities = []
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Replace all <br> tags with newlines first
            for br in soup.find_all('br'):
                br.replace_with('\n')
            
            # Get all text content from the entire HTML
            full_html_text = soup.get_text()
            
            # Find all facility entries (marked by <strong> tags)
            facility_blocks = soup.find_all('strong')
            
            for block in facility_blocks:
                facility_name = block.get_text().strip()
                if not facility_name:
                    continue
                
                # For each facility, extract the text that follows it
                # Split the full text and find the section for this facility
                facility_section = self.extract_facility_section(full_html_text, facility_name)
                
                if facility_section:
                    lines = [line.strip() for line in facility_section.split('\n') if line.strip()]
                    
                    # Parse facility details
                    facility_info = self.parse_facility_details(facility_name, lines, county, url_path, color)
                    if facility_info:
                        facilities.append(facility_info)
        
        except Exception as e:
            logger.error(f"Error parsing facility HTML: {e}")
        
        return facilities
    
    def extract_facility_section(self, full_text: str, facility_name: str) -> str:
        """Extract the text section for a specific facility."""
        try:
            # Find the facility name in the text
            start_pos = full_text.find(facility_name)
            if start_pos == -1:
                return ""
            
            # Find the end of this facility's section (next facility name or end of text)
            # Look for the next facility name (another line starting with capital letters)
            lines = full_text[start_pos:].split('\n')
            facility_lines = [lines[0]]  # Include the facility name line
            
            for i, line in enumerate(lines[1:], 1):
                line = line.strip()
                if not line:
                    continue
                
                # Stop if we hit another facility name (starts with capital and doesn't look like address/info)
                if (line[0].isupper() and 
                    'correctional' in line.lower() and 
                    line != facility_name and
                    not any(keyword in line.lower() for keyword in ['custody', 'male', 'female', 'rd', 'street', 'ave', 'drive'])):
                    break
                
                facility_lines.append(line)
            
            return '\n'.join(facility_lines)
            
        except Exception as e:
            logger.warning(f"Error extracting facility section for {facility_name}: {e}")
            return ""
    
    def parse_facility_details(self, name: str, lines: List[str], county: str, url_path: str, color: str) -> Optional[Dict]:
        """Parse individual facility details from text lines."""
        try:
            facility = {
                'name': name,
                'county': county,
                'state': 'North Carolina',
                'agency': 'North Carolina Department of Adult Correction (DAC)',
                'facility_type': self.color_types.get(color, 'Unknown'),
                'color_code': color,
                'facility_url': self.base_url + url_path if url_path.startswith('/') else url_path
            }
            
            # Join all lines to get full text for better parsing
            full_text = ' '.join(lines)
            
            # Parse custody level and gender from the lines
            for line in lines:
                line_lower = line.lower()
                
                # Extract custody levels
                if any(keyword in line_lower for keyword in ['close', 'medium', 'minimum', 'custody']):
                    facility['custody_level'] = line
                
                # Extract gender
                if 'male' in line_lower and 'female' not in line_lower:
                    facility['gender'] = 'Male'
                elif 'female' in line_lower:
                    facility['gender'] = 'Female'
                
                # Extract reentry facility designation
                if 'reentry' in line_lower:
                    facility['reentry_facility'] = True
            
            # Extract address using regex patterns on full text
            # Look for street address patterns
            address_patterns = [
                r'(\d+\s+[A-Za-z\s]+(?:Rd|Road|St|Street|Ave|Avenue|Dr|Drive|Blvd|Boulevard|Ln|Lane|Way|Ct|Court|Hwy|Highway)\.?)',
                r'(\d+\s+[A-Za-z\s]+\d+)',  # Highway numbers
            ]
            
            for pattern in address_patterns:
                match = re.search(pattern, full_text, re.IGNORECASE)
                if match:
                    facility['street_address'] = match.group(1).strip()
                    break
            
            # Extract city, state, zip (NC + 5-digit zip pattern)
            city_state_zip_match = re.search(r'([A-Za-z\s]+),?\s*NC\s+(\d{5})', full_text)
            if city_state_zip_match:
                facility['city'] = city_state_zip_match.group(1).strip().rstrip(',')
                facility['zip_code'] = city_state_zip_match.group(2)
            
            return facility
            
        except Exception as e:
            logger.error(f"Error parsing facility details for {name}: {e}")
            return None
    
    def is_address_line(self, line: str) -> bool:
        """Determine if a line contains a street address."""
        address_indicators = [
            r'\d+\s+\w+.*(?:rd|road|st|street|ave|avenue|dr|drive|blvd|boulevard|ln|lane|way|ct|court|hwy|highway)',
            r'\d+\s+[A-Z][a-z]+.*\d+',  # Number + words + number (like highway numbers)
            r'\d+\s+\w+\s+\w+.*rd\.',   # Specific patterns like "Old Landfill Rd."
        ]
        
        for pattern in address_indicators:
            if re.search(pattern, line, re.IGNORECASE):
                return True
        return False
    
    def enhance_facility_data(self, facility: Dict) -> Optional[Dict]:
        """Enhance facility data by scraping individual facility pages."""
        try:
            facility_url = facility.get('facility_url')
            if not facility_url:
                return facility
            
            # Skip if URL looks incomplete or invalid
            if not facility_url.startswith('http'):
                return facility
            
            response = self.session.get(facility_url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract additional details from facility page
            enhanced_data = self.extract_facility_page_data(soup)
            facility.update(enhanced_data)
            
            # Geocode the address if we have one
            if facility.get('street_address') and facility.get('city'):
                coords = self.geocode_address(facility)
                if coords:
                    facility['latitude'], facility['longitude'] = coords
            
            return facility
            
        except Exception as e:
            logger.warning(f"Error enhancing facility {facility.get('name', 'Unknown')}: {e}")
            return facility
    
    def extract_facility_page_data(self, soup: BeautifulSoup) -> Dict:
        """Extract additional data from individual facility pages."""
        data = {}
        
        try:
            # Look for warden information
            warden_patterns = [
                r'warden[:\s]*([^<\n]+)',
                r'superintendent[:\s]*([^<\n]+)'
            ]
            
            page_text = soup.get_text()
            for pattern in warden_patterns:
                match = re.search(pattern, page_text, re.IGNORECASE)
                if match:
                    data['warden'] = match.group(1).strip()
                    break
            
            # Look for capacity information
            capacity_patterns = [
                r'capacity[:\s]*(\d+)',
                r'houses?\s+(\d+)',
                r'(\d+)\s*(?:bed|cell|offender)'
            ]
            
            for pattern in capacity_patterns:
                match = re.search(pattern, page_text, re.IGNORECASE)
                if match:
                    data['capacity'] = int(match.group(1))
                    break
            
            # Look for phone numbers
            phone_match = re.search(r'phone[:\s]*(\(\d{3}\)\s*\d{3}-\d{4}|\d{3}-\d{3}-\d{4})', page_text, re.IGNORECASE)
            if phone_match:
                data['phone'] = phone_match.group(1)
            
            # Extract address from structured data if not already found
            address_section = soup.find('p', string=re.compile(r'Address:', re.IGNORECASE))
            if address_section:
                address_text = address_section.get_text()
                address_match = re.search(r'Address:\s*([^P]+?)(?:Phone|$)', address_text, re.IGNORECASE)
                if address_match:
                    full_address = address_match.group(1).strip()
                    # Parse street, city, state, zip
                    lines = [line.strip() for line in full_address.split('\n') if line.strip()]
                    if lines:
                        data['parsed_street_address'] = lines[0]
                        if len(lines) > 1:
                            city_state_zip = lines[1]
                            city_match = re.search(r'([^,]+),?\s*NC\s+(\d{5})', city_state_zip)
                            if city_match:
                                data['parsed_city'] = city_match.group(1).strip()
                                data['parsed_zip_code'] = city_match.group(2)
            
        except Exception as e:
            logger.warning(f"Error extracting page data: {e}")
        
        return data
    
    def geocode_address(self, facility: Dict) -> Optional[Tuple[float, float]]:
        """Geocode facility address to get coordinates."""
        try:
            # Build full address
            address_parts = []
            
            if facility.get('street_address'):
                address_parts.append(facility['street_address'])
            elif facility.get('parsed_street_address'):
                address_parts.append(facility['parsed_street_address'])
            
            city = facility.get('city') or facility.get('parsed_city')
            zip_code = facility.get('zip_code') or facility.get('parsed_zip_code')
            
            if city:
                address_parts.append(f"{city}, NC")
            if zip_code:
                address_parts.append(zip_code)
            
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
        import time
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
    scraper = NorthCarolinaScraper()
    facilities = scraper.scrape_facilities()
    
    print(f"Found {len(facilities)} North Carolina correctional facilities:")
    for facility in facilities[:5]:  # Show first 5
        print(f"- {facility['name']}")
        print(f"  County: {facility.get('county', 'Unknown')}")
        print(f"  Type: {facility.get('facility_type', 'Unknown')}")
        if facility.get('street_address'):
            print(f"  Address: {facility['street_address']}")
        if facility.get('city'):
            print(f"  City: {facility['city']}, NC {facility.get('zip_code', '')}")
        print()

if __name__ == "__main__":
    main()
