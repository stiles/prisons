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

class WashingtonScraper:
    """Scraper for Washington Department of Corrections facilities."""
    
    def __init__(self):
        self.base_url = "https://doc.wa.gov"
        self.facilities_url = "https://doc.wa.gov/about-doc/locations/prison-facilities/prisons-map"
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
        Scrape all Washington correctional facilities.
        
        Returns:
            List of facility dictionaries with details and coordinates
        """
        logger.info("Starting Washington facilities scrape...")
        
        # Get facility data from the map page
        facilities = self.get_facilities_from_map_page()
        
        if not facilities:
            logger.error("Failed to get facility data from map page")
            return []
        
        logger.info(f"Found {len(facilities)} facilities from map page")
        
        # Enhance facilities with additional data from table and individual pages
        enhanced_facilities = []
        for i, facility in enumerate(facilities, 1):
            try:
                logger.info(f"Processing facility {i}/{len(facilities)}: {facility['name']}")
                
                # Enhance with individual page data if available
                if facility.get('detail_url'):
                    enhanced_data = self.get_facility_details(facility['detail_url'])
                    facility.update(enhanced_data)
                
                enhanced_facilities.append(facility)
                
                # Rate limiting - be respectful
                time.sleep(0.3)
                
            except Exception as e:
                logger.error(f"Error processing {facility.get('name', 'Unknown')}: {e}")
                enhanced_facilities.append(facility)  # Add anyway
                continue
        
        logger.info(f"Successfully processed {len(enhanced_facilities)} facilities")
        return enhanced_facilities
    
    def get_facilities_from_map_page(self) -> List[Dict]:
        """Extract facility information from the map page with embedded coordinates."""
        try:
            response = self.session.get(self.facilities_url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            facilities = []
            
            # Find all geolocation elements with facility data
            geolocation_elements = soup.find_all('div', class_='geolocation-location')
            
            for element in geolocation_elements:
                facility_data = self.parse_geolocation_element(element)
                if facility_data:
                    facilities.append(facility_data)
            
            # Also extract facilities from the table if available
            table_facilities = self.extract_table_facilities(soup)
            
            # Merge data from both sources
            facilities = self.merge_facility_data(facilities, table_facilities)
            
            return facilities
            
        except Exception as e:
            logger.error(f"Error getting facilities from map page: {e}")
            return []
    
    def parse_geolocation_element(self, element) -> Optional[Dict]:
        """Parse a geolocation element to extract facility data."""
        try:
            facility = {
                'state': 'Washington',
                'agency': 'Washington Department of Corrections (WADOC)'
            }
            
            # Extract coordinates from data attributes
            lat = element.get('data-lat')
            lng = element.get('data-lng')
            if lat and lng:
                facility['latitude'] = float(lat)
                facility['longitude'] = float(lng)
            
            # Extract facility name
            title_element = element.find('h2', class_='location-title')
            if title_element:
                facility['name'] = title_element.get_text().strip()
            
            # Extract address information
            address_element = element.find('p', class_='address')
            if address_element:
                address_info = self.parse_address_element(address_element)
                facility.update(address_info)
            
            # Extract phone number
            phone_element = element.find('a', href=lambda x: x and x.startswith('tel:'))
            if phone_element:
                phone_text = phone_element.get_text().strip()
                facility['phone'] = phone_text
            
            # Extract detail page URL
            more_info_link = element.find('a', string='More Info')
            if more_info_link:
                detail_url = more_info_link.get('href')
                if detail_url:
                    if detail_url.startswith('/'):
                        detail_url = self.base_url + detail_url
                    facility['detail_url'] = detail_url
            
            # Determine facility type
            facility['facility_type'] = self.determine_facility_type(facility.get('name', ''))
            
            return facility
            
        except Exception as e:
            logger.warning(f"Error parsing geolocation element: {e}")
            return None
    
    def parse_address_element(self, address_element) -> Dict:
        """Parse address information from an address element."""
        address_info = {}
        
        try:
            # Extract street address
            street_element = address_element.find('span', class_='address-line1')
            if street_element:
                address_info['street_address'] = street_element.get_text().strip()
            
            # Extract city
            city_element = address_element.find('span', class_='locality')
            if city_element:
                address_info['city'] = city_element.get_text().strip()
            
            # Extract zip code
            zip_element = address_element.find('span', class_='postal-code')
            if zip_element:
                address_info['zip_code'] = zip_element.get_text().strip()
                
        except Exception as e:
            logger.warning(f"Error parsing address element: {e}")
        
        return address_info
    
    def extract_table_facilities(self, soup: BeautifulSoup) -> List[Dict]:
        """Extract facility data from the table on the page."""
        table_facilities = []
        
        try:
            # Find the facilities table
            table = soup.find('table', class_='footable')
            if not table:
                return table_facilities
            
            rows = table.find('tbody').find_all('tr') if table.find('tbody') else []
            
            for row in rows:
                cells = row.find_all('td')
                if len(cells) >= 3:
                    facility = {
                        'state': 'Washington',
                        'agency': 'Washington Department of Corrections (WADOC)'
                    }
                    
                    # Extract name from second cell
                    name_cell = cells[1]
                    facility['name'] = name_cell.get_text().strip()
                    
                    # Extract address and phone from third cell
                    contact_cell = cells[2]
                    contact_info = self.parse_contact_cell(contact_cell)
                    facility.update(contact_info)
                    
                    # Extract detail URL from fourth cell if available
                    if len(cells) >= 4:
                        detail_cell = cells[3]
                        detail_link = detail_cell.find('a')
                        if detail_link:
                            detail_url = detail_link.get('href')
                            if detail_url and detail_url.startswith('/'):
                                detail_url = self.base_url + detail_url
                            facility['detail_url'] = detail_url
                    
                    # Determine facility type
                    facility['facility_type'] = self.determine_facility_type(facility['name'])
                    
                    table_facilities.append(facility)
                    
        except Exception as e:
            logger.warning(f"Error extracting table facilities: {e}")
        
        return table_facilities
    
    def parse_contact_cell(self, contact_cell) -> Dict:
        """Parse contact information from a table cell."""
        contact_info = {}
        
        try:
            # Extract address
            address_element = contact_cell.find('p', class_='address')
            if address_element:
                address_info = self.parse_address_element(address_element)
                contact_info.update(address_info)
            
            # Extract phone
            phone_element = contact_cell.find('a', href=lambda x: x and x.startswith('tel:'))
            if phone_element:
                contact_info['phone'] = phone_element.get_text().strip()
                
        except Exception as e:
            logger.warning(f"Error parsing contact cell: {e}")
        
        return contact_info
    
    def merge_facility_data(self, map_facilities: List[Dict], table_facilities: List[Dict]) -> List[Dict]:
        """Merge facility data from map and table sources."""
        # Create a lookup for table facilities by name
        table_lookup = {}
        for facility in table_facilities:
            name = self.normalize_facility_name(facility['name'])
            table_lookup[name] = facility
        
        # Merge map facilities with table data
        merged_facilities = []
        seen_names = set()
        
        for map_facility in map_facilities:
            name = self.normalize_facility_name(map_facility['name'])
            seen_names.add(name)
            
            # Merge with table data if available
            if name in table_lookup:
                table_data = table_lookup[name]
                # Map data takes precedence for coordinates
                merged = {**table_data, **map_facility}
                merged_facilities.append(merged)
            else:
                merged_facilities.append(map_facility)
        
        # Add any table facilities not found in map data
        for table_facility in table_facilities:
            name = self.normalize_facility_name(table_facility['name'])
            if name not in seen_names:
                merged_facilities.append(table_facility)
        
        return merged_facilities
    
    def normalize_facility_name(self, name: str) -> str:
        """Normalize facility name for comparison."""
        # Remove common abbreviations and normalize
        normalized = re.sub(r'\s*\([^)]*\)\s*', '', name)  # Remove parenthetical abbreviations
        normalized = re.sub(r'[^\w\s]', '', normalized.lower()).strip()
        return normalized
    
    def determine_facility_type(self, name: str) -> str:
        """Determine facility type based on name."""
        name_lower = name.lower()
        
        if 'penitentiary' in name_lower:
            return 'State Penitentiary'
        elif 'corrections center' in name_lower:
            return 'Corrections Center'
        elif 'correctional complex' in name_lower:
            return 'Correctional Complex'
        elif 'reentry center' in name_lower:
            return 'Reentry Center'
        elif 'justice center' in name_lower:
            return 'Justice Center'
        elif 'for women' in name_lower:
            return 'Women\'s Facility'
        else:
            return 'Correctional Facility'
    
    def get_facility_details(self, detail_url: str) -> Dict:
        """Get additional facility details from individual facility page."""
        details = {}
        
        try:
            response = self.session.get(detail_url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for "At a Glance" section with facility details
            glance_section = soup.find('div', class_='field--name-field-at-a-glance')
            if glance_section:
                glance_details = self.parse_at_a_glance_section(glance_section)
                details.update(glance_details)
            
            # Look for other structured data
            # Extract capacity information
            capacity_match = re.search(r'Capacity:\s*(\d+)', soup.get_text(), re.IGNORECASE)
            if capacity_match:
                details['capacity'] = int(capacity_match.group(1))
            
            # Extract custody level
            custody_match = re.search(r'Custody Level:\s*([^\n\r]+)', soup.get_text(), re.IGNORECASE)
            if custody_match:
                details['custody_level'] = custody_match.group(1).strip()
            
            # Extract year opened
            year_match = re.search(r'Year Opened:\s*(\d{4})', soup.get_text(), re.IGNORECASE)
            if year_match:
                details['year_opened'] = int(year_match.group(1))
            
            # Extract gender information
            text_content = soup.get_text().lower()
            if 'male inmates' in text_content:
                details['gender'] = 'Male'
            elif 'female inmates' in text_content or 'women' in text_content:
                details['gender'] = 'Female'
            
        except Exception as e:
            logger.warning(f"Error getting facility details from {detail_url}: {e}")
        
        return details
    
    def parse_at_a_glance_section(self, section) -> Dict:
        """Parse the 'At a Glance' section for facility details."""
        details = {}
        
        try:
            text_content = section.get_text()
            
            # Extract capacity
            capacity_match = re.search(r'Capacity:\s*(\d+)', text_content, re.IGNORECASE)
            if capacity_match:
                details['capacity'] = int(capacity_match.group(1))
            
            # Extract custody level
            custody_match = re.search(r'Custody Level:\s*([^\n\r]+)', text_content, re.IGNORECASE)
            if custody_match:
                details['custody_level'] = custody_match.group(1).strip()
            
            # Extract year opened
            year_match = re.search(r'Year Opened:\s*(\d{4})', text_content, re.IGNORECASE)
            if year_match:
                details['year_opened'] = int(year_match.group(1))
            
            # Extract gender information
            if 'male inmates' in text_content.lower():
                details['gender'] = 'Male'
            elif 'female inmates' in text_content.lower():
                details['gender'] = 'Female'
                
        except Exception as e:
            logger.warning(f"Error parsing at-a-glance section: {e}")
        
        return details


def main():
    """Main function for testing the scraper."""
    scraper = WashingtonScraper()
    facilities = scraper.scrape_facilities()
    
    print(f"Found {len(facilities)} Washington correctional facilities:")
    for facility in facilities[:10]:  # Show first 10
        print(f"- {facility['name']}")
        if facility.get('facility_type'):
            print(f"  Type: {facility['facility_type']}")
        if facility.get('street_address'):
            print(f"  Address: {facility['street_address']}")
        if facility.get('city'):
            print(f"  City: {facility['city']}, WA {facility.get('zip_code', '')}")
        if facility.get('phone'):
            print(f"  Phone: {facility['phone']}")
        if facility.get('capacity'):
            print(f"  Capacity: {facility['capacity']}")
        if facility.get('custody_level'):
            print(f"  Custody Level: {facility['custody_level']}")
        if facility.get('latitude'):
            print(f"  Coordinates: {facility['latitude']}, {facility['longitude']}")
        print()

if __name__ == "__main__":
    main()
