# Changelog

All notable changes to the Prison Data Scraper project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.5.0] - 2024-09-28

### Added
- **S3 Cloud Storage Integration**: Automated upload to `stilesdata.com` bucket
  - AWS profile support using `AWS_PROFILE_NAME` environment variable
  - Public data access at `https://stilesdata.com/prisons/{jurisdiction}/`
  - Standalone S3 upload utility (`s3_upload.py`)
  - Integrated upload option (`--upload-s3` flag)
- **Michigan Department of Corrections (MDOC) scraper** - 23 facilities
  - Browser headers required for 403 protection bypass
  - Comprehensive warden, address, security level data extraction
  - 56.5% geocoding success rate

### Changed
- Updated total coverage to **499 facilities across 9 jurisdictions (42% US population)**
- Enhanced documentation with S3 usage examples and public URLs
- Updated repository structure to include S3 upload functionality

## [0.4.0] - 2024-09-28

### Added
- **North Carolina Department of Adult Correction (DAC) scraper** - 58 facilities
  - Direct CSV API access with embedded HTML facility data
  - Color-coded facility type classification system
  - 96.6% address extraction success (56/58 facilities)
  - Comprehensive custody level and gender parsing
- Multi-service geocoding fallback system (Google Maps API, Nominatim, Photon)

### Changed
- Updated total coverage to **476 facilities across 8 jurisdictions (40% US population)**

## [0.3.0] - 2024-09-28

### Added
- **Georgia Department of Corrections (GDC) scraper** - 67 facilities
  - JSON data extraction from embedded map features
  - Pre-geocoded coordinates (100% coordinate coverage)
  - State facility filtering (excludes county jails)
- **Pennsylvania Department of Corrections (PA DOC) scraper** - 24 facilities
  - Dynamic facility directory parsing from side navigation
  - Comprehensive leadership data (superintendents, deputies, business managers)
  - Facility statistics (acres, structures, housing units, employees)
  - 95.8% geocoding success rate (23/24 facilities)
- **Florida Department of Corrections (FDC) scraper** - 77 facilities
  - Advanced facility list extraction with multiple parsing strategies
  - Comprehensive facility data including capacity, population, and programs
  - Enhanced address parsing with fallback mechanisms

### Changed
- Updated total coverage to **418 facilities across 7 jurisdictions (37% US population)**
- Enhanced geocoding system with multiple service fallbacks
- Improved error handling and data validation

## [0.2.0] - 2024-09-28

### Added
- Illinois Department of Corrections (IDOC) scraper
- Support for 29 Illinois correctional facilities
- Enhanced address parsing with robust fallback logic for complex address blocks
- Content fragment parsing for facility-specific data extraction
- 100% geocoding success rate for Illinois facilities

### Changed
- Updated README.md to include Illinois jurisdiction
- Updated PLANNING.md with Illinois implementation details
- Reorganized next steps priorities (Florida now Priority 1)

### Technical Details
- Illinois scraper handles multi-fragment facility pages
- Enhanced address parsing skips labels, PO Boxes, and phone numbers
- Combines data from multiple content fragments per facility page
- Extracts warden, capacity, population, security level, and program data

## [0.1.0] - 2024-09-27

### Added
- Initial project setup with modular architecture
- Federal Bureau of Prisons (BOP) scraper - 122 facilities
- California Department of Corrections (CDCR) scraper - 31 facilities  
- New York Department of Corrections (DOCCS) scraper - 42 facilities
- Texas Department of Criminal Justice (TDCJ) scraper - 103 facilities
- Unified command-line interface (`fetch.py`)
- Multi-tier geocoding system (Google Maps API, Nominatim, Photon)
- Export to JSON, CSV, and GeoJSON formats
- Comprehensive facility data extraction including:
  - Basic information (name, type, security level)
  - Location data with coordinates
  - Contact information
  - Operational data (capacity, population, programs)
  - Administrative details (wardens, staff counts)

### Technical Features
- Modular scraper architecture with jurisdiction-specific modules
- Rate limiting and respectful scraping practices
- SSL certificate handling for problematic sites
- Address parsing and validation
- Coordinate bounds checking per jurisdiction
- Error handling and graceful failure recovery

### Coverage
- 298 total facilities across 4 jurisdictions
- 27% of US population coverage (88.8M residents)
- 100% geocoding success rate across all jurisdictions

---

## Project Milestones

### v0.5.0 Achievements
- **499 total facilities** across **9 jurisdictions**
- **42% US population coverage** (139.5M residents)
- **S3 cloud storage** with public data access
- **Advanced geocoding** with multi-service fallbacks
- **Comprehensive data formats** (JSON, CSV, GeoJSON)

### Technical Evolution
- **v0.1.0**: Basic scraping (4 jurisdictions, 298 facilities)
- **v0.2.0**: Enhanced parsing (5 jurisdictions, 327 facilities) 
- **v0.3.0**: Multi-state expansion (7 jurisdictions, 418 facilities)
- **v0.4.0**: Advanced geocoding (8 jurisdictions, 476 facilities)
- **v0.5.0**: Cloud integration (9 jurisdictions, 499 facilities)
