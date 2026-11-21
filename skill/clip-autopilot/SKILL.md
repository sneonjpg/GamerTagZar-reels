---
name: clip-autopilot
description: Run a hands-off short-form clipping page. Records live streams, cuts vertical captioned clips, screens them, gets the owner's approval in chat, posts to Instagram/YouTube/X, and makes sure paid-campaign clips are submitted on time. Use when someone wants to run a clipping page, earn from clipping campaigns, automate Shorts/Reels from streams, or set up "approve and post" from their phone.
---

# Clip Autopilot

A page that makes its own clips. The owner only does two things: tap **Approve** on a clip in chat, and paste a link into the campaign page when nudged. Everything else runs on free infrastructure.

Proven on GamerTagZar (GTA 6, launched Nov 2026): first campaign clip reached 2,532 Instagram views on day one.

## The loop

```
Twitch live streams ──▶ GitHub Actions (hourly, free) ──▶ clips + captions + rule check in the repo
                                                              │
                                    Claude screens, writes hooks, sends to chat
                                                              │
                                              Owner taps Approve (phone)
                                                              │
                         Make.com scenario posts to Instagram Reels + YouTube Shorts (+ X via Buffer)
                                                              │
                     Campaign clip? ─▶ Claude fetches the live link ─▶ push nudge ─▶ owner submits (<30 min)
```

## Components (all free tiers)

| Piece | Tool | Notes |
|---|---|---|
| Recording + cutting | GitHub Actions, public repo | `auto-clips.yml` hourly; matrix records streams in parallel |
| Clip engine | `clip-desk/scripts` (Python + ffmpeg + faster-whisper) | `auto.py` = record → moments → cut → check |
| Moment scoring | chat spikes, loudness, hype words | `live.py`, `moments.py` |
| Posting | Make.com scenario with inputs | IG `CreateAReelPost`, YouTube `uploadVideo`, Buffer for X |
| Link lookup | Firecrawl Alexandria `scrapecreators instagram/user-reels` | ~2 credits; Make won't return post links |
| Approvals | Claude chat (`SendUserFile` + tap-to-answer questions) | Owner watches the clip itself before approving |
| Timed posts | `send_later` scheduled messages | Only for clips with nothing to submit |

## Setup checklist (about 1 hour)

1. Public GitHub repo with `clip-desk/`, `page/`, `.github/workflows/`. Give the Claude GitHub App access to it.
2. Accounts: Instagram professional (Creator) linked to a Facebook Page; YouTube channel; optional X via Buffer.
3. Make.com: connect YouTube + "Instagram for Business (Facebook login)". Free plan = 2 active scenarios; one publisher scenario covers all platforms.
4. Join campaigns (Content Rewards, ClipFlip). Put campaign streamers in `page/streamers.csv` (name, url, tag, platforms, campaign link).
5. Put growth streamers (same language as the page) in `page/growth_streamers.txt`.
6. Fill `page/playbook.md` (handle, platforms, time zone) and `page/platforms.md`.

## Rules that protect the money (learned the hard way)

- **Submit within 30 minutes** (Content Rewards rejects older posts). So campaign clips post **the moment the owner approves**, never on a timer while they're away, and the link + submit button are pushed to their phone within ~2 minutes.
- **On-screen ad disclosure** at the start of every paid clip (small "#ad" for 2.5 s). Caption #ad alone can be rejected. Growth clips get none.
- **No story cutscenes or spoilers** in launch weeks (publisher takedowns). Screen every clip; reject cutscenes before the owner sees them.
- **Clips 30–45 s** for watch time. Chat-spike clips: 18 s before, 22 s after.
- **Instagram video bitrate under 5 Mbps** (encode with `-maxrate 4500k`), H.264, AAC 48 kHz, faststart.
- **New YouTube channels hit a daily upload cap.** Retry the YouTube copy 24 h later; Instagram is usually where early views come from.
- **Datacenter IPs can't download YouTube.** Use Twitch (or the campaign's own footage pack). Never work around a site's bot protection.
- **Same-language streamers only** for growth clips; top-viewer lists are full of other languages.
- Weight effort to what pays: campaign streamers 40 min / 8 clips per run; growth streamers 20 min / 4 clips.

## Hooks that worked

Secret or insider framing, always true to what's on screen:
- "Wait... GTA 6 cars are keyless?" (2,532 views)
- "Did you know you can rob a $150,000 bank in GTA 6?"
- "I just found out you make $2,000 driving a van in GTA 6"
- "Nobody told me GTA 6 has basketball"

Avoid: bare labels ("funny moment"), "wait for it", made-up quotes.

## Two clip styles

- **clean** (paid campaigns): hook box, word captions, small #ad. Nothing that could break a brief.
- **growth** (exploratory): adds emoji stickers that pop on key words (Twemoji, CC-BY) and an end-card question that invites comments ("Would you try this? Comment below"). Test new effects here first.

## Daily rhythm

- Hourly: workflow records and cuts.
- When the owner is free: Claude brings the best 2–6 clips; owner approves; campaign clips post and get submitted on the spot; growth clips post about an hour apart.
- Evening: log views (Instagram reels endpoint returns play counts), note the best hook as a rule in `page/learning.md`.

## Selling this

Package = the repo template + this skill + a 1-hour setup call. Buyers supply their own accounts and niche (any streamed game or creator with clipping campaigns). Be honest in the pitch: income depends on approved views and campaign budgets; nothing is guaranteed.
