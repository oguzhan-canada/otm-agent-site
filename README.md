# OTM-Agent — Public Site

Live dashboard and documentation for the **OTM-Agent** project: an LLM-orchestrated agentic system for satellite-based oil tank monitoring and commodity intelligence.

**Live site:** https://oguzhan-canada.github.io/otm-agent-site/

---

## Pages

| Page | Description |
|------|-------------|
| [Dashboard (Home)](index.html) | Live SAR monitoring dashboard — real-time tank signals, daily trends, oil-price correlation, AI chat assistant |
| [Architecture](architecture.html) | System diagrams, skill library, memory tiers, persona module |
| [Methods](methods.html) | OOS holdout policy, causal filter, reward design |
| [Benchmarks](benchmarks.html) | 8-benchmark evaluation suite with baselines |
| [Paper](paper.html) | Technical report overview |
| [About](about.html) | Author info, infrastructure, disclaimer |

## Dashboard Features

- **4 global hubs monitored:** Cushing 🇺🇸, Rotterdam 🇳🇱, Fujairah 🇦🇪, Singapore 🇸🇬
- **13 floating-roof tanks** tracked via Sentinel-1 SAR radar
- **Daily Trend chart** with available capacity % and WTI crude overlay
- **Oil Price vs. Tank Signal** correlation chart with Pearson r
- **AI Chat Widget** with data-driven analysis (local keyword routing + Cloud Run agent API)
- **Auto-extend logic** for sparse SAR observation periods (14d/30d windows)

## Stack

- **Static HTML/CSS/JS** — no build tools, no framework, single-file dashboard
- **GitHub Pages** — hosting (auto-deploys from `master`)
- **Inter + JetBrains Mono** — typography (Google Fonts)
- **Chart.js** — dashboard charts (CDN)
- **Dark mode default** — light mode toggle

## Infrastructure

The dashboard connects to live APIs on Google Cloud Run:

| Service | Purpose |
|---------|---------|
| `otm-api-dev` | SAR observation data, tank features, region signals |
| `otm-agent-chat` | AI agent API (Claude-powered analysis) |
| GCP Project | `oil-tank-monitoring-123` |

Data pipeline runs daily at 02:00 UTC via Cloud Scheduler → Cloud Run Jobs.

## Data Sources

- **Sentinel-1 SAR** — C-band radar, 6–12 day revisit per location
- **WTI Crude Oil** — EIA weekly report prices (via GitHub-hosted CSV)
- **Pipeline history** — 9+ years of observations (Apr 2017 – present)

## Recent Updates (May 2026)

- Dashboard is now the homepage (no separate Home/Dashboard split)
- Removed Audit and Changelog pages (content consolidated)
- Added available capacity % (inverted from fill estimate for better visual contrast)
- Backfilled 5-week SAR data gap (Apr 14 – May 21) via Earth Engine
- AI chat now returns data-driven analysis with Pearson correlation, trend computation, and market interpretation
- Added cache-busting headers and auto-extend logic for sparse data windows

## License

MIT
