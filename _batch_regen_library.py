#!/usr/bin/env python3
"""Full library PDF regen via LilyPond pipeline.

Steps:
  1. Baseline stats + tar backup (notes.json + notes/)
  2. Delete generated part PDFs (*_Bb.pdf, *_Eb.pdf, ...)
  3. rerender_pdfs.py (29 PDSA) + _batch_reformat.py (31 other multi-version)
  4. ingest_joplin / ingest_gb_native / ingest_pdsa (idempotent dedup)
  5. Validate JSON, compare counts, clear file_id on regenerated parts
  6. Restart trumpetbot

Run on server: cd /root/trumpet-jazz-bot && ./.venv/bin/python _batch_regen_library.py
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time

ROOT = os.environ.get("JT_BOT_ROOT", "/root/trumpet-jazz-bot")
PY_BIN = os.path.join(ROOT, ".venv/bin/python")

GENERATED_SUFFIXES = (
    "_Bb.pdf",
    "_Eb.pdf",
    "_concert.pdf",
    "_guitar.pdf",
    "_bass.pdf",
    "_Bb_tenor.pdf",
)


def log(msg: str, log_fp) -> None:
    line = f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}"
    print(line, flush=True)
    log_fp.write(line + "\n")
    log_fp.flush()


def is_generated_part(filename: str) -> bool:
    return any(filename.endswith(suffix) for suffix in GENERATED_SUFFIXES)


def stats() -> dict:
    notes = json.load(open(os.path.join(ROOT, "notes.json"), encoding="utf-8"))
    works = len(notes)
    versions = sum(len(w.get("versions", [])) for w in notes)
    file_ids = sum(
        1 for w in notes for v in w.get("versions", []) if v.get("file_id")
    )
    gen_on_disk = 0
    gen_missing = 0
    for w in notes:
        for v in w.get("versions", []):
            f = v.get("file", "")
            if not is_generated_part(f):
                continue
            ap = os.path.join(ROOT, "notes", f)
            if os.path.exists(ap):
                gen_on_disk += 1
            else:
                gen_missing += 1
    return {
        "works": works,
        "versions": versions,
        "file_ids": file_ids,
        "gen_on_disk": gen_on_disk,
        "gen_missing": gen_missing,
    }


def run(cmd: list[str], log_fp) -> None:
    log("RUN: " + " ".join(cmd), log_fp)
    subprocess.check_call(cmd, cwd=ROOT)


def clear_generated_file_ids(notes: list) -> int:
    cleared = 0
    for work in notes:
        for version in work.get("versions", []):
            if is_generated_part(version.get("file", "")) and version.get("file_id"):
                version["file_id"] = None
                cleared += 1
    return cleared


def missing_pdfs(notes: list) -> list[str]:
    missing = []
    for work in notes:
        for version in work.get("versions", []):
            ap = os.path.join(ROOT, "notes", version["file"])
            if not os.path.exists(ap):
                missing.append(version["file"])
    return missing


def main() -> int:
    os.chdir(ROOT)
    log_path = os.path.join(ROOT, "batch_regen.log")
    with open(log_path, "a", encoding="utf-8", buffering=1) as log_fp:
        try:
            baseline = stats()
            log("BASELINE " + json.dumps(baseline), log_fp)
            json.dump(
                {"baseline": baseline, "started": time.time()},
                open(os.path.join(ROOT, "batch_regen_baseline.json"), "w"),
            )

            ts = time.strftime("%Y%m%d-%H%M%S")
            tar = f"/root/notes-backup-{ts}.tgz"
            run(["tar", "czf", tar, "notes.json", "notes/"], log_fp)
            log(f"BACKUP {tar} size={os.path.getsize(tar)}", log_fp)

            notes = json.load(open("notes.json", encoding="utf-8"))
            deleted = 0
            for work in notes:
                for version in work.get("versions", []):
                    f = version.get("file", "")
                    if not is_generated_part(f):
                        continue
                    ap = os.path.join("notes", f)
                    if os.path.exists(ap):
                        os.remove(ap)
                        deleted += 1
            log(f"DELETED {deleted} generated part PDFs", log_fp)

            works_before = len(notes)
            run([PY_BIN, "rerender_pdfs.py"], log_fp)
            run([PY_BIN, "_batch_reformat.py"], log_fp)

            notes_mid = json.load(open("notes.json", encoding="utf-8"))
            log(
                f"AFTER RERENDER works={len(notes_mid)} (was {works_before})",
                log_fp,
            )

            for script in (
                "ingest_joplin.py",
                "ingest_gb_native.py",
                "ingest_pdsa.py",
            ):
                run([PY_BIN, script], log_fp)

            run([PY_BIN, "_build_catalog.py"], log_fp)
            staging = os.path.join(ROOT, "web-staging/public/app/catalog.json")
            os.makedirs(os.path.dirname(staging), exist_ok=True)
            shutil.copy("/tmp/catalog.json", staging)
            cat_n = len(json.load(open("/tmp/catalog.json", encoding="utf-8"))["items"])
            log(f"CATALOG rebuilt {cat_n} items -> {staging}", log_fp)

            notes = json.load(open("notes.json", encoding="utf-8"))
            json.load(open("notes.json", encoding="utf-8"))

            cleared = clear_generated_file_ids(notes)
            with open("notes.json", "w", encoding="utf-8") as f:
                json.dump(notes, f, ensure_ascii=False, indent=2)

            after = stats()
            log("AFTER " + json.dumps(after), log_fp)
            log(f"CLEARED {cleared} file_ids", log_fp)
            log(f"DELTA works {baseline['works']} -> {after['works']}", log_fp)
            log(
                f"DELTA versions {baseline['versions']} -> {after['versions']}",
                log_fp,
            )

            missing = missing_pdfs(notes)
            if missing:
                log(f"WARNING missing PDFs: {len(missing)}", log_fp)
                for path in missing[:20]:
                    log("  MISSING " + path, log_fp)
            else:
                log("ALL version PDFs present on disk", log_fp)

            if after["works"] != baseline["works"]:
                log("ERROR work count changed — check dedup!", log_fp)
                return 2
            if after["versions"] != baseline["versions"]:
                log("ERROR version count changed!", log_fp)
                return 2

            run(["systemctl", "restart", "trumpetbot"], log_fp)
            status = subprocess.check_output(
                ["systemctl", "is-active", "trumpetbot"], text=True
            ).strip()
            log("BOT STATUS " + status, log_fp)
            log("BATCH_DONE", log_fp)
            return 0
        except Exception as exc:
            log("FATAL " + repr(exc), log_fp)
            raise


if __name__ == "__main__":
    sys.exit(main())