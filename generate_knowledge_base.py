#!/usr/bin/env python3
"""
Generate a 409A knowledge base from Slack data.

Reads local CSVs + uses pre-gathered Slack MCP data, sends to Claude API,
writes markdown files to knowledge-base/.
"""

import csv
import json
import re
import os
from datetime import datetime
from pathlib import Path
import anthropic

# ── Constants ──────────────────────────────────────────────────────────────────

REPO_ROOT = Path(__file__).parent
CSV_DIR = REPO_ROOT / "slack_compressed_channels"
USERS_CSV = REPO_ROOT / "results" / "users.csv"
OUTPUT_DIR = REPO_ROOT / "knowledge-base"

# Pre-gathered Slack MCP data (from live searches across all relevant channels)
# Format: list of {channel, date, from, text}
SLACK_MCP_DATA = """
=== CHANNEL: #valuators ===

[Aug 4, 2025] Kristoffer Warren:
"We are attempting to move 80%+ of 409A Quality Assurance to AI, and will be releasing blocks of the overall project to the broader team once they have gone through preliminary testing. Currently, only the DLOM workflow is ready for release. We are striving towards covering all basics of 409A. Additional blocks will be released once they have passed preliminary testing. Shoutout to folks that have gotten us this far: Brendan Rigby, Firmaye, ZacBair, Sean, david.higbee, Robel."

[Aug 11, 2025] Kristoffer Warren:
"Quick update on moving 409A Quality Assurance to AI. Three AI-friendly policies are now available: DLOM, New! Comparable Companies, New! Pre-Seed Benchmarking. Please continue utilizing this workflow to begin using the AI at your discretion until an agentic workflow is built."

[Sep 22, 2025] Kristoffer Warren:
"We're excited to share a few updates regarding AVA! 1. Gemini Gems are now shareable. 2. We've added Standard and Hybrid Equity Adjustments, which means that AVA now covers all of Standard Non-Benchmarking 409A. 3. AVA can officially help with Benchmarking! We are asking that everyone use AVA whenever applicable. Next steps: visiting all 409A Delivery teams to demonstrate AVA; monitoring usage of AVA for adoption; Expansion of policies to include DTC, DTC EA, Basket Backsolve, DFC, Non-Revenue Multiple GPCs, etc."

[Apr 10, 2026] Jordan Agnew:
"CapIQ is now available in Carta's internal Claude marketplace, as well as some initial skills for 409A comp screening."

[Feb 19, 2026] Victor Huang:
"The UK Val Eng team is developing a new UK Val product with the intent to migrate users from CapDesk to Carta. The new product will be integrated with CapHub and our 409A card. We need at least one analyst to help participate in a testing session next week."

[Jul 29, 2025] Daniel Gladstone:
"The gist of it is that the 409A tends to be conservative enough that it's either more strict or close enough to other tax authorities that it suffices for similar use cases. It's not uncommon that foreign clients we work with simply use the 409A report anyway as they know the local regulations are largely the same. However, they bear this 'risk' of non-specific guidance exposure, as we only provide support for 409A matters. They should just confirm with their own legal and tax authorities to make sure. FWIW I've worked with a number of Canadian companies over the years and I don't think I've ever had one come back and say they ran into issues."

[Jul 29, 2025] Jackson Reed (prompted the discussion):
"As it relates to option issuance, how do we communicate they can use 409As as an indication of value for non-US Employees. The two examples I had today are Netherlands and Canada. Based on what I've read, there really isn't any formal code that other countries need to adhere to like IRC 409A, but it's based on being reasonable and defensible broadly speaking so a 409A should suffice."

[May 12, 2026] Jennifer Hamblet:
"This LLC is insisting that their Class B shares need to adjust on the LLC platform based on additional dilution/issuances. All values in a 409A should be static, correct? There wouldn't be a situation where it would be fluid?"

[Apr 2025] Matthew Green (in #valuators):
"Exxat, Inc. reached out hoping to get a signed version of the 409A report due to 'local regulatory obligations in India'. OR a formal declaration on Carta's official letterhead stating: A) It is Carta's policy not to sign 409A reports; and B) The report provided is a legally valid document, even though it is unsigned."

[Apr 2025] Mami Ishikawa (in #valuators):
"Glydways, Inc. is requesting Carta to be a fact witness that can testify as to the creation of the 409A report and the company valuation for litigation."

=== CHANNEL: #advisory-services-questions ===

[Feb 6, 2026] Brendan Rigby:
"It looks like this is their first 409A and they fundamentally disagree with the backsolve methodology. We're at 14% PoP and they're pushing for 10% PoP. We have precedent for adjusting the Hybrid scenario weightings for Biotech companies so we could send them a very aggressive draft showing 90/10 weightings at 8% PoP but I think their frustration is rooted in a non-biotech specific model. What are your thoughts, Daniel Gladstone?"

[Mar 20, 2026] Brendan Rigby:
"The discrepancy is rooted in the different assumptions used for post-money equity value versus a 409A valuation. Specifically, a post-money valuation typically assumes all shares are worth the most recent Series A price. In contrast, a 409A analysis accounts for the complex capital structure of the Company. It recognizes that Series A Preferred shares carry liquidation preferences and seniority that Common shares do not. Because Common shares sit lower in the capital stack and lack these protections, they are valued at a discount to the Preferred price."

[Mar 23, 2026] Brendan Rigby:
"Looks like for the 409A we kept it consistent with the prior at 90% [volatility], this looks to be tied closest with Coinbase which is a better comparable than Crypto miners (MARA, Riot, Argo, BTCS) and pure token-backed companies (Circle) with volatilities that reflect commodity/crypto asset exposure, not company fundamentals."

[Mar 13, 2026] Brendan Rigby:
"G&E reports are usually required to be independent reports representing the value of a gift as of the transfer date, and are reviewed by the IRS as such. I don't think it would be acceptable to give the IRS a 409A report. We can leverage the 409A to execute the G&E (part of why our G&E's are so competitively priced) but the required standards/inputs/outputs differ."

[Apr 8, 2026] Rizwan Ahmed:
"Since the ESOP valuation has not been determined as of now we can't do PWERM so we can just follow the standard procedure such as GPC/DCF/backsolve to value the company for 409A."

[Apr 27, 2026] Brendan Rigby:
"Our Fair market value conclusion was for the Class B share class; for 409A purposes (option strike valuations), we are trying to determine the FMV of the share class into which options strike."

[Apr 27, 2026] Brendan Rigby:
"The FMV of common (as of the warrant valuation date) is an input for our common warrant valuation model; as a result, without sourcing one externally or creating one internally via an independent 409A, we're unable to execute the analysis. It sounds like they need help understanding that the 409A FMV is an input for the common warrant valuation, as such we're happy to do it, but we need to do the 409A first."

[Jun 2, 2026] Brendan Rigby:
"We typically don't issue side letters with signatures. We can describe/explain the methodology and inputs via email but the only formal documentation regarding the analysis is contained within the 409A report itself."

[Jun 2, 2026] Rizwan Ahmed:
"Suggestions for response on common stock warrant exercise interaction with 409A: By way of context, the warrants' presence does put a modest, strike-price-dependent downward pressure on the common value today, which is captured within the valuation model. Cash injection and new shares issuance have offsetting impact. Common's position in the waterfall sits at the bottom and lacks liquidation preferences. Exercise is a reflection of growth, not a cause of it."

[Jun 16, 2026] Brendan Rigby:
"Agreed with Daniel that economically they seem similar and that, for 409A purposes, the valuations are executed on a minority (non-controlling) stakeholder basis for both share classes, so they would not differ in a 409A valuation on that front."

[May 18, 2026 — Bot] Advisory Services bot:
"BDO has specifically requested that one of the individuals listed in the 'Appraiser Bio & credentials' exhibit join the call (Alex, Jon, Riz, or Runar). They have been comparing our 409A to a PPA valuation done in 2024."

=== CHANNEL: #val-sales ===

[May 1, 2026] Shannon Olson (prompted):
"A client is concerned that since the turnaround is so quick, there could be a lot of automation/AI used rather than an actual analyst who completes it. He is also wondering if 'an accredited analyst' signs off on it."

[Jun 16, 2026] Rizwan Ahmed (drafted official response):
"Carta 409A valuation reports do not have signature section. Every valuation report is delivered as an official, corporate document featuring Carta's formal corporate designation, valuation team credentials, and a Summary section that certifies the Fair Market Value (FMV) conclusion. The report is made final when Company's board/management accepts it inside the platform. This internal workflow creates a secure, digital audit trail of authorization. Carta stands behind its valuations as a corporate entity. Should our auditors have any questions regarding the valuation report, Carta's Valuation Services team provides audit defense support to walk through the methodologies, assumptions, and data sets used — meaning a physical signature is not required to engage Carta's support or defend the safe harbor status."

[Jun 15, 2026] Ashley Ryan (prompted):
"A PE backed LLC is evaluating us for CT + 409A. Auditor claim: 'There are valuation methods (i.e., Monte-Carlo models) Carta historically does not have the ability to use. These methods may be determined to be the most appropriate dependent on the Company.'"

[Jun 16, 2026] Rizwan Ahmed (official response to Monte Carlo audit objection):
"Carta has capability to handle these complex valuations. Methodology Selection & Weighting: For every valuation, Carta evaluates the appropriateness of the OPM Back-Solve, Income Approach (DCF), and Market Approaches (Guideline Public/Transactions). Complex Capital Structures: We design our models to handle complex equity features, including seniority tranches, liquidation preferences, participating rights, and performance-based vesting. Advanced Modeling (Monte Carlo & Path-Dependent Features): While standard 409A valuations typically leverage the closed-form Black-Scholes OPM, Carta can handle complex valuations also as needed. If a company's capital structure features path-dependent elements, we do have the capability to deploy Monte Carlo simulations to isolate value."

[Jun 16, 2026] Ariana Nurisso (prompted):
"Are our 409As signed? I have a PE backed portfolio company who requires their valuations to be signed."

[Jun 16, 2026] Ariana Nurisso (follow-up on IRA transfer case):
"They have 30 shareholders who transfer stock into an IRA. They have historically used an outside CPA to do their 409A and used that 409A valuation as the price for the transfer. On the form for the IRA custodian, the CPA signs it. Since they are looking to transfer 409A services to Carta, we are trying to come up with a solution for them as they require their 409A signed by the provider. Before Ian left, he had suggested we do a custom engagement for them, similar to a G&E valuation but our Legal team will amend the EL to be specific for their needs. In this situation, would we 1) sign the 409A so they can use it for their intended purposes or 2) do we sign G&E valuations that they can use for the IRA transfer? [tagging Jon Grupp]"

[May 5, 2026] Ariana Nurisso (prompted):
"Goldman Sachs Private Equity purchased the majority of CarltonOne's stock in 2024. BDO is requesting the 409A valuation. I believe we will need Carta's permission to share this outside its original intended purpose."

[Jun 1, 2026] Jake Pavicich:
"Can we normalize executive compensation in the valuation? The founders are working full-time but not paying themselves (~$300-400K/year each in market-rate exec comp). Also: What standard discounts do we apply for a company with 0 outside investment and $4.7M in revenue in 2025? Customer asked about DLOM, minority discount, and a customer concentration discount."

[Apr 27, 2026] Dana Zhang:
"Can we restrict access to specific sections of a 409A within Carta? A PE firm's practice is to only share the DLOM valuation — the full report (comparables, overall valuation methodology, etc.) is strictly need-to-know basis."

[May 26, 2026] Daniel Gladstone:
"I'd give them this link and point them to the '409A valuation vs fundraising valuation' section. Basically a 409A would generally provide a lower value which would mean more potential upside for employees, better incentivizing them."

=== CHANNEL: #valuation-support ===

[Nov 20, 2025] Daniel Gladstone:
"Potentially yes [multiple 409As needed]. A 409A immediately before they close (assuming they haven't signed the term sheet yet). A 409A after the term sheet is signed/money starts to come in (material event). A 409A next year if 12 months have elapsed since their prior one or they bring on another investor (assuming that it's material). Will more than likely depend on when they get the first 409A and when the round closes."

[May 29, 2026] Tessa Horne:
"Hey [Rick] — there were some major changes made to the 409A ledger for international company types. I'm going to cross post this to #international-team-public and tag in some people to help us trouble shoot this."

[Jun 2, 2026] Evan Rydinski:
"For 409A, we send almost all of our customers a delivery timeline once we have processed their request. The timeline varies depending on segment. The only customers that do not get a delivery timeline estimate are companies on the LLC platform and customers requesting a non-409A valuation (Gift Tax, Warrant Val, etc)."

=== CHANNEL: #erp-delivery-alerts ===

[Jun 10, 2026] Evan Rydinski (via #erp-delivery-alerts + Group DM with Brendan Rigby, Daniel Gladstone, Jon Grupp, Rizwan Ahmed):
"Hey team, we have a bit of a backlog on the delivery side for what the Advisors handle. As they get used to working in the delivery function to their jobs, I'd like to set them up for success by having a backlog that isn't all projects due in short order. My ask of you all is if you all could each pick up one project from the Advisor Assignment Queue today and move it forward — top four lines of Unassigned 409A section. The link above to our new consolidated delivery and metrics hub — Corporation Station. Similar to other queues we've had in the past, the ask is that you indicate a project is taken using the dropdown in the row on the right side. Thank you all for helping get our team on track as we transition to the new model!"

=== GROUP DM: Evan Rydinski, Ian Kawamoto, Jon Grupp, Rizwan Ahmed ===

[Apr 21, 2026] Evan Rydinski:
"Yeah, to clarify, I'm looking for a commitment on what you both can do without analyst help. The issue is not having enough coverage on the high end of 409A delivery, so that is the gap I'm looking to fill."

=== DM: Firmaye Tarekegn / Jon Grupp ===

[May 26, 2026] Firmaye Tarekegn:
"Hey Jon, quick sanity check before I send this to auditors. We have a warrant/409A alignment issue, we modeled a senior cash breakpoint in the warrant valuation but treated the warrants as penny warrants in the 409A. Auditors are asking why the two don't align. Warrant Treatment in the 409A Valuation: The Series B Preferred Warrants carry a $0.01 exercise price and grant the holder two settlement options upon exercise: (1) receipt of Series B Preferred Stock, or (2) a cash payment per the Supplement Provision. We treat the warrants as economically equivalent to Series B Preferred shares and allocate them through the OPM at the same liquidation breakpoint and payoff structure as the underlying Series B Preferred Stock."

[May 28, 2026] Jon Grupp:
"As participating shares I am guessing including them in the breakpoints for the 409A reduces the value to common and that is why audit is asking. Since the warrants have the option to take either the cash position or the Series B shares we should follow the best economic outcome for the warrants as that is what an investor and market participant would do."

=== CHANNEL: #derp-corp-escalation ===

[May 29, 2026] Tessa Horne:
"We have a client for whom we missed an adjustment to the CN interest accrual in the delivery of their 409A which was caught in audit. They appear to be more concerned about the process miss and impact on 'other ways they use their 409A beyond issuing options.' Can we have a TM jump on this? It seems like offering to hop on a call early next week may be a decent next step here. [tagging Rizwan Ahmed, Brendan Rigby, Daniel Gladstone] — Rizwan Ahmed, I believe you helped Firmaye with the revisions for this one."

=== CHANNEL: #valuations-csat ===

[Jun 9, 2026] Evan Rydinski:
"This was largely a problem on delivery side where we missed performance units and the way those had been treated in previous 409As from another provider. Jen and Jon Grupp quickly jumped on the case and were given unrealistic revision expectations (EOD same day) by the customer to perform a Monte Carlo. Complex breakpoints and Monte Carlo sensitivity were done expeditiously to resolve the customer's audit questions as soon as possible. No further follow up needed here as I believe the combination of initial mis-delivery and failure to meet unrealistic turnaround time for revision are sticking points. We can learn from the delivery mistake, but did everything on the back end to make this right."

=== CHANNEL: #ramp-services-questions ===

[Apr 16, 2026] Rizwan Ahmed:
"If we read the call summary notes by Firmaye, my main concern is that the company should actually be in a black period right now and not considering issuing options because the situation is in flux (risk of options granted at inflated value during black out period). They are waiting for a number of items to be sorted out given the regulatory issues that came up immediately after signing of LOI. I am not sure and maybe worth checking whether the company has discussed this aspect with their counsel and why they are considering issuing options now under this situation rather than waiting for things to sort out. Even client is saying that the value is diminishing by the day. I can leave some notes in the val station on this for any analyst who takes it up in case we decide to proceed now with 409A rather than waiting for issues to resolve. Scenario analysis could be considered with heavy documentation of risks and caveats related to assumptions."

=== GROUP DM: Jon Grupp, Brendan Rigby, Nate Norton ===

[May 8, 2026] Jon Grupp:
"They did however say they are seeing a lot of divergence over the last couple years of higher prices for 718 and a different number for 409A."
"""

ANALYSIS_PROMPT = """You are analyzing Slack message data from Carta's 409A valuation team (Jan 2025 - Jun 2026).
Your task is to identify major decisions and generate a structured knowledge base.

Identify 10-18 distinct, significant decisions. A "decision" means a concrete choice was made, a policy was established, a standard response was codified, or a significant change was implemented. Exclude routine Q&A with no clear resolution.

Categories (only these three):
- methodology: how valuations are performed technically
- operational: internal workflows, team structure, tooling, delivery processes
- client-handling: how to respond to client/auditor situations, what Carta will/won't do

For each decision, provide:
- slug: kebab-case identifier (e.g. "ava-ai-qa-rollout")
- title: concise title
- date: YYYY-MM (best estimate)
- category: one of the three above
- summary: 1-2 sentence summary of what was decided
- context: 2-4 sentences of background / why this came up
- outcome: what was specifically decided or established
- participants: list of {name, role} for key people involved
- key_quotes: list of 1-3 direct quotes from the data that best capture the decision

Also provide a people list: for each unique person who appears in decisions, provide:
- name: full name
- slug: firstname-lastname kebab-case
- role: their apparent function (e.g. "Director of Valuation Delivery", "Senior Analyst", "Methodology Lead")
- decisions: list of decision slugs they were involved in
- involvement_pattern: 1 sentence describing how they typically contribute

Return ONLY valid JSON with this structure:
{
  "decisions": [...],
  "people": [...]
}"""

# ── Helpers ────────────────────────────────────────────────────────────────────

def load_user_map():
    """Build {uid_int: display_name} from results/users.csv."""
    user_map = {}
    if USERS_CSV.exists():
        with open(USERS_CSV, encoding="utf-8") as f:
            for row in csv.DictReader(f):
                uid = row.get("id", "")
                name = row.get("name", "")
                if uid.startswith("U") and uid[1:].isdigit():
                    user_map[int(uid[1:])] = name
    return user_map


def read_csv_messages(user_map):
    """Read 409A-relevant messages from local CSVs, resolving user IDs to names."""
    messages = []
    for csv_path in sorted(CSV_DIR.glob("*.csv")):
        channel = csv_path.stem
        rows = []
        try:
            with open(csv_path, encoding="utf-8") as f:
                for row in csv.DictReader(f):
                    text = row.get("m", "")
                    if "409" in text:
                        rows.append(row)
        except Exception:
            continue

        for row in rows:
            uid_raw = row.get("u", "")
            try:
                uid_int = int(uid_raw)
                name = user_map.get(uid_int, f"U{uid_int}")
            except ValueError:
                name = uid_raw

            ts = row.get("t", "")
            text = row.get("m", "").strip()
            if text:
                messages.append(f"[{ts}] #{channel} — {name}: {text[:500]}")

    return messages


def slugify(name):
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def write_index(decisions, output_dir):
    rows = []
    for d in sorted(decisions, key=lambda x: x["date"]):
        people_links = ", ".join(
            f"[{p['name']}](people/{p['slug']}.md)"
            for p in d.get("participants", [])
        )
        rows.append(
            f"| {d['date']} | [{d['title']}](decisions/{d['slug']}.md) "
            f"| {d['category']} | {people_links} |"
        )

    table = "\n".join(rows)
    content = f"""# 409A Decisions Knowledge Base

This knowledge base documents major 409A valuation decisions made at Carta between January 2025 and June 2026. It covers methodology choices, operational changes, and client-handling policies.

Sources: Slack channels (#advisory-services-questions, #val-sales, #valuation-support, #erp-delivery-alerts, #valuators, #ramp-services-questions) and direct messages involving the valuation leadership team.

## Decision Timeline

| Date | Decision | Category | Key People |
|------|----------|----------|------------|
{table}

## Browse by Person

See the [people/](people/) directory for profiles of each contributor.
"""
    (output_dir / "index.md").write_text(content, encoding="utf-8")


def write_decision(d, output_dir):
    people_section = "\n".join(
        f"- **[{p['name']}](../people/{slugify(p['name'])}.md)** — {p.get('role', '')}"
        for p in d.get("participants", [])
    )
    quotes = "\n\n".join(
        f"> {q}" for q in d.get("key_quotes", [])
    )
    content = f"""# {d['title']}

**Date:** {d['date']}
**Category:** {d['category']}

## Summary

{d['summary']}

## Context

{d['context']}

## What Was Decided

{d['outcome']}

## People Involved

{people_section}

## Key Quotes

{quotes}
"""
    path = output_dir / "decisions" / f"{d['slug']}.md"
    path.write_text(content, encoding="utf-8")


def write_person(p, all_decisions, output_dir):
    decision_links = []
    for slug in p.get("decisions", []):
        match = next((d for d in all_decisions if d["slug"] == slug), None)
        if match:
            decision_links.append(
                f"- [{match['title']}](../decisions/{slug}.md) ({match['date']}, {match['category']})"
            )
    decisions_section = "\n".join(decision_links) if decision_links else "_None recorded._"

    content = f"""# {p['name']}

**Role:** {p.get('role', 'Unknown')}

## Involvement Pattern

{p.get('involvement_pattern', '')}

## Decisions Involved In

{decisions_section}
"""
    path = output_dir / "people" / f"{p['slug']}.md"
    path.write_text(content, encoding="utf-8")


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    print("Loading user map...")
    user_map = load_user_map()
    print(f"  {len(user_map)} users loaded")

    print("Reading local CSV messages...")
    csv_messages = read_csv_messages(user_map)
    print(f"  {len(csv_messages)} 409A-relevant messages from CSVs")

    # Combine CSV sample (cap at 300 messages to stay within context) with MCP data
    csv_sample = csv_messages[:300]
    corpus = SLACK_MCP_DATA + "\n\n=== LOCAL CSV MESSAGES (sampled) ===\n" + "\n".join(csv_sample)

    print("Calling Claude API to analyze decisions...")
    client = anthropic.Anthropic()
    response = client.messages.create(
        model="claude-opus-4-8",
        max_tokens=8000,
        thinking={"type": "adaptive"},
        messages=[
            {
                "role": "user",
                "content": f"{ANALYSIS_PROMPT}\n\n--- MESSAGE DATA ---\n{corpus}"
            }
        ]
    )

    # Extract JSON from response
    raw = ""
    for block in response.content:
        if block.type == "text":
            raw = block.text
            break

    # Strip markdown code fences if present
    raw = re.sub(r"^```(?:json)?\s*", "", raw.strip())
    raw = re.sub(r"\s*```$", "", raw.strip())

    data = json.loads(raw)
    decisions = data["decisions"]
    people = data["people"]

    print(f"  {len(decisions)} decisions identified")
    print(f"  {len(people)} people identified")

    # Ensure slugs are set
    for d in decisions:
        if "slug" not in d or not d["slug"]:
            d["slug"] = slugify(d["title"])
    for p in people:
        if "slug" not in p or not p["slug"]:
            p["slug"] = slugify(p["name"])

    # Create output directories
    OUTPUT_DIR.mkdir(exist_ok=True)
    (OUTPUT_DIR / "decisions").mkdir(exist_ok=True)
    (OUTPUT_DIR / "people").mkdir(exist_ok=True)

    print("Writing markdown files...")
    write_index(decisions, OUTPUT_DIR)
    for d in decisions:
        write_decision(d, OUTPUT_DIR)
        print(f"  decisions/{d['slug']}.md")
    for p in people:
        write_person(p, decisions, OUTPUT_DIR)
        print(f"  people/{p['slug']}.md")

    print(f"\nDone. Knowledge base written to {OUTPUT_DIR}/")
    print(f"  {len(decisions)} decision files")
    print(f"  {len(people)} people files")
    print(f"  1 index.md")


if __name__ == "__main__":
    main()
