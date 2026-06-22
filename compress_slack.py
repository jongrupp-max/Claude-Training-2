#!/usr/bin/env python3
"""
Compress Slack channel exports to human-content-only CSV.
Strips bots, system messages, blocks, attachments, image URLs, and Slack markup.
Outputs per-channel CSVs with short user IDs plus a shared users legend.
"""

import csv
import json
import re
import zipfile
from datetime import datetime, timezone
from pathlib import Path

ZIPS = [
    ("general-20260622T160644Z-3-001.zip", "general"),
    ("parents-20260622T160646Z-3-001.zip", "parents"),
    ("random-20260622T160649Z-3-001.zip",  "random"),
]

OUTPUT_DIR = Path("results")

SKIP_SUBTYPES = {
    "bot_message", "channel_join", "channel_leave", "channel_purpose",
    "channel_topic", "channel_name", "channel_archive", "channel_unarchive",
    "pinned_item", "unpinned_item", "message_deleted", "message_changed",
    "ekm_access_denied", "file_share", "slackbot_response",
}


def clean_text(text: str) -> str:
    """Convert Slack mrkdwn markup to plain readable text."""
    text = re.sub(r"<(https?://[^|>]+)\|([^>]+)>", r"\2", text)
    text = re.sub(r"<(https?://[^>]+)>", r"[link]", text)
    text = re.sub(r"<@[A-Z0-9]+>", "@user", text)
    text = re.sub(r"<!(\w+)>", r"@\1", text)
    text = re.sub(r"<#[A-Z0-9]+\|([^>]+)>", r"#\1", text)
    return text.strip()


def ts_to_dt(ts: str) -> str:
    return datetime.fromtimestamp(float(ts), tz=timezone.utc).strftime("%m-%d %H:%M")


def extract_message(msg: dict) -> dict | None:
    subtype = msg.get("subtype", "")
    if subtype in SKIP_SUBTYPES:
        return None

    if msg.get("bot_id") or msg.get("username") == "Slackbot":
        return None

    user_profile = msg.get("user_profile", {})
    user_name = (
        user_profile.get("display_name")
        or user_profile.get("real_name")
        or msg.get("user", "unknown")
    )

    text = clean_text(msg.get("text", ""))
    if not text:
        return None

    return {
        "ts": ts_to_dt(msg.get("ts", "")),
        "user": user_name,
        "text": text,
    }


def process_zip(zip_path: str, channel: str) -> list:
    messages = []
    with zipfile.ZipFile(zip_path) as zf:
        json_files = sorted(n for n in zf.namelist() if n.endswith(".json"))
        for name in json_files:
            with zf.open(name) as f:
                try:
                    data = json.load(f)
                except json.JSONDecodeError:
                    print(f"  Skipping malformed: {name}")
                    continue
                for msg in data:
                    extracted = extract_message(msg)
                    if extracted:
                        messages.append(extracted)

    messages.sort(key=lambda m: m["ts"])
    return messages


def build_user_legend(all_messages: list[list]) -> dict:
    """Assign a short ID (U01, U02, ...) to each unique username across all channels."""
    seen = {}
    for messages in all_messages:
        for msg in messages:
            name = msg["user"]
            if name not in seen:
                seen[name] = f"U{len(seen)+1:02d}"
    return seen  # name -> short_id


def main():
    OUTPUT_DIR.mkdir(exist_ok=True)

    # First pass: collect all messages
    all_messages = []
    for zip_path, channel in ZIPS:
        print(f"Processing #{channel}...")
        all_messages.append(process_zip(zip_path, channel))

    # Build cross-channel user legend
    legend = build_user_legend(all_messages)

    # Write legend CSV
    legend_path = OUTPUT_DIR / "users.csv"
    with open(legend_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "name"])
        for name, uid in sorted(legend.items(), key=lambda x: x[1]):
            writer.writerow([uid, name])
    print(f"\nUser legend: {len(legend)} users -> {legend_path}")

    # Write per-channel CSVs with short user IDs
    for (zip_path, channel), messages in zip(ZIPS, all_messages):
        out_path = OUTPUT_DIR / f"{channel}.csv"
        with open(out_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["ts", "uid", "text"])
            for msg in messages:
                writer.writerow([msg["ts"], legend[msg["user"]], msg["text"]])

        zip_size = Path(zip_path).stat().st_size
        out_size = out_path.stat().st_size
        print(f"  #{channel}: {len(messages)} messages | {zip_size//1024}KB -> {out_size//1024}KB ({100*out_size//zip_size}% of original)")

    print("\nDone. Results in ./compressed/")


if __name__ == "__main__":
    main()
