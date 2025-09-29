# US prison location scraper

Collects data about correctional facilities from multiple jurisdictions, starting with federal prisons and expanding to state systems. This project is a work in progress. 

## Coverage so far

| Jurisdiction | Agency | Facilities | Institutions data |
|--------------|--------|------------|------|
| **Federal** | Bureau of Prisons (BOP) | 122 | [CSV](https://stilesdata.com/prisons/federal/federal_prisons.csv) \| [JSON](https://stilesdata.com/prisons/federal/federal_prisons.json) \| [GeoJSON](https://stilesdata.com/prisons/federal/federal_prisons.geojson) |
| **Texas** | Dept. of Criminal Justice (TDCJ) | 103 | [CSV](https://stilesdata.com/prisons/texas/texas_prisons.csv) \| [JSON](https://stilesdata.com/prisons/texas/texas_prisons.json) \| [GeoJSON](https://stilesdata.com/prisons/texas/texas_prisons.geojson) |
| **Florida** | Dept. of Corrections (FDC) | 77 | [CSV](https://stilesdata.com/prisons/florida/florida_prisons.csv) \| [JSON](https://stilesdata.com/prisons/florida/florida_prisons.json) \| [GeoJSON](https://stilesdata.com/prisons/florida/florida_prisons.geojson) |
| **Georgia** | Dept. of Corrections (GDC) | 67 | [CSV](https://stilesdata.com/prisons/georgia/georgia_prisons.csv) \| [JSON](https://stilesdata.com/prisons/georgia/georgia_prisons.json) \| [GeoJSON](https://stilesdata.com/prisons/georgia/georgia_prisons.geojson) |
| **North Carolina** | Dept. of Adult Correction (DAC) | 58 | [CSV](https://stilesdata.com/prisons/north_carolina/north_carolina_prisons.csv) \| [JSON](https://stilesdata.com/prisons/north_carolina/north_carolina_prisons.json) \| [GeoJSON](https://stilesdata.com/prisons/north_carolina/north_carolina_prisons.geojson) |
| **New York** | Dept. of Corrections and Community Supervision (DOCCS) | 42 | [CSV](https://stilesdata.com/prisons/new_york/new_york_prisons.csv) \| [JSON](https://stilesdata.com/prisons/new_york/new_york_prisons.json) \| [GeoJSON](https://stilesdata.com/prisons/new_york/new_york_prisons.geojson) |
| **Virginia** | Dept. of Corrections (VADOC) | 37 | [CSV](https://stilesdata.com/prisons/virginia/virginia_prisons.csv) \| [JSON](https://stilesdata.com/prisons/virginia/virginia_prisons.json) \| [GeoJSON](https://stilesdata.com/prisons/virginia/virginia_prisons.geojson) |
| **California** | Dept. of Corrections and Rehabilitation (CDCR) | 31 | [CSV](https://stilesdata.com/prisons/california/california_prisons.csv) \| [JSON](https://stilesdata.com/prisons/california/california_prisons.json) \| [GeoJSON](https://stilesdata.com/prisons/california/california_prisons.geojson) |
| **Illinois** | Dept. of Corrections (IDOC) | 29 | [CSV](https://stilesdata.com/prisons/illinois/illinois_prisons.csv) \| [JSON](https://stilesdata.com/prisons/illinois/illinois_prisons.json) \| [GeoJSON](https://stilesdata.com/prisons/illinois/illinois_prisons.geojson) |
| **Pennsylvania** | Dept. of Corrections (PA DOC) | 24 | [CSV](https://stilesdata.com/prisons/pennsylvania/pennsylvania_prisons.csv) \| [JSON](https://stilesdata.com/prisons/pennsylvania/pennsylvania_prisons.json) \| [GeoJSON](https://stilesdata.com/prisons/pennsylvania/pennsylvania_prisons.geojson) |
| **Michigan** | Dept. of Corrections (MDOC) | 23 | [CSV](https://stilesdata.com/prisons/michigan/michigan_prisons.csv) \| [JSON](https://stilesdata.com/prisons/michigan/michigan_prisons.json) \| [GeoJSON](https://stilesdata.com/prisons/michigan/michigan_prisons.geojson) |
| **Missouri** | Dept. of Corrections (MODOC) | 19 | [CSV](https://stilesdata.com/prisons/missouri/missouri_prisons.csv) \| [JSON](https://stilesdata.com/prisons/missouri/missouri_prisons.json) \| [GeoJSON](https://stilesdata.com/prisons/missouri/missouri_prisons.geojson) |
| **Indiana** | Dept. of Correction (IDOC) | 18 | [CSV](https://stilesdata.com/prisons/indiana/indiana_prisons.csv) \| [JSON](https://stilesdata.com/prisons/indiana/indiana_prisons.json) \| [GeoJSON](https://stilesdata.com/prisons/indiana/indiana_prisons.geojson) |
| **Arizona** | Dept. of Corrections (ADOC) | 15 | [CSV](https://stilesdata.com/prisons/arizona/arizona_prisons.csv) \| [JSON](https://stilesdata.com/prisons/arizona/arizona_prisons.json) \| [GeoJSON](https://stilesdata.com/prisons/arizona/arizona_prisons.geojson) |
| **Tennessee** | Dept. of Correction (TDOC) | 15 | [CSV](https://stilesdata.com/prisons/tennessee/tennessee_prisons.csv) \| [JSON](https://stilesdata.com/prisons/tennessee/tennessee_prisons.json) \| [GeoJSON](https://stilesdata.com/prisons/tennessee/tennessee_prisons.geojson) |
| **Washington** | Dept. of Corrections (WADOC) | 13 | [CSV](https://stilesdata.com/prisons/washington/washington_prisons.csv) \| [JSON](https://stilesdata.com/prisons/washington/washington_prisons.json) \| [GeoJSON](https://stilesdata.com/prisons/washington/washington_prisons.geojson) |
| **Maryland** | Dept. of Public Safety and Correctional Services (DPSCS) | 13 | [CSV](https://stilesdata.com/prisons/maryland/maryland_prisons.csv) \| [JSON](https://stilesdata.com/prisons/maryland/maryland_prisons.json) \| [GeoJSON](https://stilesdata.com/prisons/maryland/maryland_prisons.geojson) |
| **Massachusetts** | Dept. of Correction (MADOC) | 8 | [CSV](https://stilesdata.com/prisons/massachusetts/massachusetts_prisons.csv) \| [JSON](https://stilesdata.com/prisons/massachusetts/massachusetts_prisons.json) \| [GeoJSON](https://stilesdata.com/prisons/massachusetts/massachusetts_prisons.geojson) |

**Total Coverage**: 714 facilities across 18 jurisdictions

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
python fetch.py --states texas,illinois,north_carolina,michigan,virginia,washington,arizona,massachusetts

# Upload to S3 after scraping
python fetch.py --states michigan --upload-s3
```

## S3 data storage

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

**Public data access**: All data is available at `https://stilesdata.com/prisons/` with the following structure:
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
