# TDCB Lab dashboard

React, TypeScript, and Vite research interface for the FastAPI simulation engine.

## Run locally

From the repository root, start the engine:

```powershell
python -m uvicorn api.main:app --reload --port 8000
```

In another terminal:

```powershell
cd dashboard
npm ci
npm run dev
```

Open the local URL printed by Vite. REST requests and WebSocket streams are proxied to port 8000. No frontend environment variables are required for local development.

## Production build

```powershell
npm --prefix dashboard run build
python -m uvicorn api.main:app --port 8000
```

Open http://localhost:8000. Run the backend from the repository root so it can locate the dashboard build and experiment artifacts.

## Workspace

- Live simulation: configuration, interactive trust network, node inspector, measured episode charts, and event log.
- Metrics explorer: saved CSV metrics and an episode-window scrubber.
- Attack laboratory: attack descriptions and summaries calculated from recorded runs.
- Scenario library: illustrative IoT presets; loading a preset opens experiment setup.
- Experiment results: search, agent and attack filters, sorting, replay, CSV download, and comparison selection.
- Compare runs: up to six recorded F1 trajectories and configuration summaries.
- System architecture: interactive descriptions of the implemented simulation components.
- Export and present: CSV/ZIP downloads, current configuration JSON, screen recording, and the paper-figure command.

The results UI uses /experiments. The /results path is reserved for the backend API.

## Presentation and accessibility

Use **Present** in the header to hide navigation, and **Exit presentation** to restore it. Print styles remove navigation and controls.

Use Alt+1 through Alt+8 to switch views. Escape closes the node inspector. Standard browser copy, refresh, and export shortcuts are preserved.

The UI includes keyboard focus indicators, labeled controls, responsive layouts, reduced-motion support, and locally bundled IBM Plex fonts.

## Interpreting results

Charts use recorded values. Unavailable metrics are not replaced with fabricated measurements. The network uses schematic delegate links, not measured physical topology. Transaction counts are not labeled as transactions per second.

Scenario presets and attack descriptions are illustrative. Performance summaries are drawn from saved experiments with potentially different settings; use matched configurations and repeated seeds for research comparisons.

The optional FHE path uses TenSEAL if available and otherwise mock encryption. The UI describes this implementation limitation explicitly.
