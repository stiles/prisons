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

### ✅ Implemented Jurisdictions (327 Total Facilities)

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

### ✅ Technical Features
- **Google Maps API Integration**: Primary geocoding with `GOOGLE_MAPS_API_KEY`
- **Multi-tier Geocoding Fallbacks**: Nominatim, Photon, manual coordinates
- **Rate Limiting**: Respectful delays (0.1s Google API, 1s free services)
- **Error Resilience**: SSL handling, graceful failures, detailed reporting
- **Data Validation**: Coordinate bounds checking per jurisdiction
- **Export Formats**: JSON, CSV, GeoJSON for all jurisdictions

## Next Steps - Expansion by Population

### Priority 1: Florida (22.6M residents) 
- **Target**: Florida Department of Corrections (FDC)
- **Estimated Facilities**: ~50+ facilities (large system)
- **Research Needed**:
  - Locate FDC facility directory
  - Analyze data availability and structure
  - Check for API endpoints or structured data
- **Implementation**: Create `scrapers/florida.py`

### Priority 2: Pennsylvania (13.0M residents)
- **Target**: Pennsylvania Department of Corrections (PA DOC)
- **Estimated Facilities**: ~25-30 facilities
- **Future consideration after Florida**

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

- **Total Facilities**: 327 across 5 jurisdictions
- **Geographic Coverage**: 31% of US population (101.6M residents)
- **Geocoding Success**: 100% across all jurisdictions
- **Data Formats**: JSON, CSV, GeoJSON for all
- **Known Capacity**: 147,270+ inmates (Texas data available)

## Repository Structure
```
prisons/
├── fetch.py                 # Main orchestrator script
├── scrapers/               # Jurisdiction-specific modules
│   ├── __init__.py
│   ├── federal.py          # BOP scraper
│   ├── california.py       # CDCR scraper  
│   ├── new_york.py         # DOCCS scraper
│   ├── texas.py            # TDCJ scraper
│   ├── illinois.py         # IDOC scraper
│   └── florida.py          # FDC scraper (planned)
├── data/                   # Output data by jurisdiction
│   ├── federal/
│   ├── california/
│   ├── new_york/
│   ├── texas/
│   └── illinois/
├── README.md               # User documentation
├── PLANNING.md             # This file
└── requirements.txt        # Python dependencies
```

This planning document should be updated as new jurisdictions are added and features are implemented.
