# EvoAgent
This update adds AS-FDVM (Adaptive Search - Fractal Darwinian Virtual Machines) with minimal, non-breaking endpoints and UI features while preserving all Phase 1/2 functionality.

## What's new

### DeepSeek-OCR Integration (NEW)

- **Third Competitive Agent**: DeepSeek-OCR has been added as a specialized agent for OCR and document understanding tasks
- **Module**: `src/deepseek_ocr.py` - Provides DeepSeekOCRAgent class with image processing capabilities
- **Agent Features**:
  - Image and document processing with OCR
  - Statistics tracking for performance monitoring
  - API integration placeholder (ready for production implementation)
  - Factory function for easy agent instantiation
- **Competitive Evolution**: DeepSeek-OCR participates in the competitive evolution loop alongside DeepSeek-R1 and Qwen2.5-Coder
- **Configuration**: Set `DEEPSEEK_API_KEY` environment variable for API access
- **Status**: Framework integration complete; OCR processing pipeline ready for attachment

### Core AS-FDVM Features

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

## How to run

- Local dev
  
- Backend: uvicorn/flask from backend/ (Flask dev server already configured at port 5000 in app.py)
  
- Frontend: vite dev server at port 3001
  
- Ensure Neo4j and Prometheus/Grafana per existing compose

- Compose
  
- docker compose up --build

## API quick test

- curl -X POST localhost:5000/categorize -H 'Content-Type: application/json' -d '{"text":"try a new approach"}'

- curl -X POST localhost:5000/spawn -H 'Content-Type: application/json' -d '{"category":"innovation"}'

- curl localhost:5000/graph

- curl localhost:5000/status

## DeepSeek-OCR Usage

### Basic OCR Agent Usage

```python
from src.deepseek_ocr import create_ocr_agent

# Initialize agent
ocr_agent = create_ocr_agent(api_key="your-api-key")

# Process an image
result = ocr_agent.process_image(
    image_path="/path/to/document.png",
    prompt="Extract all text and structure from this document"
)

print(f"OCR Result: {result}")
print(f"Statistics: {ocr_agent.get_stats()}")
```

### Competitive Evolution with OCR

The competitive evolution system now supports three agents:

1. **DeepSeek-R1**: Reasoning and general coding tasks
2. **Qwen2.5-Coder**: Specialized coding tasks
3. **DeepSeek-OCR**: OCR and document understanding (NEW)

To run competitive evolution with OCR tasks:

```bash
# Set environment variables
export DEEPSEEK_API_KEY="your-key-here"
export R1_ENDPOINT="http://localhost:8001/v1"
export QWEN_ENDPOINT="http://localhost:8002/v1"

# Run competitive evolution
python src/competitive_evolution.py
```

### OCR Task Examples

The system is ready to handle OCR-specific tasks. Example task structure:

```python
ocr_task = Task(
    name="invoice_extraction",
    domain="ocr",
    description="Extract structured data from invoice images",
    test_cases=[
        {"input": "invoice_001.png", "expected": {"total": 1234.56, "vendor": "Example Corp"}},
        {"input": "invoice_002.png", "expected": {"total": 567.89, "vendor": "Test Inc"}},
    ]
)
```

## Notes

- ML/NLP logic is stubbed with deterministic/dummy implementations; replace with your models as available

- Phase 1/2 endpoints and features remain intact

- No credentials or secrets changed

- **DeepSeek-OCR**: Framework integration complete; actual OCR API calls marked with TODO comments for production implementation

- **OCR Pipeline**: The `_call_api` method in `deepseek_ocr.py` indicates where the actual OCR processing pipeline should be attached

## Changelog

- **feat(ocr)**: Add DeepSeek-OCR agent module with image processing capabilities

- **feat(competitive)**: Integrate DeepSeek-OCR into competitive evolution framework

- **docs**: Update README with DeepSeek-OCR usage and integration details

- feat(backend): add AS-FDVM engine and REST routes

- feat(frontend): AS-FDVM UI surfaces in Chat/Graph/Metrics/Control panes

- docs: README updated with new endpoints and usage

## Architecture

### Agent System

```
┌─────────────────────────────────────────────────┐
│         Competitive Evolution System            │
├─────────────────────────────────────────────────┤
│                                                 │
│  ┌──────────────┐  ┌──────────────┐           │
│  │ DeepSeek-R1  │  │ Qwen2.5-     │           │
│  │              │  │ Coder        │           │
│  └──────────────┘  └──────────────┘           │
│                                                 │
│         ┌──────────────────────┐               │
│         │  DeepSeek-OCR (NEW) │               │
│         │  - Image Processing  │               │
│         │  - Document OCR      │               │
│         │  - Data Extraction   │               │
│         └──────────────────────┘               │
│                                                 │
│  All agents compete and evolve solutions       │
│  for tasks in their respective domains          │
│                                                 │
└─────────────────────────────────────────────────┘
```

### DeepSeek-OCR Integration Points

1. **Agent Module**: `src/deepseek_ocr.py` - Core OCR agent implementation
2. **Competitive Loop**: `src/competitive_evolution.py` - Agent orchestration
3. **Metrics**: Prometheus metrics for OCR agent health and performance
4. **Task Structure**: Support for image-based test cases and evaluation

## Future Enhancements

- [ ] Complete OCR API integration with production endpoints
- [ ] Add vision task benchmarks for R1/Qwen comparison
- [ ] Expand OCR task domain definitions
- [ ] Implement structured data extraction pipelines
- [ ] Add OCR-specific fitness evaluation metrics
