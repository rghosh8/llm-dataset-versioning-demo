#!/usr/bin/env python
import argparse
import json
import os
import random


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--base_dir",
        type=str,
        default="data/versions/demo-wikitext",
        help="Base directory for dataset versions",
    )
    parser.add_argument(
        "--version",
        type=str,
        required=True,
        help="Version to inspect, e.g. v1.0.0",
    )
    args = parser.parse_args()

    version_dir = os.path.join(args.base_dir, args.version)
    metadata_path = os.path.join(version_dir, "metadata.json")
    manifest_path = os.path.join(version_dir, "manifest.json")

    if not os.path.exists(metadata_path):
        raise FileNotFoundError(f"No metadata at {metadata_path}")

    with open(metadata_path, "r", encoding="utf-8") as f:
        meta = json.load(f)

    print("=== METADATA ===")
    for k, v in meta.items():
        print(f"{k}: {v}")

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    if not manifest:
        print("\nNo shards found in manifest.")
        return

    shard_entry = random.choice(manifest)
    shard_file = shard_entry["file"]
    shard_path = os.path.join(version_dir, "shards", shard_file)

    print("\n=== RANDOM SAMPLE ===")
    print(f"From shard: {shard_file}")
    with open(shard_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
        if not lines:
            print("(shard is empty)")
            return
        sample_line = random.choice(lines)
        sample = json.loads(sample_line)
        text = sample.get("text", "")
        print(text[:500], "..." if len(text) > 500 else "")


if __name__ == "__main__":
    main()
