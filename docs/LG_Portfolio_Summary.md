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
| **Evaluation suite** | 8 domain-specific benchmarks with bootstrap CIs and 5 baselines. Three pre-registered benchmarks completed at planned scale with full audit trail: transparent v1→v2 reporting, both original and corrected results preserved. Two exploratory benchmarks executed at reduced scale (not pre-registered, statistically underpowered — reported for transparency). Seven audit cycles documented (OOS leakage, model retrain, skill-retention measurement, planner stop-condition, cost tracking, v3.0.0 architecture, process slip detection). | OOS Replay v1.0: 54.4% (n=237); v1.1: 50.0% (n=110, +2.5pp same-period), Skill-Retention 81.7% confirmed in v1.1 ($1.65), Persona-Align null confirmed (p=0.70, $1.77). Exploratory: Mem-Utility null (−0.064, n=25, $1.39), MultiTurn-Persona underpowered (+0.173, p=0.109, n=7, $2.57). Total v1.1: $20.51 ($0.51 over $20 cap) |
| **Chat demo** | Agent-first chat (v3.0.0) validated with 28-query smoke test across 5 tiers | 27/28 pass, 1 marginal fixed. Average latency 57s. Progressive typing indicator. |

---

## What's Novel

**The audit cycle as methodology.** I treated my own pipeline as if it were a paper I was reviewing. The static analysis test (`test_oos_leakage.py`) scans every SQL query — including Python f-strings parsed via AST — for the holdout filter. This caught 20+ queries that would have leaked post-cutoff data into training. A second test suite (`test_causal_leakage.py`) prevents the agent's memory system from accessing future information during OOS replay by threading a `query_ts` parameter through all retrieval paths. Together, these enforce two layers of data integrity that most agentic systems lack entirely.

**Honest reporting throughout the audit cycle.** The OOS Replay v1.1 directional accuracy of 50.0% (n=110, CI 40.9–60.0%) is statistically indistinguishable from chance — the honest measurement of the composite trading signal under strict OOS holdout. Rather than framing this as a setback, the project distinguishes what the agent does well (81.7% plan inclusion on the skill router) from what the underlying signal does poorly (dilution of the 65% in-sample regime classifier through near-chance composite components). Strategy refinement is a separate v0.3 workstream; the agentic AI evaluation stands on its own.

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

*Honest scope: live trading is paper-only; strategy v2 (regime-weighted ML composite) is scoped but not yet backtested against live BQ data; v0.2 roadmap includes activation steering and multimodal SAR encoding. Three pre-registered benchmarks executed at planned scale with real agent calls: OOS Replay v1.0 (54.4% directional accuracy, n=237, full-year, CI crosses 50%), v1.1 re-run with data fixes (50.0%, n=110 compressed, +2.5pp over v1.0 same period — within pre-registered 1–5pp expectation), Persona-Align (null result — v0.1 persona conditioning below detection threshold, 196 agent calls; v1.1 confirmed null with p=0.70, $1.77), Skill-Retention (81.7% plan inclusion — 5.1× random baseline, 14/20 skills at 100%, 60 probes; v1.1 confirmed identical result at $1.65). Two exploratory benchmarks executed at reduced scale without pre-registration: Mem-Utility (null result — memory does not detectably improve response quality, −0.064, CI crosses zero, n=25 of designed 500, $1.39) and MultiTurn-Persona (statistically underpowered — +0.173 convergence delta, p=0.109, n=7 of designed 100, $2.57; result not interpretable at this sample size). v1.1 benchmark suite total cost: $20.51 ($16.55 for pre-registered benchmarks, $3.96 for exploratory; $0.51 over committed $20 API credit cap due to cost variance). Seven audit cycles documented with preserved trails: OOS leakage, model retrain, skill-retention measurement, planner stop-condition, cost tracking, v3.0.0 architecture verification, and process slip detection — the methodology applied to its own author (see docs/v3_0_0_audit.md). Chat demo validated with 28-query smoke test (27/28 pass). Paper methodology §8 populated with all results.*
