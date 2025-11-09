#!/usr/bin/env python
from __future__ import annotations

import argparse
import gzip
import os
import sys
import time
import zipfile
from dataclasses import dataclass
from typing import Iterable, List, Tuple

import shutil

# 在项目根目录执行
# python script/compress_logs.py
# python script/compress_logs.py --threshold 100MB
# python script/compress_logs.py --log-dir logs --format zip
# python script/compress_logs.py --recursive --keep-original

@dataclass(frozen=True)
class CompressPlanItem:
    source_path: str
    target_path: str
    method: str  # 'gz' or 'zip'
    size_bytes: int


def parse_size(size_str: str) -> int:
    """
    Parse human-readable size strings like '10MB', '512KB', '1G', '1024'.
    Defaults to bytes if unit missing.
    """
    s = size_str.strip().upper().replace(" ", "")
    units = {
        "B": 1,
        "K": 1024,
        "KB": 1024,
        "M": 1024 ** 2,
        "MB": 1024 ** 2,
        "G": 1024 ** 3,
        "GB": 1024 ** 3,
    }
    for unit, multiplier in units.items():
        if s.endswith(unit):
            number_part = s[: -len(unit)]
            if not number_part:
                raise ValueError(f"Invalid size value: {size_str}")
            return int(float(number_part) * multiplier)
    # No unit -> bytes
    return int(float(s))


def human_size(num_bytes: int) -> str:
    units = ["B", "KB", "MB", "GB", "TB"]
    size = float(num_bytes)
    unit_idx = 0
    while size >= 1024 and unit_idx < len(units) - 1:
        size /= 1024.0
        unit_idx += 1
    return f"{size:.1f}{units[unit_idx]}"


def iter_files(directory: str, recursive: bool) -> Iterable[str]:
    if recursive:
        for dirpath, _, filenames in os.walk(directory):
            for fname in filenames:
                yield os.path.join(dirpath, fname)
    else:
        if not os.path.isdir(directory):
            return
        for fname in os.listdir(directory):
            path = os.path.join(directory, fname)
            if os.path.isfile(path):
                yield path


def is_already_compressed(path: str) -> bool:
    lower = path.lower()
    return lower.endswith(".gz") or lower.endswith(".zip")


def plan_compression(
    files: Iterable[str],
    threshold_bytes: int,
    method: str,
) -> List[CompressPlanItem]:
    plan: List[CompressPlanItem] = []
    for fpath in files:
        if is_already_compressed(fpath):
            continue
        try:
            size = os.path.getsize(fpath)
        except OSError:
            continue
        if size < threshold_bytes:
            continue
        if method == "gz":
            target = fpath + ".gz"
        else:
            target = fpath + ".zip"
        plan.append(CompressPlanItem(source_path=fpath, target_path=target, method=method, size_bytes=size))
    return plan


def compress_gz(source: str, target: str) -> None:
    # Stream copy to gzip, preserving file mtime in gzip header
    mtime = int(os.path.getmtime(source))
    with open(source, "rb") as fin, gzip.open(target, "wb", compresslevel=6, mtime=mtime) as fout:
        shutil.copyfileobj(fin, fout, length=1024 * 1024)
    # Align mtime of compressed file to source for easier retention policies
    try:
        os.utime(target, (mtime, mtime))
    except Exception:
        pass


def compress_zip(source: str, target: str) -> None:
    # Store with deflate compression and arcname as basename
    with zipfile.ZipFile(target, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.write(source, arcname=os.path.basename(source))
    try:
        mtime = int(os.path.getmtime(source))
        os.utime(target, (mtime, mtime))
    except Exception:
        pass


def perform_compression(plan: List[CompressPlanItem], keep_original: bool) -> Tuple[int, List[str]]:
    successes = 0
    messages: List[str] = []
    for item in plan:
        try:
            if os.path.exists(item.target_path):
                messages.append(f"Skip (exists): {item.target_path}")
                continue
            os.makedirs(os.path.dirname(item.target_path) or ".", exist_ok=True)
            if item.method == "gz":
                compress_gz(item.source_path, item.target_path)
            else:
                compress_zip(item.source_path, item.target_path)
            if not keep_original:
                try:
                    os.remove(item.source_path)
                except PermissionError:
                    # Possibly opened by a running process; keep original
                    messages.append(f"Warning: cannot delete open file: {item.source_path}")
            successes += 1
            messages.append(f"Compressed ({item.method}): {item.source_path} -> {item.target_path} ({human_size(item.size_bytes)})")
        except Exception as exc:
            messages.append(f"Error compressing {item.source_path}: {exc}")
    return successes, messages


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Compress log files in a directory when they exceed a size threshold."
    )
    parser.add_argument(
        "--log-dir",
        default="logs",
        help="Directory containing log files (default: logs)",
    )
    parser.add_argument(
        "--threshold",
        default="10MB",
        help="Minimum file size to trigger compression, e.g., 10MB, 512KB (default: 10MB)",
    )
    parser.add_argument(
        "--format",
        choices=["gz", "zip"],
        default="gz",
        help="Compression format (default: gz)",
    )
    parser.add_argument(
        "--recursive",
        action="store_true",
        help="Scan subdirectories recursively",
    )
    parser.add_argument(
        "--keep-original",
        action="store_true",
        help="Keep original files after compression (default: delete originals)",
    )
    return parser


def main(argv: List[str] | None = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    log_dir = os.path.abspath(args.log_dir)
    threshold_bytes = parse_size(args.threshold)

    if not os.path.exists(log_dir) or not os.path.isdir(log_dir):
        print(f"Log directory not found: {log_dir}")
        return 1

    files = list(iter_files(log_dir, recursive=args.recursive))
    plan = plan_compression(files, threshold_bytes=threshold_bytes, method=args.format)

    if not plan:
        print(f"No files reached threshold ({args.threshold}) in {log_dir}. Nothing to do.")
        return 0

    count, msgs = perform_compression(plan, keep_original=bool(args.keep_original))
    for m in msgs:
        print(m)
    print(f"Done. Compressed {count} file(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())


