# Deployment Checklist

## Pre-Deployment

### Environment Setup
- [ ] Verify Python 3.12 is installed
- [ ] Install all dependencies: `py -3.12 -m pip install -r apps/api/requirements.txt`
- [ ] Configure environment variables in `.env` or `config/config.yaml`
  - [ ] `QLIB_MODEL_DIR` - Directory for storing trained models
  - [ ] `QLIB_MIN_SHARPE_RATIO` - Minimum Sharpe ratio threshold (default: 1.5)
  - [ ] `QLIB_TRAINING_CRON` - Training schedule (default: `0 2 * * 0`)
  - [ ] `QLIB_RISK_REPORT_CRON` - Risk report schedule (default: `30 15 * * 1-5`)
- [ ] Verify MongoDB connection settings
- [ ] Configure DingTalk webhook for alerts (optional)

### Database Preparation
- [ ] Ensure MongoDB is running and accessible
- [ ] Create MongoDB indexes: `py -3.12 scripts/create_indexes.py`
- [ ] Verify index creation with `--dry-run` first if needed
- [ ] Test database connectivity

### Backup
- [ ] Create pre-deployment backup: `py -3.12 scripts/backup_mongodb.py --verify`
- [ ] Verify backup integrity
- [ ] Store backup in secure location
- [ ] Document backup location and timestamp

---

## Deployment Steps

### 1. Stop Services
```bash
# Stop scheduler service
sudo systemctl stop scheduler-service

# Stop any running training jobs
pkill -f qlib_train || true

# Verify services stopped
sudo systemctl status scheduler-service
```

### 2. Deploy Code
```bash
# Pull latest code
git pull origin main

# Install/update dependencies
py -3.12 -m pip install -r apps/api/requirements.txt

# Verify no import errors
py -3.12 -c "from apps.api.app.core.config import settings; print(settings)"
```

### 3. Database Migrations
```bash
# Create indexes (if not exists)
py -3.12 scripts/create_indexes.py

# Verify indexes created
py -3.12 -c "
from pymongo import MongoClient
from apps.api.app.core.config import settings
client = MongoClient(settings.mongodb_host, settings.mongodb_port)
db = client[settings.mongodb_database]
for coll in ['qlib_models', 'backtest_results', 'risk_reports']:
    print(f'{coll}: {list(db[coll].list_indexes())}')
"
```

### 4. Configure Log Rotation
```bash
# Copy logrotate config (Linux only)
sudo cp config/logrotate.conf /etc/logrotate.d/qlib-training

# Replace placeholders
sudo sed -i 's|{{LOG_DIR}}|/home/fantom/datastore/logs|g' /etc/logrotate.d/qlib-training
sudo sed -i 's|{{USER}}|fantom|g' /etc/logrotate.d/qlib-training
sudo sed -i 's|{{GROUP}}|fantom|g' /etc/logrotate.d/qlib-training

# Set permissions
sudo chmod 644 /etc/logrotate.d/qlib-training

# Test configuration
sudo logrotate -d /etc/logrotate.d/qlib-training
```

### 5. Start Services
```bash
# Start API server
py -3.12 -m uvicorn apps.api.main:app --host 0.0.0.0 --port 8000 &

# Start scheduler service
sudo systemctl start scheduler-service

# Verify services running
sudo systemctl status scheduler-service
```

---

## Post-Deployment Verification

### Smoke Tests

#### 1. Health Check
```bash
# Basic health check
curl http://localhost:8000/health

# Detailed health check (if implemented)
curl http://localhost:8000/api/v1/health/full
```

#### 2. MongoDB Connectivity
```bash
py -3.12 -c "
from pymongo import MongoClient
from apps.api.app.core.config import settings
client = MongoClient(settings.mongodb_host, settings.mongodb_port)
client.admin.command('ping')
print('MongoDB: OK')
"
```

#### 3. Check Collections
```bash
py -3.12 -c "
from pymongo import MongoClient
from apps.api.app.core.config import settings
client = MongoClient(settings.mongodb_host, settings.mongodb_port)
db = client[settings.mongodb_database]
collections = ['qlib_models', 'backtest_results', 'risk_reports', 
               'scheduler_jobs', 'job_executions', 'dingtalk_configs']
for c in collections:
    count = db[c].count_documents({})
    print(f'{c}: {count} documents')
"
```

#### 4. Scheduler Status
```bash
# Check scheduler API
curl -H "Authorization: Bearer <token>" \
  http://localhost:8000/api/v1/scheduler/jobs

# Check scheduled jobs exist
curl -H "Authorization: Bearer <token>" \
  http://localhost:8000/api/v1/scheduler/job-types
```

#### 5. Model Directory
```bash
# Verify model directory exists and is writable
ls -la ./models/
mkdir -p ./models
touch ./models/test.txt && rm ./models/test.txt && echo "Models dir: OK"
```

#### 6. Log Files
```bash
# Check logs are being written
tail -f logs/app.log &
sleep 5
# Should see startup logs

# Create log directory if needed
mkdir -p logs/training_jobs logs/executions logs/archive
```

### Integration Tests

#### 1. Test Qlib Training Endpoint
```bash
curl -X POST -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"model_type": "lgbm", "instruments": "csi300"}' \
  http://localhost:8000/api/v1/qlib/train
```

#### 2. Test Backtest Endpoint
```bash
curl -X POST -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"model_id": "<model_id>", "start_date": "2024-01-01", "end_date": "2024-12-31"}' \
  http://localhost:8000/api/v1/backtest/run
```

#### 3. Test Scheduler Job Creation
```bash
curl -X POST -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Job",
    "job_type": "qlib_train",
    "cron_expression": "0 3 * * *",
    "config": {"model_type": "lgbm"},
    "enabled": false
  }' \
  http://localhost:8000/api/v1/scheduler/jobs
```

---

## Monitoring Setup

### 1. Configure Health Monitoring
```bash
# Add cron job for health checks
crontab -e
# Add line:
*/5 * * * * curl -sf http://localhost:8000/health || echo "Health check failed" | mail -s "Alert" admin@example.com
```

### 2. Configure Failure Alerts
- Ensure DingTalk webhook is configured in settings
- Test alert delivery:
```bash
py -3.12 -c "
from app.notify.dingtalk import DingTalkNotifier
notifier = DingTalkNotifier(webhook_url='your_webhook', secret='your_secret')
notifier.send(markdown='## Test Alert\nDeployment test message')
"
```

### 3. Setup Log Monitoring
```bash
# Add log monitoring cron
crontab -e
# Add line:
*/10 * * * * grep -i 'error\|exception' /home/fantom/datastore/logs/app.log | tail -100 >> /tmp/error_log.txt
```

---

## Rollback Procedure

If deployment fails:

### 1. Stop Services
```bash
sudo systemctl stop scheduler-service
pkill -f uvicorn || true
```

### 2. Restore from Backup
```bash
# List available backups
ls -la ./backups/

# Restore specific backup (dry run first)
py -3.12 scripts/rollback.py ./backups/backup_<timestamp> --dry-run

# Actual restore
py -3.12 scripts/rollback.py ./backups/backup_<timestamp> --force
```

### 3. Revert Code
```bash
git log --oneline -5
git reset --hard <previous_commit>
py -3.12 -m pip install -r apps/api/requirements.txt
```

### 4. Restart Services
```bash
sudo systemctl start scheduler-service
```

---

## Post-Deployment Tasks

### Immediate
- [ ] Verify all health checks pass
- [ ] Check logs for errors
- [ ] Verify scheduler jobs are running
- [ ] Test API endpoints

### Within 1 Hour
- [ ] Monitor first scheduled job execution
- [ ] Check DingTalk alerts are working
- [ ] Verify log rotation is active

### Within 24 Hours
- [ ] Review job execution history
- [ ] Check disk space usage
- [ ] Verify backup completed successfully
- [ ] Review system performance

---

## Troubleshooting

### MongoDB Connection Issues
```bash
# Check MongoDB is running
sudo systemctl status mongod

# Test connection
py -3.12 -c "
from pymongo import MongoClient
from apps.api.app.core.config import settings
client = MongoClient(settings.mongodb_host, settings.mongodb_port)
print(client.server_info())
"
```

### Scheduler Not Running
```bash
# Check scheduler service
sudo systemctl status scheduler-service
sudo journalctl -u scheduler-service -n 50

# Manual start for debugging
py -3.12 apps/api/scheduler_standalone.py
```

### Training Jobs Failing
```bash
# Check logs
tail -f logs/qlib_training.log

# Verify Qlib installation
py -3.12 -c "import qlib; qlib.init(); print('Qlib: OK')"

# Check model directory permissions
ls -la ./models/
```

---

## Contact

- **DevOps**: devops@example.com
- **On-call**: Check PagerDuty
- **Documentation**: `/docs` endpoint
