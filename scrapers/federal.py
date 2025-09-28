"""
Federal prison data scraper for Bureau of Prisons (BOP) facilities.
"""

import requests
import pandas as pd
import time
import re
from bs4 import BeautifulSoup


class FederalScraper:
    """Scraper for federal prison data from the Bureau of Prisons."""
    
    def __init__(self):
        self.headers = {
            'referer': 'https://www.bop.gov/locations/map.jsp',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36',
        }
        
        self.loc_cols_to_keep = [
            'code', 'name', 'securityLevel', 'region', 'latitude', 'longitude', 
            'url', 'timeZone', 'address', 'city', 'state', 'zipCode', 
            'phoneNumber', 'contactEmail', 'locationtype', 'privateFacl', 
            'gender', 'special', 'type', 'faclTypeDescription', 'hasCamp', 'imageNormal'
        ]

    def scrape_facility_codes(self):
        """Scrape facility codes from the BOP facilities list page"""
        
        print("Fetching current facility list from BOP website...")
        
        headers = {
            'referer': 'https://www.bop.gov/locations/',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36',
        }
        
        try:
            response = requests.get('https://www.bop.gov/locations/list.jsp', headers=headers, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            facility_codes = set()
            
            # Find all facility links in the list
            facil_list_cont = soup.find('div', id='facil_list_cont')
            if not facil_list_cont:
                print("Warning: Could not find facility list container")
                return []
            
            # Method 1: Extract from URLs like /locations/institutions/ald/
            institution_links = facil_list_cont.find_all('a', href=re.compile(r'/locations/institutions/\w+/'))
            for link in institution_links:
                href = link.get('href')
                # Extract code from URL: /locations/institutions/ald/ -> ald
                match = re.search(r'/locations/institutions/(\w+)/', href)
                if match:
                    code = match.group(1).upper()
                    facility_codes.add(code)
            
            # Method 2: Extract from data-code attributes (for FCC facilities)
            fcc_links = facil_list_cont.find_all('a', {'data-code': True})
            for link in fcc_links:
                code = link.get('data-code').upper()
                facility_codes.add(code)
            
            # Method 3: Extract from ccm (RRM) URLs like /locations/ccm/cat/
            ccm_links = facil_list_cont.find_all('a', href=re.compile(r'/locations/ccm/\w+'))
            for link in ccm_links:
                href = link.get('href')
                # Extract code from URL: /locations/ccm/cat/ -> cat
                match = re.search(r'/locations/ccm/(\w+)', href)
                if match:
                    code = match.group(1).upper()
                    facility_codes.add(code)
            
            # Method 4: Look for other facility types (training centers, etc.)
            other_links = facil_list_cont.find_all('a', href=re.compile(r'/locations/\w+'))
            for link in other_links:
                href = link.get('href')
                # Special cases for central office and training facilities
                if '/locations/central_office/' in href:
                    facility_codes.add('BOP')
                elif '/locations/grand_prairie/' in href:
                    facility_codes.add('GRA')
                elif 'training_centers' in href:
                    # For Glynco training center
                    facility_codes.add('GLN')
            
            facility_codes_list = sorted(list(facility_codes))
            
            print(f"Successfully scraped {len(facility_codes_list)} facility codes from BOP website")
            print(f"Codes: {', '.join(facility_codes_list[:10])}{'...' if len(facility_codes_list) > 10 else ''}")
            
            return facility_codes_list
            
        except requests.exceptions.RequestException as e:
            print(f"Error fetching facility list: {e}")
            print("Falling back to static facility codes...")
            return self._get_fallback_codes()
        except Exception as e:
            print(f"Error parsing facility list: {e}")
            print("Falling back to static facility codes...")
            return self._get_fallback_codes()

    def _get_fallback_codes(self):
        """Fallback list of facility codes if scraping fails"""
        return [
            'ALD', 'ALI', 'ALX', 'ASH', 'ATL', 'CAT', 'ATW', 'CBR', 'BAS', 'BMX',
            'BEC', 'BEN', 'BER', 'BSY', 'BIG', 'BRO', 'BRY', 'BUX', 'CAA', 'CRW',
            'BOP', 'CCC', 'CCH', 'CCN', 'COX', 'CUM', 'CDA', 'DAN', 'CDT', 'DEV',
            'DUB', 'DTH', 'EDG', 'ERE', 'ELK', 'ENG', 'EST', 'FAI', 'FLX', 'FOX',
            'FTD', 'FTW', 'GIL', 'GLN', 'GRA', 'GRE', 'GUA', 'HAX', 'HER', 'HON',
            'HOU', 'JES', 'CKC', 'LAT', 'LVN', 'LEE', 'LEW', 'LEX', 'LOX', 'CLB',
            'LOR', 'LOS', 'MAN', 'MNA', 'MAR', 'MCR', 'MCD', 'MCK', 'MEM', 'MEN',
            'MIA', 'MIM', 'CMM', 'MXR', 'MIL', 'CMS', 'MON', 'CMY', 'MRG', 'DET',
            'CNV', 'NYM', 'CNK', 'NCR', 'NER', 'OAX', 'OKL', 'COR', 'OTV', 'OXF',
            'PEK', 'PEN', 'PEX', 'PHL', 'CPA', 'PHX', 'CPH', 'CPG', 'POX', 'CRL',
            'RBK', 'RCH', 'CSC', 'SAF', 'CSA', 'SDC', 'SST', 'SCH', 'SEA', 'SET',
            'CSE', 'SHE', 'SCR', 'SER', 'SPG', 'CST', 'TDG', 'TAL', 'TRM', 'THX',
            'TEX', 'TOM', 'TRV', 'TCX', 'VIX', 'WAS', 'WXR', 'WIL', 'YAN', 'YAX'
        ]

    def fetch_prison_data(self, code):
        """Fetch data for a single prison code"""
        params = {
            'todo': 'query',
            'output': 'json',
            'code': code,
        }
        
        try:
            response = requests.get('https://www.bop.gov/PublicInfo/execute/phyloc', 
                                  params=params, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            location_info = data.get('Locations', [])
            
            if location_info:
                # Get population info if available
                pop_info = data.get('Popreport', {}).get('BOP', [])
                population = int(pop_info[0]['popCount']) if pop_info else None
                
                # Create dataframe with available columns
                df = pd.DataFrame(location_info)
                available_cols = [col for col in self.loc_cols_to_keep if col in df.columns]
                df = df[available_cols]
                
                if population is not None:
                    df['population'] = population
                    
                return df
            else:
                print(f"No location data found for code: {code}")
                return pd.DataFrame()
                
        except requests.exceptions.RequestException as e:
            print(f"Error fetching data for {code}: {e}")
            return pd.DataFrame()
        except Exception as e:
            print(f"Unexpected error for {code}: {e}")
            return pd.DataFrame()

    def scrape_all(self):
        """Scrape all federal prison data"""
        print("Starting federal prison data collection...")
        
        # Get current facility codes from BOP website
        prison_codes = self.scrape_facility_codes()
        
        if not prison_codes:
            print("Error: No facility codes could be retrieved")
            return pd.DataFrame()
        
        all_prisons = []
        failed_codes = []
        
        print(f"\nFetching data for {len(prison_codes)} federal prisons...")
        
        for i, code in enumerate(prison_codes, 1):
            print(f"Fetching {i}/{len(prison_codes)}: {code}")
            
            df = self.fetch_prison_data(code)
            
            if not df.empty:
                all_prisons.append(df)
            else:
                failed_codes.append(code)
            
            # Rate limiting - be respectful to the server
            time.sleep(0.5)
        
        if all_prisons:
            # Combine all data
            combined_df = pd.concat(all_prisons, ignore_index=True)
            
            # Clean up data types
            numeric_cols = ['latitude', 'longitude', 'population']
            for col in numeric_cols:
                if col in combined_df.columns:
                    combined_df[col] = pd.to_numeric(combined_df[col], errors='coerce')
            
            print(f"\nSuccessfully fetched data for {len(combined_df)} federal facilities")
            
            if failed_codes:
                print(f"Failed to fetch: {len(failed_codes)} codes: {', '.join(failed_codes)}")
                
            # Show facility types
            if 'type' in combined_df.columns:
                print(f"\nFacility types:")
                print(combined_df['type'].value_counts())
                
            # Show security levels
            if 'securityLevel' in combined_df.columns:
                print(f"\nSecurity levels:")
                print(combined_df['securityLevel'].value_counts())
            
            return combined_df
        else:
            print("No federal data was successfully fetched.")
            return pd.DataFrame()
