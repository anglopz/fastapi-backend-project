# Changelog

All notable changes to the FastShip API project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.2.0] - 2026-01-08

### Added
- Section 30: API Testing Enhancements
  - Centralized test data module (`tests/example.py`)
  - Authentication fixtures (seller_token, partner_token, client_with_auth)
  - ASGITransport for better FastAPI testing
  - Session-scoped fixtures for performance
- Database initialization script (`scripts/init_db.py`)
- Comprehensive API documentation (Section 28)
  - General metadata (contact, license, servers)
  - Endpoint metadata (12 endpoints documented)
  - Model metadata (11 schemas documented)
  - 30+ response examples

### Fixed
- Exception handler print shadowing bug
- Import errors in test files (relative imports)
- Database initialization (all models now imported)
- Test compatibility with new fixtures

### Changed
- Enhanced `create_db_tables()` to import all models
- Updated test infrastructure with new fixtures
- Improved error handling documentation

## [1.1.0] - 2026-01-07

### Added
- Section 27: API Middleware
  - Request logging with performance metrics
  - Request ID generation and tracking
  - Async logging via Celery
  - Response headers (X-Request-ID)
- Section 26: Error Handling
  - Custom exception hierarchy (FastShipError)
  - Automatic exception handler registration
  - Consistent JSON error responses
  - Domain-specific exceptions
- Section 24: Celery Integration
  - Distributed task queue with Redis
  - Background email/SMS tasks
  - Task retry logic with exponential backoff
  - Celery worker container

### Changed
- Replaced FastAPI BackgroundTasks with Celery
- Enhanced error handling system
- Improved request logging

## [1.0.0] - 2025-12-30

### Added
- Section 20: Email Confirmation
  - Email verification for sellers and partners
  - Redis token storage (24-hour expiry)
  - Rate-limited confirmation attempts
- Section 21: Password Reset
  - Secure password reset functionality
  - Reset tokens with expiration (1 hour)
  - Email notifications
- Section 22: SMS Verification
  - Twilio SMS integration
  - 6-digit verification codes
  - Email fallback when phone not provided
- Section 23: Review System
  - 5-star rating system
  - Token-based review submission
  - One review per shipment enforcement
  - HTML review form

### Changed
- Added client contact fields to shipments (email required, phone optional)
- Enhanced email service with SMS support

## [0.9.0] - 2025-12-22

### Added
- Core API functionality
- JWT authentication (sellers and delivery partners)
- Shipment management
- PostgreSQL database with UUID support
- Redis integration (cache and token blacklist)
- Docker Compose setup
- Basic test suite

### Changed
- Unified security configuration
- Cleaned up main.py structure
- Improved code organization

---

## Version History

- **1.2.0**: Sections 24-30 complete, production-ready
- **1.1.0**: Infrastructure enhancements (Celery, middleware, error handling)
- **1.0.0**: Authentication enhancements (email, SMS, reviews)
- **0.9.0**: Initial release with core functionality

---

**Format**: [Version] - Date  
**Categories**: Added, Changed, Deprecated, Removed, Fixed, Security

