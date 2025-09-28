#!/usr/bin/env python3

import requests
import json
import re
from bs4 import BeautifulSoup
from typing import Dict, List, Optional, Tuple
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GeorgiaScraper:
    """Scraper for Georgia Department of Corrections facilities."""
    
    def __init__(self):
        self.base_url = "https://gdc.georgia.gov"
        self.facilities_url = "https://gdc.georgia.gov/find-location"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def scrape_facilities(self) -> List[Dict]:
        """
        Scrape all Georgia correctional facilities.
        
        Returns:
            List of facility dictionaries with details and coordinates
        """
        logger.info("Starting Georgia facilities scrape...")
        
        # Get the main page with embedded JSON data
        response = self.session.get(self.facilities_url)
        response.raise_for_status()
        
        # Extract JSON data from the page
        facilities_data = self.extract_json_data(response.text)
        
        if not facilities_data:
            logger.error("Failed to extract facilities data from page")
            return []
        
        # Filter to state prisons only (exclude county jails as noted in requirements)
        state_facilities = self.filter_state_facilities(facilities_data)
        
        logger.info(f"Found {len(state_facilities)} state correctional facilities")
        
        # Process each facility
        processed_facilities = []
        for facility in state_facilities:
            processed_facility = self.process_facility(facility)
            if processed_facility:
                processed_facilities.append(processed_facility)
        
        logger.info(f"Successfully processed {len(processed_facilities)} facilities")
        return processed_facilities
    
    def extract_json_data(self, html_content: str) -> List[Dict]:
        """
        Extract facility data from embedded JSON in the HTML page.
        
        Args:
            html_content: Raw HTML content from the facilities page
            
        Returns:
            List of facility data dictionaries
        """
        try:
            # Look for the geofield map data in the script tags
            # The data is in a complex nested structure, so we need to find the features array
            pattern = r'"features":\s*(\[.*?\])\s*\}\s*\}\s*\}'
            match = re.search(pattern, html_content, re.DOTALL)
            
            if not match:
                logger.error("Could not find facilities JSON data in page")
                return []
            
            features_json = match.group(1)
            
            # Clean up the JSON - remove any trailing content that might break parsing
            # Find the last complete feature object
            bracket_count = 0
            last_valid_pos = 0
            
            for i, char in enumerate(features_json):
                if char == '{':
                    bracket_count += 1
                elif char == '}':
                    bracket_count -= 1
                    if bracket_count == 0:
                        last_valid_pos = i + 1
            
            # Extract up to the last complete feature
            if last_valid_pos > 0:
                clean_json = features_json[:last_valid_pos] + ']'
                # Remove any trailing commas before the closing bracket
                clean_json = re.sub(r',\s*\]$', ']', clean_json)
            else:
                clean_json = features_json
            
            features = json.loads(clean_json)
            
            logger.info(f"Extracted {len(features)} facilities from JSON data")
            return features
            
        except (json.JSONDecodeError, AttributeError) as e:
            logger.error(f"Error parsing JSON data: {e}")
            # Try a simpler approach - look for individual feature objects
            try:
                feature_pattern = r'\{"type":"Feature".*?\}(?=,\{"type":"Feature"|\])'
                features = []
                for match in re.finditer(feature_pattern, html_content, re.DOTALL):
                    try:
                        feature = json.loads(match.group(0))
                        features.append(feature)
                    except json.JSONDecodeError:
                        continue
                
                logger.info(f"Extracted {len(features)} facilities using fallback method")
                return features
                
            except Exception as e2:
                logger.error(f"Fallback parsing also failed: {e2}")
                return []
    
    def filter_state_facilities(self, facilities_data: List[Dict]) -> List[Dict]:
        """
        Filter facilities to include only state prisons, excluding county jails.
        
        Args:
            facilities_data: List of all facility data
            
        Returns:
            List of state facility data only
        """
        state_facilities = []
        
        # Keywords that indicate state facilities vs county jails
        state_keywords = [
            'state prison', 'correctional institution', 'diagnostic', 'transitional center',
            'women\'s facility', 'womens facility', 'detention center', 'training center',
            'reentry', 'substance abuse center', 'integrated treatment', 'reinvestment center'
        ]
        
        exclude_keywords = [
            'county jail', 'county correctional institution', 'sheriff', 'headquarters',
            'forum river center', 'service of lawsuits'
        ]
        
        for facility in facilities_data:
            try:
                # Get facility title from the data
                title_html = facility.get('properties', {}).get('data', {}).get('title', '')
                
                # Extract clean title text
                soup = BeautifulSoup(title_html, 'html.parser')
                title = soup.get_text().strip().lower()
                
                if not title:
                    continue
                
                # Skip if it's a county facility or other excluded type
                if any(keyword in title for keyword in exclude_keywords):
                    continue
                
                # Include if it matches state facility keywords or doesn't contain "county"
                if any(keyword in title for keyword in state_keywords) or 'county' not in title:
                    state_facilities.append(facility)
                    
            except Exception as e:
                logger.warning(f"Error processing facility for filtering: {e}")
                continue
        
        logger.info(f"Filtered to {len(state_facilities)} state facilities from {len(facilities_data)} total")
        return state_facilities
    
    def process_facility(self, facility_data: Dict) -> Optional[Dict]:
        """
        Process a single facility's data into our standard format.
        
        Args:
            facility_data: Raw facility data from JSON
            
        Returns:
            Processed facility dictionary or None if processing fails
        """
        try:
            properties = facility_data.get('properties', {})
            geometry = facility_data.get('geometry', {})
            data = properties.get('data', {})
            
            # Extract facility name
            title_html = data.get('title', '')
            soup = BeautifulSoup(title_html, 'html.parser')
            name = soup.get_text().strip()
            
            if not name:
                logger.warning("Facility missing name, skipping")
                return None
            
            # Extract coordinates
            coordinates = geometry.get('coordinates', [])
            if len(coordinates) >= 2:
                longitude, latitude = coordinates[0], coordinates[1]
            else:
                logger.warning(f"Facility {name} missing coordinates")
                longitude, latitude = None, None
            
            # Extract URL for additional details
            facility_url = None
            if soup.find('a'):
                href = soup.find('a').get('href', '')
                if href.startswith('/'):
                    facility_url = self.base_url + href
            
            # Get additional details from the facility page if URL available
            additional_details = {}
            if facility_url:
                additional_details = self.scrape_facility_details(facility_url)
            
            # Build facility record
            facility = {
                'name': name,
                'latitude': latitude,
                'longitude': longitude,
                'entity_id': properties.get('entity_id'),
                'facility_url': facility_url,
                'state': 'Georgia',
                'agency': 'Georgia Department of Corrections (GDC)',
                **additional_details
            }
            
            return facility
            
        except Exception as e:
            logger.error(f"Error processing facility: {e}")
            return None
    
    def scrape_facility_details(self, facility_url: str) -> Dict:
        """
        Scrape additional details from individual facility page.
        
        Args:
            facility_url: URL of the facility's detail page
            
        Returns:
            Dictionary of additional facility details
        """
        try:
            response = self.session.get(facility_url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            details = {}
            
            # Extract address information
            address_info = self.extract_address_info(soup)
            details.update(address_info)
            
            # Extract facility type/description
            description = self.extract_description(soup)
            if description:
                details['description'] = description
            
            # Extract any additional metadata
            metadata = self.extract_metadata(soup)
            details.update(metadata)
            
            return details
            
        except Exception as e:
            logger.warning(f"Error scraping facility details from {facility_url}: {e}")
            return {}
    
    def extract_address_info(self, soup: BeautifulSoup) -> Dict:
        """Extract address information from facility page."""
        address_info = {}
        
        try:
            # Look for address patterns in the page content
            text_content = soup.get_text()
            
            # Common address patterns
            address_patterns = [
                r'(\d+\s+[A-Za-z\s]+(?:Street|St|Avenue|Ave|Road|Rd|Drive|Dr|Boulevard|Blvd|Lane|Ln|Way|Circle|Cir|Court|Ct))',
                r'(P\.?O\.?\s+Box\s+\d+)',
            ]
            
            for pattern in address_patterns:
                match = re.search(pattern, text_content, re.IGNORECASE)
                if match:
                    address_info['street_address'] = match.group(1).strip()
                    break
            
            # Look for city, state, zip patterns
            city_state_zip_pattern = r'([A-Za-z\s]+),\s*GA\s+(\d{5}(?:-\d{4})?)'
            match = re.search(city_state_zip_pattern, text_content)
            if match:
                address_info['city'] = match.group(1).strip()
                address_info['state'] = 'GA'
                address_info['zip_code'] = match.group(2)
            
            # Look for phone numbers
            phone_pattern = r'\((\d{3})\)\s*(\d{3})-(\d{4})'
            match = re.search(phone_pattern, text_content)
            if match:
                address_info['phone'] = f"({match.group(1)}) {match.group(2)}-{match.group(3)}"
                
        except Exception as e:
            logger.warning(f"Error extracting address info: {e}")
        
        return address_info
    
    def extract_description(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract facility description/summary."""
        try:
            # Look for meta description
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            if meta_desc and meta_desc.get('content'):
                return meta_desc.get('content').strip()
            
            # Look for main content paragraphs
            content_areas = soup.find_all(['p', 'div'], class_=re.compile(r'content|description|summary'))
            for area in content_areas:
                text = area.get_text().strip()
                if len(text) > 50:  # Reasonable description length
                    return text
                    
        except Exception as e:
            logger.warning(f"Error extracting description: {e}")
        
        return None
    
    def extract_metadata(self, soup: BeautifulSoup) -> Dict:
        """Extract additional metadata from facility page."""
        metadata = {}
        
        try:
            # Look for capacity, population, or other facility stats
            text_content = soup.get_text()
            
            # Capacity patterns
            capacity_patterns = [
                r'capacity[:\s]+(\d+)',
                r'houses?\s+(?:up\s+to\s+)?(\d+)\s+(?:inmates?|offenders?)',
                r'(\d+)[-\s]bed',
            ]
            
            for pattern in capacity_patterns:
                match = re.search(pattern, text_content, re.IGNORECASE)
                if match:
                    metadata['capacity'] = int(match.group(1))
                    break
            
            # Security level patterns
            security_patterns = [
                r'(minimum|medium|maximum|close|administrative)\s+security',
                r'security\s+level[:\s]+(\w+)',
                r'level\s+(\d+)',
            ]
            
            for pattern in security_patterns:
                match = re.search(pattern, text_content, re.IGNORECASE)
                if match:
                    metadata['security_level'] = match.group(1).strip()
                    break
                    
        except Exception as e:
            logger.warning(f"Error extracting metadata: {e}")
        
        return metadata

def main():
    """Main function for testing the scraper."""
    scraper = GeorgiaScraper()
    facilities = scraper.scrape_facilities()
    
    print(f"Found {len(facilities)} Georgia state correctional facilities:")
    for facility in facilities[:5]:  # Show first 5
        print(f"- {facility['name']}")
        if facility.get('latitude') and facility.get('longitude'):
            print(f"  Location: {facility['latitude']}, {facility['longitude']}")
        if facility.get('street_address'):
            print(f"  Address: {facility['street_address']}")
        print()

if __name__ == "__main__":
    main()
