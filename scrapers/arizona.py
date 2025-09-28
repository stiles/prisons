#!/usr/bin/env python3

import requests
import re
import json
from bs4 import BeautifulSoup
from typing import Dict, List, Optional, Tuple
import logging
import time

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ArizonaScraper:
    """Scraper for Arizona Department of Corrections facilities."""
    
    def __init__(self):
        self.base_url = "https://corrections.az.gov"
        self.facilities_url = "https://corrections.az.gov/adcrr-prisons"
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
        Scrape all Arizona correctional facilities.
        
        Returns:
            List of facility dictionaries with details and coordinates
        """
        logger.info("Starting Arizona facilities scrape...")
        
        # Get facility data from the embedded JSON
        facilities = self.get_facilities_from_json()
        
        if not facilities:
            logger.error("Failed to get facility data from embedded JSON")
            return []
        
        logger.info(f"Found {len(facilities)} facilities from embedded JSON")
        
        # Enhance facilities with additional data from individual pages
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
    
    def get_facilities_from_json(self) -> List[Dict]:
        """Extract facility information from the embedded JSON data."""
        try:
            response = self.session.get(self.facilities_url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find the script tag with drupal-settings-json
            script_tag = soup.find('script', {'data-drupal-selector': 'drupal-settings-json'})
            if not script_tag:
                logger.error("Could not find drupal-settings-json script tag")
                return []
            
            # Parse the JSON data
            json_data = json.loads(script_tag.string)
            
            # Navigate to the leaflet map features
            leaflet_data = json_data.get('leaflet', {})
            map_key = None
            for key in leaflet_data.keys():
                if key.startswith('leaflet-map-view-facility-map'):
                    map_key = key
                    break
            
            if not map_key:
                logger.error("Could not find leaflet map data")
                return []
            
            features = leaflet_data[map_key].get('features', [])
            logger.info(f"Found {len(features)} features in JSON data")
            
            facilities = []
            for feature in features:
                facility_data = self.parse_json_feature(feature)
                if facility_data:
                    facilities.append(facility_data)
            
            return facilities
            
        except Exception as e:
            logger.error(f"Error getting facilities from JSON: {e}")
            return []
    
    def parse_json_feature(self, feature: Dict) -> Optional[Dict]:
        """Parse a JSON feature to extract facility data."""
        try:
            facility = {
                'state': 'Arizona',
                'agency': 'Arizona Department of Corrections (ADOC)'
            }
            
            # Extract coordinates
            lat = feature.get('lat')
            lng = feature.get('lon')
            if lat and lng:
                facility['latitude'] = float(lat)
                facility['longitude'] = float(lng)
            
            # Extract entity ID
            entity_id = feature.get('entity_id')
            if entity_id:
                facility['entity_id'] = entity_id
            
            # Parse the popup content for detailed information
            popup_html = feature.get('popup', '')
            if popup_html:
                popup_data = self.parse_popup_content(popup_html)
                facility.update(popup_data)
            
            # Parse the label for facility name (fallback)
            label_html = feature.get('label', '')
            if label_html and not facility.get('name'):
                label_soup = BeautifulSoup(label_html, 'html.parser')
                link = label_soup.find('a')
                if link:
                    facility['name'] = link.get_text().strip()
                    # Extract detail URL
                    href = link.get('href')
                    if href and href.startswith('/'):
                        facility['detail_url'] = self.base_url + href
            
            # Determine facility type
            if facility.get('name'):
                facility['facility_type'] = self.determine_facility_type(facility['name'])
            
            return facility
            
        except Exception as e:
            logger.warning(f"Error parsing JSON feature: {e}")
            return None
    
    def parse_popup_content(self, popup_html: str) -> Dict:
        """Parse popup HTML content to extract facility information."""
        popup_data = {}
        
        try:
            soup = BeautifulSoup(popup_html, 'html.parser')
            
            # Extract facility name from title
            title_element = soup.find('h5', class_='field-content')
            if title_element:
                title_link = title_element.find('a')
                if title_link:
                    popup_data['name'] = title_link.get_text().strip()
                    # Extract detail URL
                    href = title_link.get('href')
                    if href and href.startswith('/'):
                        popup_data['detail_url'] = self.base_url + href
            
            # Extract address information
            address_element = soup.find('p', class_='address')
            if address_element:
                address_info = self.parse_address_element(address_element)
                popup_data.update(address_info)
            
        except Exception as e:
            logger.warning(f"Error parsing popup content: {e}")
        
        return popup_data
    
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
    
    def determine_facility_type(self, name: str) -> str:
        """Determine facility type based on name."""
        name_lower = name.lower()
        
        if 'correctional center' in name_lower:
            return 'Correctional Center'
        elif 'complex' in name_lower:
            return 'Prison Complex'
        elif 'facility' in name_lower:
            return 'Correctional Facility'
        else:
            return 'Prison Complex'  # Default for Arizona
    
    def get_facility_details(self, detail_url: str) -> Dict:
        """Get additional facility details from individual facility page."""
        details = {}
        
        try:
            response = self.session.get(detail_url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract warden information
            warden_info = self.extract_warden_info(soup)
            details.update(warden_info)
            
            # Extract capacity information
            capacity_info = self.extract_capacity_info(soup)
            details.update(capacity_info)
            
            # Extract mailing address if different from physical
            mailing_info = self.extract_mailing_address(soup)
            details.update(mailing_info)
            
            # Extract facility overview/description
            overview_info = self.extract_overview_info(soup)
            details.update(overview_info)
            
            # Extract unit information
            units_info = self.extract_units_info(soup)
            details.update(units_info)
            
        except Exception as e:
            logger.warning(f"Error getting facility details from {detail_url}: {e}")
        
        return details
    
    def extract_warden_info(self, soup: BeautifulSoup) -> Dict:
        """Extract warden information from facility page."""
        warden_info = {}
        
        try:
            # Look for warden profile section
            warden_section = soup.find('div', class_='field--name-field-warden-profile')
            if warden_section:
                # Extract warden name from heading
                warden_heading = warden_section.find('h4')
                if warden_heading:
                    warden_text = warden_heading.get_text().strip()
                    # Extract name after "Warden "
                    warden_match = re.search(r'Warden\s+(.+)', warden_text)
                    if warden_match:
                        warden_info['warden'] = warden_match.group(1).strip()
                
                # Extract warden contact info
                contact_text = warden_section.get_text()
                
                # Extract phone
                phone_match = re.search(r'\((\d{3})\)\s*(\d{3})-(\d{4})', contact_text)
                if phone_match:
                    warden_info['warden_phone'] = f"({phone_match.group(1)}) {phone_match.group(2)}-{phone_match.group(3)}"
                
                # Extract email
                email_match = re.search(r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', contact_text)
                if email_match:
                    warden_info['warden_email'] = email_match.group(1)
                    
        except Exception as e:
            logger.warning(f"Error extracting warden info: {e}")
        
        return warden_info
    
    def extract_capacity_info(self, soup: BeautifulSoup) -> Dict:
        """Extract capacity information from facility page."""
        capacity_info = {}
        
        try:
            # Look for capacity in overview section
            overview_section = soup.find('div', class_='field--name-body')
            if overview_section:
                overview_text = overview_section.get_text()
                
                # Extract capacity
                capacity_match = re.search(r'capacity to house\s+([0-9,]+)', overview_text, re.IGNORECASE)
                if capacity_match:
                    capacity_str = capacity_match.group(1).replace(',', '')
                    capacity_info['capacity'] = int(capacity_str)
                
                # Extract security levels
                if 'maximum security' in overview_text.lower():
                    capacity_info['security_level'] = 'Maximum'
                elif 'high custody' in overview_text.lower():
                    capacity_info['security_level'] = 'High'
                elif 'medium' in overview_text.lower():
                    capacity_info['security_level'] = 'Medium'
                elif 'minimum' in overview_text.lower():
                    capacity_info['security_level'] = 'Minimum'
                    
        except Exception as e:
            logger.warning(f"Error extracting capacity info: {e}")
        
        return capacity_info
    
    def extract_mailing_address(self, soup: BeautifulSoup) -> Dict:
        """Extract mailing address information."""
        mailing_info = {}
        
        try:
            # Look for mailing address section
            mailing_section = soup.find('div', class_='field--name-field-mailing-address')
            if mailing_section:
                address_element = mailing_section.find('p', class_='address')
                if address_element:
                    # Extract mailing address components
                    street_element = address_element.find('span', class_='address-line1')
                    if street_element:
                        mailing_info['mailing_address'] = street_element.get_text().strip()
                    
                    city_element = address_element.find('span', class_='locality')
                    zip_element = address_element.find('span', class_='postal-code')
                    if city_element and zip_element:
                        mailing_info['mailing_city_zip'] = f"{city_element.get_text().strip()}, AZ {zip_element.get_text().strip()}"
                        
        except Exception as e:
            logger.warning(f"Error extracting mailing address: {e}")
        
        return mailing_info
    
    def extract_overview_info(self, soup: BeautifulSoup) -> Dict:
        """Extract overview/description information."""
        overview_info = {}
        
        try:
            # Look for overview section
            overview_section = soup.find('div', class_='field--name-body')
            if overview_section:
                # Extract first paragraph as description
                first_paragraph = overview_section.find('p')
                if first_paragraph:
                    description = first_paragraph.get_text().strip()
                    if len(description) > 50:  # Only if substantial
                        overview_info['description'] = description
                        
        except Exception as e:
            logger.warning(f"Error extracting overview info: {e}")
        
        return overview_info
    
    def extract_units_info(self, soup: BeautifulSoup) -> Dict:
        """Extract information about facility units."""
        units_info = {}
        
        try:
            # Look for units section
            units_section = soup.find('div', class_='field--name-field-units')
            if units_section:
                # Count units
                unit_elements = units_section.find_all('div', class_='field--name-field-title')
                if unit_elements:
                    unit_names = []
                    for unit_element in unit_elements:
                        unit_name = unit_element.get_text().strip()
                        if unit_name:
                            unit_names.append(unit_name)
                    
                    if unit_names:
                        units_info['units'] = unit_names
                        units_info['unit_count'] = len(unit_names)
                        
        except Exception as e:
            logger.warning(f"Error extracting units info: {e}")
        
        return units_info


def main():
    """Main function for testing the scraper."""
    scraper = ArizonaScraper()
    facilities = scraper.scrape_facilities()
    
    print(f"Found {len(facilities)} Arizona correctional facilities:")
    for facility in facilities[:10]:  # Show first 10
        print(f"- {facility['name']}")
        if facility.get('facility_type'):
            print(f"  Type: {facility['facility_type']}")
        if facility.get('street_address'):
            print(f"  Address: {facility['street_address']}")
        if facility.get('city'):
            print(f"  City: {facility['city']}, AZ {facility.get('zip_code', '')}")
        if facility.get('warden'):
            print(f"  Warden: {facility['warden']}")
        if facility.get('capacity'):
            print(f"  Capacity: {facility['capacity']}")
        if facility.get('security_level'):
            print(f"  Security Level: {facility['security_level']}")
        if facility.get('latitude'):
            print(f"  Coordinates: {facility['latitude']}, {facility['longitude']}")
        print()

if __name__ == "__main__":
    main()
