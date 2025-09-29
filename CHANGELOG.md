# Changelog

All notable changes to the Prison Data Scraper project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.11.0] - 2025-09-29

### Added
- **Missouri Department of Corrections (MODOC) scraper** - 19 facilities
  - Advanced multi-source data integration (facilities + warden pages)
  - Facility acronym system (ACC, BCC, CCC, etc.) for precise identification
  - 100% coordinate coverage with perfect geocoding
  - 100% phone and address coverage
  - 94.7% warden coverage (18/19 facilities, 1 vacant position)
  - Pagination support for scalable data collection
  - Intelligent data filtering (excludes probation offices)
  - Comprehensive security level classifications (Minimum, Medium, Maximum, Diagnostic)
  - Specialized facility types (Treatment Centers, Reception Centers, etc.)

### Changed
- Updated total coverage to **714 facilities across 18 jurisdictions**
- Enhanced README table with Missouri inclusion
- Improved multi-source data merging capabilities
- Added facility acronym tracking for precise facility identification

### Technical
- Implemented advanced data merging by facility acronym
- Added robust pagination handling for multi-page facility listings
- Enhanced facility type classification algorithms
- Improved data filtering to focus on correctional institutions

## [0.10.0] - 2025-09-29

### Added
- **Maryland Department of Public Safety and Correctional Services (DPSCS) scraper** - 13 facilities
  - SSL certificate bypass for problematic government websites
  - Complex text parsing from unstructured contact information
  - 69.2% coordinate coverage with multi-tier geocoding
  - 84.6% phone coverage and 76.9% address coverage
  - 100% warden coverage with comprehensive staff information
  - Historical data extraction (facility opening years dating to 1932)
  - Security level and facility classification parsing
  - Staff hierarchy extraction (wardens, assistant wardens, administrators)

### Changed
- Updated total coverage to **695 facilities across 17 jurisdictions**
- Enhanced README table with Maryland inclusion
- Improved SSL handling for government websites with certificate issues
- Added comprehensive staff data extraction capabilities

### Technical
- Implemented SSL certificate verification bypass
- Enhanced unstructured text parsing for contact information
- Added staff hierarchy extraction algorithms
- Improved facility details parsing (security levels, opening years)

## [0.9.0] - 2025-09-28

### Added
- **Massachusetts Department of Correction (MADOC) scraper** - 8 facilities
  - ScrapeOps proxy integration to bypass 403 restrictions
  - Leaflet map data extraction from embedded JavaScript
  - 100% coordinate coverage with precise geocoding
  - 100% phone and address coverage
  - Comprehensive facility type classification (Pre-Release Centers, State Hospitals, Treatment Centers, etc.)
  - Robust fallback system with hardcoded data when live scraping fails
  - Advanced web scraping techniques for restrictive government websites

### Changed
- Updated total coverage to **664 facilities across 15 jurisdictions**
- Enhanced README table with Massachusetts inclusion
- Improved proxy-based scraping capabilities for blocked websites
- Added ScrapeOps proxy support as environment variable option

### Technical
- Implemented multi-tier data access (proxy → fallback)
- Added JavaScript data extraction capabilities
- Enhanced facility type detection algorithms
- Improved error handling for government website restrictions

## [0.8.0] - 2025-09-28

### Added
- **Tennessee Department of Correction (TDOC) scraper** - 15 facilities
  - Regional facility organization (East, Middle, West Tennessee + Contract/Private)
  - 86.7% warden coverage with comprehensive contact information
  - 80.0% address coverage with detailed facility locations
  - Individual facility page enhancement with capacity and security levels
  - Comprehensive facility type classification (Penitentiary, Complex, Center, etc.)
  - Retry logic for connection stability

### Changed
- Updated total coverage to **656 facilities across 14 jurisdictions**
- Enhanced README table with Tennessee inclusion
- Improved connection handling with retry mechanisms

## [0.7.0] - 2025-09-28

### Added
- **Arizona Department of Corrections (ADOC) scraper** - 15 facilities
  - Embedded JSON data extraction from Drupal settings
  - 100% coordinate coverage (pre-geocoded data)
  - 93.3% warden coverage with contact details
  - Individual facility page enhancement with capacity, security levels, and unit details
  - Rich facility information including warden profiles and descriptions
- **Automated README table generation** (`update_readme_table.py`)
  - Dynamic facility count updates from CSV data
  - Sorted table by facility count (high to low)
  - Automated total coverage calculation

### Changed
- **Simplified README table structure** - Removed confusing population column, added clear facility counts
- Updated total coverage to **641 facilities across 13 jurisdictions**
- Enhanced table readability with facility-count-based sorting
- Streamlined documentation with automated table maintenance

## [0.6.0] - 2025-09-28

### Added
- **Washington Department of Corrections (WADOC) scraper** - 13 facilities
  - Pre-geocoded coordinates from embedded geolocation data
  - 76.9% coordinate coverage (10/13 facilities)
  - Individual facility page enhancement with capacity and custody levels
  - Dual data source integration (map + table data)
  - Comprehensive facility type classification (Penitentiary, Corrections Center, Reentry Center)

### Changed
- Updated total coverage to **549 facilities across 11 jurisdictions (47% US population)**
- Enhanced next steps priorities (Ohio postponed due to website issues, New Jersey moved up)

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

### v0.11.0 Achievements
- **714 total facilities** across **18 jurisdictions**
- **Advanced multi-source data integration** (Missouri's facilities + warden pages)
- **Perfect data quality** (Missouri: 100% coordinates, phones, addresses)
- **SSL certificate handling** for problematic government websites
- **Facility acronym systems** for precise identification
- **Comprehensive staff hierarchies** (wardens, assistants, administrators)
- **Historical facility data** (opening years dating to 1932)
- **S3 cloud storage** with public data access at `https://stilesdata.com/prisons/`

### Technical Evolution
- **v0.1.0**: Basic scraping (4 jurisdictions, 298 facilities)
- **v0.2.0**: Enhanced parsing (5 jurisdictions, 327 facilities) 
- **v0.3.0**: Multi-state expansion (7 jurisdictions, 418 facilities)
- **v0.4.0**: Advanced geocoding (8 jurisdictions, 476 facilities)
- **v0.5.0**: Cloud integration (9 jurisdictions, 499 facilities)
- **v0.6.0**: Pre-geocoded sources (11 jurisdictions, 549 facilities)
- **v0.7.0**: Automated documentation (13 jurisdictions, 641 facilities)
- **v0.8.0**: Regional organization (14 jurisdictions, 656 facilities)
- **v0.9.0**: Proxy integration (15 jurisdictions, 664 facilities)
- **v0.10.0**: SSL handling (17 jurisdictions, 695 facilities)
- **v0.11.0**: Multi-source integration (18 jurisdictions, 714 facilities)
