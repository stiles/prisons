# Prison Data Scraper

Collects comprehensive data about correctional facilities from multiple jurisdictions, starting with federal prisons and expanding to state systems.

## Coverage

| Jurisdiction | Agency | Facilities | Population | Status |
|--------------|--------|------------|------------|---------|
| **Federal** | Bureau of Prisons (BOP) | 122 | 334.2M | ✅ Complete |
| **California** | Dept. of Corrections and Rehabilitation (CDCR) | 31 | 39.0M | ✅ Complete |
| **Texas** | Dept. of Criminal Justice (TDCJ) | 103 | 30.0M | ✅ Complete |
| **New York** | Dept. of Corrections and Community Supervision (DOCCS) | 42 | 19.3M | ✅ Complete |
| **Illinois** | Dept. of Corrections (IDOC) | 29 | 12.8M | ✅ Complete |
| **Florida** | Dept. of Corrections (FDC) | 77 | 22.6M | ✅ Complete |
| **Pennsylvania** | Dept. of Corrections (PA DOC) | 24 | 13.0M | ✅ Complete |
| **Georgia** | Dept. of Corrections (GDC) | 67 | 10.9M | ✅ Complete |
| **North Carolina** | Dept. of Adult Correction (DAC) | 58 | 10.7M | ✅ Complete |
| **Michigan** | Dept. of Corrections (MDOC) | 23 | 10.0M | ✅ Complete |

**Total Coverage**: 499 facilities across 9 jurisdictions (42% of US population)

## How it works

The scraper uses a modular architecture where each jurisdiction has its own specialized scraper module that handles the unique data sources and formats for that system. Each scraper discovers facility lists, extracts detailed information from individual facility pages, and geocodes addresses to provide precise coordinates.

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
python fetch.py --states north_carolina
python fetch.py --states federal
python fetch.py --states texas,illinois,north_carolina,michigan

# Upload to S3 after scraping
python fetch.py --states michigan --upload-s3
```

## S3 Data Storage

The system can automatically upload data to S3 for public access:

```bash
# Upload all existing data to S3
python s3_upload.py

# Upload with custom bucket
python s3_upload.py --bucket my-bucket-name

# List current S3 contents
python s3_upload.py --list

# Generate public URLs for a jurisdiction
python s3_upload.py --urls michigan
```

**Public Data Access**: All data is available at `https://stilesdata.com/prisons/` with the following structure:
- `https://stilesdata.com/prisons/{jurisdiction}/{jurisdiction}_prisons.json`
- `https://stilesdata.com/prisons/{jurisdiction}/{jurisdiction}_prisons.csv` 
- `https://stilesdata.com/prisons/{jurisdiction}/{jurisdiction}_prisons.geojson`

## Output structure

Data is organized by jurisdiction in the `data/` directory. Each jurisdiction exports three formats:

```
data/
├── {jurisdiction}/
│   ├── {jurisdiction}_prisons.json    # Complete facility data
│   ├── {jurisdiction}_prisons.csv     # Tabular format
│   └── {jurisdiction}_prisons.geojson # Geo format
```

## Data fields

All facilities include core location data (name, address, coordinates) and jurisdiction information. Additional fields vary by system but commonly include:

- **Basic info**: Facility codes, types, security levels, operational status
- **Location**: Street addresses, cities, counties, regions, precise coordinates
- **Contact**: Phone numbers, email addresses, facility websites
- **Operational**: Capacity, current population, gender restrictions, custody levels
- **Administrative**: Wardens/superintendents, staff counts, operational costs
- **Programs**: Educational, vocational, and rehabilitation programs
- **Infrastructure**: Housing units, medical facilities, special populations

The level of detail varies significantly between jurisdictions based on data availability from official sources.

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

Geographic coordinates for each location is obtained by using the Google Maps Geocoding API if a `GOOGLE_MAPS_API_KEY` environment variable is set. In some cases, coordinates were obtained from the prison agencies themselves. 