# Claude Training 3 — Session Log
**Date:** July 13, 2026  
**User:** jon.grupp@carta.com  
**Branch:** `claude/gfind-training-3-ver8rh`  
**Data source:** `PROD_DB.CLAUDE_TRAINING_SALESFORCE`

---

## Session Overview

This session completed Charly Kevers' Claude Training 3 exercise using Salesforce CRM data in Snowflake. The goal was to build a revenue and collections analysis telling a coherent business story across three areas: pipeline health, ARR by product, and invoice collections.

---

## What We Did

### 1. Schema Exploration
- Located the correct Snowflake schema: `PROD_DB.CLAUDE_TRAINING_SALESFORCE` (initially misidentified as `TRAINGING_SALESFORCE`)
- Mapped 8 tables via `INFORMATION_SCHEMA.COLUMNS`:
  - `ACCOUNT` — customer master (type, entity type, funding stage)
  - `CONTACT` — contacts linked to accounts
  - `OPPORTUNITY` — deals with stage, amount, close date, win/loss flags
  - `OPPORTUNITY_LINE_ITEM` — ARR line items (`IS_ARR_C`, `TOTAL_PRICE`, `PRODUCT_NAME_TEXT_C`)
  - `INVOICE` — billing records (status, balance, invoice date, due date)
  - `PAYMENT` — payment records linked to invoices
  - `CASE` — support cases
  - `TASK` — activity records

### 2. Revenue & Collections Analysis
**Approach:** Planned the analysis before running queries — identified tables needed per question, agreed on 3 batched SQL queries for token efficiency.

**Queries run (in parallel):**
1. Pipeline health — `GROUP BY STAGE_NAME` + quarterly trend + loss reasons
2. ARR breakdown — `OPPORTUNITY_LINE_ITEM JOIN OPPORTUNITY JOIN ACCOUNT GROUP BY PRODUCT_NAME_TEXT_C, TYPE, ENTITY_TYPE_C`
3. Invoice collections — `GROUP BY STATUS` with aging buckets via `DATEDIFF`

**Key findings:**
- **Pipeline:** 88.6% win rate, $20.1M won, $56.2M open pipeline, $18.3M late-stage. #1 loss reason: No Decision (not competitors or price).
- **ARR:** Cap Table leads at $8.3M (40% of total). Fund Admin × VC Firms is highest-ACV repeatable segment at $124K avg. Two parallel motions: high-volume Corp/LLC and high-ACV Fund.
- **Collections:** 80% collected ($42.5M of $52.9M). No 180+ day open AR. $2.2M aged 61–180 days needs follow-up. $4.3M in cancellations (8.1%) requires root-cause audit.

**Note on date range:** SQL filter `DATEADD(year, -1, CURRENT_DATE())` correctly pulls 12 months (Jul 13 2025 – Jul 13 2026). However, the training dataset has dense closed-won data through Nov 2025 only; Dec 2025–Jun 2026 records are mostly open pipeline with future close dates.

### 3. Lead Source Analysis
**Question:** Which lead sources generate the most closed-won ARR?

**Query:** `OPPORTUNITY JOIN OPPORTUNITY_LINE_ITEM` filtered to IS_WON + IS_ARR_C, grouped by `LEAD_SOURCE`

**Results (9 sources):**

| Lead Source    | ARR    | Deals | Avg ACV |
|----------------|--------|-------|---------|
| Web            | $5.0M  | 50    | $65K    |
| Content/SEO    | $3.8M  | 23    | $107K   |
| Referral       | $3.2M  | 41    | $54K    |
| Event          | $2.0M  | 28    | $41K    |
| Inbound Demo   | $1.9M  | 29    | $54K    |
| Partner        | $1.5M  | 16    | $69K    |
| Outbound SDR   | $1.3M  | 21    | $44K    |
| Paid Search    | $1.3M  | 12    | $65K    |
| Direct         | $97K   | 6     | $16K    |

**Key insight:** Web leads volume; Content/SEO leads deal quality at $107K avg ACV (64% above Web). Referral is most CAC-efficient. Outbound SDR underperforms vs Paid Search on same ARR with more deals.

---

## Outputs Produced

| File | Description |
|------|-------------|
| `revenue_collections_report.html` | Polished self-contained HTML report with exec summary, section commentary, pipeline + ARR + collections charts, and 5 key takeaways |
| `lead_source_dashboard.html` | Interactive dashboard — ARR bars, ACV bars, bubble efficiency chart, and data table by lead source |
| `session_log.md` | This file |

---

## Tools & Techniques Used

- **Snowflake:** `mcp__Snowflake__execute_sql` — direct SQL aggregations, no full table scans
- **Dataviz skill:** `/dataviz` — palette validation via `validate_palette.js` before building charts; ordinal blue ramp for single-series bars, categorical 8-slot palette for multi-series bubble chart
- **Chart.js 4.4** — quarterly bar chart and bubble chart; custom CSS bars for all other charts
- **All queries ran in parallel** where possible to minimize token usage

---

## SQL Patterns Used

```sql
-- ARR by product and segment
SELECT oli.PRODUCT_NAME_TEXT_C, a.TYPE, a.ENTITY_TYPE_C,
       COUNT(DISTINCT o.ID), SUM(oli.TOTAL_PRICE), AVG(oli.TOTAL_PRICE)
FROM OPPORTUNITY_LINE_ITEM oli
JOIN OPPORTUNITY o ON oli.OPPORTUNITY_ID = o.ID
JOIN ACCOUNT a ON o.ACCOUNT_ID = a.ID
WHERE o.IS_WON = TRUE
  AND o.CLOSE_DATE >= DATEADD(year, -1, CURRENT_DATE())
  AND oli.IS_ARR_C = TRUE
GROUP BY 1, 2, 3

-- Invoice aging buckets
SELECT STATUS,
  SUM(CASE WHEN DATEDIFF(day, INVOICE_DATE, CURRENT_DATE()) BETWEEN 0 AND 30 THEN BALANCE ELSE 0 END),
  SUM(CASE WHEN DATEDIFF(day, INVOICE_DATE, CURRENT_DATE()) BETWEEN 31 AND 60 THEN BALANCE ELSE 0 END),
  -- ... etc
FROM INVOICE
GROUP BY STATUS

-- Lead source ARR
SELECT o.LEAD_SOURCE, COUNT(DISTINCT o.ID), SUM(oli.TOTAL_PRICE), AVG(oli.TOTAL_PRICE)
FROM OPPORTUNITY o
JOIN OPPORTUNITY_LINE_ITEM oli ON oli.OPPORTUNITY_ID = o.ID
WHERE o.IS_WON = TRUE
  AND o.CLOSE_DATE >= DATEADD(year, -1, CURRENT_DATE())
  AND oli.IS_ARR_C = TRUE
GROUP BY 1
```
