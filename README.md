# LLM Dataset Versioning Demo

This is a tiny end-to-end project to learn **dataset versioning** for LLM work.

It shows how to:

- Build versioned datasets (`v1.0.0`, `v1.1.0`) from a HuggingFace source
- Save each version under `data/versions/<dataset_name>/<version>/`
- Create shards, a manifest, and metadata per version
- Automate everything with a `Makefile`
- (Optionally) tag dataset versions in git / push to HuggingFace / track with DVC

## Project Layout

```text
llm-dataset-versioning-demo/
├── Makefile
├── README.md
├── requirements.txt
├── .gitignore
├── configs/
│   ├── dataset-v1.0.yaml
│   └── dataset-v1.1.yaml
├── data/
│   ├── raw/
│   │   └── README.md
│   └── versions/
├── scripts/
│   ├── build_dataset.py
│   └── inspect_version.py
