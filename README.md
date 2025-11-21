# code-quality-analyzer-45203-45212

Bug Detector Backend (FastAPI)
- Service: code-quality-analyzer-45203-45212/bug_detector_backend
- Framework: FastAPI
- Purpose: Accept user code and return static analysis findings

Run
- The environment is preconfigured to run the service on port 3001.
- OpenAPI docs at /docs (e.g., http://localhost:3001/docs).

Core Endpoints
- GET /health -> { "status": "ok" }
- GET /version -> { "name": "bug-detector-backend", "version": "0.1.0" }
- POST /analyze
  Request:
  {
    "code": "print('debug')\\n# TODO: fix\\n",
    "language": "python"
  }
  Response (example):
  {
    "findings": [
      { "type": "debug_statement", "message": "Debug/print statement detected", "line": 1, "severity": "low" },
      { "type": "todo_comment", "message": "Found TODO/FIXME comment", "line": 2, "severity": "low" }
    ],
    "summary": { "count_by_severity": { "low": 2, "medium": 0, "high": 0 } }
  }

Example curl
curl -s -X POST http://localhost:3001/analyze \
  -H 'Content-Type: application/json' \
  -d '{"code":"print(\"debug\")\n# TODO: fix\n","language":"python"}' | jq .

Notes
- CORS is permissive by default for integration. Restrict allow_origins in production as needed.
- The analyzer uses simple heuristics for Python and JavaScript/TypeScript:
  - Detects debug statements (print/console.*)
  - Detects TODO/FIXME comments
  - Detects dangerous eval/exec and innerHTML assignment
  - Hints for unreachable code after return (heuristic)
  - Detects broad except: in Python