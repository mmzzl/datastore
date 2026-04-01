# Developer Setup Guide

This guide helps developers set up the quantitative trading system for local development.

## Prerequisites

### Required Software

| Software | Version | Purpose |
|----------|---------|---------|
| Python | 3.12 | Backend runtime |
| Node.js | 18+ | Frontend runtime |
| MongoDB | 6.0+ | Data storage |
| Git | Latest | Version control |

### Platform-Specific Notes

**Windows**:
- Use `py -3.12` command for Python
- Install MongoDB via MSI installer or Docker

**Linux/macOS**:
- Use `python3.12` or create a virtual environment
- Install MongoDB via package manager

---

## Backend Setup

### 1. Clone Repository

```bash
git clone <repository-url>
cd datastore
```

### 2. Create Virtual Environment (Recommended)

```bash
# Windows
py -3.12 -m venv venv
venv\Scripts\activate

# Linux/macOS
python3.12 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r apps/api/requirements.txt
```

### 4. Configure MongoDB

**Option A: Local MongoDB**

```bash
# Start MongoDB service
mongod --dbpath /path/to/data

# Or via Docker
docker run -d -p 27017:27017 --name mongodb mongo:6.0
```

**Option B: Remote MongoDB**

Update `apps/api/config/config.yaml`:
```yaml
mongodb:
  host: "your-mongodb-host"
  port: 27017
  username: "admin"
  password: "your_password"
  database: "eastmoney_news"
```

### 5. Configure Environment

Copy and edit configuration:
```bash
cp apps/api/config/config.yaml.example apps/api/config/config.yaml
```

Key configuration sections:
```yaml
# Application
app:
  name: "News API"
  version: "1.0.0"

# Authentication
auth:
  username: "admin"
  password: "hashed_password"

# JWT
jwt:
  secret_key: "your-secret-key"
  algorithm: "HS256"
  access_token_expire_minutes: 30

# Logging
logging:
  level: "INFO"
  file: "logs/app.log"
```

### 6. Initialize Data

```bash
# Scrape K-line data (optional)
py -3.12 apps/api/stock_kline_scraper.py

# Run initial data collection
py -3.12 apps/api/initial_data_loader.py
```

### 7. Run Development Server

```bash
# Start FastAPI server
py -3.12 -m uvicorn apps.api.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at:
- API: http://localhost:8000
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### 8. Run Scheduler (Optional)

```bash
# Run scheduler standalone
py -3.12 apps/api/scheduler_standalone.py
```

---

## Frontend Setup

### 1. Navigate to Frontend

```bash
cd frontend/vue-admin
```

### 2. Install Dependencies

```bash
npm install
```

### 3. Configure API Proxy

The development server proxies API requests to the backend.

`vite.config.ts` (already configured):
```typescript
server: {
  proxy: {
    '/api': {
      target: 'http://localhost:8000',
      changeOrigin: true,
    },
  },
}
```

### 4. Run Development Server

```bash
npm run dev
```

The frontend will be available at http://localhost:5173

### 5. Build for Production

```bash
npm run build
npm run preview  # Preview production build
```

---

## Qlib Setup (Optional)

For ML-based stock selection features:

### 1. Install Qlib

```bash
pip install pyqlib
```

### 2. Initialize Qlib Data

```python
import qlib
from qlib.config import REG_CN

qlib.init(
    provider_uri="~/.qlib/qlib_data/cn_data",
    region=REG_CN,
)
```

### 3. Download Qlib Data (if needed)

```bash
python -m qlib.run.get_data qlib_data --target_dir ~/.qlib/qlib_data/cn_data --region cn
```

### 4. Verify Installation

```python
from app.qlib import MongoDataProvider
from app.data_source import DataSourceManager

data_manager = DataSourceManager()
provider = MongoDataProvider(data_manager=data_manager)

# Test data loading
df = provider.load_data(
    instruments=["SH600000"],
    start_time="2023-01-01",
    end_time="2024-01-01"
)
print(df.head())
```

---

## Development Workflow

### Running Both Services

**Terminal 1 - Backend**:
```bash
cd D:\datastore
py -3.12 -m uvicorn apps.api.main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 - Frontend**:
```bash
cd D:\datastore\frontend\vue-admin
npm run dev
```

### Hot Reload

Both services support hot reload:
- **Backend**: FastAPI `--reload` flag restarts on file changes
- **Frontend**: Vite automatically reloads on file changes

### Database Management

**View Collections**:
```bash
mongosh
use eastmoney_news
show collections
```

**Common Collections**:
| Collection | Purpose |
|------------|---------|
| `news` | News articles |
| `kline` | K-line data |
| `holdings` | User holdings |
| `backtest_results` | Backtest history |
| `qlib_models` | ML model metadata |
| `risk_reports` | Risk analysis reports |
| `scheduler_jobs` | Scheduled jobs |
| `dingtalk_configs` | DingTalk notification configs |

### Logging

Logs are written to `logs/app.log`:
```bash
# View live logs
tail -f logs/app.log

# Windows
Get-Content logs/app.log -Wait
```

---

## IDE Setup

### VS Code

Recommended extensions:
- Python (Microsoft)
- Pylance
- Vue - Official
- TypeScript Vue Plugin (Volar)
- ESLint

`settings.json`:
```json
{
  "python.defaultInterpreterPath": "${workspaceFolder}/venv/Scripts/python.exe",
  "python.analysis.typeCheckingMode": "basic",
  "editor.formatOnSave": true
}
```

### PyCharm

1. Open project root
2. Configure Python 3.12 interpreter
3. Enable Django/FastAPI support
4. Configure run configurations for backend

---

## Troubleshooting

### Common Issues

**1. MongoDB Connection Failed**
```
Error: MongoDB connection refused
```
Solution: Ensure MongoDB is running
```bash
# Check MongoDB status
mongosh --eval "db.runCommand({ ping: 1 })"
```

**2. Port Already in Use**
```
Error: [Errno 10048] error while attempting to bind on address
```
Solution: Kill process using the port
```bash
# Windows
netstat -ano | findstr :8000
taskkill /PID <pid> /F

# Linux/macOS
lsof -i :8000
kill -9 <pid>
```

**3. Import Errors**
```
ModuleNotFoundError: No module named 'app'
```
Solution: Run from project root with PYTHONPATH
```bash
set PYTHONPATH=D:\datastore\apps\api
py -3.12 -m uvicorn apps.api.main:app --reload
```

**4. Frontend API Errors**
```
Network Error / CORS Error
```
Solution: Ensure backend is running and CORS is configured

**5. Qlib Initialization Errors**
```
RuntimeError: Qlib not initialized
```
Solution: Check Qlib data installation
```bash
python -m qlib.run.get_data qlib_data --region cn
```

---

## Next Steps

1. Read [API Documentation](api.md) for available endpoints
2. Review [Qlib Integration](qlib-integration.md) for ML features
3. Check [Scheduler Documentation](scheduler.md) for automation
4. See [User Guide](user-guide.md) for frontend usage
