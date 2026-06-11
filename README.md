# SPIA — Personal Privacy Auditor

Self-hosted tool that scans the surface web, deep web, and dark web for exposed personal information. BYO API keys model — you own the software, you control the data.

## Quick Start (Docker)

```bash
cp .env.example .env
# Edit .env with your API key

export POSTGRES_USER=spia_user
export POSTGRES_PASSWORD=your_db_password
export SPIA_API_KEY=your_api_key

docker compose -f docker-compose.prod.yml up -d --build
```

Open http://localhost — Audit | Settings | Pricing

## Development

```bash
# Backend
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000

# Frontend
cd frontend
npm install
npm run dev
```

## License Keys

```bash
# Generate trial keys (14 days)
python tools/generate_license.py trial

# Generate pro keys (1 year)
python tools/generate_license.py pro --count 100 --output keys.json

# Generate enterprise keys (lifetime)
python tools/generate_license.py enterprise
```

Keys format: `SPIA-{PLAN}-{random}`

## Architecture

| Layer | Stack |
|-------|-------|
| Backend | FastAPI + Uvicorn + httpx + BeautifulSoup4 |
| Search | SerpAPI → Google CSE → DuckDuckGo (auto fallback) |
| ML | XGBoost + scikit-learn (bot/fake profile detector) |
| Frontend | React 18 + TypeScript + Vite + TailwindCSS |
| Infra | Docker Compose (API, Nginx, PostgreSQL, Redis) |

## BYO API Keys

Users configure their own API keys in Settings:

| API | Purpose | Get Key |
|-----|---------|---------|
| SerpAPI | Google search results | serpapi.com |
| Google CSE | Custom search engine | console.cloud.google.com |
| HIBP | Breach database | haveibeenpwned.com/API/Key |
| Dehashed | Deep breach search | dehashed.com |
| IntelX | Dark web intelligence | intelx.io |
| Twitter | Social profile scanning | developer.twitter.com |

## Security

- API key auth on all endpoints
- Rate limiting (30 req/min per IP)
- SSRF protection (blocked internal IPs)
- Input sanitization (XSS/SQLi detection)
- Security headers (CSP, HSTS, X-Frame-Options)
- No telemetry, no tracking, no data sharing

## License

SPIA is source-available. To use in production, purchase a license key. See Pricing page for details.
