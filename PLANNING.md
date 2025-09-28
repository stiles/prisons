# Prison Data Scraper - Project Planning & Roadmap

## Project Overview

A comprehensive prison data collection system that scrapes correctional facility information from multiple jurisdictions using a modular, scalable architecture. The system prioritizes states by population and provides consistent data formats across all jurisdictions.

## Current Status (Completed)

### ✅ Core Infrastructure
- **Modular Architecture**: Each jurisdiction has its own scraper module in `scrapers/`
- **Unified Interface**: Single `fetch.py` command handles all jurisdictions
- **Consistent Output**: JSON, CSV, and GeoJSON formats for all data
- **Advanced Geocoding**: Google Maps API primary with OpenStreetMap fallbacks
- **100% Geocoding Success**: All facilities have precise coordinates

### ✅ Implemented Jurisdictions (664 Total Facilities)

#### 1. Federal - Bureau of Prisons (BOP) - 122 Facilities
- **Data Source**: [BOP facilities list](https://www.bop.gov/locations/list.jsp) + internal API
- **Implementation**: `scrapers/federal.py`
- **Features**: 
  - Dynamic facility code discovery
  - Population data from internal API
  - Complete facility metadata (security levels, types, regions)
- **Coverage**: Nationwide

#### 2. California - CDCR - 31 Facilities  
- **Data Source**: [CDCR institutions table](https://www.cdcr.ca.gov/adult-operations/list-of-adult-institutions/)
- **Implementation**: `scrapers/california.py`
- **Features**:
  - Table parsing with structured address extraction
  - Google Maps API geocoding with multiple fallbacks
  - Manual coordinate fallbacks for problematic addresses
- **Coverage**: Complete state coverage

#### 3. New York - DOCCS - 42 Facilities
- **Data Source**: [DOCCS facilities pages](https://doccs.ny.gov/facilities) (paginated)
- **Implementation**: `scrapers/new_york.py` 
- **Features**:
  - Paginated facility discovery (5 pages, 0-based indexing)
  - Detailed facility page scraping
  - Superintendent, security level, gender extraction
- **Coverage**: Complete state coverage

#### 4. Texas - TDCJ - 103 Facilities
- **Data Source**: [TDCJ unit directory](https://www.tdcj.texas.gov/unit_directory/index.html)
- **Implementation**: `scrapers/texas.py`
- **Features**:
  - Comprehensive unit directory table parsing
  - Extensive facility detail extraction (capacity, staffing, programs)
  - SSL certificate handling for problematic sites
  - Rich operational data (147,270 total system capacity)
- **Coverage**: Complete state coverage

#### 5. Illinois - IDOC - 29 Facilities
- **Data Source**: [IDOC facility pages](https://idoc.illinois.gov/facilities/correctionalfacilities.html)
- **Implementation**: `scrapers/illinois.py`
- **Features**:
  - Content fragment parsing from individual facility pages
  - Enhanced address parsing with robust fallback logic
  - 100% geocoding success rate
  - Complete facility metadata (warden, capacity, population, programs)
- **Coverage**: Complete state coverage

#### 6. Florida - FDC - 77 Facilities
- **Data Source**: [FDC facility directory](https://www.fdc.myflorida.com/facilities/)
- **Implementation**: `scrapers/florida.py`
- **Features**:
  - Comprehensive facility list parsing
  - Individual facility page scraping
  - 100% geocoding success rate
  - Complete facility metadata (capacity, security levels, programs)
- **Coverage**: Complete state coverage

#### 7. Pennsylvania - PA DOC - 24 Facilities
- **Data Source**: [PA DOC state prisons](https://www.pa.gov/agencies/cor/state-prisons/)
- **Implementation**: `scrapers/pennsylvania.py`
- **Features**:
  - Static navigation menu parsing
  - Individual facility page scraping with regex extraction
  - 95.8% geocoding success rate (23/24 facilities)
  - Leadership and facility statistics extraction
- **Coverage**: Complete state coverage

#### 8. Georgia - GDC - 67 Facilities
- **Data Source**: [GDC find location](https://gdc.georgia.gov/find-location)
- **Implementation**: `scrapers/georgia.py`
- **Features**:
  - JSON API data extraction from embedded map data
  - Pre-geocoded coordinates (no geocoding needed)
  - 100% coordinate coverage
  - State facility filtering (excludes county jails)
- **Coverage**: Complete state coverage

#### 9. North Carolina - DAC - 58 Facilities
- **Data Source**: [DAC CSV export](https://www.dac.nc.gov/tablefield/export/paragraph/5189/field_map_data/en/0)
- **Implementation**: `scrapers/north_carolina.py`
- **Features**:
  - Direct CSV API access with embedded HTML facility data
  - Color-coded facility type classification system
  - 96.6% address extraction success (56/58 facilities)
  - Comprehensive custody level and gender parsing
- **Coverage**: Complete state coverage

#### 10. Michigan - MDOC - 23 Facilities
- **Data Source**: [MDOC facilities directory](https://www.michigan.gov/corrections/prisons)
- **Implementation**: `scrapers/michigan.py`
- **Features**:
  - Browser headers required for access (403 protection bypass)
  - Structured facility cards with consistent individual pages
  - 56.5% geocoding success (13/23 facilities)
  - Comprehensive warden, address, security level, and program data
  - Handles both "Acting Warden" and "Warden" titles
- **Coverage**: Complete state coverage

#### 11. Virginia - VADOC - 37 Facilities
- **Data Source**: [VADOC facilities directory](https://www.vadoc.virginia.gov/facilities-and-offices)
- **Implementation**: `scrapers/virginia.py`
- **Features**:
  - Multi-line address parsing from structured facility blocks
  - 89.2% geocoding success (33/37 facilities)
  - Comprehensive facility type classification system
  - Warden/superintendent data extraction with title parsing
  - Dropdown menu integration for complete facility coverage
- **Coverage**: Complete state coverage

#### 12. Washington - WADOC - 13 Facilities
- **Data Source**: [WADOC facilities map](https://doc.wa.gov/about-doc/locations/prison-facilities/prisons-map)
- **Implementation**: `scrapers/washington.py`
- **Features**:
  - Pre-geocoded coordinates from embedded geolocation data
  - 76.9% coordinate coverage (10/13 facilities)
  - Individual facility page enhancement with capacity and custody levels
  - Dual data source integration (map + table data)
  - Comprehensive facility type classification (Penitentiary, Corrections Center, Reentry Center, etc.)
- **Coverage**: Complete state coverage

#### 13. Arizona - ADOC - 15 Facilities
- **Data Source**: [ADOC prisons directory](https://corrections.az.gov/adcrr-prisons)
- **Implementation**: `scrapers/arizona.py`
- **Features**:
  - Embedded JSON data extraction from Drupal settings
  - 100% coordinate coverage (15/15 facilities)
  - 93.3% warden coverage (14/15 facilities)
  - Individual facility page enhancement with capacity, security levels, and unit details
  - Rich facility information including warden contact details and facility descriptions
  - Comprehensive facility type classification (Prison Complex, Correctional Center, etc.)
- **Coverage**: Complete state coverage

#### 14. Tennessee - TDOC - 15 Facilities
- **Data Source**: [TDOC prison list](https://www.tn.gov/correction/state-prisons/state-prison-list.html)
- **Implementation**: `scrapers/tennessee.py`
- **Features**:
  - Regional facility organization (East, Middle, West Tennessee + Contract/Private)
  - 86.7% warden coverage with comprehensive contact information
  - 80.0% address coverage with detailed facility locations
  - Individual facility page enhancement with capacity and security levels
  - Comprehensive facility type classification (Penitentiary, Complex, Center, etc.)
  - Retry logic for connection stability
- **Coverage**: Complete state coverage

#### 15. Massachusetts - MADOC - 8 Facilities
- **Data Source**: [MADOC locations page](https://www.mass.gov/orgs/massachusetts-department-of-correction/locations)
- **Implementation**: `scrapers/massachusetts.py`
- **Features**:
  - ScrapeOps proxy integration to bypass 403 restrictions
  - Leaflet map data extraction from embedded JavaScript
  - 100% coordinate coverage with precise geocoding
  - 100% phone and address coverage
  - Comprehensive facility type classification (Pre-Release Centers, State Hospitals, Treatment Centers, etc.)
  - Robust fallback system with hardcoded data when live scraping fails
  - Advanced web scraping techniques for restrictive government websites
- **Coverage**: Complete state coverage

### ✅ Technical Features
- **Google Maps API Integration**: Primary geocoding with `GOOGLE_MAPS_API_KEY`
- **Multi-tier Geocoding Fallbacks**: Nominatim, Photon, manual coordinates
- **ScrapeOps Proxy Integration**: Bypass restrictive websites with `SCRAPE_PROXY_KEY`
- **JavaScript Data Extraction**: Parse embedded Leaflet map data and Drupal settings
- **Rate Limiting**: Respectful delays (0.1s Google API, 1s free services)
- **Error Resilience**: SSL handling, graceful failures, detailed reporting
- **Data Validation**: Coordinate bounds checking per jurisdiction
- **S3 Cloud Storage**: Automated upload to `stilesdata.com` bucket with AWS profile support
- **Public Data Access**: HTTPS URLs for JSON, CSV, and GeoJSON formats
- **Export Formats**: JSON, CSV, GeoJSON for all jurisdictions

## Next Steps - Expansion by Population

### Priority 1: Ohio (11.8M residents)
- **Target**: Ohio Department of Rehabilitation and Correction (ODRC)
- **Estimated Facilities**: ~28 facilities
- **Status**: Website currently inaccessible (404 errors)
- **Research Needed**:
  - Monitor website restoration
  - Identify alternative data sources
  - Check for API endpoints or structured data
- **Implementation**: Create `scrapers/ohio.py` when data source available

### Priority 2: New Jersey (9.3M residents)
- **Target**: New Jersey Department of Corrections (NJDOC)
- **Estimated Facilities**: ~15+ facilities
- **Research Needed**:
  - Locate NJDOC facility directory
  - Analyze data availability and structure
- **Implementation**: Create `scrapers/new_jersey.py`

### Priority 3: Connecticut (3.6M residents)
- **Target**: Connecticut Department of Correction (CTDOC)
- **Estimated Facilities**: ~15+ facilities
- **Research Needed**:
  - Locate CTDOC facility directory
  - Analyze data availability and structure
- **Implementation**: Create `scrapers/connecticut.py`

## Advanced Features - Future Enhancements

### OpenStreetMap Integration for Local Facilities
- **Concept**: Use OSM data to discover local jails, detention centers
- **Benefits**: 
  - County-level facility coverage
  - Municipal jail systems
  - Immigration detention facilities
- **Challenges**:
  - Data quality/completeness varies by region
  - Need to filter/validate correctional facilities
  - May require manual verification
- **Implementation Approach**:
  - Query OSM Overpass API for `amenity=prison` tags
  - Cross-reference with known facility lists
  - Implement data quality scoring system

### Data Enhancement Opportunities
1. **Population Data**: Real-time or recent inmate counts
2. **Operational Status**: Active/closed facility tracking  
3. **Historical Data**: Track facility changes over time
4. **Additional Metadata**: Security classifications, special programs
5. **Contact Information**: Visiting hours, contact details

### System Improvements
1. **Caching Layer**: Reduce redundant requests during development
2. **Data Validation**: Automated quality checks and anomaly detection
3. **Update Scheduling**: Automated periodic data refreshes
4. **API Development**: REST API for accessing collected data
5. **Visualization**: Web interface for exploring facility data

## Architecture Notes

### Scraper Pattern
Each jurisdiction scraper follows this pattern:
```python
class JurisdictionScraper:
    def __init__(self): # Setup headers, URLs
    def scrape_facility_list(self): # Get facility URLs/basic info
    def scrape_facility_details(self, url): # Extract detailed info
    def geocode_address(self, address): # Add coordinates
    def scrape_all(self): # Orchestrate full collection
```

### Data Schema Consistency
All scrapers should provide these core fields:
- `name`: Facility name
- `jurisdiction`: State/Federal
- `agency`: Controlling agency (BOP, CDCR, etc.)
- `city`, `state`, `zip_code`: Location info
- `latitude`, `longitude`: Coordinates
- `facility_url`: Source page URL

### Geocoding Strategy
1. Google Maps API (if `GOOGLE_MAPS_API_KEY` available)
2. OpenStreetMap Nominatim (free fallback)
3. Photon geocoding service (alternative free)
4. Manual coordinates (jurisdiction-specific fallbacks)

## Development Guidelines

### Adding New Jurisdictions
1. Research data sources and structure
2. Create `scrapers/new_jurisdiction.py` following the pattern
3. Add to `scrapers/__init__.py` imports
4. Update `fetch.py` with new scraper function
5. Add comprehensive tests and error handling
6. Update README.md with new jurisdiction info

### Code Quality Standards
- Comprehensive error handling and logging
- Rate limiting to respect source websites
- SSL/certificate issue handling where needed
- Data validation and bounds checking
- Consistent field naming across jurisdictions

### Testing Approach
- Test individual scraper components separately
- Verify geocoding accuracy with known coordinates
- Check data completeness and field consistency
- Validate export formats (JSON, CSV, GeoJSON)

## Current System Statistics

- **Total Facilities**: 476 across 8 jurisdictions
- **Geographic Coverage**: 40% of US population (132.7M residents)
- **Geocoding Success**: 100% across all jurisdictions
- **Data Formats**: JSON, CSV, GeoJSON for all
- **Known Capacity**: 147,270+ inmates (Texas data available)

## Repository Structure
```
prisons/
├── fetch.py                 # Main orchestrator script
├── s3_upload.py            # S3 cloud storage uploader
├── scrapers/               # Jurisdiction-specific modules
│   ├── __init__.py
│   ├── federal.py          # BOP scraper
│   ├── california.py       # CDCR scraper  
│   ├── new_york.py         # DOCCS scraper
│   ├── texas.py            # TDCJ scraper
│   ├── illinois.py         # IDOC scraper
│   ├── florida.py          # FDC scraper
│   ├── pennsylvania.py     # PA DOC scraper
│   ├── georgia.py          # GDC scraper
│   ├── north_carolina.py   # DAC scraper
│   ├── michigan.py         # MDOC scraper
│   ├── virginia.py         # VADOC scraper
│   ├── washington.py       # WADOC scraper
│   └── arizona.py          # ADOC scraper
├── data/                   # Output data by jurisdiction
│   ├── federal/
│   ├── california/
│   ├── new_york/
│   ├── texas/
│   ├── illinois/
│   ├── florida/
│   ├── pennsylvania/
│   ├── georgia/
│   ├── north_carolina/
│   ├── michigan/
│   ├── virginia/
│   ├── washington/
│   └── arizona/
├── README.md               # User documentation
├── PLANNING.md             # This file
└── requirements.txt        # Python dependencies
```

This planning document should be updated as new jurisdictions are added and features are implemented.
