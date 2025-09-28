"""
Illinois state prison data scraper for IDOC facilities.
"""

import requests
import pandas as pd
import re
import json
import time
import os
from bs4 import BeautifulSoup
from bs4 import NavigableString
from urllib.parse import urljoin


class IllinoisScraper:
    """Scraper for Illinois Department of Corrections (IDOC) facilities."""
    
    def __init__(self):
        self.headers = {
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36',
        }
        
        self.base_url = 'https://idoc.illinois.gov'
        self.facilities_url = 'https://idoc.illinois.gov/facilities/correctionalfacilities.html'

    def _parse_address(self, address_text):
        """Parse address text into structured components"""
        if not address_text:
            return {
                'street_address': None,
                'city': None,
                'state': 'IL',
                'zip_code': None,
                'phone': None,
                'fax': None
            }
        
        lines = [line.strip() for line in address_text.split('\n') if line.strip()]
        
        # Extract phone and fax numbers
        phone = None
        fax = None
        address_lines = []
        
        for line in lines:
            if line.startswith('Phone:'):
                phone = line.replace('Phone:', '').strip()
            elif line.startswith('Fax:'):
                fax = line.replace('Fax:', '').strip()
            else:
                address_lines.append(line)
        
        # Extract city, state, zip (last line)
        city, state, zip_code = None, 'IL', None
        if address_lines:
            city_state_zip = address_lines[-1].strip()
            # Match pattern like "City, IL 12345" or "City, IL 12345-1234"
            match = re.match(r'^(.+),\s*([A-Z]{2})\s+(\d{5}(?:-\d{4})?)$', city_state_zip)
            if match:
                city, state, zip_code = match.groups()
                address_lines = address_lines[:-1]
        
        # Remaining lines are street address
        street_address = '\n'.join(address_lines) if address_lines else None
        
        return {
            'street_address': street_address,
            'city': city,
            'state': state,
            'zip_code': zip_code,
            'phone': phone,
            'fax': fax
        }

    def _extract_facility_data(self, soup):
        """Extract facility data from individual facility page"""
        data = {
            'warden': None,
            'capacity': None,
            'population': None,
            'security_level': None,
            'gender': None,
            'opened': None,
            'cost_per_individual': None,
            'programs': []
        }
        
        # Extract warden name
        warden_element = soup.find(string=re.compile(r'.*Warden'))
        if warden_element:
            # Look for the warden name in the parent or next elements
            parent = warden_element.parent
            if parent:
                warden_text = parent.get_text(strip=True)
                # Extract name before ", Warden"
                match = re.search(r'^(.+?),?\s*Warden', warden_text)
                if match:
                    data['warden'] = match.group(1).strip()
        
        # Extract facility data from structured content
        facility_data_section = soup.find('h2', string='Facility Data')
        if facility_data_section:
            data_content = facility_data_section.find_next_sibling()
            if data_content:
                text = data_content.get_text()
                
                # Extract capacity
                capacity_match = re.search(r'Operational Capacity:\s*([0-9,]+)', text)
                if capacity_match:
                    data['capacity'] = int(capacity_match.group(1).replace(',', ''))
                
                # Extract population
                population_match = re.search(r'Population:\s*([0-9,]+)', text)
                if population_match:
                    data['population'] = int(population_match.group(1).replace(',', ''))
                
                # Extract security level
                if 'Medium Security' in text:
                    data['security_level'] = 'Medium'
                elif 'Maximum Security' in text:
                    data['security_level'] = 'Maximum'
                elif 'Minimum Security' in text:
                    data['security_level'] = 'Minimum'
                
                # Extract gender
                if 'Adult Male' in text:
                    data['gender'] = 'Male'
                elif 'Adult Female' in text:
                    data['gender'] = 'Female'
                
                # Extract opened date
                opened_match = re.search(r'Opened:\s*([A-Za-z]+ \d{4})', text)
                if opened_match:
                    data['opened'] = opened_match.group(1)
                
                # Extract cost per individual
                cost_match = re.search(r'Average Annual Cost Per Individual:\s*\$([0-9,]+)', text)
                if cost_match:
                    data['cost_per_individual'] = cost_match.group(1)
        
        # Extract programs
        programs = []
        
        # Academic programs
        academic_section = soup.find('h3', string='Academic Programs') or soup.find('b', string='Academic:')
        if academic_section:
            program_list = academic_section.find_next('ul')
            if program_list:
                for li in program_list.find_all('li'):
                    programs.append(f"Academic: {li.get_text(strip=True)}")
        
        # Career and Technical Education
        career_section = soup.find('h3', string='Career and Technical Education') or soup.find('b', string='Career and Technical Education:')
        if career_section:
            program_list = career_section.find_next('ul')
            if program_list:
                for li in program_list.find_all('li'):
                    programs.append(f"Career/Technical: {li.get_text(strip=True)}")
        
        # Other programs
        other_section = soup.find('b', string='Other:')
        if other_section:
            program_list = other_section.find_next('ul')
            if program_list:
                for li in program_list.find_all('li'):
                    programs.append(f"Other: {li.get_text(strip=True)}")
        
        data['programs'] = programs
        
        return data

    def scrape_facility_list(self):
        """Get the list of Illinois facilities from the list page.

        Strategy:
        1) Prefer parsing anchors under ul.cmp-cf-list
        2) Fallback: scan all anchors matching facility.*.html
        3) Final fallback: use known facility list
        """
        print("Fetching Illinois prison facility list...")
        
        try:
            response = requests.get(self.facilities_url, headers=self.headers, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            facilities = []
            seen_urls = set()
            
            # 1) Prefer the structured list on the page
            list_container = soup.find('ul', class_=re.compile(r'\bcmp-cf-list\b'))
            if list_container:
                for a in list_container.find_all('a', href=True):
                    href = a['href']
                    name_text = a.get_text(strip=True)
                    facility_url = urljoin(self.base_url, href)
                    if facility_url not in seen_urls and 'facility.' in facility_url:
                        facilities.append({'name': name_text, 'facility_url': facility_url})
                        seen_urls.add(facility_url)
            
            # 2) Fallback: scan any anchor that looks like a facility link
            if not facilities:
                for a in soup.find_all('a', href=True):
                    href = a['href']
                    if '/facilities/correctionalfacilities/' in href and 'facility.' in href and href.endswith('.html'):
                        facility_url = urljoin(self.base_url, href)
                        if facility_url in seen_urls:
                            continue
                        name = a.get_text(strip=True)
                        if not name:
                            # Derive a reasonable name from the slug as last resort
                            slug_match = re.search(r'facility\.([^.]+)\.html', facility_url)
                            if slug_match:
                                slug = slug_match.group(1)
                                name = ' '.join([w.capitalize() for w in slug.replace('-', ' ').split()])
                        facilities.append({'name': name, 'facility_url': facility_url})
                        seen_urls.add(facility_url)
            
            # If we didn't find facilities in metadata, use a known list
            if not facilities:
                print("Could not extract from page, using known facility list...")
                known_facilities = [
                    "Big Muddy River Correctional Center",
                    "Centralia Correctional Center", 
                    "Danville Correctional Center",
                    "Decatur Correctional Center",
                    "Dixon Correctional Center",
                    "East Moline Correctional Center",
                    "Graham Correctional Center",
                    "Hill Correctional Center",
                    "Illinois River Correctional Center",
                    "Jacksonville Correctional Center",
                    "Joliet Inpatient Treatment Center",
                    "Joliet Treatment Center",
                    "Lawrence Correctional Center",
                    "Lincoln Correctional Center",
                    "Logan Correctional Center",
                    "Menard Correctional Center",
                    "Menard Medium Security Unit",
                    "Pinckneyville Correctional Center",
                    "Pontiac Correctional Center",
                    "Pontiac Medium Security Unit",
                    "Robinson Correctional Center",
                    "Shawnee Correctional Center",
                    "Sheridan Correctional Center",
                    "Southwestern Illinois Correctional Center",
                    "Stateville Correctional Center",
                    "Taylorville Correctional Center",
                    "Vandalia Correctional Center",
                    "Vienna Correctional Center",
                    "Western Illinois Correctional Center"
                ]
                
                for facility_name in known_facilities:
                    slug = facility_name.lower().replace(' ', '-').replace('&', 'and')
                    facility_url = f"{self.base_url}/content/soi/idoc/en/facilities/correctionalfacilities/facility.{slug}.html"
                    facilities.append({'name': facility_name, 'facility_url': facility_url})
            
            print(f"Found {len(facilities)} Illinois facilities")
            return facilities
            
        except Exception as e:
            print(f"Error fetching Illinois facility list: {e}")
            return []

    def parse_facility_data(self, facility_data):
        """Parse facility data from content fragment HTML"""
        parsed_data = {
            'street_address': None,
            'city': None,
            'state': 'IL',
            'zip_code': None,
            'phone': None,
            'fax': None,
            'warden': facility_data.get('warden'),
            'capacity': None,
            'population': None,
            'security_level': None,
            'gender': None,
            'opened': None,
            'cost_per_individual': None,
            'programs': []
        }

        # Normalize warden field if it contains trailing label
        if parsed_data['warden']:
            m = re.search(r'^(.+?),\s*Warden', parsed_data['warden'])
            if m:
                parsed_data['warden'] = m.group(1).strip()
        
        # Parse address from HTML
        address_html = facility_data.get('address_html', '')
        if address_html:
            address_soup = BeautifulSoup(address_html, 'html.parser')
            # First pass: generic extraction (also captures Phone/Fax)
            address_text = address_soup.get_text('\n', strip=True)
            address_info = self._parse_address(address_text)
            parsed_data.update(address_info)

            # Prefer the Business Mail block for geocoding (avoid PO Box/IC mail)
            business_label = None
            for tag in address_soup.find_all(['b', 'strong']):
                if tag.get_text(strip=True).lower().startswith('business mail'):
                    business_label = tag
                    break
            if business_label:
                parent_p = business_label.find_parent('p') or business_label.parent
                lines = []
                # Collect text nodes after the label within the same paragraph
                for sib in business_label.next_siblings:
                    if isinstance(sib, NavigableString):
                        text = str(sib).strip()
                        if text:
                            lines.append(text)
                    elif getattr(sib, 'name', None) == 'br':
                        continue
                    else:
                        text = sib.get_text('\n', strip=True)
                        if text:
                            lines.extend([t for t in text.split('\n') if t])
                # Fallback: if above produced nothing, parse the whole paragraph sans label
                if not lines and parent_p:
                    para_text = parent_p.get_text('\n', strip=True)
                    parts = [p for p in para_text.split('\n') if p and not p.lower().startswith('business mail')]
                    lines = parts

                # Expect street on first line, city/state/zip on next
                if len(lines) >= 2:
                    street_line = lines[0].strip()
                    city_state_zip = lines[1].strip()
                    m = re.match(r'^(.+),\s*([A-Z]{2})\s+(\d{5}(?:-\d{4})?)$', city_state_zip)
                    if m:
                        parsed_data['street_address'] = street_line
                        parsed_data['city'] = m.group(1)
                        parsed_data['state'] = m.group(2)
                        parsed_data['zip_code'] = m.group(3)
                
            # Enhanced fallback: parse the full address text for any City, IL ZIP pattern
            if not parsed_data.get('city') or not parsed_data.get('street_address'):
                all_lines = [l.strip() for l in address_text.split('\n') if l.strip()]
                for idx, line in enumerate(all_lines):
                    # Look for City, IL ZIP pattern
                    m = re.match(r'^(.+),\s*IL\s+(\d{5}(?:-\d{4})?)$', line)
                    if m:
                        parsed_data['city'] = m.group(1)
                        parsed_data['state'] = 'IL'
                        parsed_data['zip_code'] = m.group(2)
                        
                        # Find the best street address line before this
                        for street_idx in range(idx-1, -1, -1):
                            candidate = all_lines[street_idx].strip()
                            # Skip labels, PO Boxes, and other non-street lines
                            if (not candidate.endswith(':') and 
                                'P.O. Box' not in candidate and 
                                'Individual in Custody' not in candidate and
                                'Business Mail' not in candidate and
                                len(candidate) > 5 and
                                not re.match(r'^\(\d{3}\)', candidate)):  # Skip phone numbers
                                parsed_data['street_address'] = candidate
                                break
                        break
        
        # Parse facility data from HTML
        facility_data_html = facility_data.get('facility_data_html', '')
        if facility_data_html:
            facility_soup = BeautifulSoup(facility_data_html, 'html.parser')
            text = facility_soup.get_text()
            
            # Extract capacity
            capacity_match = re.search(r'Operational Capacity:\s*([0-9,]+)', text)
            if capacity_match:
                parsed_data['capacity'] = int(capacity_match.group(1).replace(',', ''))
            
            # Extract population
            population_match = re.search(r'Population:\s*([0-9,]+)', text)
            if population_match:
                parsed_data['population'] = int(population_match.group(1).replace(',', ''))
            
            # Extract security level
            if 'Medium Security' in text:
                parsed_data['security_level'] = 'Medium'
            elif 'Maximum Security' in text:
                parsed_data['security_level'] = 'Maximum'
            elif 'Minimum Security' in text:
                parsed_data['security_level'] = 'Minimum'
            
            # Extract gender
            if 'Adult Male' in text:
                parsed_data['gender'] = 'Male'
            elif 'Adult Female' in text:
                parsed_data['gender'] = 'Female'
            
            # Extract opened date
            opened_match = re.search(r'Opened:\s*([A-Za-z]+ \d{4})', text)
            if opened_match:
                parsed_data['opened'] = opened_match.group(1)
            
            # Extract cost per individual
            cost_match = re.search(r'Average Annual Cost Per Individual:\s*\$([0-9,]+)', text)
            if cost_match:
                parsed_data['cost_per_individual'] = cost_match.group(1)
        
        # Parse facility information for programs
        facility_info_html = facility_data.get('facility_info_html', '')
        if facility_info_html:
            info_soup = BeautifulSoup(facility_info_html, 'html.parser')
            programs = []
            
            # Find program lists
            program_sections = info_soup.find_all('b')
            for section in program_sections:
                section_text = section.get_text(strip=True)
                if section_text.endswith(':'):
                    section_name = section_text[:-1]  # Remove colon
                    # Find the next ul element
                    next_ul = section.find_next('ul')
                    if next_ul:
                        for li in next_ul.find_all('li'):
                            program_name = li.get_text(strip=True)
                            if program_name:
                                programs.append(f"{section_name}: {program_name}")
            
            parsed_data['programs'] = programs
        
        return parsed_data

    def scrape_facility_details(self, facility_url, expected_name=None):
        """Scrape detailed information from individual facility page"""
        try:
            response = requests.get(facility_url, headers=self.headers, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find content fragments - facilities are embedded as articles with data attributes
            all_articles = soup.find_all('article')
            facility_articles = []
            for article in all_articles:
                classes = article.get('class', [])
                if any('cmp-contentfragment--' in cls for cls in classes):
                    facility_articles.append(article)
            
            if not facility_articles:
                print(f"  Warning: No content fragments found on {facility_url}")
                return {}
            
            # Select the first fragment that has actual facility data
            # (diagnostics show the first fragment has the correct facility-specific content)
            selected = None
            for a in facility_articles:
                # Check if this fragment has facility data
                data_el = a.select_one('.cmp-contentfragment__element--facilityData .cmp-contentfragment__element-value')
                if data_el and data_el.get_text(strip=True):
                    selected = a
                    break
            
            article = selected or facility_articles[0]
            facility_data = {}

            # Parse data from all fragments (data is split across fragments)
            try:
                for frag in facility_articles:
                    # Address block
                    if not facility_data.get('address_html'):
                        addr_el = frag.select_one('.cmp-contentfragment__element--facilityAddress')
                        if addr_el:
                            val = addr_el.select_one('.cmp-contentfragment__element-value') or addr_el
                            facility_data['address_html'] = str(val)

                    # Facility Data block
                    if not facility_data.get('facility_data_html'):
                        data_el = frag.select_one('.cmp-contentfragment__element--facilityData')
                        if data_el:
                            val = data_el.select_one('.cmp-contentfragment__element-value') or data_el
                            facility_data['facility_data_html'] = str(val)

                    # Warden block
                    if not facility_data.get('warden'):
                        warden_el = frag.select_one('.cmp-contentfragment__element--facilityWarden .cmp-contentfragment__element-value')
                        if warden_el:
                            facility_data['warden'] = warden_el.get_text(strip=True)

                    # Facility Information block
                    if not facility_data.get('facility_info_html'):
                        info_el = frag.select_one('.cmp-contentfragment__element--facilityInformation')
                        if info_el:
                            val = info_el.select_one('.cmp-contentfragment__element-value') or info_el
                            facility_data['facility_info_html'] = str(val)

                    # Visitation block
                    if not facility_data.get('visitation_html'):
                        visit_el = frag.select_one('.cmp-contentfragment__element--visitation')
                        if visit_el:
                            val = visit_el.select_one('.cmp-contentfragment__element-value') or visit_el
                            facility_data['visitation_html'] = str(val)
            except Exception:
                pass
            
            # Parse JSON data from data-cmp-data-layer attribute
            data_layer = article.get('data-cmp-data-layer')
            
            if data_layer and not facility_data.get('address_html'):
                try:
                    # Decode HTML entities and parse JSON
                    import html
                    decoded_data = html.unescape(data_layer)
                    json_data = json.loads(decoded_data)

                    # Choose the correct entry: prefer matching dc:title to expected_name
                    entries = [v for v in json_data.values() if isinstance(v, dict) and 'elements' in v]
                    chosen = None
                    if entries and expected_name:
                        for v in entries:
                            if v.get('dc:title') and expected_name.lower() in v.get('dc:title', '').lower():
                                chosen = v
                                break
                    if not chosen and entries:
                        chosen = entries[0]

                    if chosen:
                        elements = chosen.get('elements', [])
                        for element in elements:
                            title = element.get('xdm:title', '')
                            text = element.get('xdm:text', '')

                            if title == 'Facility Address' and text:
                                facility_data['address_html'] = text
                            elif title == 'Facility Data' and text:
                                facility_data['facility_data_html'] = text
                            elif title == 'Warden' and text:
                                facility_data['warden'] = text
                            elif title == 'Facility Information' and text:
                                facility_data['facility_info_html'] = text
                            elif title == 'Visitation' and text:
                                facility_data['visitation_html'] = text

                except (json.JSONDecodeError, KeyError) as e:
                    print(f"  Warning: Could not parse data layer: {e}")
            
            return facility_data
            
        except Exception as e:
            print(f"  Error scraping facility details from {facility_url}: {e}")
            return {}

    def geocode_address(self, address_components):
        """Geocode facility address using multiple services"""
        if not address_components.get('street_address') or not address_components.get('city'):
            return None, None
        
        # Construct full address
        address_parts = []
        if address_components.get('street_address'):
            address_parts.append(address_components['street_address'])
        if address_components.get('city'):
            address_parts.append(address_components['city'])
        if address_components.get('state'):
            address_parts.append(address_components['state'])
        if address_components.get('zip_code'):
            address_parts.append(address_components['zip_code'])
        
        full_address = ', '.join(address_parts)
        
        # Try Google Maps API first if available
        google_api_key = os.environ.get('GOOGLE_MAPS_API_KEY')
        if google_api_key:
            try:
                geocode_url = f"https://maps.googleapis.com/maps/api/geocode/json"
                params = {
                    'address': full_address,
                    'key': google_api_key
                }
                
                response = requests.get(geocode_url, params=params, timeout=10)
                response.raise_for_status()
                data = response.json()
                
                if data['status'] == 'OK' and data['results']:
                    location = data['results'][0]['geometry']['location']
                    print(f"  ✓ Geocoded with Google Maps: {full_address}")
                    time.sleep(0.1)  # Rate limiting
                    return location['lat'], location['lng']
                    
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
            
            response = requests.get(nominatim_url, params=params, 
                                  headers={'User-Agent': 'PrisonDataScraper/1.0'}, 
                                  timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data:
                print(f"  ✓ Geocoded with Nominatim: {full_address}")
                time.sleep(1)  # Rate limiting for free service
                return float(data[0]['lat']), float(data[0]['lon'])
                
        except Exception as e:
            print(f"  Nominatim geocoding failed: {e}")
        
        # Fallback to Photon
        try:
            photon_url = "https://photon.komoot.io/api/"
            params = {
                'q': full_address,
                'limit': 1
            }
            
            response = requests.get(photon_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data.get('features'):
                coords = data['features'][0]['geometry']['coordinates']
                print(f"  ✓ Geocoded with Photon: {full_address}")
                time.sleep(1)  # Rate limiting
                return coords[1], coords[0]  # Photon returns [lon, lat]
                
        except Exception as e:
            print(f"  Photon geocoding failed: {e}")
        
        print(f"  ✗ Failed to geocode: {full_address}")
        return None, None

    def scrape_all(self):
        """Scrape all Illinois prison facility data"""
        print("Starting Illinois Department of Corrections (IDOC) scraper...")
        
        # Get facility list
        facilities = self.scrape_facility_list()
        if not facilities:
            return pd.DataFrame()
        
        all_facilities = []
        
        for i, facility in enumerate(facilities, 1):
            print(f"\n[{i}/{len(facilities)}] Processing: {facility['name']}")
            
            # Get detailed facility information from individual page
            facility_details = self.scrape_facility_details(facility['facility_url'], expected_name=facility['name'])
            
            # Parse the facility data
            details = self.parse_facility_data(facility_details)
            
            # Geocode the facility
            lat, lon = self.geocode_address(details)
            
            # Combine all data
            facility_data = {
                'name': facility['name'],
                'jurisdiction': 'Illinois',
                'agency': 'Illinois Department of Corrections (IDOC)',
                'facility_url': facility['facility_url'],
                'street_address': details.get('street_address'),
                'city': details.get('city'),
                'state': details.get('state', 'IL'),
                'zip_code': details.get('zip_code'),
                'phone': details.get('phone'),
                'fax': details.get('fax'),
                'latitude': lat,
                'longitude': lon,
                'warden': details.get('warden'),
                'capacity': details.get('capacity'),
                'population': details.get('population'),
                'security_level': details.get('security_level'),
                'gender': details.get('gender'),
                'opened': details.get('opened'),
                'cost_per_individual': details.get('cost_per_individual'),
                'programs': '; '.join(details.get('programs', []))
            }
            
            all_facilities.append(facility_data)
            
            # Rate limiting
            time.sleep(1)
        
        df = pd.DataFrame(all_facilities)
        
        # Validate coordinates are within Illinois bounds
        if not df.empty:
            # Illinois approximate bounds: 36.97°N to 42.51°N, 87.02°W to 91.51°W
            valid_coords = df[
                (df['latitude'].between(36.5, 43.0)) & 
                (df['longitude'].between(-92.0, -87.0))
            ]
            
            invalid_coords = df[
                ~((df['latitude'].between(36.5, 43.0)) & 
                  (df['longitude'].between(-92.0, -87.0))) &
                df['latitude'].notna() & df['longitude'].notna()
            ]
            
            if not invalid_coords.empty:
                print(f"\nWarning: {len(invalid_coords)} facilities have coordinates outside Illinois bounds:")
                for _, facility in invalid_coords.iterrows():
                    print(f"  - {facility['name']}: {facility['latitude']}, {facility['longitude']}")
        
        print(f"\n✓ Successfully scraped {len(df)} Illinois facilities")
        geocoded_count = df[df['latitude'].notna()].shape[0]
        print(f"✓ Geocoded {geocoded_count}/{len(df)} facilities ({geocoded_count/len(df)*100:.1f}%)")
        
        return df
