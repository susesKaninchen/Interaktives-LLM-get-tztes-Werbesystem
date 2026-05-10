# Interaktives LLM-gestütztes Werbesystem

Ein modernes Werbesystem mit KI-gestützter Kundenakquise und persönlicher Ansprache.

## 🚀 Was wurde verbessert (v0.2.0)

### Backend-Verbesserungen
- **✅ Robustes State Management**: Strukturierte Conversations-State-Klasse mit Persistenz und Validierung
- **✅ WebSocket-Stabilität**: Heartbeat-Mechanismus, Reconnect-Logik und verbesserte Fehlerbehandlung
- **✅ Überarbeiteter Intent-Router**: Besserer Kontext (10 statt 3 Nachrichten), Fallback-Logik und Konfidenzbewertung
- **✅ Stabiler Crawler**: Headless-Playwright, Rate-Limiting, Caching und Retry-Logik
- **✅ Sicherheitsmechanismen**: Rate-Limiting, Input-Validation, SQL/XSS-Schutz
- **✅ Performance-Optimierungen**: Response-Caching, Performance-Monitoring
- **✅ Umfassende Tests**: Unit-Tests für State Management, Security und Integration

### Frontend-Verbesserungen
- **✅ Bessere UX**: Loading States, Progress Indikatoren, Error Toasts
- **✅ Robustere Fehlerbehandlung**: Strukturierte Fehleranzeigen mit Details
- **✅ Verbesserte Responsiveness**: Optimistische UI Updates
- **✅ Verbessertes Design**: Moderneres UI mit besseren Visualisierungen

## 🛠️ Tech Stack

- **Frontend**: React + Vite + TypeScript + Zustand + TailwindCSS
- **Backend**: Python FastAPI (async) + SQLAlchemy (async) + Alembic
- **Database**: SQLite (aiosqlite) + ChromaDB (vector search)
- **Agents**: LangGraph (graph-based orchestration)
- **LLM**: OpenAI-compatible API (TH Luebeck Server)

## 📋 Entwicklung

### Backend Setup
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

### DB Migrations
```bash
cd backend
alembic upgrade head
```

### Tests ausführen
```bash
cd backend
python -m pytest tests/ -v
```

## 📁 Projektstruktur

```
├── backend/
│   ├── app/
│   │   ├── agents/          # LangGraph Agents und State Management
│   │   ├── routers/         # API Endpoints (inkl. verbesserte WebSocket)
│   │   ├── services/        # LLM und andere Services
│   │   ├── db/             # Datenbank Models und Vector Store
│   │   ├── security.py     # Security Middleware und Validation
│   │   ├── performance.py  # Performance Optimierungen
│   │   └── main.py         # FastAPI Application
│   └── tests/              # Unit und Integration Tests
├── frontend/
│   └── src/
│       ├── components/     # React Komponenten (inkl. neue Error/Status UI)
│       ├── store/          # Zustand Store (verbesserte Fehlerbehandlung)
│       └── api/            # HTTP und WebSocket Clients
├── config.yaml            # LLM Konfiguration
└── data/                  # Runtime Daten (SQLite, ChromaDB, Cache)
```

## 🔧 Konfiguration

Die LLM-Konfiguration wird in `config.yaml` definiert:

```yaml
llm:
  default_model: "oss-120b"
  models:
    oss-120b:
      base_url: "https://models.mylab.th-luebeck.dev/v1/"
      api_key: "TH-Luebeck"
      model_name: "gpt-oss-120b"
      temperature: 0.7
      max_tokens: 4096
  routing:
    router: "oss-120b"      # Für Intent-Klassifizierung
    agents: "qwen-27b"      # Für Content-Generierung
```

## 🔒 Sicherheit

Das System enthält folgende Sicherheitsmaßnahmen:

- **Rate Limiting**: 60 Requests/Minute, 1000 Requests/Stunde pro IP
- **Input Validation**: Schutz gegen SQL Injection und XSS
- **URL Sanitization**: Nur HTTP/HTTPS URLs erlaubt
- **Security Headers**: Standard HTTP Security Headers
- **State Validation**: Konsistenzprüfung des Conversations-States

## 🚨 Bekannte Issues und TODOs

### Hohe Priorität
- [ ] Persistence für WebSocket-Reconnect implementieren
- [ ] Verbesserte Pagination für große Konversationen
- [ ] Lazy Loading für Nachrichten

### Mittlere Priorität  
- [ ] Redis für verteiltes Caching
- [ ] Monitoring Dashboard
- [ ] Observability/Metrics

### Niedrige Priorität
- [ ] Multi-User Support
- [ ] Roles und Permissions
- [ ] Advanced Analytics

## 📊 Performance

Das System wurde für folgende Performance optimiert:

- **Response Time**: < 2s für normale Queries
- **WebSocket Latency**: < 100ms für Status-Updates
- **Crawler Performance**: ~10s für typische Websites (mit Cache)
- **Memory Usage**: < 500MB für typische Workloads

## 🧪 Testing

Das System enthält umfassende Tests:

```bash
# Alle Tests
pytest tests/ -v

# Nur Unit Tests
pytest tests/test_conversation_state.py tests/test_security.py -v

# Nur Integration Tests
pytest tests/test_integration.py -v

# Mit Coverage
pytest tests/ --cov=app --cov-report=html
```

## 📈 Monitoring

Performance und Cache Stats können über folgende Endpoints abgerufen werden:

```bash
# Performance Statistiken
GET /api/stats/performance

# Cache Statistiken  
GET /api/stats/cache

# Health Check
GET /api/health
```

---

**Version**: 0.2.0  
**Letztes Update**: 2025-01-10
