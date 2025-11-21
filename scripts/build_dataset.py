#!/usr/bin/env python
import argparse
import json
import math
import os
from datetime import datetime
from hashlib import sha256

import yaml
from datasets import load_dataset
from tqdm import tqdm


def load_config(path: str) -> dict:
    with open(path, "r") as f:
        return yaml.safe_load(f)


def clean_text(text: str, cfg: dict) -> str:
    if text is None:
        return ""
    if cfg.get("strip_empty_lines", True):
        lines = [l.strip() for l in text.splitlines()]
        text = "\n".join([l for l in lines if l])
    if cfg.get("normalize_whitespace", True):
        # simple whitespace normalization
        text = " ".join(text.split())
    return text


def filter_example(text: str, filter_cfg: dict) -> bool:
    if text is None:
        return False
    n = len(text)
    min_chars = filter_cfg.get("min_chars", 0)
    max_chars = filter_cfg.get("max_chars", 10_000_000)
    return (n >= min_chars) and (n <= max_chars)


def ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)


def shard_iter(examples, shard_size: int):
    """Yield chunks of size shard_size."""
    current = []
    for ex in examples:
        current.append(ex)
        if len(current) >= shard_size:
            yield current
            current = []
    if current:
        yield current


def write_shard(path: str, records):
    """Write a JSONL shard and return its sha256 hash and line count."""
    h = sha256()
    count = 0
    with open(path, "w", encoding="utf-8") as f:
        for rec in records:
            line = json.dumps(rec, ensure_ascii=False)
            f.write(line + "\n")
            h.update(line.encode("utf-8"))
            count += 1
    return h.hexdigest(), count


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config",
        type=str,
        required=True,
        help="Path to dataset config YAML (e.g. configs/dataset-v1.0.yaml)",
    )
    args = parser.parse_args()

    cfg = load_config(args.config)
    version = cfg["version"]
    src_cfg = cfg["source"]
    filt_cfg = cfg.get("filters", {})
    proc_cfg = cfg.get("processing", {})
    out_cfg = cfg["output"]

    base_dir = out_cfg["base_dir"]
    dataset_name = out_cfg["dataset_name"]
    shard_size = out_cfg["shard_size"]

    # Version directory: data/versions/demo-wikitext/v1.0.0/
    version_dir = os.path.join(base_dir, dataset_name, version)
    shards_dir = os.path.join(version_dir, "shards")
    ensure_dir(shards_dir)

    print(f"Building dataset '{dataset_name}' version {version}")
    print(f"Output directory: {version_dir}")

    # Load HF dataset
    ds = load_dataset(
        src_cfg["hf_dataset"],
        src_cfg.get("hf_config"),
        split=src_cfg.get("split", "train"),
    )

    print(f"Loaded raw dataset with {len(ds)} examples")

    processed = []
    total_raw = 0
    total_kept = 0

    for ex in tqdm(ds, desc="Processing"):
        total_raw += 1
        text = ex.get("text", "")
        text = clean_text(text, proc_cfg)
        if not filter_example(text, filt_cfg):
            continue
        processed.append({"text": text})
        total_kept += 1

    print(f"Kept {total_kept} / {total_raw} examples after filtering")

    # Write shards + manifest
    manifest_lines = []
    num_tokens_est = 0  # rough estimate: len(text.split())
    shard_index = 0

    for shard_recs in tqdm(
        shard_iter(processed, shard_size),
        total=math.ceil(len(processed) / shard_size) if processed else 0,
        desc="Writing shards",
    ):
        shard_name = f"part-{shard_index:05d}.jsonl"
        shard_path = os.path.join(shards_dir, shard_name)
        digest, count = write_shard(shard_path, shard_recs)
        manifest_lines.append(
            {
                "file": shard_name,
                "sha256": digest,
                "num_records": count,
            }
        )
        for r in shard_recs:
            num_tokens_est += len(r["text"].split())
        shard_index += 1

    # Write manifest.txt (human-friendly) and manifest.json (machine readable)
    manifest_txt_path = os.path.join(version_dir, "manifest.txt")
    with open(manifest_txt_path, "w", encoding="utf-8") as f:
        for entry in manifest_lines:
            f.write(
                f"{entry['file']} sha256={entry['sha256']} num_records={entry['num_records']}\n"
            )

    manifest_json_path = os.path.join(version_dir, "manifest.json")
    with open(manifest_json_path, "w", encoding="utf-8") as f:
        json.dump(manifest_lines, f, indent=2)

    # Metadata
    metadata = {
        "version": version,
        "dataset_name": dataset_name,
        "created_at": datetime.utcnow().isoformat() + "Z",
        "num_raw_examples": total_raw,
        "num_examples": len(processed),
        "num_shards": shard_index,
        "estimated_num_tokens": num_tokens_est,
        "source": src_cfg,
        "filters": filt_cfg,
        "processing": proc_cfg,
        "shard_size": shard_size,
        # in a real project, also store git commit hash here:
        # "build_commit": "<git-hash>",
        "config_path": os.path.abspath(args.config),
    }

    metadata_path = os.path.join(version_dir, "metadata.json")
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    print("Done!")
    print(f"Metadata: {metadata_path}")
    print(f"Manifest: {manifest_txt_path}")


if __name__ == "__main__":
    main()
