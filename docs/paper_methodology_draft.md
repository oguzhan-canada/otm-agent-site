# OTM-Agent: Agentic AI for Satellite-Based Commodity Intelligence

## Technical Report — Detailed Outline

---

### Abstract (~250 words)

- **Problem:** Commodity analysts manually integrate satellite imagery, market data, and econometric models to form storage/trading views. This requires expertise across remote sensing, time series analysis, and market microstructure — rarely found in one person.
- **Approach:** OTM-Agent — an LLM-orchestrated agentic system that wraps an operational 3-stage oil tank monitoring pipeline (SAR processing → feature engineering → signal generation) with a typed skill library (20 skills, 7 categories), 4-tier memory, Bayesian persona vectors, and multi-objective reward grounded in paper-trading P&L.
- **Key results:** 65.4% regime classification accuracy (vs 52.9% baseline); 52.8% EIA direction alignment; 8-benchmark evaluation suite with OOS holdout enforcement (12-month holdout, 5 static leakage tests, 48 queries audited); 258 tests (254 passing, 4 pre-existing failures documented). First benchmark (OTM-Persona-Align) production runner complete — 50 queries, cosine divergence + Jaccard skill distance, Wilcoxon test, bootstrap CIs.
- **Framing note:** Audit identified 20+ unfiltered training queries; all models trained from scratch with verified OOS integrity. The audit prevented future leakage rather than correcting historical leakage.
- **Public dashboard:** Live at https://oguzhan-canada.github.io/otm-agent-site/ — real-time SAR monitoring, oil-price correlation, AI chat analysis.

---

### §1. Introduction (~1.5 pages)

1.1 **The commodity intelligence problem**
- Oil storage monitoring from satellite SAR imagery (Sentinel-1)
- 4 global hubs (Cushing, Rotterdam, Fujairah, Singapore), 13 tank farms
- Current workflow: manual image analysis → spreadsheet models → trading desk
- Gap: no feedback loop, no memory across sessions, no systematic evaluation

1.2 **Why agentic AI?**
- Not just a model — an orchestrated system that selects skills, maintains context, adapts strategy
- Distinction from chatbot/RAG: agent has *typed actions* with preconditions, side effects, and measurable outcomes
- LLM as planner, not predictor — the ML models do prediction, the LLM decides what to run and when

1.3 **Contributions**
1. An operational agentic system over an existing industrial pipeline (SAR → Kalman → signals → paper trading)
2. Typed skill library with dependency DAG, retention probes, and category-aware selection
3. 4-tier memory system (episodic, semantic, procedural, working) with configurable retention
4. Bayesian persona vectors (64-d) for analyst-aligned behavior conditioning
5. Multi-objective reward function: `R = w₁·R_pnl + w₂·R_task + w₃·R_memory + w₄·R_consistency + w₅·R_retention - C_cost`
6. OOS holdout discipline with static analysis enforcement (pytest CI gate)
7. 8-benchmark evaluation suite and unified Streamlit dashboard for agent introspection

1.4 **Paper organization**
- Brief roadmap of remaining sections

---

### §2. Related Work (~1.5 pages)

2.1 **Satellite-based commodity monitoring**
- SAR for oil storage estimation (Sentinel-1 literature)
- Existing commercial solutions (Orbital Insight, Kayrros, Ursa Space)
- Gap: none integrate agentic decision-making

2.2 **LLM-based agents for decision-making**
- ReAct, Toolformer, Gorilla, TaskWeaver
- Financial agents: BloombergGPT, FinGPT
- Gap: most lack typed skill contracts, persistent memory, and grounded reward

2.3 **Offline RL for language agents**
- DPO (Rafailov et al., 2023) vs PPO
- Reward modeling from human feedback vs environment feedback
- Our approach: environment feedback (P&L) as ground truth, DPO for fine-tuning

2.4 **Evaluation of agentic systems**
- Existing benchmarks (SWE-bench, AgentBench, ToolBench)
- Gap: domain-specific benchmarks for commodity/finance agents
- Our contribution: 8 OTM-specific benchmarks

---

### §3. System Architecture (~2.5 pages)

3.1 **Base pipeline overview**
- Stage 1: Sentinel-1 SAR → tank segmentation → confidence scoring → Kalman filter → hub state
  - 5,124 SAR observations, 309 hub-state-day records (Cushing)
  - Kalman convergence: early variance 0.066 → late 0.045
- Stage 2: Market data ingestion → linkage features (347 rows) → regime/spread/EIA models → backtest
  - Data sources: calendar spreads (20K rows, 1986–2026), WTI prices (40K rows), EIA releases (1.1K)
- Stage 3: Signal generation → paper trading → governance scorecard → API
  - Daily composite signal from 3 Stage 2 models

3.2 **Agent layer architecture**

```
┌─────────────────────────────────────────────────────┐
│                    OTM-Agent                         │
│  ┌──────────┐  ┌──────────┐  ┌───────────────────┐  │
│  │ Planner  │→ │ Executor │→ │ Reward / Eval     │  │
│  │ (LLM)    │  │ (Skills) │  │ (Multi-objective) │  │
│  └────┬─────┘  └──────────┘  └───────────────────┘  │
│       │             ↑                                │
│  ┌────▼─────┐  ┌────┴─────┐                         │
│  │ Memory   │  │ Persona  │                         │
│  │ (4-tier) │  │ (64-d)   │                         │
│  └──────────┘  └──────────┘                         │
└─────────────────────────────────────────────────────┘
         ↕                    ↕
┌─────────────────┐  ┌──────────────────┐
│ Stage 1-3       │  │ External APIs    │
│ Pipeline        │  │ (BQ, Cloud Run)  │
└─────────────────┘  └──────────────────┘
```

3.3 **Planner**
- LLM generates skill sequences given state, memory, persona
- Max 3 replans per turn; 0.50 cost cap
- Plan validation: skill existence check, precondition verification

3.4 **Executor**
- Typed skill dispatch with error handling
- Side-effect tracking for memory updates
- Execution trace logging for dashboard replay

---

### §4. Skill Library (~2 pages)

4.1 **Design principles**
- Each skill: name, category, preconditions, side effects, retention probe
- Skills wrap existing pipeline components — no new models, just orchestrated access
- Dependency DAG prevents invalid skill sequences

4.2 **Skill taxonomy (7 categories, 20 skills)**

| Category | Skills | Example |
|----------|--------|---------|
| BigQuery | fetch_tank_features, fetch_market_data, fetch_calendar_spreads | SQL queries against BQ |
| Compute | run_kalman_filter, compute_tightness_index, compute_spread_zscore | In-memory computation |
| ML | predict_regime, predict_spread_direction, predict_eia_surprise | Model inference |
| Cloud Run | trigger_sar_pipeline, trigger_daily_signals | Job orchestration |
| Trade | generate_trade_signal, execute_paper_trade, check_position_limits | Trading actions |
| LLM | summarize_market_state, explain_signal_rationale, draft_report | Language generation |
| Alert | check_anomaly_thresholds, send_alert_notification | Monitoring |

4.3 **Retention probes**
- After skill execution, agent is queried to recall key outputs
- Retention score contributes to R_retention in reward function
- Prevents "tool-using without understanding" failure mode

---

### §5. Memory System (~1.5 pages)

5.1 **Architecture**
- 4 tiers: episodic (specific events), semantic (facts/rules), procedural (skill sequences), working (current context)
- Each tier: store, retrieve, decay, consolidate operations

5.2 **Memory-informed planning**
- Planner retrieves relevant episodes before generating skill sequence
- Semantic memory provides domain facts (e.g., "Cushing capacity is 76M barrels")
- Procedural memory recalls successful skill chains from similar contexts

5.3 **Memory utility in reward**
- R_memory rewards effective retrieval and consolidation
- Prevents memory hoarding (too much retrieval) and memory neglect (never using stored context)

---

### §6. Persona Modeling (~1 page)

6.1 **Bayesian persona vectors**
- 64-dimensional vector representing analyst preferences and risk profile
- Updated via Bayesian posterior after each interaction
- Dimensions: risk tolerance, timeframe preference, data source trust, signal threshold, etc.

6.2 **Persona-conditioned planning**
- Same market state → different skill sequences depending on persona
- Conservative persona: more validation skills before trading
- Aggressive persona: faster signal-to-trade pipeline

6.3 **Persona alignment evaluation**
- OTM-Persona-Align benchmark: does agent behavior match stated persona?
- OTM-MultiTurn-Persona: does persona remain consistent across turns?

---

### §7. Reward Function (~1.5 pages)

7.1 **Multi-objective formulation**
```
R = w₁·R_pnl + w₂·R_task + w₃·R_memory + w₄·R_consistency + w₅·R_retention - C_cost
```

7.2 **Component definitions**
- **R_pnl:** Delayed paper-trading P&L (lagged by EIA release cycle, ~7 days)
  - *Note on negative Sharpe (-0.10):* P&L reward is correlated with trade quality but does not guarantee profitability. Agent value is measured by recommendation alignment with subsequent market direction, not absolute returns. Current strategy needs refinement (see §10).
- **R_task:** Did the skill complete successfully? Correct outputs?
- **R_memory:** Was retrieved context useful? Was new context stored appropriately?
- **R_consistency:** Do successive turns maintain coherent state?
- **R_retention:** Can the agent recall key facts from recent skill executions?
- **C_cost:** LLM API cost + compute cost (bounded by planner's 0.50 cap)

7.3 **DPO training (Phase B)**
- Generate paired trajectories (preferred vs rejected) from reward signal
- Fine-tune base model with DPO loss
- Target: Qwen 2.5 7B for cost-efficient deployment

---

### §8. Evaluation (~3 pages) ← *This is the section that sells the paper*

8.1 **OOS holdout protocol**
- Cutoff: 2025-05-01 (12-month holdout window)
- Enforcement: static AST analysis via pytest (5 tests, CI-blocking)
- 48 training-table queries identified and audited
- 20+ queries received date filter additions
- Runtime guard: `TrainingBQClient` wrapper with pragma exceptions
- Policy document: `docs/oos_holdout_policy.md`

*Framing A (recommended):* "Audit identified 20+ training queries lacking the OOS cutoff filter. Static analysis test added to CI to prevent regression. Models were retrained from scratch against the corrected query set; this is the first set of training runs with verified OOS integrity. The audit thus prevented future leakage rather than correcting historical leakage."

8.2 **Benchmark suite (8 benchmarks)**

| Benchmark | What it measures | Key design choice |
|-----------|-----------------|-------------------|
| OTM-LongCtx | Agent performance with large context windows | Not raw context window — tests *useful* context utilization |
| OTM-Skill-Retention | Can agent recall skill outputs after N turns? | Prevents "use and forget" pattern |
| OTM-Persona-Align | Does behavior match stated persona? | Tests persona vector actually influences planning |
| OTM-DistShift | Robustness to distribution shift in market data | Regime changes, volatility spikes |
| OTM-OOS-Replay | Full trajectory replay on held-out period | The integrity benchmark — uses 2025-05+ data only |
| OTM-Mem-Utility | Is memory retrieval actually useful for decisions? | Ablation: with memory vs without. **v1.1 result: −0.064 (null, CI crosses zero, n=25, $1.39)** |
| OTM-MultiTurn-Persona | Persona consistency across multi-turn sessions | Skill divergence increases across turns. **v1.1 result: +0.173 convergence delta (p=0.109, n=7, $2.57)** |
| OTM-Mem-Ablation | Which memory tier contributes most? | Drop one tier at a time, measure impact |

8.3 **Model results (OOS-clean, v0.2.0)**

| Model | Task | Metric | Value | Baseline |
|-------|------|--------|-------|----------|
| Stage 1 Kalman | SAR → hub state | EIA direction accuracy | 52.8% | 50% (random) |
| Regime classifier | Contango/backwardation | Walk-forward accuracy | 65.4% | 52.9% (majority class) |
| Spread forecaster | Spread direction | Walk-forward accuracy | 51.4% | 50% (random) |
| EIA surprise | Inventory surprise | Direction accuracy | 51.5% | 50% (random) |
| EIA surprise | Inventory surprise | RMSE | 1,606 kb | 1,616 kb (naive) |
| VAR | Tightness + spread | 1-step forecast | tightness=0.015 | — |
| GARCH | Spread volatility | Conditional vol | 2.64 | — |
| Backtest | Paper trading | Sharpe ratio | -0.10 | 0.0 (flat) |

8.4 **Interpreting the negative Sharpe**
- Spread forecaster and EIA surprise at ~51% are essentially coin-flip on noisy financial data
- Regime classifier at 65.4% carries most signal in the composite
- Strategy logic in `signal_generator.py` needs its own iteration — the agent can't rescue a strategy with no edge
- Reframing: agent's value is in *orchestration quality* (right skills, right order, right context), not in the underlying strategy's P&L
- Future work: reward shaping to emphasize recommendation alignment over absolute returns

8.5 **Test suite coverage**
- 258 tests across 12 modules (254 passing, 4 pre-existing failures documented)
- 5/5 OOS holdout tests passing
- Coverage: planner, persona, memory, skills (compute, alert), evaluation, registry, schema, training, loader

---

### §9. Dashboard (~1 page)

9.1 **Design: unified research + demo interface**
- 9 Streamlit pages: 3 migrated from existing HTML dashboards, 5 new agentic pages, 1 global index
- Single-source-of-truth: all skill names, benchmarks, model strings from `constants.py`
- Real-data-first with demo watermark fallback

9.2 **Key pages for agent introspection**
- Agent Chat (P5): interactive skill execution with traces
- Agent Traces (P6): session replay, skill DAG, cost tracking
- Memory Explorer (P7): browse all 4 memory tiers
- Persona State (P8): persona vector compass + covariance visualization
- Eval & Benchmarks (P9): benchmark comparison, reward decomposition, ablation studies

---

### §10. Discussion (~1.5 pages)

10.1 **What worked**
- Typed skill contracts: clear preconditions prevent invalid sequences
- OOS holdout enforcement: static analysis as first-class CI gate
- Audit cycle as methodology: "treat your own pipeline as a paper you're reviewing"
- Single-source-of-truth architecture across dashboard, eval, and documentation

10.2 **What needs work**
- **Strategy edge:** Spread and EIA models at ~51% don't provide meaningful signal; composite relies on regime classifier alone
- **Negative Sharpe:** Trading strategy needs independent refinement before P&L can serve as meaningful reward signal
- **Category B causal leakage:** Memory retrieval during OOS replay can still access future events (deferred to v0.2)
- **DPO training not yet executed:** Infrastructure ready (Phase B), but requires strategy edge first
- **Limited to Cushing hub:** 4 hubs in pipeline but models trained on Cushing only

10.3 **Lessons for agentic system design**
- Ground reward in environment feedback, not just human preference
- Memory is only useful if you test that it's actually used (retention probes)
- Persona modeling prevents "generic assistant" failure mode
- OOS discipline is harder for agents than for static models — more query surfaces to audit

---

### §11. Future Work (~0.5 pages)

- **v0.2:** Category B causal filter (`query_ts` on 5 memory retrieval sites) + OOS replay execution
- **v0.3:** DPO fine-tuning with corrected reward signal (requires strategy iteration first)
- **Multi-hub expansion:** Rotterdam, Fujairah, Singapore (data exists in pipeline)
- **Activation steering:** Lightweight persona adaptation without full fine-tuning
- **Live deployment:** Cloud Run → Cloud Functions event-driven architecture

---

### §12. Conclusion (~0.5 pages)

- OTM-Agent demonstrates that agentic AI can orchestrate an existing industrial ML pipeline with typed skills, persistent memory, and persona-conditioned planning
- The audit cycle — catching and preventing data leakage through static analysis — is a transferable contribution to any agentic system with training data
- Honest accounting: the underlying strategy doesn't yet have enough edge for P&L-based reward to be meaningful, but the orchestration, evaluation, and integrity infrastructure is production-ready

---

### Appendices

**A. Full skill catalog** (20 skills with preconditions, side effects, retention probes)

**B. BQ table schema and row counts** (pre/post OOS filter impact)
- `sentinel1_weekly_tank_features`: 5,124 → 4,578 (−10.7%)
- `calendar_spreads`: 20,276 → 19,804 (−2.3%)
- `market_prices`: 40,014 → 39,062 (−2.4%)

**C. OOS leakage test implementation** (AST scanning, regex patterns, allowlist)

**D. Retrain results JSON** (full structured output for all 8 models)

**E. Dashboard screenshots** (all 9 pages)

---

### Figures list (to produce during full draft)

1. System architecture diagram (§3.2)
2. Skill dependency DAG (§4)
3. Memory tier interaction diagram (§5)
4. Persona vector compass visualization (§6)
5. Reward component weights and tradeoffs (§7)
6. Walk-forward accuracy curves for regime/spread/EIA models (§8.3)
7. OOS holdout timeline diagram (§8.1)
8. Dashboard composite screenshot (§9)
