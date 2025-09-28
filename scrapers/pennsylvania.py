import requests
import pandas as pd
import re
import json
import time
import os
from bs4 import BeautifulSoup
from urllib.parse import urljoin

class PennsylvaniaScraper:
    def __init__(self):
        self.base_url = "https://www.pa.gov"
        self.facilities_url = "https://www.pa.gov/agencies/cor/state-prisons"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
    def scrape_facility_list(self):
        """Get the list of Pennsylvania facilities from the side navigation menu."""
        print("Fetching Pennsylvania prison facility list...")
        
        try:
            response = requests.get(self.facilities_url, headers=self.headers, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find the State Prisons section in the side navigation
            facilities = []
            
            # Look for the State Prisons navigation section
            state_prisons_section = None
            nav_links = soup.find_all('a', href=True)
            
            for link in nav_links:
                if 'state-prisons' in link.get('href', '') and link.get_text(strip=True) == 'State Prisons':
                    # Find the parent container that has the facility list
                    parent = link.find_parent()
                    while parent and not parent.find('ul'):
                        parent = parent.find_parent()
                    if parent:
                        state_prisons_section = parent.find('ul')
                        break
            
            if not state_prisons_section:
                # Alternative approach: look for all links that match the facility pattern
                print("Using alternative facility discovery method...")
                for link in nav_links:
                    href = link.get('href', '')
                    if '/agencies/cor/state-prisons/sci-' in href or '/agencies/cor/state-prisons/quehanna-boot-camp' in href:
                        facility_name = link.get_text(strip=True)
                        if facility_name and facility_name not in ['State Prisons']:
                            facility_url = urljoin(self.base_url, href)
                            facilities.append({
                                'name': facility_name,
                                'facility_url': facility_url
                            })
            else:
                # Extract facilities from the navigation section
                facility_links = state_prisons_section.find_all('a', href=True)
                for link in facility_links:
                    href = link.get('href', '')
                    if '/agencies/cor/state-prisons/' in href and href != '/agencies/cor/state-prisons':
                        facility_name = link.get_text(strip=True)
                        if facility_name:
                            facility_url = urljoin(self.base_url, href)
                            facilities.append({
                                'name': facility_name,
                                'facility_url': facility_url
                            })
            
            # Remove duplicates
            seen_urls = set()
            unique_facilities = []
            for facility in facilities:
                if facility['facility_url'] not in seen_urls:
                    seen_urls.add(facility['facility_url'])
                    unique_facilities.append(facility)
            
            print(f"Found {len(unique_facilities)} Pennsylvania facilities")
            return unique_facilities
            
        except Exception as e:
            print(f"Error fetching facility list: {e}")
            # Fallback to known facilities if scraping fails
            return self._get_known_facilities()
    
    def _get_known_facilities(self):
        """Fallback list of known Pennsylvania facilities."""
        known_facilities = [
            "SCI Albion", "SCI Benner Township", "SCI Cambridge Springs", "SCI Camp Hill",
            "SCI Chester", "SCI Coal Township", "SCI Dallas", "SCI Fayette", "SCI Forest",
            "SCI Frackville", "SCI Greene", "SCI Houtzdale", "SCI Huntingdon", 
            "SCI Laurel Highlands", "SCI Mahanoy", "SCI Mercer", "SCI Muncy", "SCI Phoenix",
            "SCI Pine Grove", "Quehanna Boot Camp", "SCI Rockview", "SCI Smithfield",
            "SCI Somerset", "SCI Waymart"
        ]
        
        facilities = []
        for name in known_facilities:
            # Convert name to URL format
            url_name = name.lower().replace(' ', '-').replace('sci-', 'sci-')
            facility_url = f"{self.base_url}/agencies/cor/state-prisons/{url_name}"
            facilities.append({
                'name': name,
                'facility_url': facility_url
            })
        
        return facilities
    
    def scrape_facility_details(self, facility_url, expected_name=None):
        """Scrape detailed information from individual facility page."""
        print(f"Scraping details for: {facility_url}")
        
        try:
            response = requests.get(facility_url, headers=self.headers, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            facility_data = {}
            
            # Extract facility name from title or h1
            title_elem = soup.find('h1')
            if title_elem:
                facility_data['name'] = title_elem.get_text(strip=True)
            elif expected_name:
                facility_data['name'] = expected_name
            
            # Extract address information from the sidebar
            address_section = soup.find('h2', string=re.compile(r'Facility Address', re.I))
            if address_section:
                address_parent = address_section.find_parent()
                if address_parent:
                    address_text = address_parent.get_text(strip=True)
                    facility_data['address_text'] = address_text
            
            # Extract leadership information
            leadership_section = soup.find('h2', string=re.compile(r'Leadership', re.I))
            if leadership_section:
                leadership_parent = leadership_section.find_parent()
                if leadership_parent:
                    leadership_text = leadership_parent.get_text(strip=True)
                    facility_data['leadership_text'] = leadership_text
            
            # Extract facility information from main content
            facility_info_section = soup.find('h2', string=re.compile(r'Facility Information', re.I))
            if facility_info_section:
                info_parent = facility_info_section.find_parent()
                if info_parent:
                    info_text = info_parent.get_text(strip=True)
                    facility_data['facility_info_text'] = info_text
            
            # Extract inmate information
            inmate_info_section = soup.find('h2', string=re.compile(r'Inmate Information', re.I))
            if inmate_info_section:
                inmate_parent = inmate_info_section.find_parent()
                if inmate_parent:
                    inmate_text = inmate_parent.get_text(strip=True)
                    facility_data['inmate_info_text'] = inmate_text
            
            facility_data['facility_url'] = facility_url
            return facility_data
            
        except Exception as e:
            print(f"Error scraping facility details from {facility_url}: {e}")
            return {
                'name': expected_name or 'Unknown',
                'facility_url': facility_url,
                'error': str(e)
            }
    
    def parse_facility_data(self, facility_data):
        """Parse facility data into structured format."""
        parsed_data = {
            'name': facility_data.get('name'),
            'jurisdiction': 'Pennsylvania',
            'agency': 'Pennsylvania Department of Corrections',
            'street_address': None,
            'city': None,
            'state': 'PA',
            'zip_code': None,
            'phone': None,
            'fax': None,
            'superintendent': None,
            'deputy_superintendent_centralized': None,
            'deputy_superintendent_facilities': None,
            'business_manager': None,
            'assistant': None,
            'acres_inside': None,
            'acres_outside': None,
            'operational_structures': None,
            'housing_units': None,
            'employees': None,
            'facility_url': facility_data.get('facility_url'),
            'programs': []
        }
        
        # Parse address information
        address_text = facility_data.get('address_text', '')
        if address_text:
            # Clean up the text - replace non-breaking spaces and normalize
            clean_text = address_text.replace('\xa0', ' ').replace('  ', ' ')
            
            # Extract street address - look for pattern after "Facility Address"
            street_match = re.search(r'Facility Address\s*([^(]+?)(?=[A-Z][a-z\s]+,\s*PA)', clean_text)
            if street_match:
                street = street_match.group(1).strip()
                # Clean up common artifacts
                street = re.sub(r'\s+', ' ', street)  # Multiple spaces to single
                parsed_data['street_address'] = street
            
            # Extract city, state, zip - look for pattern like "Albion, PA 16475-0001"
            city_state_zip_match = re.search(r'([A-Z][a-z\s]+),\s*PA\s+(\d{5}(?:-\d{4})?)', clean_text)
            if city_state_zip_match:
                parsed_data['city'] = city_state_zip_match.group(1).strip()
                parsed_data['zip_code'] = city_state_zip_match.group(2)
            
            # Extract phone number - look for (XXX) XXX-XXXX pattern
            phone_match = re.search(r'\((\d{3})\)\s*(\d{3})-(\d{4})', clean_text)
            if phone_match:
                parsed_data['phone'] = f"({phone_match.group(1)}) {phone_match.group(2)}-{phone_match.group(3)}"
        
        # Parse leadership information
        leadership_text = facility_data.get('leadership_text', '')
        if leadership_text:
            # Clean up the text - replace non-breaking spaces
            clean_leadership = leadership_text.replace('\xa0', ' ')
            
            # Extract superintendent - stop at "Deputy" to avoid capturing too much
            superintendent_match = re.search(r'Superintendent:\s*([^D]+?)(?=Deputy|$)', clean_leadership, re.I)
            if superintendent_match:
                parsed_data['superintendent'] = superintendent_match.group(1).strip()
            
            # Extract deputy superintendents
            deputy_centralized_match = re.search(r'Deputy Superintendent for Centralized Services:\s*([^D]+?)(?=Deputy|Business|Superintendent|$)', clean_leadership, re.I)
            if deputy_centralized_match:
                parsed_data['deputy_superintendent_centralized'] = deputy_centralized_match.group(1).strip()
            
            deputy_facilities_match = re.search(r'Deputy Superintendent for Facilities Management:\s*([^B]+?)(?=Business|Superintendent|$)', clean_leadership, re.I)
            if deputy_facilities_match:
                parsed_data['deputy_superintendent_facilities'] = deputy_facilities_match.group(1).strip()
            
            # Extract business manager
            business_manager_match = re.search(r'Business Manager:\s*([^S]+?)(?=Superintendent|$)', clean_leadership, re.I)
            if business_manager_match:
                parsed_data['business_manager'] = business_manager_match.group(1).strip()
            
            # Extract assistant
            assistant_match = re.search(r'Superintendent[\'s]? Assistant:\s*([^\n\r]+?)(?=$)', clean_leadership, re.I)
            if assistant_match:
                parsed_data['assistant'] = assistant_match.group(1).strip()
        
        # Parse facility information
        facility_info_text = facility_data.get('facility_info_text', '')
        if facility_info_text:
            # Extract acres inside perimeter
            acres_inside_match = re.search(r'Number of Acres Inside Perimeter[:\s]*(\d+)', facility_info_text, re.I)
            if acres_inside_match:
                parsed_data['acres_inside'] = int(acres_inside_match.group(1))
            
            # Extract acres outside perimeter
            acres_outside_match = re.search(r'Number of Acres Outside Perimeter[:\s]*(\d+)', facility_info_text, re.I)
            if acres_outside_match:
                parsed_data['acres_outside'] = int(acres_outside_match.group(1))
            
            # Extract operational structures
            structures_match = re.search(r'Number of Operational Structures[^:]*[:\s]*(\d+)', facility_info_text, re.I)
            if structures_match:
                parsed_data['operational_structures'] = int(structures_match.group(1))
            
            # Extract housing units
            housing_match = re.search(r'Number of Housing Units[:\s]*(\d+)', facility_info_text, re.I)
            if housing_match:
                parsed_data['housing_units'] = int(housing_match.group(1))
            
            # Extract employees
            employees_match = re.search(r'Average Number of Full-Time Employees[:\s]*(\d+)', facility_info_text, re.I)
            if employees_match:
                parsed_data['employees'] = int(employees_match.group(1))
        
        return parsed_data
    
    def geocode_address(self, facility_data):
        """Geocode facility address using multiple services."""
        if not facility_data.get('street_address') or not facility_data.get('city'):
            return None, None
        
        # Construct full address
        address_parts = [facility_data['street_address']]
        if facility_data.get('city'):
            address_parts.append(facility_data['city'])
        if facility_data.get('state'):
            address_parts.append(facility_data['state'])
        if facility_data.get('zip_code'):
            address_parts.append(facility_data['zip_code'])
        
        full_address = ', '.join(address_parts)
        
        # Try Google Maps API first if available
        google_api_key = os.environ.get('GOOGLE_MAPS_API_KEY')
        if google_api_key:
            try:
                geocode_url = "https://maps.googleapis.com/maps/api/geocode/json"
                params = {
                    'address': full_address,
                    'key': google_api_key
                }
                
                response = requests.get(geocode_url, params=params, timeout=10)
                data = response.json()
                
                if data['status'] == 'OK' and data['results']:
                    location = data['results'][0]['geometry']['location']
                    lat, lng = location['lat'], location['lng']
                    
                    # Validate coordinates are in Pennsylvania bounds
                    if 39.7 <= lat <= 42.3 and -80.6 <= lng <= -74.7:
                        print(f"  Geocoded with Google Maps: {lat:.6f}, {lng:.6f}")
                        time.sleep(0.1)  # Rate limiting
                        return lat, lng
                        
            except Exception as e:
                print(f"  Google Maps geocoding failed: {e}")
        
        # Fallback to Nominatim
        try:
            nominatim_url = "https://nominatim.openstreetmap.org/search"
            params = {
                'q': full_address,
                'format': 'json',
                'limit': 1,
                'countrycodes': 'us'
            }
            
            response = requests.get(nominatim_url, params=params, timeout=10)
            data = response.json()
            
            if data:
                lat, lng = float(data[0]['lat']), float(data[0]['lon'])
                
                # Validate coordinates are in Pennsylvania bounds
                if 39.7 <= lat <= 42.3 and -80.6 <= lng <= -74.7:
                    print(f"  Geocoded with Nominatim: {lat:.6f}, {lng:.6f}")
                    time.sleep(1)  # Rate limiting for free service
                    return lat, lng
                    
        except Exception as e:
            print(f"  Nominatim geocoding failed: {e}")
        
        print(f"  Geocoding failed for: {full_address}")
        return None, None
    
    def scrape_all(self):
        """Scrape all Pennsylvania prison facilities."""
        print("Starting Pennsylvania prison data collection...")
        
        # Get facility list
        facilities = self.scrape_facility_list()
        
        if not facilities:
            print("No facilities found!")
            return []
        
        all_facility_data = []
        
        for i, facility in enumerate(facilities, 1):
            print(f"\nProcessing facility {i}/{len(facilities)}: {facility['name']}")
            
            # Get detailed facility information
            facility_details = self.scrape_facility_details(facility['facility_url'], facility['name'])
            
            # Parse the facility data
            parsed_data = self.parse_facility_data(facility_details)
            
            # Geocode the address
            if parsed_data['street_address'] and parsed_data['city']:
                lat, lng = self.geocode_address(parsed_data)
                parsed_data['latitude'] = lat
                parsed_data['longitude'] = lng
            else:
                parsed_data['latitude'] = None
                parsed_data['longitude'] = None
            
            all_facility_data.append(parsed_data)
            
            # Small delay between requests
            time.sleep(0.5)
        
        return all_facility_data
    
    def save_data(self, data, output_dir="data/pennsylvania"):
        """Save data to JSON, CSV, and GeoJSON formats."""
        os.makedirs(output_dir, exist_ok=True)
        
        # Save JSON
        json_path = os.path.join(output_dir, "pennsylvania_prisons.json")
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"Saved JSON data to {json_path}")
        
        # Save CSV
        csv_path = os.path.join(output_dir, "pennsylvania_prisons.csv")
        df = pd.DataFrame(data)
        df.to_csv(csv_path, index=False, encoding='utf-8')
        print(f"Saved CSV data to {csv_path}")
        
        # Save GeoJSON
        geojson_path = os.path.join(output_dir, "pennsylvania_prisons.geojson")
        geojson_data = {
            "type": "FeatureCollection",
            "features": []
        }
        
        for facility in data:
            if facility.get('latitude') and facility.get('longitude'):
                feature = {
                    "type": "Feature",
                    "geometry": {
                        "type": "Point",
                        "coordinates": [facility['longitude'], facility['latitude']]
                    },
                    "properties": {k: v for k, v in facility.items() if k not in ['latitude', 'longitude']}
                }
                geojson_data["features"].append(feature)
        
        with open(geojson_path, 'w', encoding='utf-8') as f:
            json.dump(geojson_data, f, indent=2, ensure_ascii=False)
        print(f"Saved GeoJSON data to {geojson_path}")
        
        return len(data), len(geojson_data["features"])

def main():
    scraper = PennsylvaniaScraper()
    data = scraper.scrape_all()
    
    if data:
        total_facilities, geocoded_facilities = scraper.save_data(data)
        print(f"\nPennsylvania scraping completed!")
        print(f"Total facilities: {total_facilities}")
        print(f"Geocoded facilities: {geocoded_facilities}")
        print(f"Geocoding success rate: {geocoded_facilities/total_facilities*100:.1f}%")
    else:
        print("No data collected!")

if __name__ == "__main__":
    main()
