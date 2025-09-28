# Changelog

All notable changes to the Prison Data Scraper project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
