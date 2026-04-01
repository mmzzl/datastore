# Deployment Guide

This guide covers production deployment of the quantitative trading system.

## Production Requirements

### Hardware

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| CPU | 2 cores | 4+ cores |
| RAM | 4 GB | 8+ GB |
| Storage | 50 GB SSD | 100+ GB SSD |
| Network | 100 Mbps | 1 Gbps |

### Software

| Software | Version | Purpose |
|----------|---------|---------|
| Python | 3.12 | Backend runtime |
| Node.js | 18 LTS | Frontend build |
| MongoDB | 6.0+ | Database |
| Nginx | 1.24+ | Reverse proxy |

---

## Environment Variables

### Backend Configuration

Create `.env` file or set environment variables:

```bash
# Application
APP_NAME="Quantitative Trading System"
APP_VERSION="1.0.0"

# MongoDB
MONGODB_HOST=localhost
MONGODB_PORT=27017
MONGODB_USERNAME=admin
MONGODB_PASSWORD=<secure-password>
MONGODB_DATABASE=trading_db

# JWT Authentication
JWT_SECRET_KEY=<generate-secure-key>
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30

# Auth Credentials
AUTH_USERNAME=admin
AUTH_PASSWORD=<hashed-password>

# Logging
LOG_LEVEL=INFO
LOG_FILE=/var/log/trading/app.log
LOG_BACKUP_COUNT=30

# External APIs
TUSHARE_TOKEN=<your-token>

# LLM (Optional)
LLM_PROVIDER=deepseek
LLM_API_KEY=<your-api-key>
LLM_MODEL=deepseek-chat

# DingTalk (Optional)
DINGTALK_WEBHOOK=<webhook-url>
DINGTALK_SECRET=<secret>
```

### Generate Secure Keys

```bash
# JWT Secret Key (64 bytes)
python -c "import secrets; print(secrets.token_hex(32))"

# Password Hash
python -c "import hashlib; print(hashlib.sha1('your_password'.encode()).hexdigest())"
```

---

## Docker Deployment

### Dockerfile - Backend

```dockerfile
# apps/api/Dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create logs directory
RUN mkdir -p /var/log/trading

# Expose port
EXPOSE 8000

# Run application
CMD ["uvicorn", "apps.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Dockerfile - Frontend

```dockerfile
# frontend/vue-admin/Dockerfile
FROM node:18-alpine AS builder

WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

### Docker Compose

```yaml
# docker-compose.yml
version: '3.8'

services:
  mongodb:
    image: mongo:6.0
    container_name: trading-mongodb
    restart: always
    environment:
      MONGO_INITDB_ROOT_USERNAME: admin
      MONGO_INITDB_ROOT_PASSWORD: ${MONGODB_PASSWORD}
    volumes:
      - mongodb_data:/data/db
      - mongodb_config:/data/configdb
    ports:
      - "27017:27017"
    networks:
      - trading-network

  backend:
    build:
      context: ./apps/api
      dockerfile: Dockerfile
    container_name: trading-backend
    restart: always
    environment:
      - MONGODB_HOST=mongodb
      - MONGODB_PORT=27017
      - MONGODB_USERNAME=admin
      - MONGODB_PASSWORD=${MONGODB_PASSWORD}
      - JWT_SECRET_KEY=${JWT_SECRET_KEY}
    depends_on:
      - mongodb
    ports:
      - "8000:8000"
    volumes:
      - ./logs:/var/log/trading
      - ./models:/app/models
    networks:
      - trading-network

  frontend:
    build:
      context: ./frontend/vue-admin
      dockerfile: Dockerfile
    container_name: trading-frontend
    restart: always
    ports:
      - "80:80"
    depends_on:
      - backend
    networks:
      - trading-network

volumes:
  mongodb_data:
  mongodb_config:

networks:
  trading-network:
    driver: bridge
```

### Deploy with Docker Compose

```bash
# Build and start
docker-compose up -d --build

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Stop and remove volumes
docker-compose down -v
```

---

## Manual Deployment

### 1. Setup MongoDB

```bash
# Install MongoDB
sudo apt-get install -y mongodb-org

# Configure MongoDB
sudo vim /etc/mongod.conf

# Start MongoDB
sudo systemctl start mongod
sudo systemctl enable mongod

# Create admin user
mongosh
use admin
db.createUser({
  user: "admin",
  pwd: "<secure-password>",
  roles: ["root"]
})
```

### 2. Deploy Backend

```bash
# Create application user
sudo useradd -r -s /bin/false trading

# Create directories
sudo mkdir -p /opt/trading/{app,logs,models}
sudo chown -R trading:trading /opt/trading

# Clone code
cd /opt/trading/app
git clone <repository-url> .

# Create virtual environment
python3.12 -m venv venv
source venv/bin/activate
pip install -r apps/api/requirements.txt

# Configure environment
cp apps/api/config/config.yaml.example apps/api/config/config.yaml
vim apps/api/config/config.yaml
```

### 3. Create Systemd Service

```bash
# /etc/systemd/system/trading-api.service
[Unit]
Description=Trading System API
After=network.target mongod.service

[Service]
Type=simple
User=trading
Group=trading
WorkingDirectory=/opt/trading/app
Environment="PATH=/opt/trading/app/venv/bin"
ExecStart=/opt/trading/app/venv/bin/uvicorn apps.api.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start
sudo systemctl daemon-reload
sudo systemctl enable trading-api
sudo systemctl start trading-api
```

### 4. Deploy Frontend

```bash
cd frontend/vue-admin
npm ci
npm run build

# Deploy to Nginx
sudo cp -r dist/* /var/www/trading/
```

### 5. Configure Nginx

```nginx
# /etc/nginx/sites-available/trading
server {
    listen 80;
    server_name your-domain.com;

    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

    # Frontend
    location / {
        root /var/www/trading;
        try_files $uri $uri/ /index.html;
    }

    # API Proxy
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # WebSocket
    location /ws/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    # Static files caching
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff2?)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/trading /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

---

## SSL/TLS Configuration

### Let's Encrypt

```bash
# Install Certbot
sudo apt-get install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal
sudo systemctl enable certbot.timer
```

### Manual Certificate

```nginx
ssl_certificate /path/to/cert.pem;
ssl_certificate_key /path/to/key.pem;

ssl_protocols TLSv1.2 TLSv1.3;
ssl_prefer_server_ciphers on;
ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256;
```

---

## Security Considerations

### 1. Network Security

- Use firewall to restrict access
- Only expose necessary ports (80, 443)
- Use VPN for admin access

```bash
# UFW configuration
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 22/tcp  # SSH - restrict to VPN IP
sudo ufw enable
```

### 2. Application Security

- Never commit secrets to repository
- Use environment variables for sensitive data
- Enable HTTPS only
- Implement rate limiting

### 3. Database Security

- Use strong passwords
- Enable authentication
- Restrict network access
- Regular backups

```bash
# MongoDB security
mongosh
use admin
db.createRole({
  role: "backup",
  privileges: [{resource: {anyResource: true}, actions: ["anyAction"]}],
  roles: []
})
```

### 4. Logging & Monitoring

- Centralize logs
- Set up alerts for errors
- Monitor resource usage

---

## Backup Strategy

### MongoDB Backup

```bash
# Daily backup script
#!/bin/bash
BACKUP_DIR=/backup/mongodb
DATE=$(date +%Y%m%d)
mongodump --uri="mongodb://admin:password@localhost:27017" --out=$BACKUP_DIR/$DATE

# Keep last 30 days
find $BACKUP_DIR -type d -mtime +30 -exec rm -rf {} +

# Cron job (daily at 2 AM)
0 2 * * * /opt/trading/scripts/backup-mongodb.sh
```

### Application Backup

```bash
# Backup configuration and models
tar -czf /backup/trading-$(date +%Y%m%d).tar.gz \
  /opt/trading/app/apps/api/config \
  /opt/trading/app/models
```

---

## Health Checks

### Application Health

```bash
# API health check
curl http://localhost:8000/health

# Expected response
{"status": "healthy"}
```

### MongoDB Health

```bash
mongosh --eval "db.runCommand({ ping: 1 })"
```

### Monitoring Script

```python
# scripts/health_check.py
import requests
import logging

def check_api():
    try:
        r = requests.get('http://localhost:8000/health', timeout=5)
        return r.status_code == 200
    except:
        return False

def check_mongodb():
    from pymongo import MongoClient
    try:
        client = MongoClient('mongodb://localhost:27017', serverSelectionTimeoutMS=5000)
        client.admin.command('ping')
        return True
    except:
        return False

if __name__ == '__main__':
    checks = {'API': check_api(), 'MongoDB': check_mongodb()}
    for name, status in checks.items():
        status_str = 'OK' if status else 'FAIL'
        print(f"{name}: {status_str}")
```

---

## Scaling Considerations

### Horizontal Scaling

1. **Load Balancer**: Use Nginx or HAProxy
2. **Multiple API Instances**: Run multiple backend processes
3. **MongoDB Replica Set**: For database redundancy

### Vertical Scaling

1. **Increase CPU/RAM**: For computation-intensive tasks
2. **SSD Storage**: For faster database I/O
3. **GPU**: For ML model training (Qlib)
