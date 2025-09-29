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

class MissouriScraper:
    """Scraper for Missouri Department of Corrections facilities."""
    
    def __init__(self):
        self.base_url = "https://doc.mo.gov"
        self.facilities_url = "https://doc.mo.gov/facilities/all"
        self.warden_url = "https://doc.mo.gov/facilities/adult-institutions/warden-listing"
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
        Scrape all Missouri correctional facilities.
        
        Returns:
            List of facility dictionaries with details and coordinates
        """
        logger.info("Starting Missouri facilities scrape...")
        
        # Get warden information first
        warden_data = self.get_warden_data()
        logger.info(f"Found warden data for {len(warden_data)} facilities")
        
        # Get all facilities from paginated results
        all_facilities = self.get_all_facilities()
        
        if not all_facilities:
            logger.error("Failed to get facility data")
            return []
        
        logger.info(f"Found {len(all_facilities)} total facilities")
        
        # Filter to only include correctional institutions (not probation offices)
        institutions = [f for f in all_facilities if f.get('facility_type') == 'Institution']
        logger.info(f"Found {len(institutions)} correctional institutions")
        
        # Process each facility
        facilities = []
        for i, facility_data in enumerate(institutions, 1):
            try:
                logger.info(f"Processing facility {i}/{len(institutions)}: {facility_data['name']}")
                
                facility = self.process_facility(facility_data, warden_data)
                if facility:
                    facilities.append(facility)
                
                # Rate limiting - be respectful
                time.sleep(0.2)
                
            except Exception as e:
                logger.error(f"Error processing {facility_data.get('name', 'Unknown')}: {e}")
                continue
        
        logger.info(f"Successfully processed {len(facilities)} facilities")
        return facilities
    
    def get_warden_data(self) -> Dict[str, Dict]:
        """Get warden information from the warden listing page."""
        warden_data = {}
        
        try:
            response = self.session.get(self.warden_url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find the table with warden information
            table = soup.find('table', class_='table')
            if table:
                tbody = table.find('tbody')
                if tbody:
                    rows = tbody.find_all('tr')
                    for row in rows:
                        cells = row.find_all('td')
                        if len(cells) >= 4:
                            acronym = cells[0].get_text().strip()
                            security_level = cells[2].get_text().strip()
                            warden_name = cells[3].get_text().strip()
                            
                            # Clean up warden name (remove bold tags)
                            if warden_name:
                                warden_name = re.sub(r'<[^>]+>', '', warden_name).strip()
                                if warden_name == 'Vacant':
                                    warden_name = None
                            
                            if acronym:
                                warden_data[acronym] = {
                                    'security_level': security_level,
                                    'warden': warden_name
                                }
            
        except Exception as e:
            logger.warning(f"Error getting warden data: {e}")
        
        return warden_data
    
    def get_all_facilities(self) -> List[Dict]:
        """Get all facilities from all pages."""
        all_facilities = []
        page = 0
        
        while True:
            try:
                logger.info(f"Fetching page {page}")
                url = f"{self.facilities_url}?page={page}"
                response = self.session.get(url)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.content, 'html.parser')
                facilities = self.parse_facilities_page(soup)
                
                if not facilities:
                    logger.info(f"No facilities found on page {page}, stopping")
                    break
                
                all_facilities.extend(facilities)
                logger.info(f"Found {len(facilities)} facilities on page {page}")
                
                # Check if there's a next page
                if not self.has_next_page(soup):
                    logger.info("No more pages found")
                    break
                
                page += 1
                time.sleep(0.5)  # Rate limiting between pages
                
            except Exception as e:
                logger.error(f"Error fetching page {page}: {e}")
                break
        
        return all_facilities
    
    def parse_facilities_page(self, soup: BeautifulSoup) -> List[Dict]:
        """Parse facilities from a single page."""
        facilities = []
        
        try:
            # Find the table with facility information
            table = soup.find('table', class_='table')
            if table:
                tbody = table.find('tbody')
                if tbody:
                    rows = tbody.find_all('tr')
                    for row in rows:
                        facility = self.parse_facility_row(row)
                        if facility:
                            facilities.append(facility)
        
        except Exception as e:
            logger.warning(f"Error parsing facilities page: {e}")
        
        return facilities
    
    def parse_facility_row(self, row) -> Optional[Dict]:
        """Parse a single facility row from the table."""
        try:
            cells = row.find_all('td')
            if len(cells) >= 5:
                acronym = cells[0].get_text().strip()
                name = cells[1].get_text().strip()
                facility_type = cells[2].get_text().strip()
                address_cell = cells[3]
                phone = cells[4].get_text().strip()
                
                # Parse address from the structured address element
                address_info = self.parse_address_cell(address_cell)
                
                facility = {
                    'acronym': acronym,
                    'name': name,
                    'facility_type': facility_type,
                    'phone': phone if phone else None,
                    'state': 'Missouri',
                    'agency': 'Missouri Department of Corrections (MODOC)'
                }
                
                facility.update(address_info)
                return facility
                
        except Exception as e:
            logger.warning(f"Error parsing facility row: {e}")
        
        return None
    
    def parse_address_cell(self, address_cell) -> Dict:
        """Parse address information from the address cell."""
        address_info = {}
        
        try:
            # Look for structured address element
            address_p = address_cell.find('p', class_='address')
            if address_p:
                # Extract address components
                address_line1 = address_p.find('span', class_='address-line1')
                locality = address_p.find('span', class_='locality')
                admin_area = address_p.find('span', class_='administrative-area')
                postal_code = address_p.find('span', class_='postal-code')
                
                if address_line1:
                    address_info['street_address'] = address_line1.get_text().strip()
                if locality:
                    address_info['city'] = locality.get_text().strip()
                if postal_code:
                    address_info['zip_code'] = postal_code.get_text().strip()
                    
        except Exception as e:
            logger.warning(f"Error parsing address cell: {e}")
        
        return address_info
    
    def has_next_page(self, soup: BeautifulSoup) -> bool:
        """Check if there's a next page in pagination."""
        try:
            # Look for next page link
            next_link = soup.find('a', string=re.compile(r'››|Next'))
            return next_link is not None
        except:
            return False
    
    def process_facility(self, facility_data: Dict, warden_data: Dict[str, Dict]) -> Optional[Dict]:
        """Process a single facility with warden data and geocoding."""
        try:
            facility = facility_data.copy()
            
            # Add warden information if available
            acronym = facility.get('acronym')
            if acronym and acronym in warden_data:
                facility.update(warden_data[acronym])
            
            # Determine facility type
            facility['facility_type'] = self.determine_facility_type(facility['name'])
            
            # Try to geocode the address
            if facility.get('street_address') and facility.get('city'):
                coordinates = self.geocode_address(facility)
                facility.update(coordinates)
            
            return facility
            
        except Exception as e:
            logger.warning(f"Error processing facility: {e}")
            return None
    
    def determine_facility_type(self, name: str) -> str:
        """Determine facility type based on name."""
        name_lower = name.lower()
        
        if 'correctional center' in name_lower:
            return 'Correctional Center'
        elif 'correctional facility' in name_lower:
            return 'Correctional Facility'
        elif 'reception' in name_lower and 'diagnostic' in name_lower:
            return 'Reception and Diagnostic Center'
        elif 'treatment center' in name_lower:
            return 'Treatment Center'
        elif 'women\'s' in name_lower:
            return 'Women\'s Correctional Center'
        else:
            return 'Correctional Institution'
    
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
            address_parts.append('Missouri')
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
    scraper = MissouriScraper()
    facilities = scraper.scrape_facilities()
    
    print(f"Found {len(facilities)} Missouri correctional facilities:")
    for facility in facilities[:10]:  # Show first 10
        print(f"- {facility['name']} ({facility.get('acronym', 'N/A')})")
        if facility.get('facility_type'):
            print(f"  Type: {facility['facility_type']}")
        if facility.get('security_level'):
            print(f"  Security: {facility['security_level']}")
        if facility.get('warden'):
            print(f"  Warden: {facility['warden']}")
        if facility.get('street_address'):
            print(f"  Address: {facility['street_address']}")
        if facility.get('city'):
            print(f"  City: {facility['city']}, MO {facility.get('zip_code', '')}")
        if facility.get('phone'):
            print(f"  Phone: {facility['phone']}")
        if facility.get('latitude'):
            print(f"  Coordinates: {facility['latitude']}, {facility['longitude']}")
        print()

if __name__ == "__main__":
    main()
