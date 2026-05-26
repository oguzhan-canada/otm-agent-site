# OTM-Agent: Agentic AI for Satellite-Based Commodity Intelligence

**Technical Report — May 2026 (v1.1 Updated)**

---

## Abstract

Commodity analysts routinely integrate satellite imagery, market microstructure data, and econometric models to form views on global oil storage. This workflow demands expertise spanning remote sensing, time-series analysis, and energy trading — a combination rarely found in a single practitioner and difficult to systematize. We present **OTM-Agent**, an LLM-orchestrated agentic system that wraps an operational three-stage oil tank monitoring pipeline — Sentinel-1 SAR processing, feature engineering, and signal generation — with a typed skill library (20 skills across 7 categories), a four-tier memory system (episodic, semantic, procedural, working), Bayesian persona vectors (64 dimensions), and a multi-objective reward function grounded in paper-trading profit and loss. The agent's planner selects skill sequences conditioned on retrieved memory and persona state, while a separate executor dispatches typed actions with tracked preconditions and side effects. We evaluate the system using an 8-benchmark suite purpose-built for commodity intelligence agents, with a 12-month out-of-sample holdout enforced by static AST analysis integrated into CI. Five benchmarks were executed with real agent calls and re-verified across two versions (v1.0 and v1.1): OOS Replay produced 54.4% directional accuracy (n=237, CI crosses 50% — statistically indistinguishable from random); Skill-Retention achieved 81.7% plan inclusion (5.1× corrected random baseline, stable across both versions); Persona-Align confirmed a pre-registered null result (1.001× baseline, p=0.70 — in-prompt persona injection does not produce detectable behavioral change at v0.1); Mem-Utility found no detectable memory benefit (−0.064, CI crosses zero); and MultiTurn-Persona showed suggestive but non-significant persona convergence (+0.173, p=0.109). Six audit cycles identified and corrected measurement infrastructure bugs — OOS leakage in training queries, planner stop-condition errors, and incomplete cost tracking — with each fix documented, re-verified, and published transparently. Three additional cycles addressed model provenance, skill-retention measurement methodology, and v3.0.0 architecture verification — six total audit revolutions with full disclosure. Total evaluation cost: $20.51 across all v1.1 re-runs, 7× under the $150 budget. On OOS-clean data, the regime classifier achieves 65.4% walk-forward accuracy against a 52.9% majority-class baseline, Stage 1 Kalman filtering aligns with EIA inventory direction at 52.8%, and the full system produces daily composite trading signals with quantified confidence. A strategy investigation identified the root cause of the initially negative backtest Sharpe (naive tightness-delta signal with no confidence gating) and implemented a regime-weighted ML composite with walk-forward training, confidence thresholding, and drawdown-based risk controls. We release the evaluation framework, dashboard, and holdout enforcement tooling as contributions to the broader agentic AI research community.

---

## 1. Introduction

### 1.1 The Commodity Intelligence Problem

Global crude oil storage levels are among the most closely watched indicators in energy markets. Weekly inventory reports from the U.S. Energy Information Administration (EIA) regularly move crude oil futures prices by several percent, and the ability to anticipate these reports — even directionally — constitutes a significant informational advantage.

Satellite-based monitoring of oil storage tanks offers an alternative measurement channel. Synthetic Aperture Radar (SAR) imagery from the Sentinel-1 constellation can estimate tank fill levels by measuring the radar backscatter characteristics of floating-roof tanks, where the roof height varies with the volume of oil stored. Commercial providers such as Orbital Insight, Kayrros, and Ursa Space Systems have demonstrated the viability of this approach at scale.

However, translating raw SAR measurements into actionable trading signals requires integrating multiple analytical domains: image processing and quality control, state estimation under uncertainty (Kalman filtering), feature engineering that links physical measurements to market data (calendar spreads, commitment-of-traders positions, EIA release schedules), regime classification, spread forecasting, and ultimately signal generation with position sizing and risk management. This pipeline spans remote sensing, time-series econometrics, and market microstructure — expertise that is rarely combined in a single analyst or even a single team.

The OTM (Oil Tank Monitoring) system addresses this integration challenge through a three-stage pipeline deployed on Google Cloud Platform, monitoring 13 tank farms across 4 global hubs: Cushing (Oklahoma), Rotterdam, Fujairah, and Singapore. Stage 1 processes Sentinel-1 SAR observations through confidence scoring, z-score normalization, and Kalman filtering to produce daily hub-state estimates. Stage 2 ingests market data (WTI prices, calendar spreads, COT positions, EIA releases) and joins them with Stage 1 output to build linkage features, which feed regime classification, spread direction forecasting, and EIA surprise prediction models. Stage 3 generates daily composite trading signals, executes paper trades, and maintains a governance scorecard.

### 1.2 Why Agentic AI?

The existing pipeline is effective but static: it runs on a fixed schedule, executes a predetermined sequence of operations, and produces outputs that require manual interpretation. Three limitations motivate an agentic extension:

**No feedback loop.** The pipeline produces signals but does not learn from the outcomes of acting on those signals. Whether a regime prediction led to a profitable trade or a losing one, the next day's pipeline runs identically.

**No memory across sessions.** Each pipeline run is stateless. The system cannot recall that last week's EIA surprise was anomalous, that Cushing storage has been trending down for three months, or that a particular signal combination has historically preceded regime transitions.

**No adaptive behavior.** Different analysts have different risk tolerances, timeframe preferences, and trust levels for different data sources. The pipeline treats all consumers identically.

An agentic architecture addresses these limitations by introducing an LLM-based planner that selects which pipeline components to run and in what order, a persistent memory system that maintains context across sessions, a persona model that adapts behavior to individual analysts, and a reward function that closes the feedback loop between actions and outcomes.

Critically, the LLM serves as a *planner*, not a *predictor*. The statistical models in Stages 1–3 handle prediction; the LLM decides what to run, when, and how to interpret the results in context. This separation of concerns allows the agentic layer to add value through orchestration without introducing the well-documented reliability problems of using language models for numerical prediction.

### 1.3 Contributions

This work makes the following contributions:

1. **An operational agentic system over an existing industrial pipeline.** OTM-Agent wraps a production SAR-to-trading-signal pipeline with LLM-orchestrated planning, rather than building a toy environment or simulation.

2. **A typed skill library with dependency DAG.** Each of the 20 skills has declared preconditions, side effects, failure modes, and retention probes. The skill registry validates plans against a dependency graph before execution.

3. **A four-tier memory system.** Episodic, semantic, procedural, and working memory tiers provide structured context to the planner, with retrieval parameterized by state signature and query similarity.

4. **Bayesian persona vectors.** A 64-dimensional persona vector, updated via Kalman-style Bayesian inference after each interaction, conditions the planner's skill selection on analyst preferences and risk profile.

5. **A multi-objective reward function.** `R = R_directional + α·R_task + β·R_memory + γ·R_consistency + δ·R_retention − λ·C_cost`, where directional alignment with subsequent price movement provides the environment-grounded signal and auxiliary components capture task quality, memory utility, behavioral consistency, and knowledge retention. Sharpe ratio is reported as a secondary diagnostic, not the headline metric.

6. **OOS holdout enforcement via static analysis.** A pytest-based CI gate uses AST parsing to scan all training queries for the holdout date filter, preventing data leakage at the source code level.

7. **Causal leakage prevention for OOS replay.** A `query_ts` parameter threaded through all memory retrieval paths (episodic, semantic, procedural, working) and the `compare_to_history` skill prevents the agent from accessing future information during out-of-sample replay evaluation. Enforced by 16 dedicated causal leakage tests covering both local cache filtering and BQ query static analysis.

8. **An 8-benchmark evaluation suite** with domain-specific tests for long-context utilization, skill retention, persona alignment, distribution shift robustness, out-of-sample replay, memory utility, multi-turn persona consistency, and memory tier ablation. Five benchmarks executed with real agent calls and re-verified across two versions (v1.0, v1.1): 81.7% skill-inclusion accuracy (5.1× baseline), pre-registered persona null confirmed (p=0.70), directional accuracy statistically indistinguishable from random (54.4% full-year, CI crosses 50%), memory utility null (−0.064, CI crosses zero), and suggestive multi-turn persona convergence (+0.173, p=0.109). Six audit cycles documented with preserved trails. Total evaluation cost: $20.51.

9. **An audit-cycle methodology** applied to the evaluation infrastructure itself. Six complete audit cycles — OOS leakage, model retrain provenance, skill-retention measurement bugs, planner stop-condition, cost tracking, and v3.0.0 architecture verification — each discovered and corrected integrity failures with preserved audit trails and transparent disclosure. The methodology, crystallized in the operational rule "copy from source, never from memory," demonstrates that evaluation rigor should extend to the evaluation tooling, not just the system under test.

### 1.4 Paper Organization

Section 2 reviews related work across satellite commodity monitoring, LLM-based agents, offline RL for language models, and agentic evaluation. Section 3 describes the system architecture, including the base pipeline and the agent layer. Sections 4–7 detail the skill library, memory system, persona model, and reward function, respectively. Section 8 presents the evaluation methodology and results. Section 9 describes the unified dashboard for agent introspection. Section 10 discusses findings, limitations, and lessons learned. Section 11 outlines future work, and Section 12 concludes.

---

## 2. Related Work

### 2.1 Satellite-Based Commodity Monitoring

The use of SAR imagery for oil storage estimation has a growing literature. Sentinel-1 C-band SAR provides regular revisit times (6–12 days) and all-weather imaging capability, making it well-suited for monitoring floating-roof tank farms where roof displacement correlates with stored volume (Sehgal et al., 2021). Commercial systems from Orbital Insight, Kayrros, and Ursa Space Systems have operationalized this approach, providing weekly or daily storage estimates to energy trading firms and government agencies.

Previous academic work has focused primarily on the image processing pipeline: tank detection, segmentation, and fill-level estimation (Datcu et al., 2019). Less attention has been paid to the downstream challenge of translating SAR-derived storage estimates into actionable trading signals, which requires integrating the physical measurements with market data and econometric models. To our knowledge, no prior work has applied agentic AI to this integration problem.

### 2.2 LLM-Based Agents for Decision-Making

The emergence of large language models as planning and reasoning engines has spawned a rich literature on LLM-based agents. ReAct (Yao et al., 2023) interleaves reasoning and action traces; Toolformer (Schick et al., 2023) teaches models to use external tools via self-supervision; Gorilla (Patil et al., 2023) specializes in API call generation; and TaskWeaver (Qin et al., 2023) frames complex tasks as code generation with plugin support.

In the financial domain, BloombergGPT (Wu et al., 2023) demonstrates domain-specific pretraining on financial text, while FinGPT (Yang et al., 2023) provides an open-source framework for financial language models. However, these systems primarily operate as enhanced language models rather than agents with typed actions, persistent memory, and grounded reward signals.

OTM-Agent differs from these approaches in three ways: (a) skills have typed contracts with preconditions and side effects, preventing invalid action sequences; (b) a four-tier memory system maintains context across sessions rather than relying solely on in-context retrieval; and (c) the reward signal is grounded in environment feedback (paper-trading P&L) rather than human preference alone.

### 2.3 Offline RL for Language Agents

Reinforcement learning from human feedback (RLHF) has become the standard approach for aligning language models (Ouyang et al., 2022). Direct Preference Optimization (DPO; Rafailov et al., 2023) simplifies RLHF by eliminating the reward model training step, directly optimizing the policy from preference pairs.

Our approach extends DPO to an agentic setting where preference pairs are generated from environment feedback rather than human annotation. Specifically, agent trajectories whose recommended direction aligns with subsequent price movement (positive R_directional) are preferred over those that do not, with auxiliary reward components providing signal on non-financial dimensions of agent quality. This is closer to the offline RL formulation of Levine et al. (2020) than to standard RLHF, as the reward is determined by the environment rather than a human rater.

The target architecture uses Qwen 2.5 7B as the base model for DPO fine-tuning, chosen for cost-efficient deployment on Cloud Run. The fine-tuning infrastructure is built but not yet executed, pending strategy refinement to ensure the P&L reward signal carries sufficient edge (see Section 10).

### 2.4 Evaluation of Agentic Systems

Existing benchmarks for LLM-based agents — SWE-bench (Jimenez et al., 2024), AgentBench (Liu et al., 2023), ToolBench (Qin et al., 2023) — evaluate general-purpose coding or tool-use capabilities. These benchmarks do not capture the domain-specific challenges of commodity intelligence: long-horizon decision-making under uncertainty, regime-dependent strategy selection, memory-dependent context accumulation, and the need for persona-aligned behavior.

We contribute 8 domain-specific benchmarks (Section 8.2) designed to evaluate these capabilities, along with 5 baselines ranging from a scheduled rule-based system to an oracle with perfect foresight.

---

## 3. System Architecture

### 3.1 Base Pipeline

The OTM pipeline consists of three stages, each deployed as Cloud Run jobs on Google Cloud Platform with BigQuery as the primary data store.

**Stage 1: SAR Processing and State Estimation.** Raw Sentinel-1 SAR observations are processed through a confidence scoring module that assigns quality weights based on acquisition geometry, weather conditions, and temporal recency. Observations are then z-score normalized and fed into a Kalman filter that produces daily hub-state estimates — a tightness index (0 = empty, 1 = full) with associated uncertainty (variance). The Kalman filter converges from an initial variance of 0.066 to 0.045 over 309 observation days for the Cushing hub, demonstrating appropriate uncertainty reduction as evidence accumulates. The pipeline processes 5,124 SAR observations for Cushing, producing 309 hub-state-day records used downstream.

**Stage 2: Feature Engineering and Modeling.** Market data ingestion brings in WTI spot prices (40,014 records, 1986–2026), calendar spreads (20,276 records), COT positions (327 records), and EIA release schedules (1,148 records). A linkage feature builder joins Stage 1 hub-state output with market data to produce 347 aligned feature rows. Three models consume these features:

- *Regime Classifier:* LightGBM binary classifier distinguishing contango (184 samples) from backwardation (160 samples) regimes. Walk-forward evaluation with `min_train=15` expanding window.
- *Spread Direction Forecaster:* LightGBM classifier predicting next-period spread movement direction from 9 features including tightness metrics and market data.
- *EIA Surprise Predictor:* LightGBM model predicting EIA weekly inventory report direction and magnitude from hub-state features.

A backtest engine evaluates the composite strategy over the historical period.

**Stage 3: Signal Generation and Governance.** A signal generator combines Stage 2 model outputs into a daily composite trading signal (long/short/flat) with associated confidence. A paper trading module executes simulated trades, and a governance scorecard tracks prediction accuracy over time. An API endpoint exposes signals for downstream consumption.

### 3.2 Agent Layer

OTM-Agent wraps the base pipeline with five interconnected components:

```
┌──────────────────────────────────────────────────────┐
│                      OTM-Agent                        │
│                                                       │
│   ┌──────────┐    ┌──────────┐    ┌───────────────┐   │
│   │ Planner  │ →  │ Executor │ →  │ Reward / Eval │   │
│   │ (LLM)    │    │ (Skills) │    │ (Multi-obj.)  │   │
│   └────┬─────┘    └──────────┘    └───────────────┘   │
│        │               ↑                              │
│   ┌────▼─────┐    ┌────┴─────┐                        │
│   │ Memory   │    │ Persona  │                        │
│   │ (4-tier) │    │ (64-d)   │                        │
│   └──────────┘    └──────────┘                        │
│                                                       │
└───────────────────────────────────────────────────────┘
          ↕                        ↕
   ┌──────────────┐    ┌──────────────────┐
   │  Stages 1–3  │    │  External APIs   │
   │  Pipeline    │    │  (BQ, Cloud Run) │
   └──────────────┘    └──────────────────┘
```

**Figure 1.** OTM-Agent architecture. The planner generates skill sequences conditioned on memory and persona. The executor dispatches typed skills against the base pipeline. The reward module computes multi-objective feedback that updates memory and persona for subsequent turns.

### 3.3 Turn Flow

A single agent turn proceeds as follows:

1. **Context assembly.** The agent creates a `WorkingMemory` instance and populates it with the user query and any provided context.

2. **Persona retrieval.** The `PersonaManager` retrieves (or creates) the 64-d persona vector for the current user, inferring the initial mode from the query content on first contact.

3. **State signature computation.** A state signature is computed from the current regime, volatility regime, and dominant persona mode, producing an 8-character MD5 hash used to index procedural memory.

4. **Memory retrieval.** The `MemoryManager` retrieves context from all four tiers: the 3 most similar episodic memories, the 5 most relevant semantic facts, and the 2 best-performing procedural sequences for the current state signature.

5. **Plan generation.** The planner's LLM call receives the user query, retrieved memory context, persona state, and the skill catalog. It generates a structured JSON plan containing a goal, rationale, and ordered list of skill steps.

6. **Plan validation.** The skill registry validates the plan: each skill must exist, preconditions must be satisfiable from accumulated effects, no skill may appear more than 3 times, total estimated cost must not exceed $0.50, and the step count must not exceed 10.

7. **Execution.** The executor dispatches each skill in sequence, tracking side effects and recording execution traces. If a skill fails and the result indicates replanning is appropriate, the planner generates a revised plan (up to 3 replans per turn). Execution stops if cumulative cost exceeds the per-turn budget, if confidence drops below 0.30, or if a hard failure occurs.

8. **Response generation.** The agent synthesizes a natural-language response from the skill outputs, memory context, and persona-conditioned style.

9. **Memory persistence.** The turn is recorded as an episodic memory entry. Semantic facts are extracted and stored (or existing facts reinforced). The skill sequence and its reward are recorded as procedural memory. The persona vector is updated based on the interaction.

### 3.4 Configuration

Key configuration parameters, with defaults:

| Parameter | Value | Description |
|-----------|-------|-------------|
| `max_replans` | 3 | Maximum replan attempts per turn |
| `max_cost_per_turn` | $0.50 | Cost cap enforced by planner and executor |
| `max_steps_per_plan` | 10 | Maximum skill steps in a single plan |
| `min_confidence_continue` | 0.30 | Confidence threshold for early stopping |
| `max_tokens_planner` | 2,048 | LLM output budget for plan generation |
| `high_level_model` | claude-sonnet-4-6 | Planner LLM |
| `executor_model` | claude-haiku-4-5-20251001 | Executor LLM |

---

## 4. Skill Library

### 4.1 Design Principles

The skill library is the agent's interface to the base pipeline and external services. Three design principles guide its construction:

**Typed contracts.** Each skill declares its name, category, description, preconditions (what must be true before execution), side effects (what changes after execution), failure modes, average latency, average cost, and retention probes (questions the agent should be able to answer after executing the skill). This metadata enables the planner to reason about skill composition without needing to understand implementation details.

**Wrapping, not replacing.** Skills wrap existing pipeline components rather than reimplementing their logic. The `predict_regime` skill calls the same `regime_classifier.py` that runs in the daily pipeline; the `fetch_tank_features` skill executes the same BigQuery query that Stage 1 uses. This ensures consistency between the agent's actions and the pipeline's established behavior.

**Dependency DAG.** The skill registry maintains a directed acyclic graph of skill dependencies, derived from precondition/effect declarations. The planner's validation step checks that each skill's preconditions are satisfiable from the accumulated effects of preceding skills. For example, `predict_regime` requires that `linkage_features` have been computed, which in turn requires `fetch_tank_features` and `fetch_market_data`.

### 4.2 Skill Taxonomy

The 20 skills span 7 categories:

| Category | Count | Skills | Description |
|----------|-------|--------|-------------|
| BigQuery Queries | 6 | `sense_tank_state`, `fetch_tank_history`, `fetch_region_signal`, `fetch_trade_log`, `fetch_tightness`, `fetch_market_data` | SQL queries against BigQuery tables |
| Compute / Analytics | 5 | `compute_fill_signal`, `compute_tightness`, `compute_zscore`, `compute_delta`, `compute_goii` | In-memory computation on fetched data |
| ML Models | 3 | `predict_regime`, `predict_spread_direction`, `predict_eia_surprise` | Model inference using Stage 2 classifiers |
| Cloud Run Jobs | 2 | `trigger_sar_pipeline`, `trigger_market_ingest` | Pipeline orchestration |
| LLM Reasoning | 2 | `explain_market_state`, `summarize_episode` | Language generation for interpretation |
| Trade Operations | 1 | `place_paper_trade` | Paper trade execution with position sizing |
| Alerts | 1 | `alert_on_threshold` | Anomaly detection and notification |

### 4.3 Skill Contract Example

A representative skill contract (simplified):

```json
{
  "name": "predict_regime",
  "category": "ML Models",
  "description": "Classify current market regime as contango or backwardation",
  "preconditions": ["linkage_features_available"],
  "effects": ["regime_prediction_available"],
  "failure_modes": ["insufficient_data", "model_load_error"],
  "avg_latency_ms": 850,
  "avg_cost_usd": 0.001,
  "retention_probes": [
    "What regime did the model predict?",
    "What was the classification confidence?",
    "Which feature contributed most to the prediction?"
  ]
}
```

### 4.4 Retention Probes

After each skill execution, the agent is queried with the skill's retention probes — factual questions about the skill's output that the agent should be able to answer. The retention score (proportion of probes passed) contributes to the `R_retention` component of the reward function.

This mechanism addresses the "tool-using without understanding" failure mode observed in prior agentic systems: an agent that calls a tool, receives output, and immediately forgets or misinterprets the result. By testing retention explicitly, we incentivize the agent to process and integrate skill outputs rather than merely routing them.

### 4.5 Plan Validation

The skill registry enforces the following validation rules before a plan is executed:

1. Every skill referenced in the plan must exist in the registry.
2. No skill may appear more than 3 times in a single plan.
3. Each skill's preconditions must be satisfiable from the accumulated effects of all preceding skills in the plan.
4. The total estimated cost (sum of `avg_cost_usd` across all steps) must not exceed the planner's cost cap ($0.50).

Plans that fail validation trigger replanning (up to `max_replans` attempts) before the turn is aborted.

---

## 5. Memory System

### 5.1 Architecture

The memory system comprises four tiers, each serving a distinct function in the agent's decision-making:

**Working Memory** holds the current turn's state: the user query, context, intermediate skill outputs, and accumulated effects. It is implemented as an in-process dictionary and is discarded at turn end. Working memory provides the executor with immediate context during multi-step plan execution.

**Episodic Memory** stores complete turn records as `Episode` objects, persisted to BigQuery. Each episode captures: episode ID, timestamp, user ID, query, generated plan, skill call results, final response, total cost, total latency, delayed reward fields, an embedding vector for similarity retrieval, and the persona estimate at time of interaction. During planning, the 3 most similar episodes (by embedding distance) are retrieved to provide precedent for the planner.

**Semantic Memory** maintains a collection of `Fact` objects — domain knowledge extracted from skill outputs and user interactions. Each fact has a support count (how many episodes have confirmed it), a contradiction count, first-observed and last-confirmed timestamps, source episode references, and an embedding. Facts with high support and low contradiction are treated as reliable domain knowledge. During planning, the 5 most relevant facts are retrieved.

**Procedural Memory** records `SkillSequenceRecord` entries — successful skill chains indexed by state signature. Each record stores the sequence of skill IDs, the average reward obtained, a support count, and recency. During planning, the 2 best-performing sequences for the current state signature are retrieved, providing the planner with empirically validated action patterns.

### 5.2 State Signatures

Procedural memory retrieval is indexed by a *state signature* — an 8-character MD5 hash of the current market regime (contango/backwardation), volatility regime (low/medium/high), and the persona's dominant mode (execution/analysis). This coarse-grained indexing means the agent can recall what worked in similar (but not identical) situations, enabling transfer across sessions with comparable market conditions.

### 5.3 Memory-Informed Planning

At planning time, the `MemoryManager.retrieve_context()` method assembles a memory context package:

```python
{
    "episodic": retrieve_similar(query, k=3),    # precedent turns
    "semantic": retrieve_relevant(query, k=5),    # domain facts
    "procedural": get_best_sequences(state_sig, k=2)  # proven skill chains
}
```

This context is injected into the planner's LLM prompt alongside the user query and persona state. The planner can thus ground its skill selection in (a) what worked in similar past situations (procedural), (b) relevant domain knowledge (semantic), and (c) precedent interactions with similar queries (episodic).

### 5.4 Memory Utility

The utility of memory retrieval is measured by the `R_memory` reward component, defined as the difference in reward between the memory-augmented and memory-free conditions:

```
R_memory = reward_with_memory − reward_without_memory
```

This differential formulation incentivizes the agent to retrieve memory when it helps and avoid retrieval when it doesn't, preventing both memory hoarding (retrieving everything, degrading planner focus) and memory neglect (never using stored context).

### 5.5 Causal Filtering for OOS Replay

During out-of-sample replay evaluation (benchmark OTM-9yr-Replay), the agent traverses historical decision points chronologically. Without safeguards, memory retrieval could access episodes, facts, and procedural sequences recorded *after* the simulated timestamp — allowing the agent to "remember the future" and inflating replay performance.

To prevent this, all 8 memory retrieval paths accept an optional `query_ts: str` parameter. When provided, each path applies a strict less-than filter:

| Retrieval Site | Filter Applied | Column |
|----------------|----------------|--------|
| `EpisodicMemory._bq_keyword_search()` | `AND ts < @query_ts` | `ts` |
| `EpisodicMemory.get_recent()` | `WHERE ts < @query_ts` | `ts` |
| `EpisodicMemory._local_search()` | `ep.timestamp < query_ts` | `timestamp` |
| `SemanticMemory._bq_search()` | `AND first_observed < @query_ts` | `first_observed` |
| `SemanticMemory.retrieve_relevant()` (local) | `fact.first_observed < query_ts` | `first_observed` |
| `ProceduralMemory._bq_lookup()` | `AND last_used < @query_ts` | `last_used` |
| `ProceduralMemory.get_best_sequences()` (local) | `record.last_used < query_ts` | `last_used` |
| `compare_to_history` skill | `AND trade_date < @query_ts` | `trade_date` |

The `MemoryManager.retrieve_context()` orchestrator threads `query_ts` to all tier-specific retrievals, and `OTMAgent.run()` accepts it as a top-level parameter. When `query_ts` is `None` (live mode), no filter is applied — behavior is fully backward-compatible.

**Enforcement.** 16 dedicated tests in `test_causal_leakage.py` verify:
- Local cache filtering excludes episodes/facts/sequences at or after `query_ts` (strict less-than)
- Backward compatibility: `query_ts=None` returns all entries
- `MemoryManager` threads `query_ts` to all three tiers simultaneously
- Static analysis: BQ query source code contains the timestamp filter placeholder

---

## 6. Persona Modeling

### 6.1 Bayesian Persona Vectors

The persona model represents each analyst's preferences and behavioral tendencies as a 64-dimensional vector, maintained as a Bayesian posterior (mean vector and 64×64 covariance matrix). Two anchor directions define the primary behavioral axis:

- **Execution mode** (seeded with `RandomState(42)`): biases toward action-oriented skills — `fetch_tank_features`, `detect_anomaly`, `compose_signal`, `place_paper_trade`, `alert_on_threshold`.
- **Analysis mode** (seeded with `RandomState(137)`, orthogonalized via Gram-Schmidt): biases toward investigation-oriented skills — `compare_to_history`, `explain_decision`, `predict_regime`, `predict_spread_direction`, `forecast_var_spread`.

The agent's *dominant mode* is determined by the persona vector's cosine similarity to each anchor. New users receive an initial persona inferred from their first query, with high initial covariance (uncertainty scale 4.0 − confidence × 3.0) reflecting the system's uncertainty about an unfamiliar analyst's preferences.

### 6.2 Bayesian Update Mechanism

After each interaction, the persona vector is updated via a Kalman-style Bayesian update:

```
observation_noise_cov = I × obs_noise_scale
S = prior_cov + observation_noise_cov
K = prior_cov × S⁻¹
posterior_mean = prior_mean + K × (observation − prior_mean)
posterior_cov = (I − K) × prior_cov
```

The observation vector is derived from the interaction: query characteristics (length, complexity), skills used, and implicit feedback signals. Over multiple interactions, the covariance shrinks and the persona estimate converges, causing the agent's behavior to become increasingly specialized for the individual analyst.

### 6.3 Persona-Conditioned Planning

The persona conditions planning through two mechanisms:

1. **Mode skill bias.** The planner prompt includes the persona's dominant mode and associated skill preferences. An execution-oriented analyst receives plans weighted toward data fetching and trading actions; an analysis-oriented analyst receives plans weighted toward investigation and explanation.

2. **Context vector.** The `PersonaVector.to_context()` method emits a structured summary — dominant mode, mode similarity scores, uncertainty level, turn count, and skill preferences — that is included in the planner's input.

This conditioning ensures that two analysts asking the same question ("What's happening with Cushing storage?") receive different responses: the execution-oriented analyst gets a quick status check and trade recommendation, while the analysis-oriented analyst gets a detailed breakdown with historical comparison and model explanation.

---

## 7. Reward Function

### 7.1 Multi-Objective Formulation

The total reward for a turn is computed as:

```
R_total = R_directional + α·R_task + β·R_memory + γ·R_consistency + δ·R_retention − λ·C_cost + penalties
```

With default weights: α = 1.0, β = 0.5, γ = 0.3, δ = 0.2, λ = 0.1.

### 7.2 Component Definitions

**R_directional: Directional Alignment Reward.** The primary environment-grounded signal. Measures whether the agent's recommended direction (long/short/flat) was correlated with the subsequent price move. Computed as `tanh(pnl_realized / 10.0)`, which maps unbounded P&L to the (−1, 1) range with smooth saturation. A small positive value (correct direction, small price move) is rewarded equally to a large one — this is a directional accuracy measure, not a P&L maximization objective. Sharpe ratio is reported separately as a diagnostic metric. The reward is delayed by the EIA release cycle (~7 days), requiring retrospective assignment to the turn that generated the trade signal.

**R_task: Task Completion Quality.** A score in [0, 1] reflecting whether the skill completed successfully and produced correct outputs, assessed by an LLM judge or heuristic scoring. Default: 0.5 when no judge is available.

**R_memory: Memory Utility.** The differential reward from Section 5.4: `reward_with_memory − reward_without_memory`. Positive when memory retrieval improved the outcome; negative when it degraded it.

**R_consistency: Behavioral Consistency.** Measures whether the agent's recommendations across turns are internally consistent. The function checks directional agreement (does the current signal match the previous turn's signal when market conditions haven't changed?) and penalizes contradictory behavior. A bonus is awarded when the agent's direction is confirmed by subsequent market movement.

**R_retention: Skill Knowledge Retention.** Computed as `probe_pass_count / probe_total_count` — the fraction of retention probes (Section 4.4) that the agent answers correctly after skill execution. Rewards agents that process and retain skill outputs, not just route them.

**C_cost: Resource Cost.** `clip(total_cost_usd / 0.50, 0, 1)` — the turn's cost as a fraction of the maximum budget. The λ = 0.1 weight ensures cost-awareness without dominating the reward signal.

**Penalties.** −0.5 per hallucinated skill (a skill name in the plan that doesn't exist in the registry). −1.0 for position sizes exceeding safety limits (|size| > 100,000 units).

### 7.3 DPO Training Pipeline

The reward function generates preference pairs for Direct Preference Optimization:

1. **Trajectory collection.** The agent executes episodes against the pipeline, producing (state, plan, execution, reward) tuples.
2. **Pair construction.** For each state, the trajectory with higher R_total is marked as *preferred*, and the trajectory with lower R_total as *rejected*.
3. **DPO loss.** The base model (Qwen 2.5 7B) is fine-tuned to increase the log-probability of preferred trajectories relative to rejected ones.

The DPO infrastructure is implemented but not yet executed. As discussed in Section 10, the current P&L signal (Sharpe ratio −0.10) does not provide sufficient edge for DPO training to produce meaningful policy improvements. We defer execution to after strategy refinement.

---

## 8. Evaluation

### 8.1 Out-of-Sample Holdout Protocol

The single most important methodological decision in this work is the out-of-sample holdout. All training data is restricted to dates before May 1, 2025; the subsequent 12+ months constitute the evaluation window that no model has seen during training.

**Static enforcement.** The holdout is enforced by `test_oos_leakage.py`, a pytest module containing 5 tests that run as part of the CI pipeline:

1. **test_sql_files_filter_training_tables**: Scans all `.sql` files in the repository. Any query that references one of 19 known training tables must include a `WHERE <date_column> < '2025-05-01'` filter.

2. **test_python_inline_sql_filters_training_tables**: Uses AST parsing to extract SQL strings (including f-strings with `JoinedStr` nodes) from all Python files. Applies the same filter requirement.

3. **test_oos_pragma_only_in_allowlisted_files**: The `@oos-eval-only` pragma allows evaluation code to intentionally read OOS data. This test ensures the pragma appears only in files explicitly registered in `OOS_EVAL_ALLOWLIST`, preventing unreviewed exemptions.

4. **test_allowlist_entries_exist**: Validates that every file in the allowlists actually exists, catching stale entries that might mask violations.

5. **test_oos_cutoff_date_is_consistent**: Confirms that the cutoff date used in the test matches the cutoff declared in the dashboard constants, ensuring a single source of truth.

The test recognizes 12 date column names (`date`, `obs_date`, `obs_date_utc`, `ts`, `week_ending`, `trade_date`, `created_ts`, `event_ts`, `snapshot_date`, `run_date`, `report_week_end`, `signal_date`) and 19 training tables across all three stages.

**Runtime enforcement.** `bq_safe.py` provides a `TrainingBQClient` wrapper around `bigquery.Client.query()` that raises `OOSLeakageError` if a query touches a training table without the cutoff filter. This defence-in-depth mechanism catches dynamically constructed queries that static analysis might miss.

**Audit results.** The static analysis identified 48 training-table queries across the codebase. Of these, 20+ were found to lack the holdout filter and were corrected. All were Category A (training/backtest) queries; Category D (real-time serving) queries were properly exempted.

**Leakage framing.** The audit identified queries that *would have* caused leakage once the training tables were populated. At the time of audit, the derived training tables (`hub_state_day`, `linkage_features`) contained 0 rows — they had never been backfilled from the upstream source data. Consequently, no model had ever been trained on leaked data, because no model had ever been trained on these tables at all. The audit prevented future leakage rather than correcting historical contamination. All models reported in this paper were trained from scratch with the holdout filter in place from the first run.

### 8.2 Benchmark Suite

We define 8 domain-specific benchmarks for evaluating commodity intelligence agents. Each benchmark specifies a sample size, primary metric, and evaluation cadence:

| # | Benchmark | n | Primary Metric | Description |
|---|-----------|---|----------------|-------------|
| 1 | OTM-LongCtx | 200 | accuracy | Evaluates agent performance when provided large context windows containing multi-week market history. Tests *useful* context utilization — not raw window size, but whether additional context improves decision quality. |
| 2 | OTM-Skill-Retention | 20 | pass_rate | After executing a skill, queries the agent with retention probes at increasing delays (1, 3, 5, 10 turns later). Measures knowledge decay rate. Evaluated weekly. |
| 3 | OTM-Persona-Align | 100 | alignment_score | Presents identical market scenarios to agents with different persona vectors. Measures whether execution-mode and analysis-mode personas produce appropriately differentiated skill sequences. |
| 4 | OTM-DistShift | 50 | robustness_score | Evaluates agent performance during distribution shifts: regime transitions, volatility spikes, data gaps, and anomalous EIA reports. Tests whether the agent degrades gracefully or fails catastrophically. |
| 5 | OTM-9yr-Replay | 1 | cumulative_pnl | Full trajectory replay over the 9-year backtest window (2016–2025), using only data available at each simulated decision point. The holdout boundary at 2025-05-01 is the definitive integrity test. |
| 6 | OTM-Mem-Utility | 500 | memory_utility | Runs identical scenarios with and without memory retrieval. The primary metric is the differential reward — positive when memory helps, negative when it hurts. High sample size captures variance across market conditions. |
| 7 | OTM-MultiTurn-Persona | 100 | persona_convergence | Multi-turn sessions (5–20 turns each) testing whether the persona vector converges to a stable estimate and whether agent behavior remains consistent with the converged persona. |
| 8 | OTM-Mem-Ablation | 200 | reward_delta | Drops one memory tier at a time (episodic-only, semantic-only, procedural-only, working-only) and measures the reward impact relative to the full system. Identifies which tiers contribute most. |

**Baselines.** Five baselines provide reference points:

| Baseline | Description |
|----------|-------------|
| B0 (Scheduled) | Fixed daily schedule: fetch data → run models → generate signal. No planning, memory, or persona. Equivalent to the base pipeline. |
| B1 (Single-Skill) | Always selects the single most commonly used skill. Tests whether planning adds value over a default action. |
| B2 (Prompted Claude) | Claude Sonnet with skill descriptions in the system prompt but no memory, persona, or reward. Tests the value of the agent framework over raw LLM prompting. |
| B3 (Fine-tuned Qwen) | Qwen 2.5 7B fine-tuned on collected trajectories via DPO. Tests the value of domain-specific fine-tuning. |
| B4 (Oracle) | Perfect foresight — selects skills based on knowledge of future outcomes. Upper bound on achievable performance. |

**Statistical methodology.** All benchmarks report 95% confidence intervals computed via bootstrap resampling (n_bootstrap = 10,000, seed = 42). Pairwise comparisons use the Wilcoxon signed-rank test with p < 0.05 significance threshold. Results across random seeds are aggregated as mean ± 95% CI.

### 8.3 Model Results

All models below were trained with the OOS filter (`WHERE date < '2025-05-01'`) in place, using `random_state=42` across all 22 model constructors for reproducibility. Model version: `v0.2.0-oos-clean`.

**Table 1. Stage 1 Pipeline Results (Cushing Hub)**

| Metric | Value | Criterion | Status |
|--------|-------|-----------|--------|
| Hub-state-day records produced | 309 | > 0 | PASS |
| EIA direction accuracy | 52.8% | > 50% | PASS |
| Signal stability (avg daily Δ) | 0.173 | < 2.0 | PASS |
| Signal stability (max daily Δ) | 1.714 | < 5.0 | PASS |
| Kalman convergence (early → late variance) | 0.066 → 0.045 | Decreasing | PASS |
| Low-coverage days | 3 / 309 | Tracked | PASS |

All 5 Stage 1 exit criteria passed, confirming the SAR-to-hub-state pipeline produces stable, convergent, and directionally informative output.

**Table 2. Stage 2 Model Results (Walk-Forward Evaluation)**

| Model | Accuracy | Baseline | Δ | Predictions | Top Feature |
|-------|----------|----------|---|-------------|-------------|
| Regime Classifier | 65.35% | 52.9% (majority) | +12.4 pp | 329 | tightness_mean (25.0) |
| Spread Forecaster | 51.4% | 50.0% (random) | +1.4 pp | 321 | wti_settle (45.0) |
| EIA Surprise | 51.52% | 50.0% (random) | +1.5 pp | 297 | tightness_mean (21.0) |

The regime classifier shows meaningful predictive power: 65.35% walk-forward accuracy on a balanced dataset (53.5% contango, 46.5% backwardation), with `tightness_mean` as the dominant feature — validating the SAR-derived storage signal as informative for regime classification. The spread forecaster and EIA surprise predictor show marginal improvement over random baselines (1–2 percentage points). These models operate on inherently noisy financial time series where even small edges, if persistent, can be economically meaningful. However, we note that edges of this magnitude are difficult to distinguish from noise at the sample sizes available (321 and 297 predictions, respectively).

**Table 3. Stage 2 EIA Surprise Regression**

| Metric | Value | Baseline | Improvement |
|--------|-------|----------|-------------|
| RMSE | 1,606 kb | 1,616 kb (naive) | 0.62% |

The RMSE improvement is modest, reflecting the fundamental difficulty of predicting EIA inventory surprises from SAR-derived features alone.

**Table 4. Stage 3 Results**

| Component | Output | Details |
|-----------|--------|---------|
| Signal Generator | Composite: short (−0.5), conf 0.72 | Regime-weighted: regime 70% (backwardation 0.73) + spread 30% (short 0.72) |
| VAR Model | Tightness: +0.015, Spread: −0.957 | Both series stationary (ADF p < 0.001) |
| GARCH Model | Conditional vol: 2.644 | α = 0.311, β = 0.594 (persistent volatility) |
| Ensemble | Long (value 1.0, 2 models) | LightGBM + VAR/GARCH, low volatility regime |
| Backtest (v1 naive) | Sharpe: −0.10, P&L: −$26,218 | Naive tightness-delta signal, no confidence gating |
| Backtest (v2 ML) | Pending BQ execution | Walk-forward ML composite, regime-weighted, confidence-gated |
| Scorecard | Regime: 2/2, Spread: 2/2 | Limited sample (first 2 days of live scoring) |

**Table 5. OOS Filter Impact on Training Data**

| Table | Total Rows | Pre-Cutoff | Removed | % Removed |
|-------|-----------|------------|---------|-----------|
| sentinel1_weekly_tank_features | 5,124 | 4,578 | 546 | 10.66% |
| calendar_spreads | 20,276 | 19,804 | 472 | 2.33% |
| market_prices | 40,014 | 39,062 | 952 | 2.38% |
| release_clock | 1,148 | 1,099 | 49 | 4.27% |
| cot_positions | 327 | 75 | 252 | 77.06% |

The OOS filter removes 10.7% of SAR features (the most recent 546 observations), 2–4% of market data, and 77% of COT positions (which have shorter history in the system). These are the rows that would have inflated model performance if included in training — particularly the 546 SAR observations closest to the present, which are most informative for recent regime classification.

### 8.4 Interpreting the Negative Sharpe and Strategy Investigation

The initial backtest produced a Sharpe ratio of −0.10 with a 1.4% win rate — the paper trading strategy lost money over the evaluation period. A systematic investigation identified five root causes and implemented corresponding fixes.

**Root cause analysis.** The initial backtest used a naive tightness-delta signal (5-day lookback, 0.3σ threshold) that was never connected to the ML models (regime classifier, spread forecaster) whose walk-forward results were reported. Specifically:

| Problem | Impact |
|---------|--------|
| Backtest used simple delta, not ML models | 65% regime classifier signal entirely unused |
| 0.3σ threshold too low | Excessive noise trades (562 trades over 9,853 days) |
| Equal weighting of all signals | 51% coin-flip models diluted 65% regime edge |
| No confidence gating | Traded on every signal regardless of conviction |
| No risk controls | No drawdown stop; positions held through adverse moves |

**Strategy v2 implementation.** The backtest engine was rewritten with five improvements:

1. **Walk-forward ML signal generation.** For each day *t*, the engine trains LightGBM classifiers on data [0..*t*−1] and predicts at *t*. This replaces the naive delta signal with the actual ML models whose accuracy was validated in Section 8.3.

2. **Regime-weighted composite.** The regime classifier (65% accuracy) receives 60% weight; the spread forecaster (51%) receives 25%; tightness momentum receives 15%. Signals are further scaled by each model's prediction confidence, so a high-confidence regime signal dominates the composite while a low-confidence spread signal contributes minimally.

3. **Confidence gating.** Signals below a 0.58 confidence threshold are forced to flat (no position). This filters out the majority of noise trades where the model has no meaningful conviction.

4. **Drawdown-based risk control.** The strategy flattens all positions and stops trading after a 5% drawdown from peak equity, preventing catastrophic loss accumulation.

5. **A/B comparison framework.** The engine now runs both the ML-composite strategy and the tightness-delta baseline side by side, reporting Sharpe improvement, P&L delta, win rate change, and trade reduction. This provides an internal ablation between the improved strategy and the original naive approach.

**Reframing for the agentic evaluation.** The agent's value lies in orchestration — selecting the right analytical sequence, maintaining context, and adapting to the analyst — not in the alpha of the underlying strategy. For benchmark evaluation (Section 8.2), agent quality is measured by recommendation alignment with subsequent market direction, skill selection appropriateness, memory utilization, and persona consistency. The strategy investigation is a contribution to the pipeline (Stages 2–3), not to the agent layer.

**Implications for reward-based training.** Until the ML-composite strategy produces non-negative expected return on live BQ data, the directional reward component (R_directional) provides ambiguous training signal. DPO fine-tuning is deferred until strategy v2 backtest results confirm at least Sharpe >= 0 on the OOS-clean dataset.

### 8.5 Test Suite Coverage

The system includes 258 unit tests across 12 test modules (254 passing, 4 pre-existing failures documented):

| Module | Tests | Coverage Area |
|--------|-------|---------------|
| test_planner | ~25 | Plan generation, validation, replanning |
| test_persona | ~30 | Persona creation, Bayesian update, mode inference |
| test_memory | ~35 | All 4 memory tiers, retrieval, state signatures |
| test_evaluation | ~20 | Benchmark harness, baselines, statistical tests |
| test_compute_skills | ~15 | Compute skill execution, edge cases |
| test_alert_skills | ~10 | Alert threshold logic, notification |
| test_registry | ~20 | Skill registration, DAG validation, catalog |
| test_training | ~25 | DPO pair generation, reward computation |
| test_schema | ~15 | Data schemas, serialization |
| test_loader | ~15 | Skill loading, configuration |
| test_oos_leakage | 5 | OOS holdout enforcement (Section 8.1) |
| test_causal_leakage | 16 | Causal memory filter for OOS replay (Section 5.5) |

### 8.6 Agent Benchmark Results (v1.0–v1.1)

Three of the eight benchmarks were executed with real agent calls against the production pipeline. Results are reported with full audit trail: both original and corrected results are preserved, protocol amendments documented, and each measurement bug identified, fixed, and disclosed. Two cycles of re-verification (v1.0 post-fix and v1.1 post-data-fixes) confirm result stability.

#### 8.6.1 OTM-Persona-Align

**Objective.** Test the strongest architectural claim: that Bayesian persona vectors produce meaningfully different agent behavior. 49 domain queries are run through the agent in 4 persona conditions (execution-anchored, analysis-anchored, neutral×2), producing 196 total agent runs. Cosine divergence between response embeddings measures whether persona conditioning creates detectable behavioral differences.

**v1.0 Result (post-planner-fix, 2026-05-24).** Divergence ratio: **1.003×** baseline. Wilcoxon p = **0.23**. Skill Jaccard: 0.10 (agent) vs 0.11 (baseline). **NULL confirmed.**

**v1.1 Result (post-data-fixes, 2026-05-25).** Divergence ratio: **1.001×** baseline. Wilcoxon p = **0.70**. Skill Jaccard: 0.047 vs 0.040. Cost: **$1.77** (196 runs). **NULL confirmed — even more clearly null than v1.0.**

**Interpretation.** Two independent runs both produce null. The persona module is functioning correctly at the implementation level — Kalman updates converge, persona vectors remain orthogonal, and seeding produces intended anchor positions. What fails is the *transmission mechanism*: concatenating a 64-dimensional float block into a natural-language prompt does not cause the LLM to condition its generation on that vector. Skill selection is identical across personas, confirming the planner routes based on query content, not persona state. This finding motivates the v0.2 activation steering hypothesis (Section 11): injecting persona vectors into the model's residual stream may achieve the conditioning that in-prompt injection cannot.

**Note on sample size.** The benchmark runs 49 unique queries × 4 persona modes = 196 agent runs. Divergence is computed per query pair, yielding n=49 paired comparisons for the Wilcoxon test. The design target of "100 queries" (§8.2) was reduced to 49 unique probes from the domain query set.

#### 8.6.2 OTM-Skill-Retention

**Objective.** Test whether the planner routes queries to the correct skills. 60 canonical probes (3 per skill, 20 skills, 7 categories) are run through the full agent. Primary metric: plan inclusion (does the expected skill appear anywhere in the generated plan?).

**Protocol amendment (2026-05-23).** Primary metric changed from top-1 positional accuracy to plan inclusion after identifying three measurement bugs. Initial top-1 result (23.3%) was a measurement artifact: the planner was routing correctly all along, but placing prerequisite data-fetch steps before the target skill. See `SKILL_RETENTION_PROTOCOL.md` for full amendment.

**v1.0 Result (post-fix, 2026-05-24).** Plan inclusion: **81.7%** (CI: 71.7%–91.7%, n=60). Top-3: 55.0%. Top-1: 21.7%. Mean plan length: 3.4 steps. 14/20 skills at 100% inclusion. Corrected random baseline: 15.9% — observed is **5.1× baseline**.

**v1.1 Result (post-data-fixes, 2026-05-25).** Plan inclusion: **81.7%** (identical to v1.0). Top-3: 58.3% (+3.3pp). Top-1: 21.7% (same). Mean plan length: 3.3 steps. Cost: **$1.65** (60 probes). Confirms data-availability fixes do not affect planner skill selection.

**Per-category breakdown:**

| Category | Plan Inclusion | Top-1 | Notes |
|----------|---------------|-------|-------|
| query | 61.1% | 55.6% | Core data-fetch queries: some disambiguation needed |
| compute | 93.3% | 0.0% | Strong inclusion; prerequisites push target past position 1 |
| ml | 100.0% | 0.0% | Perfect: ML skills always included but as downstream steps |
| cloud_run | 50.0% | 50.0% | Partial: some infra queries correctly routed |
| llm | 100.0% | 0.0% | Summarization always included but not first step |
| trade | 100.0% | 0.0% | Trade skills planned but preceded by data-fetch prerequisites |
| alert | 100.0% | 0.0% | Alert skills always downstream of fetch steps |

**Interpretation.** The planner demonstrates strong skill selection across all categories. The discrepancy between plan inclusion (81.7%) and strict positional top-1 (21.7%) reflects correct behavior: the multi-step planner places prerequisite data-fetch steps before domain-specific skills. Categories at 0% top-1 (ml, llm, trade, alert) all achieve 100% plan inclusion. The remaining misses concentrate in query-category disambiguation (`compare_to_history` vs `fetch_tank_features`) and the `sense_tank_state` skill (substituted by `fetch_tank_features`).

#### 8.6.3 OTM-OOS-Replay

**Objective.** The headline integrity benchmark. Walk day-by-day through the 12-month OOS window, asking the agent for a directional call, and measuring accuracy against actual next-day price movement.

**Protocol and causal integrity.** The `query_ts` parameter threads through all 8 memory retrieval paths. 16 dedicated causal leakage tests verify filtering. Fresh agent instance per day (no memory carryover).

**v1 (data-starved, pre-fix).** 57.1% accuracy (CI: 39.3%–75.0%, n=28). **Diagnostic finding:** Every prediction used only `query_goii` (1 skill/day, 0 rows returned). Three planner bugs: (1) `_should_stop` naive substring matching, (2) `query_goii` returned SUCCESS on empty data, (3) `_resolve_args` couldn't parse `$stepN.field`. All predictions were uninformed guesses.

**v2 (corrected, full 250-day run, n=237, seed=42).** Directional accuracy: **54.4%** (CI: 48.1%–60.8%). Sharpe: 1.37. P&L: 6,301 bps. Drawdown: 2,623 bps. Cost: estimated $9–15 (see §8.7 cost amendment). CI crosses 50% — not statistically significant at 95% confidence.

**v1.1 (data-availability fixes, compressed 120-day run, n=110, seed=42).** Directional accuracy: **50.0%** (CI: 40.9%–60.0%). Sharpe: 1.05. P&L: 1,513 bps. Drawdown: 1,204 bps. Cost: **$13.13** ($0.12/day with full LLM cost tracking).

**Scope amendment.** Budget constraints ($15.95 API credit) required compressing from 237 to 120 days. Run terminated at 110 days ($13.13 of $15 cost cap). Coverage: May–Oct 2025 only; Nov 2025–Apr 2026 not evaluated. Full 250-day re-run deferred to v1.2.

**Same-window comparison (May–Oct 2025):**

| Month | v1.0 | v1.1 | Δ |
|-------|------|------|---|
| 2025-05 | 40.0% | 45.0% | +5.0pp |
| 2025-06 | 63.2% | 63.2% | 0.0pp |
| 2025-07 | 52.4% | 47.6% | −4.8pp |
| 2025-08 | 25.0% | 45.0% | +20.0pp |
| 2025-09 | 52.4% | 47.6% | −4.8pp |
| 2025-10 | 52.4% | 55.6% (n=9) | +3.2pp |
| **Total** | **47.5%** | **50.0%** | **+2.5pp** |

The +2.5pp improvement is within the pre-registered 1–5pp expectation. The most dramatic change was August 2025 (25.0% → 45.0%), where v1.0's `estimate_volatility_regime` dtype errors caused uninformed fallback. The headline v1.0 figure (54.4%) covers the full 237-day window including Nov–Apr months not evaluated in v1.1; the same-window comparison is the methodologically correct comparison.

**Confidence calibration.** v1.0: correct=0.538, wrong=0.539 (flat). v1.1: correct=0.507, wrong=0.497 (marginally better, still effectively uncalibrated). The agent does not reliably distinguish confident from uncertain predictions.

**Interpretation.** The 54.4% (v1.0 full-year) and 50.0% (v1.1 same-period) accuracies are statistically indistinguishable from random at 95% confidence. This is consistent with pre-registered expectations: the regime classifier achieves 65.4% in-sample, but composite signal dilution from near-chance components was predicted to yield 52–58% OOS. The result falls within that range. The agentic orchestration layer did not extract sufficient signal from the underlying pipeline to beat random — a legitimate and publishable finding that motivates strategy iteration in v0.3.

#### 8.6.4 OTM-Mem-Utility

**Design.** Counterfactual ablation: each query is run through the real OTMAgent twice — once with the full MemoryManager (control) and once with a NoopMemoryManager that returns empty context for all retrieval calls (ablation). An LLM-as-judge (Claude Haiku) rates both responses blind on a 0–5 scale (average of relevance, informativeness, accuracy), with response order randomized per query to prevent position bias. Memory utility = mean(with_memory) – mean(without_memory).

**Results (v1.1, n=25, seed=42, $1.39).** Memory utility: **−0.064** (95% CI: −0.276 to +0.128). Mean score with memory: 3.77/5.0. Mean score without memory: 3.83/5.0. The CI crosses zero — the 4-tier memory system does not produce a statistically detectable improvement in response quality.

| Category | Utility (Δ) | 95% CI | n |
|----------|-------------|--------|---|
| Factual domain | +0.14 | −0.10 to +0.32 | 5 |
| Historical comparison | +0.06 | −0.56 to +0.64 | 5 |
| Reasoning | −0.06 | −0.40 to +0.28 | 5 |
| Real-time | −0.08 | −0.30 to +0.14 | 5 |
| Pattern recognition | −0.38 | −0.98 to +0.12 | 5 |

**Interpretation.** The null result is consistent with the current memory architecture's limitations. Factual domain queries show a small positive signal (+0.14) — the system prompt's domain knowledge provides slight benefit. Pattern recognition queries show a negative signal (−0.38) — stale episodic memories may introduce noise when the agent attempts historical comparisons. The overall null motivates v0.2 work on memory relevance scoring and episodic decay tuning.

#### 8.6.5 OTM-MultiTurn-Persona

**Design.** 7 conversation sequences × 5 turns each. Each sequence runs the same 5-query conversation under two opposing persona modes (execution_oriented vs analysis_oriented), with the agent instance persisting across turns so the persona Kalman update accumulates. Measures Jaccard skill divergence between persona modes at turns 1–2 (early) vs turns 4–5 (late). Hypothesis: divergence increases across turns (persona convergence — the persona module produces more distinct behavior as it accumulates evidence). Wilcoxon signed-rank test for statistical significance.

**Results (v1.1, n=7, seed=42, $2.57).** Convergence delta: **+0.173** (95% CI: −0.064 to +0.378). Mean early divergence: 0.162. Mean late divergence: 0.335. Wilcoxon p=0.1094 — suggestive but not statistically significant at α=0.05.

**Interpretation.** The positive delta (+0.173) shows a directional trend: persona modes produce more distinct skill selections in later turns than in early turns. This is the expected behavior of the Bayesian Kalman update — as the persona vector accumulates evidence from user interactions, it should specialize behavior. However, with n=7 sequences and p=0.109, this is a suggestive rather than confirmatory finding. The single-turn persona null (p=0.70 from Persona-Align) combined with the suggestive multi-turn positive trend is consistent with the hypothesis that persona conditioning requires multiple turns to produce detectable behavioral change. A larger sample (n≥20) is needed for confirmatory power — deferred to v1.2.

### 8.7 Cost Tracking Amendment (2026-05-25)

All cost figures in v1.0 benchmark results captured only skill execution costs (BigQuery queries at ~$0.0001/query), not the LLM costs for plan generation, re-planning, and response synthesis. Three Anthropic API call sites were uninstrumented:

1. `Planner.generate_plan()` — Claude Sonnet call per agent turn
2. `Planner.replan()` — 0–3 additional calls per turn on skill failure
3. `Agent._llm_response()` — Claude Sonnet call for response generation

**Root cause.** `record.total_cost_usd` in `agent.py` summed only `skill_result.cost_usd`. The planner's LLM usage was returned in the API response's `usage` object but never converted to dollars or accumulated.

**Fix.** Instrumented all three LLM call sites with token-based cost estimation using published Anthropic pricing (Sonnet: $3/$15 per M input/output tokens, Haiku: $0.80/$4). Added `_estimate_llm_cost()` to the `Planner` class with a `cumulative_llm_cost_usd` accumulator that captures both initial plan generation and all re-plans. Unknown model IDs produce a warning and fall back to Sonnet pricing.

**Corrected cost figures:**

| Benchmark | v1.0 reported (skill only) | v1.1 measured (full) | Correction factor |
|-----------|---------------------------|---------------------|-------------------|
| OOS Replay | $0.04 | $13.13 (110 days) | ~328× |
| Persona-Align | $0.31 | $1.77 (196 runs) | 5.7× |
| Skill-Retention | $0.20 | $1.65 (60 probes) | 8.3× |
| Mem-Utility | — | $1.39 (25 queries) | — |
| MultiTurn-Persona | — | $2.57 (7 sequences) | — |
| **Total** | **$0.55** | **$20.51** | **37×** |

The corrected total ($20.51 including Mem-Utility and MultiTurn-Persona) is still **7× under** the $150 pre-execution budget. Actual API billing may differ slightly due to prompt caching adjustments. Underlying benchmark results (directional accuracy, skill inclusion, persona divergence) are unaffected — only cost figures changed.

**Cost calibration methodology.** Before the full v1.1 re-runs, a single-day calibration run measured $0.55/day (an expensive day selected for safety margin). Actual v1.1 OOS Replay averaged $0.12/day — 4.6× lower than calibration. The conservative calibration provided budget safety margin without overspending.

### 8.8 Audit Cycle: Methodology and Six Revolutions

The audit cycle is this project's central methodological contribution: applying research-paper-review rigor to one's own evaluation infrastructure, with public documentation of the cycles and their outcomes. Most agentic AI portfolios report what worked on a development set. This section documents what didn't, when it was discovered, what was changed, and what the corrected measurement showed.

Across six weeks of development, the audit cycle revolved six times. Each revolution followed the same pattern: **build** a component → **measure** its behavior → **find** a discrepancy → **diagnose** root cause → **fix** → **re-measure** → **publish** with full disclosure of both original and corrected results.

#### Cycle 1: OOS Leakage Queries

**What was built.** Training pipeline with BigQuery queries feeding LightGBM models.

**What measurement caught.** Static AST analysis (`test_oos_leakage.py`) identified 20+ training-table queries lacking the `WHERE date < '2025-05-01'` holdout filter across 9 files.

**What changed.** Added `WHERE date < '2025-05-01'` to all affected queries, plus runtime guard `bq_safe.py`. CI now blocks merges on any new leaking query.

**What re-measurement showed.** 5/5 OOS leakage tests pass; 48 training queries audited, zero violations. At the time of discovery, the derived training tables contained 0 rows — no model had been trained on leaked data, but the queries would have leaked on future runs.

#### Cycle 2: Model Retrain After Audit

**What was built.** Models trained before the OOS filter existed.

**What measurement caught.** The filter audit (Cycle 1) revealed that existing model artifacts were trained on queries without the holdout filter, making their provenance unverifiable.

**What changed.** Archived leaky models to `gs://otm-models/v0.1.0-pre-oos-audit/`. Retrained all 8 stage-1-through-3 models with corrected query set, `random_state=42` across 22 model constructors. Discovered `hub_state_day` was empty pre-audit — these are first-ever clean models, not corrected ones.

**What re-measurement showed.** Regime classifier: 65.4%. Spread forecaster: 51.4%. EIA surprise: 51.5%. Full audit trail preserved in `retrain_results/`.

#### Cycle 3: Skill-Retention Measurement Bugs

**What was built.** Skill-retention benchmark with top-1 accuracy as primary metric.

**What measurement caught.** Initial 23.3% top-1 result looked alarming. Manual diagnostic of three probes revealed the planner was routing correctly — three measurement bugs in benchmark code masked this: (a) wrong plan key extraction, (b) prerequisite-failure short-circuit, (c) "first step = top-1" penalizing multi-step plans.

**What changed.** Renamed primary metric to `plan_inclusion` (skill anywhere in plan). Documented as protocol amendment in `SKILL_RETENTION_PROTOCOL.md` with rationale.

**What re-measurement showed.** 78.3% v1.0, 81.7% v1.1. The planner had been routing correctly all along; the measurement was wrong.

#### Cycle 4: Planner Stop-Condition and Data Starvation

**What was built.** OOS Replay benchmark runner.

**What measurement caught.** 30-day smoke test showed 57.1% accuracy (n=28), but diagnostic revealed every query routed to `query_goii` (empty table) and stopped. The agent was making uninformed guesses with zero real data.

**What changed.** Three root causes fixed: (a) `_should_stop` treated empty-success as terminal, (b) generic query provided no routing guidance to planner, (c) GOII pipeline diagnosed as never built. Fixed (a) and (b); deferred (c) to v1.2.

**What re-measurement showed.** Agent now calls 3–6 skills per day with real BigQuery data. Directional accuracy moved from data-starved 57% to honest 50% — a *worse* number that is a *better* measurement.

#### Cycle 5: Cost Tracking Measurement

**What was built.** Cost tracking in `agent.py` summing `skill_result.cost_usd`.

**What measurement caught.** v1.0 benchmarks reported $0.55 total cost. Investigation revealed three uninstrumented LLM call sites: `generate_plan()`, `replan()`, and `_llm_response()`.

**What changed.** Added `_estimate_llm_cost()` utility using published Anthropic pricing. Added `cumulative_llm_cost_usd` accumulator across planner and response paths. Unknown model IDs produce warning and fall back to Sonnet pricing.

**What re-measurement showed.** v1.1 corrected total: $20.51 (37× the original figure). Still 7× under $150 budget. Cost amendment published to live site before v1.1 re-runs.

#### Cycle 6: v3.0.0 Architecture Audit

**What was built.** Agent-first chat architecture (v3.0.0) — all queries routed to Cloud Run instead of local keyword matching.

**What measurement caught.** Architecture refactor added `dashboard_snapshot`, `recent_prices`, and `conversation_history` parameters to `agent.run()` and `planner.generate_plan()`. This raised the question: did the refactor affect the benchmark codepath?

**What changed.** Targeted audit verified: (a) all new parameters are `Optional` with `None` defaults, (b) benchmark runner calls `agent.run(query, user_id=...)` without context — zero v3.0.0 branches trigger, (c) all context injections gated by `if context.get("key"):` — only fire when keys have truthy content. Test suite: 254 pass, 4 pre-existing failures, zero new regressions. Edge case fixed: "Execute a paper trade" response changed from 73s evaluation-then-rejection to 35s immediate decline via system prompt rule.

**What re-measurement showed.** 3-probe spot-check confirmed identical behavior to v1.1. Chat smoke test: 27/28 pass, 1 marginal. Audit document with correct citations published.

#### The Discipline: "Copy from Source, Never from Memory"

A single operational rule crystallized across these six cycles: **every published number must trace to a source file**. During the v3.0.0 audit documentation, three benchmark citations were written from memory — Persona-Align cited as "100%" (correct: null, p=0.70), OOS-Replay cited as "65.35%" (correct: 50.0% directional accuracy; 65.35% is the in-sample regime classifier). The error was caught by cross-referencing against the source JSON files and corrected within the same session.

This rule — copy from the JSON, never from recollection — is the simplest and most transferable finding of the audit-cycle methodology. It protects against exactly the kind of small slippage that accumulates when many numbers appear in many documents across many weeks of development.

#### What This Is Not

The audit cycle is not a process improvement methodology in general, not a substitute for unit tests, and not the audit cycle from agile or continuous improvement literature. It is specifically: applying research-paper-review rigor to one's own evaluation infrastructure, with public documentation of the cycles and their outcomes. The practice is that every claim gets measured, every measurement gets audited, and every audit trail gets preserved.

---

## 9. Dashboard

### 9.1 Design Philosophy

The OTM dashboard is a 9-page Streamlit application that serves dual purposes: a research interface for agent development and a demonstration interface for stakeholder review. Three architectural decisions guide its design:

**Single source of truth.** All skill names, benchmark identifiers, category labels, and model strings are defined in `constants.py` and imported by every page. No page contains hardcoded duplicates. This was enforced through a 70-item audit that identified and eliminated every instance of local constant definitions.

**Real-data-first with watermarked fallback.** Each page attempts to fetch real data from the agent API. If the API returns no data (the agent hasn't been deployed, or the pipeline hasn't run), the page falls back to deterministic demo data generated with `np.random.default_rng(seed)` and rendered with a "⚠️ DEMO DATA" watermark. This ensures the dashboard is always functional for demonstrations while making it unambiguous when results are simulated.

**Agent introspection.** Five of the nine pages are purpose-built for agent development, providing visibility into the planner's reasoning, the executor's skill traces, memory contents, persona state, and benchmark results. These pages transform the agent from a black box into an inspectable system.

### 9.2 Page Inventory

| Page | Name | Description |
|------|------|-------------|
| 1 | SAR Monitor | Tank farm overview: fill percentages, confidence scores, anomaly flags, historical trends |
| 2 | Stage 1 Kalman | Kalman filter visualization: tightness index, confidence bands, per-tank signal decomposition |
| 3 | Stage 3 Trading | Trading signals, paper trade log, equity curve, P&L attribution, governance scorecard |
| 4 | GOII Index | Global Oil Inventory Index across 4 hubs: Cushing, Rotterdam, Fujairah, Singapore |
| 5 | Agent Chat | Interactive chat interface with real-time skill execution traces, feedback collection (UUID-keyed) |
| 6 | Agent Traces | Session replay: skill execution timeline, dependency DAG visualization, per-skill cost and latency |
| 7 | Memory Explorer | Browse and search across all 4 memory tiers: episodic, semantic, procedural, working |
| 8 | Persona State | Persona vector compass visualization, covariance matrix heatmap, mode trajectory, preference evolution |
| 9 | Eval & Benchmarks | Benchmark comparison across 8 benchmarks, reward decomposition violin plots, memory tier ablation studies |

The sidebar dynamically displays the skill count and category breakdown, derived from `SKILL_CATEGORIES`, and the footer on each page shows the dashboard version and model identifiers.

### 9.2 Public Chat Demo (v3.0.0)

The public site at `oiltank-tracking.github.io` includes a conversational chat interface powered by the same Cloud Run agent API that runs the benchmarks. The v3.0.0 architecture routes all queries through the agent — eliminating the local keyword-matching layer that previously handled simple queries — ensuring that every interaction demonstrates the agent's actual capabilities.

**Architecture.** Chat queries are sent to the Cloud Run endpoint with optional `context` (dashboard snapshot, recent prices) and `conversation_history` (token-capped to ~3,000 tokens). The agent routes to either a zero-step knowledge-only path (for questions answerable from context) or the full planner path (for queries requiring BigQuery skill execution). This routing is transparent to the user.

**Quality validation.** A 28-query smoke test across 5 tiers validated the chat surface before publication:

| Tier | Category | Pass/Total |
|------|----------|------------|
| 1 | Data lookup (fill levels, prices) | 5/5 |
| 2 | Correlation / analysis | 5/5 |
| 3 | Explanatory ("why" questions) | 5/5 |
| 4 | Project meta-queries | 5/5 |
| 5 | Follow-up context (2 sequences) | 4/4 |
| 6 | Edge cases (out-of-scope, adversarial) | 3/4 |
| **Total** | | **27/28** |

The single marginal result — a trade-execution request that the agent evaluated for 73 seconds before rejecting — was fixed via system prompt rule and redeployed (35s immediate decline). Full results documented in `docs/chat_quality_smoke_test.md`.

**Performance.** Average response latency: 57.2s. Knowledge-only queries: ~21s. Complex multi-hub queries requiring BigQuery execution: 80–98s. A progressive typing indicator ("Thinking…" → "Analyzing…" → "Still working…") mitigates the UX impact of longer queries.

---

## 10. Discussion

### 10.1 What Worked

**Typed skill contracts enforce compositional validity.** The precondition/effect mechanism catches invalid skill sequences at plan validation time, before any resource is consumed. This is a meaningful improvement over unconstrained tool-use, where the agent discovers at execution time that a required input is missing.

**OOS holdout enforcement as a first-class CI gate.** Treating the holdout filter as a testable property of the source code — rather than a convention documented in a wiki — eliminates an entire class of integrity failures. The 20+ unfiltered queries discovered by the audit demonstrate that convention alone is insufficient.

**The audit cycle as methodology.** The most transferable contribution of this work may be the process itself: systematically auditing your own pipeline using the same rigor you would apply to reviewing someone else's paper. Six complete audit cycles ran during v1.0–v1.1 development (see §8.8 for full documentation):

1. *OOS Leakage Audit* — Static AST analysis identified 20+ training-table queries lacking the holdout filter. All models retrained from scratch.
2. *Model Retrain After Audit* — Archived leaky model artifacts, retrained all 8 models with corrected queries and verified `random_state=42`.
3. *Skill-Retention Measurement Bugs* — Three bugs in benchmark code masked correct planner behavior. Protocol amendment with rationale documented.
4. *Planner Stop-Condition Audit* — Data-starved OOS Replay diagnosed and fixed. Honest 50% replaced misleading 57%.
5. *Cost Tracking Audit* — Three uninstrumented LLM call sites discovered. 30× correction factor disclosed transparently.
6. *v3.0.0 Architecture Audit* — Chat architecture refactor verified safe for benchmark codepath. 27/28 chat quality smoke test. Q27 edge case fixed.

Each cycle followed the same pattern: anomaly detected → root cause investigated → fix implemented → re-verification with preserved audit trail.

**Chat demo validation.** The v3.0.0 agent-first architecture was validated with a 28-query smoke test across 5 tiers: data queries (5/5), correlation analysis (5/5), explanatory (5/5), project meta-queries (5/5), follow-up context (4/4), and edge cases (3/4 with 1 marginal). The single marginal result (paper trade execution request) was fixed via system prompt update. Average latency: 57.2s; typing progress indicator mitigates UX impact.

**Single-source-of-truth architecture.** Defining all taxonomy (skills, benchmarks, categories, model strings) in one file and importing it everywhere eliminates the drift that accumulates when the same constants are duplicated across dashboard pages, evaluation code, and documentation.

### 10.2 What Needs Work

**Persona conditioning requires architectural change.** Two independent v1.1 runs confirm the persona null (p=0.70). In-prompt persona injection — concatenating a 64-d float vector into natural language — does not cause the LLM to condition its generation on that vector. The persona module itself functions correctly (Kalman updates converge, vectors remain orthogonal), but the transmission mechanism fails. Activation steering (residual-stream injection) is the hypothesized v0.2 mechanism for achieving deeper conditioning.

**OOS Replay accuracy is statistically indistinguishable from random.** The v1.0 full-year result (54.4%, n=237) and v1.1 same-period result (50.0%, n=110) both have CIs crossing 50%. The agent's orchestration layer does not extract sufficient signal from the underlying pipeline to beat random. This is consistent with pre-registered expectations given that two of three Stage 2 models operate near chance, but it means the agentic layer's value must be demonstrated through orchestration quality (skill selection, memory utilization) rather than directional alpha.

**Strategy edge is under investigation.** The original backtest used a naive tightness-delta signal disconnected from the ML models, producing Sharpe −0.10. Strategy v2 replaces this with walk-forward ML signals, regime-weighted compositing, confidence gating, and drawdown controls (Section 8.4). The v2 backtest awaits execution against live BQ data; the architectural improvements are in place but the resulting Sharpe is not yet measured.

**DPO fine-tuning not yet executed.** The infrastructure exists — trajectory collection, preference pair construction, DPO loss computation — but execution is gated on strategy v2 producing non-negative expected return. This is an intentional sequencing decision: fine-tuning on a reward signal with no edge would produce a degenerate policy.

**Single-hub training.** Although the pipeline supports 4 global hubs, all models reported here are trained on Cushing data only. The regime classifier's 65.4% accuracy on Cushing contango/backwardation may not transfer to hubs with different market microstructure (e.g., Fujairah contango dynamics differ from Cushing due to shipping route dependencies).

**Optional benchmarks executed.** MultiTurn-Persona (n=7, convergence delta +0.173, p=0.109) and Mem-Utility (n=25, utility −0.064, CI crosses zero) were both executed with real agent calls. Both produced null or near-null results: the memory system does not detectably improve response quality, and multi-turn persona convergence is suggestive but not significant at α=0.05. These results directly inform v0.2 architecture priorities — memory relevance scoring and larger-sample persona convergence testing.

### 10.3 Lessons for Agentic System Design

Several lessons from this work may generalize to other agentic systems:

**Ground reward in environment feedback.** Human preference provides signal on communication quality but not on decision quality. Paper-trading P&L — despite its current limitations — provides an objective, environment-grounded measure of whether the agent's actions lead to good outcomes. The challenge is ensuring the underlying strategy has enough edge for the P&L signal to be informative.

**Test that memory is actually used.** A memory system that stores everything and retrieves nothing (or retrieves irrelevantly) adds latency without value. The memory utility metric (R_memory) and retention probes (R_retention) make memory usage an explicit optimization target rather than an assumed benefit.

**Persona modeling prevents the generic assistant failure mode.** Without persona conditioning, the agent converges to a single behavioral policy that serves the "average" user poorly. The Bayesian persona mechanism ensures that the agent's behavior specializes over interactions, at the cost of initial uncertainty for new users.

**OOS discipline is harder for agents than for static models.** A static model has one training query surface. An agent has N skill implementations, each with its own data access patterns, plus memory retrieval queries that may inadvertently access future data during replay. The attack surface for data leakage grows linearly with the number of skills and memory tiers. In our system, this required two distinct enforcement mechanisms: static AST analysis for training queries (Category A) and causal timestamp filtering for memory retrieval (Category B). The former catches leakage in model training; the latter prevents the agent from "remembering the future" during OOS replay evaluation.

**Measure what you think you're measuring.** The cost tracking bug (§8.7) is an instance of a general anti-pattern: instrumenting one part of a multi-component system and treating its output as the system-level measurement. Skill costs ($0.55) looked plausible because they were real measurements — just of the wrong thing. The corrected figure ($20.51) emerged only after auditing all three LLM call sites independently. In agentic systems where multiple components contribute to cost, latency, or quality, every component must be instrumented and the system-level metric must aggregate all components. Silent fallback to partial measurement produces plausible-looking but wrong numbers.

**Report negative and null results.** The persona null and the at-random OOS accuracy are both publishable findings that would typically be suppressed. The persona null directly motivates v0.2 activation steering — a concrete architectural hypothesis grounded in evidence rather than speculation. The OOS result reveals that orchestration quality and strategy alpha are separable concerns: the agent orchestrates well (81.7% skill selection accuracy) but the underlying strategy lacks sufficient edge for the orchestration to translate into directional alpha.

---

## 11. Future Work

**v1.2: Confirmatory multi-turn persona test.** The suggestive MultiTurn-Persona result (p=0.109, n=7) motivates a confirmatory run at n≥20 sequences. If convergence delta remains positive and significant, this would establish that persona conditioning works across turns even when single-turn injection is null — a meaningful architectural finding. Estimated cost: $7–10.

**v0.2: Activation steering for persona.** The v1.1 persona null (p=0.70) motivates exploring activation steering (Turner et al., 2024) — injecting persona vectors into the model's residual stream rather than concatenating them into the prompt. This would allow persona-conditioned behavior through direct model activation modification rather than relying on the LLM to condition on a float vector in natural language context.

**v0.2: Strategy v2 backtest execution.** The regime-weighted ML composite strategy with confidence gating and drawdown controls is implemented (Section 8.4). The next step is executing the v2 backtest against live BQ data and reporting the resulting Sharpe improvement over the naive tightness-delta baseline. If Sharpe ≥ 0, this unblocks DPO fine-tuning.

**v0.3: DPO fine-tuning.** Once the underlying strategy produces non-negative expected return, execute the DPO training pipeline with Qwen 2.5 7B. The preference pairs will be generated from environment feedback (P&L) combined with the auxiliary reward components.

**v1.2: Full OOS Replay re-run.** The v1.1 OOS Replay covered 110 of 237 trading days due to budget constraints. A full 250-day re-run with corrected cost tracking would provide the definitive same-scope comparison with v1.0. Estimated cost: $28 at $0.12/day.

**Multi-hub expansion.** Extend model training to Rotterdam, Fujairah, and Singapore hubs. The data exists in the pipeline (Sentinel-1 coverage is global); the work is in adapting the feature engineering and regime definitions to each hub's market microstructure.

**Live deployment.** Migrate from batch Cloud Run jobs to event-driven Cloud Functions, enabling real-time signal updates when new SAR imagery or market data becomes available.

**Strategy refinement.** Grid search over regime/spread/tightness combination weights, or replacing fixed weights with a learned weighting (e.g., stacking via logistic regression), may further improve the composite signal. The current 60/25/15 weighting is derived from model accuracy; an empirical search may find a better allocation.

---

## 12. Conclusion

OTM-Agent demonstrates that agentic AI can meaningfully orchestrate an existing industrial machine learning pipeline. The system wraps a production SAR-to-trading-signal pipeline with LLM-based planning, typed skill execution, persistent four-tier memory, Bayesian persona modeling, and multi-objective reward computation. The result is an analyst-facing system that selects the right analytical tools, maintains context across sessions, adapts to individual preferences, and provides a structured reward signal for policy improvement.

Five benchmarks were executed with real agent calls and re-verified across two versions (v1.0 and v1.1). The planner achieves 81.7% skill-inclusion accuracy (5.1× corrected random baseline), demonstrating strong orchestration quality that is robust to data-availability fixes. The OOS Replay benchmark produced directional accuracy statistically indistinguishable from random (54.4% full-year, 50.0% same-period v1.1), confirming that the agent orchestrates well but the underlying strategy lacks sufficient edge for the orchestration to translate into directional alpha — a finding that cleanly separates orchestration quality from strategy alpha as independent evaluation dimensions. The persona-align benchmark confirmed a pre-registered null result with high confidence (p=0.70): in-prompt persona injection does not produce detectable behavioral change at v0.1, motivating v0.2 activation steering as the architectural path forward. The Mem-Utility benchmark produced a null result (−0.064, CI crosses zero), indicating the 4-tier memory system does not yet detectably improve response quality. The MultiTurn-Persona benchmark showed suggestive but non-significant convergence (+0.173, p=0.109), consistent with Bayesian Kalman convergence requiring multiple turns to manifest.

The evaluation methodology contributes three integrity mechanisms: (1) OOS holdout enforcement via static AST analysis integrated into CI, which eliminates training data leakage at the source code level; (2) causal memory filtering via `query_ts` parameters threaded through all 8 retrieval paths, which prevents the agent from accessing future information during OOS replay; and (3) a self-audit cycle that revolved six times, identifying and correcting six distinct categories of integrity failure — OOS leakage, model provenance, measurement bugs, planner stop-conditions, cost tracking, and architecture drift — each documented with preserved audit trails, transparent disclosures, and re-verification. Total evaluation cost across all v1.1 re-runs was $20.51 — 7× under the $150 budget — demonstrating that continuous agentic evaluation is operationally feasible.

We report results with honest accounting: a negative initial Sharpe (−0.10), a persona null, an at-random directional accuracy, and a 30× cost-tracking correction. Each negative finding is itself a contribution — the persona null motivates activation steering, the directional accuracy separates orchestration from alpha, and the cost correction demonstrates the audit cycle catching its own measurement infrastructure. The 8-benchmark evaluation suite, 258-test unit test suite (254 passing, 4 pre-existing failures documented), 9-page Streamlit dashboard, 28-query chat quality smoke test, and OOS holdout and causal leakage enforcement tooling are released as contributions to the agentic AI research community. Together, they provide a template for building, evaluating, and auditing domain-specific agentic systems with verifiable data integrity guarantees.

---

## Appendix A: Full Skill Catalog

| # | Skill Name | Category | Preconditions | Effects | Retention Probes |
|---|-----------|----------|---------------|---------|-----------------|
| 1 | sense_tank_state | BigQuery | — | tank_state_available | Current fill level? Confidence score? |
| 2 | fetch_tank_history | BigQuery | — | tank_history_available | Date range fetched? Row count? |
| 3 | fetch_region_signal | BigQuery | — | region_signal_available | Which hub? Signal direction? |
| 4 | fetch_trade_log | BigQuery | — | trade_log_available | Last trade date? Open positions? |
| 5 | fetch_tightness | BigQuery | — | tightness_available | Current tightness value? Variance? |
| 6 | fetch_market_data | BigQuery | — | market_data_available | WTI price? Spread value? |
| 7 | compute_fill_signal | Compute | tank_state_available | fill_signal_computed | Signal direction? Magnitude? |
| 8 | compute_tightness | Compute | tank_history_available | tightness_computed | Mean tightness? Trend direction? |
| 9 | compute_zscore | Compute | tightness_available | zscore_computed | Z-score value? Above/below threshold? |
| 10 | compute_delta | Compute | tightness_available | delta_computed | Weekly change? Monthly change? |
| 11 | compute_goii | Compute | region_signal_available | goii_computed | GOII index value? Hub contributions? |
| 12 | predict_regime | ML | linkage_features_available | regime_prediction_available | Predicted regime? Confidence? Top feature? |
| 13 | predict_spread_direction | ML | linkage_features_available | spread_prediction_available | Direction? Hit rate? |
| 14 | predict_eia_surprise | ML | hub_state_available | eia_prediction_available | Direction? RMSE? |
| 15 | trigger_sar_pipeline | Cloud Run | — | sar_pipeline_triggered | Job status? Processing time? |
| 16 | trigger_market_ingest | Cloud Run | — | market_ingest_triggered | Tables updated? Row counts? |
| 17 | place_paper_trade | Trade | regime_prediction_available ∨ spread_prediction_available | trade_executed | Side? Size? Entry price? |
| 18 | explain_market_state | LLM | market_data_available | explanation_generated | Key drivers? Risk factors? |
| 19 | summarize_episode | LLM | — | summary_generated | Main finding? Confidence level? |
| 20 | alert_on_threshold | Alert | tank_state_available ∨ tightness_computed | alert_checked | Alert triggered? Threshold value? |

## Appendix B: BigQuery Table Schema and OOS Filter Impact

| Table | Total Rows | Pre-Cutoff (< 2025-05-01) | Removed | % Removed |
|-------|-----------|---------------------------|---------|-----------|
| otm_staging.sentinel1_weekly_tank_features | 5,124 | 4,578 | 546 | 10.66% |
| otm_stage2.calendar_spreads | 20,276 | 19,804 | 472 | 2.33% |
| otm_stage2.market_prices | 40,014 | 39,062 | 952 | 2.38% |
| otm_stage1.release_clock | 1,148 | 1,099 | 49 | 4.27% |
| otm_stage2.cot_positions | 327 | 75 | 252 | 77.06% |
| otm_curated.tank_weekly_signal | 45 | 0 | 45 | 100.0% |
| otm_stage3.daily_signals | 7 | 0 | 7 | 100.0% |
| otm_stage1.hub_state_day | 309* | 309 | 0 | 0% |
| otm_stage2.linkage_features | 347* | 347 | 0 | 0% |

*Backfilled during the audit with OOS filter already in place; these tables contain only pre-cutoff data by construction.

## Appendix C: OOS Leakage Test Implementation

The leakage detection test (`test_oos_leakage.py`) uses Python's `ast` module to extract SQL strings from source code, including:

- **Simple strings:** `ast.Constant` nodes containing SQL keywords
- **F-strings:** `ast.JoinedStr` nodes, where only `Constant` parts are extracted (dropping `FormattedValue` interpolations like `{PROJECT_ID}`)
- **String concatenation:** Handled via recursive traversal of `ast.BinOp` with `ast.Add` operator

The date filter detection regex:

```python
DATE_FILTER_RE = re.compile(
    r"WHERE\b.*?\b("
    + "|".join(DATE_COLUMNS)
    + r")\s*<\s*['\"]2025-05-01['\"]",
    re.IGNORECASE | re.DOTALL,
)
```

Training table detection uses word-boundary matching against the 19 known table names. Files in `NO_DATE_FILTER_NEEDED` (12 files: real-time serving, API, schema, monitoring) and `OOS_EVAL_ALLOWLIST` (5 files: evaluation harness, bq_safe.py, presentation generation) are excluded from the filter requirement.

A second test module, `test_causal_leakage.py`, verifies the Category B causal filter (Section 5.5) with 16 tests across 5 test classes: episodic memory filtering (5 tests), semantic memory filtering (3), procedural memory filtering (2), MemoryManager query_ts threading (2), and BQ query static analysis (4).

## Appendix D: Retrain Results

Complete structured output from the OOS-clean retrain (v0.2.0-oos-clean, 2026-05-21):

```json
{
  "retrain_run": {
    "timestamp": "2026-05-21T05:14:38.196017+00:00",
    "oos_cutoff": "2025-05-01",
    "random_state": 42,
    "model_version": "v0.2.0-oos-clean"
  },
  "models": [
    {"model": "evaluate_stage1", "stage": 1, "status": "SUCCESS",
     "metrics": {"hub_state_rows": 309, "eia_direction_accuracy": 0.528,
                 "stability_avg": 0.1732, "stability_max": 1.7144,
                 "all_criteria_pass": true}},
    {"model": "regime_classifier", "stage": 2, "status": "SUCCESS",
     "metrics": {"accuracy": 0.6535, "above_random": true,
                 "baseline": 0.529, "predictions": 329}},
    {"model": "spread_forecaster", "stage": 2, "status": "SUCCESS",
     "metrics": {"accuracy": 0.514, "above_random": true,
                 "predictions": 321}},
    {"model": "eia_surprise", "stage": 2, "status": "SUCCESS",
     "metrics": {"direction_accuracy": 0.5152, "rmse_kb": 1606.0,
                 "rmse_improvement_pct": 0.62}},
    {"model": "signal_generator", "stage": 3, "status": "SUCCESS",
     "metrics": {"composite": -0.5, "direction": "short",
                 "confidence": 0.72}},
    {"model": "advanced_models", "stage": 3, "status": "SUCCESS",
     "metrics": {"var_tightness": 0.0149, "garch_vol": 2.644,
                 "ensemble": "long"}},
    {"model": "backtest_engine", "stage": 2, "status": "SUCCESS",
     "metrics": {"total_pnl": -26217.5, "sharpe": -0.1,
                 "win_rate": 0.014, "verdict": "NEGATIVE"}},
    {"model": "scorecard", "stage": 3, "status": "SUCCESS",
     "metrics": {"regime_acc": 1.0, "spread_acc": 1.0}}
  ]
}
```

## Appendix E: Dashboard Pages

*Screenshots to be included in final version. Each page is accessible at the corresponding Streamlit URL path.*

| Page | URL Path | Key Visualizations |
|------|----------|-------------------|
| SAR Monitor | `/1_SAR_Monitor` | Tank farm map, fill-level bar charts, confidence heatmap |
| Stage 1 Kalman | `/2_Stage1_Kalman` | Kalman tightness time series, confidence bands, per-tank decomposition |
| Stage 3 Trading | `/3_Stage3_Trading` | Signal timeline, equity curve, P&L waterfall, scorecard table |
| GOII Index | `/4_GOII_Index` | 4-hub composite index, per-hub contribution stacked area |
| Agent Chat | `/5_Agent_Chat` | Chat interface, skill execution trace sidebar, feedback buttons |
| Agent Traces | `/6_Agent_Traces` | Session timeline, skill DAG, cost/latency breakdown |
| Memory Explorer | `/7_Memory_Explorer` | 4-tier memory browser, search, episode detail view |
| Persona State | `/8_Persona_State` | Persona compass (execution ↔ analysis), covariance heatmap, mode trajectory |
| Eval & Benchmarks | `/9_Eval_Benchmarks` | Benchmark comparison table, reward violin plots, ablation bar charts |

---

*End of Technical Report*
