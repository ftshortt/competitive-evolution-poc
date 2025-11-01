# EvoAgent
This update adds AS-FDVM (Adaptive Search - Fractal Darwinian Virtual Machines) with minimal, non-breaking endpoints and UI features while preserving all Phase 1/2 functionality.
What's new
- Backend: backend/asfdvm.py
  
- Categories: exploration, exploitation, innovation, stabilization, adaptation
  
- Agent lifecycle: spawn, mutate, retire; topic drift tracking and hints
  
- Adaptive search: simple scoring by fitness/interactions (placeholder for semantic search)
  
- Graph/status: nodes/edges grouped by category and generation; category stats and recent drift
- Flask routes (backward compatible):
  
- POST /categorize { text }
  
- POST /tag { content, context? }
  
- POST /spawn { category?, parent_id? }
  
- GET  /graph
  
- GET  /status
- Frontend updates
  
- ChatPane.jsx: category bubbles, seamless categorization after each message, drift hints, Dev/User toggle
  
- GraphPane.jsx: group-by Category or Generation using backend /graph
  
- MetricsPane.jsx: category evolution and recent drift from /status
  
- ControlPane.jsx: lifecycle operations (spawn by category), mode toggle
- docker-compose.yml: unchanged service layout, compatible with existing setup
How to run
- Local dev
  
- Backend: uvicorn/flask from backend/ (Flask dev server already configured at port 5000 in app.py)
  
- Frontend: vite dev server at port 3001
  
- Ensure Neo4j and Prometheus/Grafana per existing compose
- Compose
  
- docker compose up --build
API quick test
- curl -X POST localhost:5000/categorize -H 'Content-Type: application/json' -d '{"text":"try a new approach"}'
- curl -X POST localhost:5000/spawn -H 'Content-Type: application/json' -d '{"category":"innovation"}'
- curl localhost:5000/graph
- curl localhost:5000/status
Notes
- ML/NLP logic is stubbed with deterministic/dummy implementations; replace with your models as available
- Phase 1/2 endpoints and features remain intact
- No credentials or secrets changed
Changelog
- feat(backend): add AS-FDVM engine and REST routes
- feat(frontend): AS-FDVM UI surfaces in Chat/Graph/Metrics/Control panes
- docs: README updated with new endpoints and usage
