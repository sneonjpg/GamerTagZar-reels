"""Growth-clip extras: emoji stickers that pop in on key words, and an end-card question that invites comments.

Used by cut.py with --style growth. Campaign clips stay clean (--style clean, the default).
Emoji artwork: Twemoji (CC-BY 4.0, by Twitter), fetched once and cached in ~/.cache/clipdesk-emoji.
If the artwork can't be fetched, stickers are skipped and the clip is still cut.
"""
import os, re, urllib.request
from pathlib import Path

CACHE = Path(os.environ.get("CLIPDESK_EMOJI_CACHE", Path.home() / ".cache" / "clipdesk-emoji"))
TWEMOJI = "https://cdn.jsdelivr.net/gh/twitter/twemoji@14.0.2/assets/72x72/{}.png"

# word pattern -> Twemoji code point (GTA-flavoured)
EMOJI = [
    (r"money|cash|\$|dollars?|paid|rich", "1f4b0"),
    (r"bank|rob(bing|bery)?|heist|vault", "1f3e6"),
    (r"cops?|police|wanted|sirens?", "1f693"),
    (r"cars?|drive|driving|ride|race|racing", "1f3ce"),
    (r"crash(ed)?|boom|explo\w*|blew", "1f4a5"),
    (r"dead|died|die|kill(ed)?|murder\w*", "1f480"),
    (r"fire|lit|insane|crazy|wild", "1f525"),
    (r"lol|lmao|haha\w*|funny|laugh\w*", "1f602"),
    (r"what|wait|no way|bro|yo", "1f633"),
    (r"jet|plane|fly|flying|parachute", "2708"),
    (r"boat|ocean|sea|water|swim\w*", "1f30a"),
    (r"house|apartment|home|mansion|balcony", "1f3e0"),
    (r"win|won|gg|w", "1f3c6"),
    (r"gun|shoot\w*|shot", "1f3af"),
]

CTA = [
    "Would you try this? Comment below",
    "Did you know this? Yes or no below",
    "Rate this 1-10 in the comments",
    "Tag someone who needs GTA 6",
]


def _png(code):
    CACHE.mkdir(parents=True, exist_ok=True)
    f = CACHE / f"{code}.png"
    if f.exists() and f.stat().st_size > 100:
        return f
    try:
        with urllib.request.urlopen(TWEMOJI.format(code), timeout=10) as r:
            f.write_bytes(r.read())
        return f
    except Exception as e:
        print(f"emoji {code} unavailable ({str(e)[:60]}), skipping")
        return None


def stickers(words, s0, e0, gap=3.0, limit=6):
    """[(png_path, start, end)] relative to the clip start, at most one per `gap` seconds."""
    out, last = [], -99.0
    for w in words:
        if not (s0 <= w["s"] < e0):
            continue
        t = w["s"] - s0
        if t < 2.8 or t - last < gap or t > (e0 - s0) - 3.2:  # keep clear of the hook and the end card
            continue
        token = re.sub(r"[^\w$]", "", w["w"].lower())
        for pat, code in EMOJI:
            if re.fullmatch(pat, token):
                p = _png(code)
                if p:
                    out.append((p, t, min(t + 1.0, e0 - s0)))
                    last = t
                break
        if len(out) >= limit:
            break
    return out


def cta_event(duration, seed=0, y=1250):
    """ASS dialogue line for the last 2.5 s: a question that invites comments."""
    a = max(0.0, duration - 2.5)
    txt = CTA[seed % len(CTA)]
    fmt = lambda t: f"{int(t // 3600)}:{int(t % 3600 // 60):02d}:{t % 60:05.2f}"
    return f"Dialogue: 2,{fmt(a)},{fmt(duration)},Hook,,0,0,0,,{{\\pos(540,{y})\\fad(150,0)}}{txt}\n"


def overlay_graph(vgraph, items, first_input=1, y=1180, size=170):
    """Append sticker overlays to a filter graph that ends in [vo]. Each item is one extra -loop input."""
    if not items:
        return vgraph
    g = vgraph[:-len("[vo]")] + "[s0]"
    cur = "s0"
    for i, (_, a, b) in enumerate(items):
        k = first_input + i
        # pop: grows from 60% to 100% over 0.15 s
        g += (f";[{k}:v]format=rgba,scale={size}:{size}[e{i}]"
              f";[{cur}][e{i}]overlay=x=(W-w)/2:y={y}:enable='between(t,{a:.2f},{b:.2f})'[s{i + 1}]")
        cur = f"s{i + 1}"
    return g + f";[{cur}]null[vo]"
