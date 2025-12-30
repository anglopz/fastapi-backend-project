# Codebase Snapshot - Pre Advanced Sections

## Key Directories
app/
├── api/           # Routers, schemas, dependencies
├── core/          # Security, exceptions, mail
├── database/      # Models (UUID), session, redis
├── services/      # BaseService, UserService patterns
├── templates/     # HTML templates (Section 19)
└── tasks.py       # Background tasks

## Architectural Patterns
- UUID primary keys
- BaseService/UserService inheritance
- Dependency injection
- JWT authentication (Seller/Partner separate)
- Redis token blacklist
- PostgreSQL with Alembic
- Docker with healthchecks

## Integration Points for New Sections
1. Email: Use app/core/mail.py
2. Auth: Extend app/core/security.py  
3. Tasks: Use app/tasks.py or replace with Celery
4. Models: Add to app/database/models.py
5. Services: Follow BaseService pattern
