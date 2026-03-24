#!/usr/bin/env python3
"""
DTR Pipeline Sentinel — File Watcher
=====================================
Watches ~/dreams-to-reality/test_videos/ for new .mp4 files and
auto-runs the Dreams to Reality reconstruction pipeline.

Usage:
    python dtr_watcher.py                    # watch with defaults
    python dtr_watcher.py --dry-run          # show what would run, don't execute
    python dtr_watcher.py --fps 2 --max-frames 100   # override pipeline params
    python dtr_watcher.py --once <video.mp4> # run pipeline on a specific file now

Requires:
    pip install watchdog       (file watching)
    pip install pyyaml         (optional — for loading dtr-pipeline.yaml)

All other deps live in the DTR project (pycolmap, rembg, trimesh, cv2, tqdm).
"""

import argparse
import json
import logging
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

DTR_ROOT = Path("~/dreams-to-reality").expanduser()
WATCH_DIR = DTR_ROOT / "test_videos"
DREAMS_EXPORT = DTR_ROOT / "dreams_export.py"
RECORD_RESULT = DTR_ROOT / "record_result.py"
PIPELINE_TESTS = DTR_ROOT / "PIPELINE_TESTS.md"
SENTINEL_DIR = Path("~/ai-hot-sauce/sentinels").expanduser()
LOG_FILE = SENTINEL_DIR / "dtr_watcher.log"
SENTINEL_STATE = SENTINEL_DIR / "dtr_sentinel_state.json"

# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger("dtr_sentinel")


def add_file_handler():
    """Add file logging once we know the log path is writable."""
    try:
        SENTINEL_DIR.mkdir(parents=True, exist_ok=True)
        fh = logging.FileHandler(LOG_FILE, encoding="utf-8")
        fh.setFormatter(logging.Formatter(
            "%(asctime)s [%(levelname)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        ))
        log.addHandler(fh)
        log.info(f"Log file: {LOG_FILE}")
    except Exception as e:
        log.warning(f"Could not open log file {LOG_FILE}: {e}")


# ---------------------------------------------------------------------------
# Dependency checks
# ---------------------------------------------------------------------------

REQUIRED_DEPS = [
    ("watchdog", "pip install watchdog"),
    ("pycolmap",  "pip install pycolmap (or build with CUDA)"),
    ("rembg",     "pip install rembg"),
    ("trimesh",   "pip install trimesh"),
    ("cv2",       "pip install opencv-python"),
    ("tqdm",      "pip install tqdm"),
]

OPTIONAL_DEPS = [
    ("yaml",  "pip install pyyaml   — enables loading dtr-pipeline.yaml config"),
    ("vggt",  "pip install vggt     — COLMAP replacement (CVPR 2025 Best Paper)"),
]


def check_deps() -> bool:
    """Check required packages. Print status for all. Return True if all required present."""
    print("\n-- Dependency Check ------------------------------------------")
    all_ok = True
    for mod, hint in REQUIRED_DEPS:
        try:
            __import__(mod)
            print(f"  [OK]      {mod}")
        except ImportError:
            print(f"  [MISSING] {mod}  ->  {hint}")
            all_ok = False

    print()
    for mod, hint in OPTIONAL_DEPS:
        try:
            __import__(mod)
            print(f"  [OK]      {mod}  (optional)")
        except ImportError:
            print(f"  [--]      {mod}  (optional)  ->  {hint}")

    print("--------------------------------------------------------------\n")
    return all_ok


# ---------------------------------------------------------------------------
# State — track best results for regression detection
# ---------------------------------------------------------------------------

def load_state() -> dict:
    if SENTINEL_STATE.exists():
        try:
            return json.loads(SENTINEL_STATE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {
        "best_vertices": 17313,   # RK-03 (RealityScan + U2Net) — known good
        "best_faces": 34622,
        "best_pipeline": "realityscan_u2net",
        "runs": [],
    }


def save_state(state: dict):
    try:
        SENTINEL_STATE.write_text(json.dumps(state, indent=2), encoding="utf-8")
    except Exception as e:
        log.warning(f"Could not save state: {e}")


# ---------------------------------------------------------------------------
# Quality analysis
# ---------------------------------------------------------------------------

# Thresholds from dtr-pipeline.yaml
MIN_VERTICES   = 3000
MIN_FACES      = 5000
WARN_VERTICES  = 10000
WARN_FACES     = 20000
MAX_FILE_MB    = 100
MIN_FILE_KB    = 50


def analyze_glb(glb_path: Path) -> dict:
    """Return mesh stats dict: vertices, faces, watertight, size_mb."""
    stats = {"path": str(glb_path), "size_mb": 0.0}
    try:
        size = glb_path.stat().st_size
        stats["size_mb"] = size / (1024 * 1024)
        stats["size_kb"] = size / 1024
    except Exception:
        pass

    try:
        import trimesh
        m = trimesh.load(str(glb_path), force="mesh")
        if hasattr(m, "vertices"):
            stats["vertices"] = len(m.vertices)
            stats["faces"]    = len(m.faces)
            stats["watertight"] = bool(m.is_watertight)
        else:
            meshes = list(m.geometry.values())
            stats["vertices"]   = sum(len(x.vertices) for x in meshes)
            stats["faces"]      = sum(len(x.faces) for x in meshes)
            stats["watertight"] = all(x.is_watertight for x in meshes)
    except Exception as e:
        stats["error"] = str(e)

    return stats


def quality_gates(stats: dict, state: dict) -> tuple[str, list[str]]:
    """
    Return (status, messages) where status is one of:
        PASS | WARN | DEGRADED | FAILED
    messages is a list of human-readable issues / suggestions.
    """
    messages = []
    status = "PASS"

    verts = stats.get("vertices", 0)
    faces = stats.get("faces", 0)
    size_mb = stats.get("size_mb", 0)
    size_kb = stats.get("size_kb", 0)
    watertight = stats.get("watertight", False)

    if "error" in stats:
        messages.append(f"Mesh analysis failed: {stats['error']}")
        return "FAILED", messages

    # Hard minimums
    if verts < MIN_VERTICES:
        status = "FAILED"
        messages.append(
            f"Vertex count {verts} < minimum {MIN_VERTICES}. "
            "Likely failed or near-empty reconstruction.\n"
            "  → Try: --fps 2 --max-frames 100, or check video for hard cuts."
        )
    if faces < MIN_FACES:
        status = "FAILED"
        messages.append(
            f"Face count {faces} < minimum {MIN_FACES}. "
            "Mesh is too sparse for printing.\n"
            "  → Try: --mesh-mode poisson for denser output."
        )

    # File size sanity
    if size_mb > MAX_FILE_MB:
        if status == "PASS":
            status = "WARN"
        messages.append(
            f"Output is {size_mb:.1f} MB — suspiciously large (likely hallucinated geometry).\n"
            "  → Inspect in viewer. Check for mixed camera-angle segments (see SS-02/SS-05)."
        )
    if size_kb < MIN_FILE_KB:
        status = "FAILED"
        messages.append(
            f"Output is only {size_kb:.0f} KB — likely empty/corrupt file."
        )

    # Soft warnings
    if status == "PASS":
        if verts < WARN_VERTICES:
            status = "WARN"
            messages.append(
                f"Vertex count {verts} is below soft target {WARN_VERTICES}.\n"
                "  → Try: --fps 2 --max-frames 100 for a denser point cloud.\n"
                "  → Long-term: CUDA pycolmap for dense reconstruction (target 19K+ verts)."
            )
        if faces < WARN_FACES:
            if status == "PASS":
                status = "WARN"
            messages.append(
                f"Face count {faces} below soft target {WARN_FACES}.\n"
                "  → Try: --mesh-mode poisson."
            )

    # Regression check vs previous best
    best_v = state.get("best_vertices", 0)
    if verts > 0 and best_v > 0:
        drop_pct = (best_v - verts) / best_v * 100
        if drop_pct > 40 and status == "PASS":
            status = "DEGRADED"
            messages.append(
                f"Vertex count dropped {drop_pct:.0f}% vs best known ({best_v}).\n"
                "  → This pipeline variant is underperforming. Check PIPELINE_TESTS.md."
            )

    # Watertight notice (not a failure — sparse COLMAP rarely watertight)
    if not watertight and status == "PASS":
        messages.append(
            "Mesh is not watertight. Fine for viewing; may cause 3D print issues.\n"
            "  → For printing: run blender_postprocess.py or use --mesh-mode poisson."
        )

    # VGGT hint — check if installed
    try:
        import vggt  # noqa: F401
        messages.append(
            "VGGT is installed. Consider a VGGT pipeline run — "
            "may dramatically improve camera registration speed and quality."
        )
    except ImportError:
        pass

    return status, messages


def print_quality_report(video_stem: str, stats: dict, status: str,
                         messages: list[str], state: dict, elapsed: float):
    """Print a structured quality report to stdout."""
    verts = stats.get("vertices", "?")
    faces  = stats.get("faces", "?")
    wt     = stats.get("watertight", "?")
    size   = f"{stats.get('size_mb', 0):.2f} MB"
    best_v = state.get("best_vertices", "?")
    best_f = state.get("best_faces", "?")

    status_icon = {"PASS": "+", "WARN": "!", "DEGRADED": "v", "FAILED": "X"}.get(status, "?")

    print()
    print("=" * 60)
    print(f"  DTR SENTINEL RESULT  [{status_icon} {status}]  {video_stem}")
    print("=" * 60)
    print(f"  Vertices:   {verts:>10}  (best: {best_v})")
    print(f"  Faces:      {faces:>10}  (best: {best_f})")
    print(f"  Watertight: {str(wt):>10}")
    print(f"  File size:  {size:>10}")
    print(f"  Time:       {elapsed:.1f}s")
    if messages:
        print()
        print("  Notes / Suggestions:")
        for msg in messages:
            for i, line in enumerate(msg.splitlines()):
                prefix = "  * " if i == 0 else "    "
                print(f"{prefix}{line}")
    print("=" * 60)
    print()


# ---------------------------------------------------------------------------
# Pipeline runner
# ---------------------------------------------------------------------------

def find_output_glb(export_dir: Path) -> Optional[Path]:
    """Find the GLB output file in the export directory tree."""
    # dreams_export.py names it <video_stem>.glb inside export_dir
    glbs = list(export_dir.rglob("*.glb"))
    if not glbs:
        return None
    # Prefer the top-level one; fall back to deepest
    top = [g for g in glbs if g.parent == export_dir]
    return top[0] if top else glbs[0]


def run_pipeline(
    video_path: Path,
    fps: int = 1,
    max_frames: int = 60,
    mesh_mode: str = "delaunay",
    skip_dense: bool = True,
    dry_run: bool = False,
) -> Optional[Path]:
    """
    Run dreams_export.py on video_path. Returns path to output GLB or None.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    stem = video_path.stem
    export_dir = DTR_ROOT / "exports" / f"{stem}_{timestamp}"

    cmd = [
        sys.executable, str(DREAMS_EXPORT),
        str(video_path),
        "--fps", str(fps),
        "--max-frames", str(max_frames),
        "--mesh-mode", mesh_mode,
        "--output-dir", str(export_dir),
    ]
    if skip_dense:
        cmd.append("--skip-dense")

    log.info(f"Pipeline command: {' '.join(cmd)}")

    if dry_run:
        log.info("[DRY RUN] Would execute the above command. Skipping.")
        return None

    log.info(f"Starting pipeline for: {video_path.name}")
    t0 = time.time()
    try:
        result = subprocess.run(
            cmd,
            cwd=str(DTR_ROOT),
            timeout=3600,   # 60 min max — dense runs can be slow
        )
        elapsed = time.time() - t0
        if result.returncode != 0:
            log.error(f"Pipeline exited with code {result.returncode}")
            return None
        log.info(f"Pipeline completed in {elapsed:.1f}s")
        return find_output_glb(export_dir)
    except subprocess.TimeoutExpired:
        log.error("Pipeline timed out after 60 minutes")
        return None
    except Exception as e:
        log.error(f"Pipeline error: {e}")
        return None


def log_result(
    video_path: Path,
    glb_path: Path,
    frame_count: int,
    dry_run: bool = False,
):
    """Call record_result.py to append to PIPELINE_TESTS.md."""
    stem = video_path.stem
    cmd = [
        sys.executable, str(RECORD_RESULT),
        "--subject", stem,
        "--pipeline", "colmap_u2net",
        "--output", str(glb_path),
        "--frames", str(frame_count),
        "--segmented",
        "--segment-model", "u2net",
        "--notes", "Auto-logged by DTR Pipeline Sentinel",
    ]
    log.info(f"Logging result: {' '.join(cmd)}")
    if dry_run:
        log.info("[DRY RUN] Would call record_result.py. Skipping.")
        return
    try:
        subprocess.run(cmd, cwd=str(DTR_ROOT), timeout=60)
    except Exception as e:
        log.error(f"record_result.py failed: {e}")


def process_video(video_path: Path, args, state: dict):
    """Full pipeline: run → analyze → quality gate → log → update state."""
    log.info(f"New video detected: {video_path.name}")

    # Small pause to ensure the file is fully written (handles rsync/copy scenarios)
    time.sleep(args.debounce)

    if not video_path.exists():
        log.warning(f"File vanished before processing: {video_path}")
        return

    size_mb = video_path.stat().st_size / (1024 * 1024)
    log.info(f"File size: {size_mb:.1f} MB")
    if size_mb < 0.1:
        log.warning("File is <100 KB — likely incomplete. Skipping.")
        return

    t_start = time.time()

    # Run pipeline
    glb_path = run_pipeline(
        video_path=video_path,
        fps=args.fps,
        max_frames=args.max_frames,
        mesh_mode=args.mesh_mode,
        skip_dense=args.skip_dense,
        dry_run=args.dry_run,
    )

    elapsed = time.time() - t_start

    if glb_path is None or not glb_path.exists():
        log.error(f"No GLB produced for {video_path.name}")
        print()
        print(f"[DTR SENTINEL] FAILED: {video_path.stem}")
        print(f"  No output file found after pipeline run.")
        print(f"  Check: {LOG_FILE}")
        print()
        return

    log.info(f"Output GLB: {glb_path} ({glb_path.stat().st_size / 1024:.0f} KB)")

    # Analyze quality
    stats  = analyze_glb(glb_path)
    status, messages = quality_gates(stats, state)

    print_quality_report(
        video_stem=video_path.stem,
        stats=stats,
        status=status,
        messages=messages,
        state=state,
        elapsed=elapsed,
    )

    # Log result to PIPELINE_TESTS.md
    log_result(
        video_path=video_path,
        glb_path=glb_path,
        frame_count=args.max_frames,
        dry_run=args.dry_run,
    )

    # Update state if this is a new best
    verts = stats.get("vertices", 0)
    faces  = stats.get("faces", 0)
    if verts > state.get("best_vertices", 0) and not args.dry_run:
        log.info(f"New best vertex count: {verts} (was {state['best_vertices']})")
        state["best_vertices"] = verts
        state["best_faces"]    = faces
        state["best_pipeline"] = "colmap_u2net"

    # Append run to state history
    state.setdefault("runs", []).append({
        "timestamp": datetime.now().isoformat(),
        "video": video_path.name,
        "glb": str(glb_path),
        "vertices": verts,
        "faces": faces,
        "watertight": stats.get("watertight", False),
        "status": status,
        "elapsed_s": round(elapsed, 1),
    })
    if not args.dry_run:
        save_state(state)


# ---------------------------------------------------------------------------
# Watchdog event handler
# ---------------------------------------------------------------------------

def make_handler(args, state: dict):
    """Return a watchdog FileSystemEventHandler."""
    try:
        from watchdog.events import FileSystemEventHandler
    except ImportError:
        log.error("watchdog not installed. Run: pip install watchdog")
        sys.exit(1)

    class DTRHandler(FileSystemEventHandler):
        def on_created(self, event):
            if event.is_directory:
                return
            path = Path(event.src_path)
            if path.suffix.lower() != ".mp4":
                return
            log.info(f"File event: created {path.name}")
            process_video(path, args, state)

        def on_moved(self, event):
            # Handles files moved/renamed into the watch directory (common on macOS/Linux)
            if event.is_directory:
                return
            path = Path(event.dest_path)
            if path.suffix.lower() != ".mp4":
                return
            log.info(f"File event: moved → {path.name}")
            process_video(path, args, state)

    return DTRHandler()


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args():
    parser = argparse.ArgumentParser(
        description="DTR Pipeline Sentinel — watches for new videos and runs reconstruction",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python dtr_watcher.py                          # watch test_videos/, run on new .mp4
  python dtr_watcher.py --dry-run                # show commands without running
  python dtr_watcher.py --fps 2 --max-frames 100 # denser sampling
  python dtr_watcher.py --once rocket.mp4        # run pipeline once on specific file
  python dtr_watcher.py --check-deps             # check all required packages
""",
    )
    parser.add_argument(
        "--once",
        metavar="VIDEO",
        help="Run pipeline on this specific video file and exit (no watching)",
    )
    parser.add_argument(
        "--fps",
        type=int,
        default=1,
        help="Frames per second to extract (default: 1)",
    )
    parser.add_argument(
        "--max-frames",
        type=int,
        default=60,
        help="Max frames to use (default: 60). Try 100 for denser reconstruction.",
    )
    parser.add_argument(
        "--mesh-mode",
        choices=["delaunay", "poisson"],
        default="delaunay",
        help="Meshing algorithm (default: delaunay — proven better for Dreams subjects)",
    )
    parser.add_argument(
        "--no-skip-dense",
        dest="skip_dense",
        action="store_false",
        default=True,
        help="Attempt dense reconstruction (requires CUDA pycolmap — blocked on CPU-only)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would be run without executing",
    )
    parser.add_argument(
        "--check-deps",
        action="store_true",
        help="Check all required and optional dependencies and exit",
    )
    parser.add_argument(
        "--debounce",
        type=float,
        default=3.0,
        help="Seconds to wait after file creation before processing (default: 3)",
    )
    parser.add_argument(
        "--watch-dir",
        type=str,
        default=str(WATCH_DIR),
        help=f"Directory to watch (default: {WATCH_DIR})",
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    args = parse_args()
    add_file_handler()

    log.info("DTR Pipeline Sentinel starting up")
    log.info(f"DTR root:   {DTR_ROOT}")
    log.info(f"Watch dir:  {args.watch_dir}")

    if args.check_deps:
        ok = check_deps()
        sys.exit(0 if ok else 1)

    # Always run deps check at startup (non-fatal for missing optional)
    required_ok = check_deps()
    if not required_ok:
        log.warning(
            "Some required dependencies are missing. "
            "Pipeline runs will likely fail. Install missing packages first."
        )

    state = load_state()
    log.info(f"Loaded state: best={state.get('best_vertices', '?')} verts, "
             f"{len(state.get('runs', []))} previous runs")

    # --once mode: process a single file and exit
    if args.once:
        video_path = Path(args.once).expanduser().resolve()
        if not video_path.exists():
            # Try relative to watch dir
            video_path = Path(args.watch_dir) / args.once
        if not video_path.exists():
            log.error(f"Video not found: {args.once}")
            sys.exit(1)
        process_video(video_path, args, state)
        return

    # Watch mode
    watch_dir = Path(args.watch_dir).expanduser()
    if not watch_dir.exists():
        log.error(f"Watch directory does not exist: {watch_dir}")
        log.error("Create it with: mkdir -p ~/dreams-to-reality/test_videos/")
        sys.exit(1)

    try:
        from watchdog.observers import Observer
    except ImportError:
        log.error("watchdog not installed. Run: pip install watchdog")
        sys.exit(1)

    handler  = make_handler(args, state)
    observer = Observer()
    observer.schedule(handler, str(watch_dir), recursive=False)
    observer.start()

    log.info(f"Watching: {watch_dir}")
    log.info("Drop a .mp4 into test_videos/ to trigger the pipeline.")
    log.info("Press Ctrl+C to stop.\n")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        log.info("Sentinel stopped by user.")
        observer.stop()
    observer.join()


if __name__ == "__main__":
    main()
