# ASTRO Production Deployment Guide

## Prerequisites

- Node.js 18+ 
- Docker (optional)
- Linux server (Ubuntu 22.04 recommended)
- Domain with SSL certificate

## Environment Variables

Create `.env.production`:

```bash
# Server
NODE_ENV=production
PORT=5000
PROFILE=core

# Security (REQUIRED - generate strong secrets)
JWT_SECRET=your-256-bit-secret-key-here
SECURITY_CORS_ORIGIN=https://yourdomain.com

# Database
DATA_PATH=/var/lib/astro/data/astro.db

# Rate Limiting
RATE_LIMIT_WINDOW_MS=60000
RATE_LIMIT_MAX=100

# Logging
LOG_LEVEL=info
LOG_FILE=/var/log/astro/app.log
```

Generate a secure JWT secret:
```bash
openssl rand -hex 32
```

## Option 1: Direct Deployment

### 1. Install Dependencies

```bash
# Clone repository
git clone https://github.com/Senpai-Sama7/Astro.git
cd Astro

# Install production dependencies
npm ci --production

# Build TypeScript
npm run build
```

### 2. Create System User

```bash
sudo useradd -r -s /bin/false astro
sudo mkdir -p /var/lib/astro/data /var/log/astro
sudo chown -R astro:astro /var/lib/astro /var/log/astro
```

### 3. Create Systemd Service

Create `/etc/systemd/system/astro.service`:

```ini
[Unit]
Description=ASTRO Ultimate System
After=network.target

[Service]
Type=simple
User=astro
Group=astro
WorkingDirectory=/opt/astro
ExecStart=/usr/bin/node dist/index.js
Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal
Environment=NODE_ENV=production

[Install]
WantedBy=multi-user.target
```

### 4. Start Service

```bash
sudo systemctl daemon-reload
sudo systemctl enable astro
sudo systemctl start astro
sudo systemctl status astro
```

## Option 2: Docker Deployment

### 1. Build Image

```bash
docker build -t astro:latest -f Dockerfile .
```

### 2. Run Container

```bash
docker run -d \
  --name astro \
  --restart unless-stopped \
  -p 5000:5000 \
  -v /var/lib/astro/data:/app/data \
  -e NODE_ENV=production \
  -e JWT_SECRET=your-secret-here \
  -e SECURITY_CORS_ORIGIN=https://yourdomain.com \
  astro:latest
```

### 3. Docker Compose

Create `docker-compose.prod.yml`:

```yaml
version: '3.8'

services:
  astro:
    build: .
    restart: unless-stopped
    ports:
      - "5000:5000"
    volumes:
      - astro-data:/app/data
    environment:
      - NODE_ENV=production
      - JWT_SECRET=${JWT_SECRET}
      - SECURITY_CORS_ORIGIN=${CORS_ORIGIN}
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000/api/v1/health"]
      interval: 30s
      timeout: 10s
      retries: 3

volumes:
  astro-data:
```

Run:
```bash
docker-compose -f docker-compose.prod.yml up -d
```

## Nginx Reverse Proxy

Create `/etc/nginx/sites-available/astro`:

```nginx
upstream astro {
    server 127.0.0.1:5000;
    keepalive 64;
}

server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # API
    location /api/ {
        proxy_pass http://astro;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }

    # WebSocket
    location /ws {
        proxy_pass http://astro;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_read_timeout 86400;
    }

    # Static files (if serving web UI)
    location / {
        root /var/www/astro/web;
        try_files $uri $uri/ /index.html;
    }
}
```

Enable and restart:
```bash
sudo ln -s /etc/nginx/sites-available/astro /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

## SSL with Let's Encrypt

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com
```

## Monitoring

### Health Check Endpoint

```bash
curl https://yourdomain.com/api/v1/health
```

### Log Monitoring

```bash
# Systemd logs
journalctl -u astro -f

# Docker logs
docker logs -f astro
```

### Process Monitoring with PM2

```bash
npm install -g pm2
pm2 start dist/index.js --name astro
pm2 save
pm2 startup
```

## Security Checklist

- [ ] Strong JWT_SECRET (256-bit minimum)
- [ ] CORS restricted to your domain
- [ ] HTTPS enabled with valid certificate
- [ ] Rate limiting configured
- [ ] Firewall rules (only 80/443 exposed)
- [ ] Regular security updates
- [ ] Database backups configured
- [ ] Log rotation enabled

## Backup

### Database Backup

```bash
# Manual backup
cp /var/lib/astro/data/astro.db /backup/astro-$(date +%Y%m%d).db

# Automated backup (cron)
0 2 * * * cp /var/lib/astro/data/astro.db /backup/astro-$(date +\%Y\%m\%d).db
```

## Troubleshooting

### Service won't start
```bash
journalctl -u astro -n 50 --no-pager
```

### Permission issues
```bash
sudo chown -R astro:astro /var/lib/astro
```

### Port already in use
```bash
sudo lsof -i :5000
sudo kill -9 <PID>
```

### WebSocket connection issues
- Check nginx proxy_read_timeout
- Verify firewall allows WebSocket upgrade
- Check CORS configuration

## Performance Tuning

### Node.js

```bash
# Increase memory limit
NODE_OPTIONS="--max-old-space-size=4096" node dist/index.js
```

### Nginx

```nginx
# In http block
worker_connections 4096;
keepalive_timeout 65;
```

## Scaling

For high availability:

1. **Load Balancer**: Use nginx upstream with multiple instances
2. **Database**: Consider PostgreSQL for multi-instance deployments
3. **Sessions**: Use Redis for shared session storage
4. **WebSockets**: Use Redis adapter for Socket.IO

---

For support, open an issue at: https://github.com/Senpai-Sama7/Astro/issues
