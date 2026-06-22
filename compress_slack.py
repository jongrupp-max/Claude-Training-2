#!/usr/bin/env python3
"""
Compress Slack channel exports to human-content-only JSON.
Strips bots, system messages, blocks, attachments, image URLs, and Slack markup.
"""

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

OUTPUT_DIR = Path("compressed")

SKIP_SUBTYPES = {
    "bot_message", "channel_join", "channel_leave", "channel_purpose",
    "channel_topic", "channel_name", "channel_archive", "channel_unarchive",
    "pinned_item", "unpinned_item", "message_deleted", "message_changed",
    "ekm_access_denied", "file_share", "slackbot_response",
}


def clean_text(text: str) -> str:
    """Convert Slack mrkdwn markup to plain readable text."""
    # <http://url|label> or <http://url> -> label or url
    text = re.sub(r"<(https?://[^|>]+)\|([^>]+)>", r"\2", text)
    text = re.sub(r"<(https?://[^>]+)>", r"[link]", text)
    # <@USERID> -> @user
    text = re.sub(r"<@[A-Z0-9]+>", "@user", text)
    # <!channel>, <!here>, <!everyone>
    text = re.sub(r"<!(\w+)>", r"@\1", text)
    # <#CHANNELID|name> -> #name
    text = re.sub(r"<#[A-Z0-9]+\|([^>]+)>", r"#\1", text)
    return text.strip()


def ts_to_dt(ts: str) -> str:
    return datetime.fromtimestamp(float(ts), tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def extract_message(msg: dict) -> dict | None:
    # Skip system/bot subtypes
    subtype = msg.get("subtype", "")
    if subtype in SKIP_SUBTYPES:
        return None

    # Skip bot messages
    if msg.get("bot_id") or msg.get("username") == "Slackbot":
        return None

    # Must have a real user
    user_profile = msg.get("user_profile", {})
    user_name = (
        user_profile.get("display_name")
        or user_profile.get("real_name")
        or msg.get("user", "unknown")
    )

    text = clean_text(msg.get("text", ""))
    if not text:
        return None

    ts = msg.get("ts", "")
    thread_ts = msg.get("thread_ts")

    out = {
        "ts": ts_to_dt(ts),
        "user": user_name,
        "text": text,
    }
    if thread_ts and thread_ts != ts:
        out["is_reply"] = True

    # Include reactions if present (human signal)
    reactions = msg.get("reactions")
    if reactions:
        out["reactions"] = [
            {"emoji": r["name"], "count": r["count"]}
            for r in reactions
        ]

    return out


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

    # Sort chronologically
    messages.sort(key=lambda m: m["ts"])
    return messages


def main():
    OUTPUT_DIR.mkdir(exist_ok=True)
    for zip_path, channel in ZIPS:
        print(f"Processing #{channel}...")
        messages = process_zip(zip_path, channel)
        out_path = OUTPUT_DIR / f"{channel}.json"
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(messages, f, indent=2, ensure_ascii=False)

        zip_size = Path(zip_path).stat().st_size
        out_size = out_path.stat().st_size
        print(f"  {len(messages)} messages | {zip_size//1024}KB -> {out_size//1024}KB ({100*out_size//zip_size}% of original)")

    print("\nDone. Results in ./compressed/")


if __name__ == "__main__":
    main()
