#!/usr/bin/env python3
"""
make_frames.py — build the scroll-film renditions for index.html from the
ORIGINAL video clip(s).

    python3 tools/make_frames.py clips/           # a folder with one MP4 per scene (sorted by name)
    python3 tools/make_frames.py film.mp4         # one MP4, split into SCENES equal parts
    python3 tools/make_frames.py film.mp4 --cuts 7.9,15.8,23.1,31.0,38.6,46.2   # one MP4, your own cut times (s)

Options
    --per-scene 60     frames per scene (default 60; 20 = the old build)
    --scenes 7         number of scenes/movements on the page (must match SCENES in index.html)
    --quality 82       WebP quality (80–85 is visually lossless for this kind of 3D footage)
    --mobile-x 0.5     where the phone crop sits horizontally (0 = left edge, 1 = right edge),
                       one value, or one per scene: --mobile-x 0.5,0.55,0.5,0.45,0.5,0.5,0.5
    --out frames       output folder (writes <out>/d and <out>/m)

Output
    frames/d/frame_0001.webp …   1280x720  landscape  — desktop / laptop / tablet
    frames/m/frame_0001.webp …    720x1080 portrait   — phones (full source height, centre slice)

Then in index.html set
    RENDITIONS = { d:{ dir:"frames/d", perScene:60 }, m:{ dir:"frames/m", perScene:60 } }
    USE_MOBILE_SET = true        (and USE_M=true in the <head> preload one-liner)
"""
import argparse, json, os, shutil, subprocess, sys, tempfile

def run(cmd):
    r = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if r.returncode:
        sys.exit("ffmpeg failed:\n" + " ".join(cmd) + "\n" + r.stderr[-2000:])
    return r.stdout

def duration(path):
    out = run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", path])
    return float(json.loads(out)["format"]["duration"])

def extract(src, start, length, n, out_dir, first_no, quality, mobile_x, tmp):
    """n evenly spaced frames from [start, start+length) of src -> d + m renditions."""
    # 1. pull the n frames once, full resolution, lossless PNG
    shutil.rmtree(tmp, ignore_errors=True); os.makedirs(tmp)
    fps = n / length
    run(["ffmpeg", "-loglevel", "error", "-y", "-ss", f"{start:.4f}", "-t", f"{length:.4f}", "-i", src,
         "-vf", f"fps={fps:.6f}:round=down", "-frames:v", str(n), "-vsync", "vfr",
         os.path.join(tmp, "src_%04d.png")])
    got = sorted(f for f in os.listdir(tmp) if f.startswith("src_"))
    if len(got) < n:                      # a short clip: repeat the last frame rather than shift the timeline
        for k in range(len(got), n):
            shutil.copy(os.path.join(tmp, got[-1]), os.path.join(tmp, f"src_{k+1:04d}.png"))
    # 2. encode both renditions
    for k in range(n):
        src_png = os.path.join(tmp, f"src_{k+1:04d}.png")
        no = first_no + k
        run(["ffmpeg", "-loglevel", "error", "-y", "-i", src_png,
             "-vf", "scale=1280:720:flags=lanczos", "-c:v", "libwebp", "-quality", str(quality), "-compression_level", "6",
             os.path.join(out_dir, "d", f"frame_{no:04d}.webp")])
        # portrait: full source height, 2:3 window, placed at mobile_x
        run(["ffmpeg", "-loglevel", "error", "-y", "-i", src_png,
             "-vf", f"crop=ih*2/3:ih:(iw-ih*2/3)*{mobile_x}:0,scale=720:1080:flags=lanczos",
             "-c:v", "libwebp", "-quality", str(quality), "-compression_level", "6",
             os.path.join(out_dir, "m", f"frame_{no:04d}.webp")])

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("source")
    ap.add_argument("--per-scene", type=int, default=60)
    ap.add_argument("--scenes", type=int, default=7)
    ap.add_argument("--quality", type=int, default=82)
    ap.add_argument("--mobile-x", default="0.5")
    ap.add_argument("--cuts", default="")
    ap.add_argument("--out", default="frames")
    a = ap.parse_args()

    xs = [float(x) for x in a.mobile_x.split(",")]
    if len(xs) == 1: xs = xs * a.scenes
    if len(xs) != a.scenes: sys.exit("--mobile-x needs 1 value or one per scene")

    # scene list: [(file, start, length)]
    scenes = []
    if os.path.isdir(a.source):
        clips = sorted(f for f in os.listdir(a.source) if f.lower().endswith((".mp4", ".mov", ".webm", ".mkv")))
        if len(clips) != a.scenes: sys.exit(f"found {len(clips)} clips, expected {a.scenes}")
        for c in clips:
            p = os.path.join(a.source, c); scenes.append((p, 0.0, duration(p)))
    else:
        d = duration(a.source)
        cuts = [float(c) for c in a.cuts.split(",")] if a.cuts else [d * i / a.scenes for i in range(1, a.scenes)]
        if len(cuts) != a.scenes - 1: sys.exit(f"--cuts needs {a.scenes-1} values")
        edges = [0.0] + cuts + [d]
        for i in range(a.scenes):
            scenes.append((a.source, edges[i], edges[i+1] - edges[i]))

    for sub in ("d", "m"):
        shutil.rmtree(os.path.join(a.out, sub), ignore_errors=True); os.makedirs(os.path.join(a.out, sub))
    tmp = tempfile.mkdtemp(prefix="wv_frames_")
    no = 1
    for i, (src, start, length) in enumerate(scenes):
        print(f"scene {i+1}/{a.scenes}: {os.path.basename(src)} {start:.2f}s +{length:.2f}s -> frames {no}..{no+a.per_scene-1}")
        extract(src, start, length, a.per_scene, a.out, no, a.quality, xs[i], tmp)
        no += a.per_scene
    shutil.rmtree(tmp, ignore_errors=True)

    def size(sub):
        return sum(os.path.getsize(os.path.join(a.out, sub, f)) for f in os.listdir(os.path.join(a.out, sub))) / 1e6
    total = a.per_scene * a.scenes
    print(f"\ndone: {total} frames per rendition — d {size('d'):.1f} MB, m {size('m'):.1f} MB")
    print(f"now set in index.html:  perScene:{a.per_scene}  (both renditions)  and  USE_MOBILE_SET = true, USE_M=true")

if __name__ == "__main__":
    main()
