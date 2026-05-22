# OTM-Agent — Public Site

Static HTML/CSS site for the OTM-Agent project: an LLM-orchestrated agentic system for satellite-based oil tank monitoring and commodity intelligence.
https://oguzhan-canada.github.io/otm-agent-site/dashboard.html


## Pages

| Page | Description |
|------|-------------|
| [Home](index.html) | Project overview, key metrics, architecture diagram |
| [Architecture](architecture.html) | System diagrams, skill library, memory tiers, persona module |
| [Methods](methods.html) | OOS holdout policy, causal filter, reward design |
| [Benchmarks](benchmarks.html) | 8-benchmark evaluation suite with baselines |
| [Dashboard](dashboard.html) | Live SAR monitoring dashboard (pulls from Cloud Run API) |
| [Audit](audit.html) | Data integrity audit cycle narrative |
| [Changelog](changelog.html) | Reverse-chronological project updates |
| [About](about.html) | Author info, infrastructure, disclaimer |

## Stack

- **Static HTML/CSS** — no build tools, no framework
- **GitHub Pages** — hosting
- **Inter + JetBrains Mono** — typography (Google Fonts)
- **Chart.js** — dashboard charts (CDN)
- **Dark mode default** — light mode toggle

## Infrastructure

The dashboard page connects to live APIs on Google Cloud Run:
- `otm-api-dev` — SAR observation data
- GCP Project: `oil-tank-monitoring-123`

## License

MIT
