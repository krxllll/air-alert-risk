# Air Alert Risk

Web application for visualizing the risk of air alerts in Ukrainian regions
based on historical data and SARIMAX forecasting.

## Tech Stack

### Backend
- Python 3.12
- FastAPI
- SARIMAX / statsmodels
- Docker

### Frontend
- Vue 3
- Vite
- TypeScript
- pnpm

### Infrastructure
- Docker
- docker-compose
- PostgreSQL, Redis, Nginx

---

## Project Structure

air-alert-risk/\
├── backend/ # FastAPI backend\
│ ├── app/\
│ │ └── main.py\
│ ├── Dockerfile\
│ └── requirements.txt\
│\
├── frontend/ # Vite + Vue frontend\
│ ├── src/\
│ ├── Dockerfile\
│ └── vite.config.ts\
│\
├── docker-compose.yml\
├── .env.example\
└── README.md

---

## Prerequisites

- Docker
- Docker Compose
- pnpm (for local frontend dev, optional)

---

## Running the project (Docker)

```bash
docker-compose up --build
```

- Frontend: http://localhost:5173
- Backend health check: http://localhost:8000/health
- API via frontend proxy: http://localhost:5173/api/health

---

## Development Notes

- Backend runs only inside Docker
- Local Python venv is used only for IDE autocompletion
- No CORS configuration required (frontend uses proxy)

