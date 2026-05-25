# OTM-Agent: Portfolio Summary for LG AI Research

**Candidate:** Oguzhan Tekin | **Target Role:** LG AI Research — Agentic AI | **Date:** May 22, 2026

**Live Dashboard:** https://oguzhan-canada.github.io/otm-agent-site/

---

## What I Built

**OTM-Agent** is an LLM-orchestrated agent that turns an existing production oil-storage monitoring pipeline into an autonomous decision-making system. The agent composes 20 typed skills, retrieves from a 4-tier memory, adapts to user persona, and is evaluated under strict OOS holdout enforcement. The underlying pipeline (Sentinel-1 SAR → Kalman → spread forecasting → trading signals) runs on GCP across 13 tank farms in 4 global hubs (Cushing, Rotterdam, Fujairah, Singapore).

| Layer | What it does | Key numbers |
|-------|-------------|-------------|
| **20-skill typed library** | Typed preconditions, effects, failure modes, retention probes across 7 categories | 20 skills, DAG-validated; 81.7% plan inclusion (5.1× corrected random baseline of 15.9%; 14/20 skills at 100%) |
| **4-tier memory** | Episodic, semantic, procedural, working — with causal timestamp filtering for OOS replay | 8 retrieval paths, all causally filtered |
| **Bayesian persona** | 64-dim persona vector, Kalman-updated per interaction, conditions planner skill selection | Pre-registered null at v0.1 confirmed post-fix. Re-verified after planner stop-condition fix — null holds with multi-step execution. v0.2 activation steering is the path forward |
| **Multi-objective reward** | R_directional + task quality + memory utility + consistency + retention − cost | 6 components, independently backfillable |
| **OOS holdout enforcement** | Static AST analysis in CI scans every training query for date filter | Caught 20+ unfiltered queries across 12 files |
| **Evaluation suite** | 8 domain-specific benchmarks with bootstrap CIs and 5 baselines. Three benchmarks completed with full audit trail: transparent v1→v2 reporting, both original and corrected results preserved. All v1.1 re-runs complete. Six audit cycles documented (OOS leakage, model retrain, skill-retention measurement, planner stop-condition, cost tracking, v3.0.0 architecture). | OOS Replay v1.0: 54.4% (n=237); v1.1: 50.0% (n=110, +2.5pp same-period), Skill-Retention 81.7% confirmed in v1.1 ($1.65 full cost), Persona-Align null confirmed in v1.1 (p=0.70, $1.77 full cost). Total v1.1: $16.55 |
| **Chat demo** | Agent-first chat (v3.0.0) validated with 28-query smoke test across 5 tiers | 27/28 pass, 1 marginal fixed. Average latency 57s. Progressive typing indicator. |

---

## What's Novel

**The audit cycle as methodology.** I treated my own pipeline as if it were a paper I was reviewing. The static analysis test (`test_oos_leakage.py`) scans every SQL query — including Python f-strings parsed via AST — for the holdout filter. This caught 20+ queries that would have leaked post-cutoff data into training. A second test suite (`test_causal_leakage.py`) prevents the agent's memory system from accessing future information during OOS replay by threading a `query_ts` parameter through all retrieval paths. Together, these enforce two layers of data integrity that most agentic systems lack entirely.

**Honest reporting under adversity.** The initial backtest produced Sharpe −0.10. Rather than hiding this, I diagnosed five root causes — naive signal aggregation, no confidence gating, equal weighting of 51% coin-flip models alongside a 65% regime classifier — and scoped a regime-weighted ML composite with walk-forward training and drawdown controls as the corrective workstream. The paper frames the agent's value as orchestration quality (skill selection, memory utilization, persona adaptation) — not P&L — while treating strategy improvement as separate from agentic AI evaluation.

---

## Where the Integrity Controls Are

```
otm_agent/tests/test_oos_leakage.py      → 5 tests: static AST scan for holdout filter
otm_agent/tests/test_causal_leakage.py   → 16 tests: memory can't see the future during replay  
otm_agent/bq_safe.py                     → runtime guard: raises OOSLeakageError on unfiltered queries
retrain_results/retrain_first_clean_run.json → 8 models, structured OOS-clean metrics
docs/oos_holdout_policy.md               → policy document with audit trail
```

---

## What This Demonstrates for the Role

The LG JD asks for "translate research into production-grade prototypes." This portfolio directly evidences that:

- **Research → Production:** SAR image processing, Kalman filtering, and regime classification running on GCP with BigQuery, Cloud Run, and a Streamlit dashboard.
- **Agentic AI design:** Skill composition, memory-informed planning, persona-conditioned behavior, and multi-objective reward — the core capabilities the role is hiring for.
- **Evaluation rigor:** OOS holdout enforcement, causal leakage prevention, 8-benchmark suite with statistical methodology — the kind of evaluation infrastructure that separates research prototypes from publishable work.
- **Self-correction under audit:** The most transferable skill demonstrated here isn't building the system — it's finding what's wrong with it and fixing it with receipts.

**What I'd build first at LG (90-day proposal):** Extend the OTM-Agent skill-library + memory + persona pattern to a domain LG cares about — smart home appliance orchestration, where a similar agentic architecture could compose device skills (HVAC, refrigerator, washer), retrieve user behavioral memory, and adapt to household persona. Same architecture, applied to LG's product domain. The OTM work is a transferable template, not a one-off.

---

## Key Files for Review

| Priority | File | Purpose |
|----------|------|---------|
| Start here | [Live Dashboard](https://oguzhan-canada.github.io/otm-agent-site/) | Interactive SAR monitoring + AI chat |
| Start here | `docs/OTM_Agent_Presentation.pptx` | 12-slide visual overview |
| Deep dive | `docs/OTM_Agent_Technical_Report.md` | Full 23-page technical report |
| Integrity | `otm_agent/tests/test_oos_leakage.py` | The audit that caught 20+ leaks |
| Architecture | `otm_agent/memory.py` | 4-tier memory with causal filter |
| Results | `retrain_results/retrain_first_clean_run.json` | All 8 models, OOS-clean metrics |

---

*Honest scope: live trading is paper-only; strategy v2 (regime-weighted ML composite) is scoped but not yet backtested against live BQ data; v0.2 roadmap includes activation steering and multimodal SAR encoding. Three benchmarks executed with real agent calls: OOS Replay v1.0 (54.4% directional accuracy, n=237, full-year, CI crosses 50%), v1.1 re-run with data fixes (50.0%, n=110 compressed, +2.5pp over v1.0 same period — within pre-registered 1–5pp expectation), Persona-Align (null result — v0.1 persona conditioning below detection threshold, 196 agent calls; v1.1 confirmed null with p=0.70, $1.77 full cost), and Skill-Retention (81.7% plan inclusion — 5.1× random baseline, 14/20 skills at 100%, 60 probes; v1.1 confirmed identical result at $1.65 full LLM cost). Total v1.0 estimated cost: $15–25 (corrected after discovering cost tracking only captured skill execution — see cost amendment §8.5.2). v1.1 total cost: $16.55 with full LLM tracking (OOS $13.13 + Skill-Retention $1.65 + Persona-Align $1.77). Six audit cycles documented with preserved trails: OOS leakage, model retrain, skill-retention measurement, planner stop-condition, cost tracking, v3.0.0 architecture verification (see docs/v3_0_0_audit.md). Chat demo validated with 28-query smoke test (27/28 pass). Following the v3.0.0 architecture change, a targeted audit verified that benchmark codepath behavior remained consistent (see docs/v3_0_0_audit.md). Paper methodology §8 populated with all results.*
