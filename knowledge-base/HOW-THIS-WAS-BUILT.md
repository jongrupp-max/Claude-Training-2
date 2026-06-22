# How This Knowledge Base Was Built

**Date:** 2026-06-22  
**Author:** Claude Code (claude-sonnet-4-6) working with Jon Grupp  
**Session goal:** Document major 409A decisions from the last 18 months into a structured, navigable wiki

---

## Overview

This knowledge base was created in a single Claude Code session. The workflow was:

1. Search Slack channels for 409A-related decisions and discussions
2. Synthesize findings into structured decision records in-context
3. Write markdown files directly (no external API calls — all analysis happened in the session)
4. Commit and push to `claude/sleepy-galileo-4ss87z`

---

## Data Sources

### Slack (primary source)

Searched using the Slack MCP tool (`slack_search_public_and_private`) across these channels, with date filter `after:2024-12-31`:

| Channel | What it contained |
|---|---|
| `#valuation-support` | Methodology escalations, warrant/OPM questions, biotech/crypto precedents |
| `#valuators` | Team-wide announcements, AVA QA tool rollout, CapIQ + Claude integration |
| `#advisory-services-questions` | Audit defense playbooks, no-signature policy, Monte Carlo objection handling |
| `#val-sales` | IRA transfer custom engagement, sales methodology questions |
| `#erp-delivery-alerts` | Delivery model restructure, Corporation Station hub, timeline policy |
| `#ramp-services-questions` | International ledger changes, CSM-reported platform issues |

Key search queries included:
- `409A decision methodology after:2024-12-31`
- `warrant OPM alignment`
- `Monte Carlo audit`
- `AVA QA rollout`
- `delivery model advisor assignment`
- `IRA transfer signed valuation`
- `international ledger changes`
- `blackout period options`
- `no signature audit trail`

### Local CSVs (secondary/reference)

The repository contains `slack_compressed_channels/` — compressed Slack export CSVs with columns `u,t,m` (user_id integer, timestamp, message). These were available as backup but Slack MCP live search was the primary extraction method.

### User name resolution

`results/users.csv` maps Slack short IDs (e.g. `U319`) to real names. Integer user IDs in the CSV files correspond to the numeric portion of these short IDs.

Key mappings used:
- U319 → Daniel Gladstone
- U439 → Rizwan Ahmed
- U81 → Jordan Agnew
- U242 → Ian Kawamoto
- U216 → Kristoffer Warren

---

## Methodology

The original plan was to run a Python script (`generate_knowledge_base.py`) that would load Slack data and call the Claude API to synthesize decisions. This was blocked because sending internal Slack data to an external API is not permitted in this environment.

**Workaround:** Since all the Slack searches and decision synthesis happened in-context during the session (via Slack MCP tools), the analysis was already complete. The markdown files were written directly using the Write tool — no script execution needed.

---

## Files Created

```
knowledge-base/
├── index.md                                      # Chronological timeline of all 15 decisions
├── HOW-THIS-WAS-BUILT.md                         # This file
├── decisions/
│   ├── ava-ai-qa-rollout.md                      # Methodology, 2025-08
│   ├── foreign-client-409a-guidance.md           # Methodology, 2025-07
│   ├── biotech-hybrid-scenario-weighting.md      # Methodology, 2026-02
│   ├── crypto-volatility-selection-coinbase.md   # Methodology, 2026-03
│   ├── capiq-claude-comp-screening.md            # Methodology, 2026-04
│   ├── warrant-opm-alignment-policy.md           # Methodology, 2026-05
│   ├── international-409a-ledger-changes.md      # Methodology, 2026-05
│   ├── blackout-period-options-caution.md        # Client-handling, 2026-04
│   ├── advisor-delivery-model-restructure.md     # Operational, 2026-06
│   ├── delivery-timeline-communication-policy.md # Operational, 2026-06
│   ├── upmarket-team-backlog-management.md       # Operational, 2026-06
│   ├── monte-carlo-expedited-delivery.md         # Operational, 2026-06
│   ├── no-signature-policy-audit-trail.md        # Client-handling, 2026-06
│   ├── monte-carlo-audit-objection-response.md   # Client-handling, 2026-06
│   └── ira-transfer-custom-engagement.md         # Client-handling, 2026-06
└── people/
    ├── evan-rydinski.md
    ├── brendan-rigby.md
    ├── daniel-gladstone.md
    ├── rizwan-ahmed.md
    ├── jon-grupp.md
    ├── kristoffer-warren.md
    ├── firmaye-tarekegn.md
    ├── ian-kawamoto.md
    └── tessa-horne.md
```

A zip archive of all files is also in the repo root: `knowledge-base.zip`

---

## Decisions Captured

### Methodology (7)

| Decision | Date | Key People |
|---|---|---|
| [Foreign Client 409A Guidance](decisions/foreign-client-409a-guidance.md) | 2025-07 | Daniel Gladstone |
| [AVA AI QA System Rollout](decisions/ava-ai-qa-rollout.md) | 2025-08 | Kristoffer Warren, Brendan Rigby, Firmaye Tarekegn |
| [Biotech Hybrid Scenario Weighting](decisions/biotech-hybrid-scenario-weighting.md) | 2026-02 | Brendan Rigby, Daniel Gladstone |
| [Crypto Volatility Selection (Coinbase)](decisions/crypto-volatility-selection-coinbase.md) | 2026-03 | Brendan Rigby, Daniel Gladstone |
| [CapIQ + Claude AI Comp Screening](decisions/capiq-claude-comp-screening.md) | 2026-04 | Kristoffer Warren |
| [Warrant/OPM Alignment Policy](decisions/warrant-opm-alignment-policy.md) | 2026-05 | Jon Grupp, Firmaye Tarekegn, Rizwan Ahmed |
| [International 409A Ledger Changes](decisions/international-409a-ledger-changes.md) | 2026-05 | Tessa Horne |

### Operational (4)

| Decision | Date | Key People |
|---|---|---|
| [Advisor Delivery Model Restructure](decisions/advisor-delivery-model-restructure.md) | 2026-06 | Evan Rydinski, Brendan Rigby, Daniel Gladstone, Jon Grupp |
| [Delivery Timeline Communication Policy](decisions/delivery-timeline-communication-policy.md) | 2026-06 | Evan Rydinski |
| [Upmarket Team Backlog Management](decisions/upmarket-team-backlog-management.md) | 2026-06 | Evan Rydinski |
| [Monte Carlo Expedited Delivery Precedent](decisions/monte-carlo-expedited-delivery.md) | 2026-06 | Evan Rydinski, Jon Grupp |

### Client-Handling (4)

| Decision | Date | Key People |
|---|---|---|
| [Blackout Period Options Caution](decisions/blackout-period-options-caution.md) | 2026-04 | Rizwan Ahmed |
| [No-Signature Policy / Audit Trail](decisions/no-signature-policy-audit-trail.md) | 2026-06 | Rizwan Ahmed, Daniel Gladstone |
| [Monte Carlo Audit Objection Response](decisions/monte-carlo-audit-objection-response.md) | 2026-06 | Rizwan Ahmed, Brendan Rigby, Daniel Gladstone |
| [IRA Transfer Custom Engagement](decisions/ira-transfer-custom-engagement.md) | 2026-06 | Jon Grupp, Ian Kawamoto |

---

## People Documented (9)

| Person | Role |
|---|---|
| [Evan Rydinski](people/evan-rydinski.md) | Head of Valuation Delivery |
| [Brendan Rigby](people/brendan-rigby.md) | Methodology Lead |
| [Daniel Gladstone](people/daniel-gladstone.md) | Senior Methodology Analyst |
| [Rizwan Ahmed](people/rizwan-ahmed.md) | Audit Defense / Senior Analyst |
| [Jon Grupp](people/jon-grupp.md) | Senior Valuation Advisor |
| [Kristoffer Warren](people/kristoffer-warren.md) | AI/QA Innovation Lead |
| [Firmaye Tarekegn](people/firmaye-tarekegn.md) | Valuation Analyst |
| [Ian Kawamoto](people/ian-kawamoto.md) | Sales Methodology Support (departed mid-2026) |
| [Tessa Horne](people/tessa-horne.md) | Operations & CSM Liaison |

---

## Scope Notes

- **Time range:** July 2025 – June 2026
- **Decision types included:** Methodology, Operational, Client-handling
- **Excluded:** Pricing decisions, policy changes without documented Slack discussion, personnel/HR matters
- **Completeness:** Based on Slack MCP search results; decisions discussed only in DMs or undiscoverable channels may be missing
