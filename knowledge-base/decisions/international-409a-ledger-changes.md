# International 409A Ledger Changes

**Date:** 2026-05
**Category:** methodology

## Summary

Major changes were made to the 409A ledger for international company types, causing platform errors for CSMs and customers. The issue was escalated and cross-posted to the international team for troubleshooting.

## Context

In May 2026, a CSM (Rick) flagged that something was wrong with the 409A for a client — Tessa Horne identified that major changes had been made to the 409A ledger for international company types. The root cause was a platform-side change that had downstream effects on how international companies could submit and process 409A requests. At least one company had a 409A resegmented from NON_US_409A to PRE_SEED_BENCHMARK (seen in #erp-delivery-alerts), indicating the segmentation logic was also affected.

## What Was Decided

- Issue escalated to #international-team-public and relevant international team members tagged
- The changes were acknowledged as intentional (ledger update) but the downstream CSM/client impact required troubleshooting
- Delivery team (Evan Rydinski) separately noted that some companies were being resegmented, affecting which delivery queue they appeared in

## People Involved

- **[Tessa Horne](../people/tessa-horne.md)** — Operations & CSM Liaison; identified the issue and escalated to the international team

## Key Quotes

> "Hey [Rick] — there were some major changes made to the 409A ledger for international company types. I'm going to cross post this to #international-team-public and tag in some people to help us trouble shoot this." — Tessa Horne, May 2026
