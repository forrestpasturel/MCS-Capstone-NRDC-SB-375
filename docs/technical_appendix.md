# Technical Appendix: Methodology, Data Sources, and Limitations

This framework supports reproducible, data-driven performance assessments for California's regional transportation planning and funding via SB 1087 (amending SB 375).

---

## 1. The Diagnostic: Identifying the Failure (Corrective Action Status)
### Goal
Measure the real-world implementation gap by mapping actual per-capita VMT trajectories against adopted Sustainable Communities Strategy (SCS) targets, while cross-referencing community vulnerability.

### Data Sources
*   **VMTIndex (or equivalent):** Granular (Census Block Group or tract) per-capita VMT tracking to determine precise trend deviations from baseline.
*   **CalEnviroScreen 4.0/4.1:** Highlighting pollution burden, diesel PM, and traffic density metrics against spatial VMT growth.

### Methodology
1. Evaluate regional compliance over rolling cycles (SB 375 mandates).
2. Measure correlation between localized VMT increases and CalEnviroScreen disadvantaged community indices using spatial joins.
3. Quantify regions eligible for Pillar 1 "Corrective Action".

---

## 2. The Verification: Debunking Congestion Relief
### Goal
Measure the actual time-savings impact of highway widening events to demonstrate the economic and environmental cost of induced demand.

### Data Sources
*   **Caltrans PeMS (Performance Measurement System):** Baseline detector data evaluating speeds and flows both pre- and post-widening over 3+ year windows.
*   **NCST Induced Travel Calculator:** Estimates proportional elasticity for new lane miles added.

### Methodology
1. Pull PeMS historical data for specific segments (e.g., I-80 corridor).
2. Clean baseline and operation years, omitting anomalous construction delays to find stabilized flow rates.
3. Use the NCST calculator to output implied 20-year CO₂-equivalent penalties for capacity added logic (Pillar 2 Mitigation).

---

## 3. The Vision: Modeling the Climate Floor
### Goal
Quantify emission offsets (GHG delta) associated with alternative project planning, establishing an objective cutoff score for funding eligibility.

### Data Sources
*   **Regional Travel Demand Model (TDM):** Project-specific ridership / vehicle volume estimates for Baseline (No-Build/Capacity Expansion) vs Alternative (Multi-modal).
*   **EMFAC2021/202x:** California Air Resources Board emissions factor outputs for projected corridors.

### Methodology
1. Ingest TDM baseline VMT vs alternate mode VMT outputs.
2. Filter EMFAC datasets for identical horizon years.
3. Calculate explicit 20-year GHG offsets for a hypothetical multimodal project versus standard capacity addition, generating the "Climate Floor" metric (Pillar 3).
