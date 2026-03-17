# Artemis Frontend

Vite + React + TypeScript dashboard for Project Artemis. Runs at `http://localhost:5173`.

## Dev

```bash
npm install
npm run dev
```

Requires the FastAPI backend running at `http://localhost:8000`:

```bash
# from project root
uv run uvicorn api.server:app --reload
```

See the [root README](../README.md) for full setup and usage.
