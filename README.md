# Prison Data Scraper

Collects comprehensive data about correctional facilities from multiple jurisdictions, starting with federal prisons and expanding to state systems.

## Supported jurisdictions

- **Federal**: Bureau of Prisons (BOP) facilities - 122 facilities
- **California**: California Department of Corrections and Rehabilitation (CDCR) - 31 facilities  
- **New York**: New York Department of Corrections and Community Supervision (DOCCS) - 42 facilities
- **Texas**: Texas Department of Criminal Justice (TDCJ) - 103 facilities
- **Illinois**: Illinois Department of Corrections (IDOC) - 29 facilities

## How it works

The scraper uses a modular architecture with jurisdiction-specific modules that handle the unique data sources and formats for each system:

- **Federal**: Dynamically scrapes facility codes from the [BOP facilities list](https://www.bop.gov/locations/list.jsp) and fetches detailed data via their internal API
- **California**: Parses facility data from the [CDCR institutions table](https://www.cdcr.ca.gov/adult-operations/list-of-adult-institutions/)
- **New York**: Scrapes paginated facility listings from [DOCCS facilities pages](https://doccs.ny.gov/facilities) and extracts detailed information from individual facility pages
- **Texas**: Scrapes the comprehensive [TDCJ unit directory table](https://www.tdcj.texas.gov/unit_directory/index.html) and detailed facility pages with extensive operational data
- **Illinois**: Parses facility content fragments from [IDOC facility pages](https://idoc.illinois.gov/facilities/correctionalfacilities.html) with enhanced address parsing for 100% geocoding success

## Usage

Install dependencies:
```bash
pip install -r requirements.txt
```

Scrape all supported jurisdictions:
```bash
python fetch.py
```

Scrape specific jurisdictions:
```bash
python fetch.py --states federal,california,new_york,texas,illinois
python fetch.py --states california
python fetch.py --states federal
python fetch.py --states new_york
python fetch.py --states texas
python fetch.py --states illinois
```

## Output structure

Data is organized by jurisdiction in the `data/` directory:

```
data/
├── federal/
│   ├── federal_prisons.json
│   ├── federal_prisons.csv
│   └── federal_prisons.geojson
├── california/
│   ├── california_prisons.json
│   ├── california_prisons.csv
│   └── california_prisons.geojson
├── new_york/
│   ├── new_york_prisons.json
│   ├── new_york_prisons.csv
│   └── new_york_prisons.geojson
├── texas/
│   ├── texas_prisons.json
│   ├── texas_prisons.csv
│   └── texas_prisons.geojson
└── illinois/
    ├── illinois_prisons.json
    ├── illinois_prisons.csv
    └── illinois_prisons.geojson
```

## Data fields

### Federal facilities
- Basic info: code, name, type, security level, population
- Location: address, city, state, zip, coordinates, timezone, region
- Contact: phone, email, URL
- Operational: gender restrictions, special populations, camp facilities

### California facilities  
- Basic info: name, acronym, jurisdiction, agency
- Location: street address, city, state, zip code, coordinates
- Contact: phone number
- Links: facility detail page URLs

### New York facilities
- Basic info: name, jurisdiction, agency, superintendent
- Location: street address, city, state, zip code, coordinates, counties served
- Contact: phone number
- Operational: security level, gender restrictions
- Links: facility detail page URLs

### Texas facilities
- Basic info: name, unit code, jurisdiction, agency, unit full name
- Location: street address, city, state, zip code, coordinates, region, county
- Contact: phone number, location description
- Operational: facility type, gender, capacity, custody levels, operator
- Staffing: total employees, security staff, non-security staff, medical staff
- Programs: educational programs, additional programs, volunteer initiatives
- Operations: agricultural operations, manufacturing, facility operations
- Links: facility detail page URLs

### Illinois facilities
- Basic info: name, jurisdiction, agency
- Location: street address, city, state, zip code, coordinates
- Contact: phone number, fax number
- Operational: security level, gender, capacity, population, opened date
- Administrative: warden name, cost per individual
- Programs: academic programs, career/technical education, other programs
- Links: facility detail page URLs

## Technical details

- **Modular architecture**: Each jurisdiction has its own scraper module
- **Unified interface**: Single command-line tool handles all jurisdictions
- **Consistent output**: All scrapers export JSON, CSV, and GeoJSON formats
- **Advanced geocoding**: Uses Google Maps API (if `GOOGLE_MAPS_API_KEY` available) with OpenStreetMap fallbacks
- **Rate limiting**: Respectful delays between requests
- **Error handling**: Graceful failure handling with detailed reporting
- **Extensible design**: Easy to add new states and jurisdictions

The scraper automatically adapts to facility changes and respects each website through appropriate rate limits and proper request patterns.

### Geocoding

California facilities are geocoded using multiple methods for maximum accuracy:

1. **Google Maps Geocoding API** (primary, if `GOOGLE_MAPS_API_KEY` environment variable is set)
2. **OpenStreetMap Nominatim** (fallback)
3. **Photon geocoding service** (fallback)
4. **Manual coordinates** (final fallback for known problematic addresses)

This ensures 100% geocoding success rate for mapping and spatial analysis.
