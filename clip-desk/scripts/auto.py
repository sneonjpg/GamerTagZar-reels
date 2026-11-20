"""One-shot clip run for GamerTagZar: get footage, find the best moments, cut vertical clips, collect them.

live mode: records a live stream for --minutes with live.py; chat spikes become the moments.
           If chat gave no spikes, the whole recording is scored instead.
vod mode:  downloads a finished video (first --minutes only) and scores it with moments.py.

Every clip is cut with cut.py, checked with check.py and copied to --out with a clips.md summary
(time, transcript, rule check). No hook is burned in unless --hook is given: hooks are written after
a human or Claude has read what happens in each clip.

usage: python auto.py <url-or-file> --mode live|vod --minutes 20 --top 3 --layout blur --out page/media/edits/run
"""
import argparse, shutil, subprocess, sys
from pathlib import Path
HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
from common import job_dir, load_json, run, tool


def py(script, *args, check=True):
    print(f"\n$ {script} {' '.join(map(str, args))}", flush=True)
    r = subprocess.run([sys.executable, str(HERE / script), *map(str, args)])
    if check and r.returncode != 0:
        sys.exit(f"{script} failed ({r.returncode})")
    return r.returncode


def concat_segments(ld):
    segs = sorted(ld.glob("seg_*.ts"))
    if not segs:
        return None
    lst = ld / "all.txt"
    lst.write_text("".join(f"file '{s.resolve().as_posix()}'\n" for s in segs), encoding="utf-8")
    out = ld / "recording.mp4"
    run([tool("ffmpeg"), "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy",
         "-movflags", "+faststart", str(out)])
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src"); ap.add_argument("--mode", choices=["live", "vod"], default="vod")
    ap.add_argument("--minutes", type=float, default=20); ap.add_argument("--top", type=int, default=3)
    ap.add_argument("--layout", choices=["fill", "blur"], default="blur")
    ap.add_argument("--hook", default=""); ap.add_argument("--out", required=True)
    ap.add_argument("--no-transcribe", action="store_true")
    ap.add_argument("--name", default="", help="streamer name for captions, e.g. KreekCraft")
    ap.add_argument("--tag", default="", help="campaign hashtag, e.g. #KreekCraft")
    ap.add_argument("--campaign", default="", help="campaign link; empty = growth clip for GamerTagZar (no #ad)")
    a = ap.parse_args()
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    nt = ["--no-transcribe"] if a.no_transcribe else []

    # 1. footage -> list of (job_dir, pick numbers)
    jobs = []
    if a.mode == "live":
        py("live.py", a.src, "--minutes", a.minutes, check=False)
        ld = job_dir(a.src) / "live"
        spikes = sorted(ld.glob("spike_*.mp4"), key=lambda p: int(p.stem.split("_")[1]))[: a.top]
        for s in spikes:  # chat spikes first: the moments chat reacted to
            if py("moments.py", s, "--top", 1, "--min", 30, "--max", 40, *nt, check=False) == 0:
                jobs.append((job_dir(str(s)), [1]))
        need = a.top - len(jobs)
        if need > 0:  # fill the rest from the whole recording (loudness + hype words)
            rec = concat_segments(ld)
            if not rec and not jobs:
                sys.exit("nothing was recorded: the stream may be offline or the site refused the download")
            if rec:
                print(f"{len(jobs)} chat spike clip(s), scoring the whole recording for {need} more", flush=True)
                if py("moments.py", rec, "--top", need, "--min", 30, "--max", 45, *nt, check=False) == 0:
                    jobs.append((job_dir(str(rec)), list(range(1, need + 1))))
    else:
        py("moments.py", a.src, "--top", a.top, "--min", 30, "--max", 45, "--max-minutes", int(a.minutes), *nt)
        jobs.append((job_dir(a.src), list(range(1, a.top + 1))))

    # 2. cut, check, collect
    lines = [f"# Clips: {a.src}", "", f"mode {a.mode}, {a.minutes:g} min, layout {a.layout}", ""]
    k = 0
    for d, picks in jobs:
        cands = {c["n"]: c for c in load_json(d / "candidates.json")["candidates"]}
        for p in picks:
            if p not in cands:
                continue
            args = [d, "--pick", p, "--layout", a.layout]
            if a.hook:
                args += ["--hook", a.hook]
            if py("cut.py", *args, check=False) != 0:
                continue
            clip = d / "edits" / f"clip_{p}.mp4"
            k += 1
            dest = out / f"clip_{k}.mp4"
            shutil.copy(clip, dest)
            chk = subprocess.run([sys.executable, str(HERE / "check.py"), str(dest)], capture_output=True, text=True)
            c = cands[p]
            lines += [f"## clip_{k}.mp4", f"- source time: {c['start']:.0f}s to {c['end']:.0f}s ({c['end'] - c['start']:.0f}s)",
                      f"- why: {', '.join(c['why'])}", f"- said: {c['text'] or '(no transcript)'}",
                      f"- rule check: {'PASS' if 'RESULT: PASS' in chk.stdout else 'FAIL'}", ""]
            if a.name:
                who, tag = a.name, a.tag or "#" + a.name.replace(" ", "")
                ad = "#ad " if a.campaign else ""
                lines += [f"- campaign: {a.campaign or 'none (growth clip for GamerTagZar, no #ad)'}", "",
                          "Captions (replace WHAT HAPPENS with what happens in the clip):", "",
                          f"- YouTube Shorts title: `{ad}{who} WHAT HAPPENS in GTA 6 {tag} #Shorts`",
                          f"- YouTube description: `Clip from {who}'s GTA 6 stream. Credit: {who} {tag} #GTA6`",
                          f"- X: `{ad}{who} WHAT HAPPENS in GTA 6 \U0001F3A5 {who} {tag}`",
                          f"- TikTok: `{ad}{who} WHAT HAPPENS in GTA 6 {tag} #GTA6 #gaming`",
                          f"- Instagram: `{ad}{who} WHAT HAPPENS in GTA 6 \U0001F3A5 {who} {tag} #GTA6 #GTAVI #gaming`", ""]
            lines += ["```", chk.stdout.strip(), "```", ""]
            shutil.copy(d / "candidates.md", out / f"candidates_{d.name}.md")
    (out / "clips.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"\n{k} clip(s) -> {out}")
    if k == 0:
        sys.exit("no clips were cut")


if __name__ == "__main__":
    main()
