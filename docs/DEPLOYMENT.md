# FastShip API - Deployment Guide

## Overview

This guide covers deploying the FastShip API to production environments.

## Prerequisites

- Docker & Docker Compose installed
- PostgreSQL 15+ (or use Docker)
- Redis 7+ (or use Docker)
- Domain name (optional, for production)
- SSL certificate (for HTTPS in production)

## Environment Setup

### 1. Environment Variables

Create a `.env` file based on `env.example`:

```bash
# Security
JWT_SECRET=your-very-secure-secret-key-change-in-production
JWT_ALGORITHM=HS256

# Database
POSTGRES_SERVER=db
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your-secure-password
POSTGRES_DB=fastapi_db

# Redis
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_URL=redis://redis:6379

# Email (SMTP)
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
MAIL_FROM=noreply@fastship.com
MAIL_PORT=587
MAIL_SERVER=smtp.gmail.com
MAIL_FROM_NAME=FastShip
MAIL_STARTTLS=true
MAIL_SSL_TLS=false
USE_CREDENTIALS=true
VALIDATE_CERTS=true

# SMS (Twilio)
TWILIO_SID=your-twilio-sid
TWILIO_AUTH_TOKEN=your-twilio-auth-token
TWILIO_NUMBER=+1234567890
```

### 2. Production Secrets

**Important**: Never commit `.env` files to version control!

- Use strong, unique `JWT_SECRET`
- Use secure database passwords
- Use production SMTP credentials
- Use production Twilio credentials

## Docker Deployment

### Quick Start

```bash
# Clone repository
git clone <repository-url>
cd app

# Copy environment file
cp env.example .env
# Edit .env with production values

# Start services
docker-compose up -d

# Check logs
docker-compose logs -f api

# Verify health
curl http://localhost:8000/health
```

### Production Docker Compose

For production, consider:

1. **Remove volume mounts** (use built images)
2. **Set restart policies**: `restart: always`
3. **Configure resource limits**
4. **Use Docker secrets** for sensitive data
5. **Enable health checks**

Example production `docker-compose.prod.yml`:

```yaml
services:
  api:
    build: .
    restart: always
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 1G
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
    # Remove volumes in production
    # volumes:
    #   - .:/code
```

## Database Setup

### Initial Migration

```bash
# Run migrations
docker-compose exec api alembic upgrade head

# Or tables auto-create on startup (via lifespan_handler)
```

### Database Backup

```bash
# Backup
docker-compose exec db pg_dump -U postgres fastapi_db > backup.sql

# Restore
docker-compose exec -T db psql -U postgres fastapi_db < backup.sql
```

## Redis Setup

### Redis Persistence

Redis data is persisted in Docker volume `redis_data`.

### Redis Configuration

For production, configure Redis persistence:

```yaml
redis:
  image: redis:7-alpine
  command: redis-server --appendonly yes
  volumes:
    - redis_data:/data
```

## Reverse Proxy (Nginx)

### Nginx Configuration

Example Nginx configuration:

```nginx
server {
    listen 80;
    server_name api.fastship.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### SSL/HTTPS

Use Let's Encrypt with Certbot:

```bash
sudo certbot --nginx -d api.fastship.com
```

## Monitoring

### Health Checks

- **API Health**: `GET /health`
- **Database**: PostgreSQL health check in Docker
- **Redis**: Connection check in application

### Logging

Logs are stored in `logs/` directory:
- Request logs via Celery
- Application logs
- Error logs

### Monitoring Tools

Consider integrating:
- **Prometheus**: Metrics collection
- **Grafana**: Visualization
- **Sentry**: Error tracking
- **Datadog**: APM

## Scaling

### Horizontal Scaling

1. **API**: Run multiple API containers behind load balancer
2. **Celery Workers**: Scale workers based on task volume
3. **Database**: Use read replicas for read-heavy workloads
4. **Redis**: Use Redis Cluster for high availability

### Load Balancer

Use Nginx or cloud load balancer:

```nginx
upstream api_backend {
    least_conn;
    server api1:8000;
    server api2:8000;
    server api3:8000;
}
```

## Security Checklist

- [ ] Strong JWT secret
- [ ] Secure database passwords
- [ ] HTTPS enabled
- [ ] Environment variables secured
- [ ] Database backups configured
- [ ] Rate limiting enabled (if applicable)
- [ ] CORS configured (if needed)
- [ ] Security headers set
- [ ] Regular dependency updates
- [ ] Log monitoring enabled

## Backup Strategy

### Database Backups

```bash
# Daily backup script
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
docker-compose exec -T db pg_dump -U postgres fastapi_db | gzip > backups/db_$DATE.sql.gz
```

### Redis Backups

Redis data is in Docker volume. Backup the volume:

```bash
docker run --rm -v app_redis_data:/data -v $(pwd)/backups:/backup \
  alpine tar czf /backup/redis_$(date +%Y%m%d).tar.gz /data
```

## Troubleshooting

### Common Issues

1. **Database Connection Failed**
   - Check `POSTGRES_*` environment variables
   - Verify database container is running
   - Check network connectivity

2. **Redis Connection Failed**
   - Check `REDIS_*` environment variables
   - Verify Redis container is running
   - Check Redis logs

3. **Celery Tasks Not Running**
   - Verify Celery worker container is running
   - Check Celery logs
   - Verify Redis connection

4. **Email Not Sending**
   - Check SMTP credentials
   - Verify email settings
   - Check Celery worker logs

### Debug Mode

For debugging, enable verbose logging:

```bash
# In docker-compose.yml
environment:
  - LOG_LEVEL=DEBUG
```

## Production Checklist

- [ ] Environment variables configured
- [ ] Database migrations applied
- [ ] SSL/HTTPS configured
- [ ] Monitoring set up
- [ ] Backups configured
- [ ] Health checks passing
- [ ] Logging configured
- [ ] Security measures in place
- [ ] Performance tested
- [ ] Documentation updated

---

**Last Updated**: January 8, 2026

