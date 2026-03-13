# Interaktives LLM-gestuetztes Werbesystem

## Tech Stack
- **Frontend**: React + Vite + TypeScript + Zustand + TailwindCSS
- **Backend**: Python FastAPI (async) + SQLAlchemy (async) + Alembic
- **Database**: SQLite (aiosqlite) + ChromaDB (vector search)
- **Agents**: LangGraph (graph-based orchestration)
- **LLM**: OpenAI-compatible API (TH Luebeck Server)

## Development
- Backend: `cd backend && uvicorn app.main:app --reload`
- Frontend: `cd frontend && npm run dev`
- DB Migrations: `cd backend && alembic upgrade head`

## Project Structure
- `config.yaml` - LLM endpoints, models, settings
- `backend/` - FastAPI backend with LangGraph agents
- `frontend/` - React+Vite frontend
- `data/` - Runtime data (SQLite, ChromaDB) - gitignored
