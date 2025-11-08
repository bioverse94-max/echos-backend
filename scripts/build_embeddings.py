#!/usr/bin/env python3
"""
Precompute embeddings for each concept + era CSV and write JSON files to embeddings/<concept>/<era>.json
Usage:
  python scripts/build_embeddings.py --concept freedom --eras 1900s,2020s
This script expects files named data/<era>_<concept>.csv (e.g. data/1900s_freedom.csv)
"""
import argparse
from sentence_transformers import SentenceTransformer
from pathlib import Path
import json

MODEL_NAME = "paraphrase-MiniLM-L6-v2"  # small + fast for hackathon

def read_csv_lines(path: Path):
    lines = []
    with path.open("r", encoding="utf8") as f:
        for ln in f:
            ln = ln.strip()
            if ln:
                lines.append(ln)
    return lines

def build_embeddings_for(concept: str, eras: list[str], out_base: Path, data_base: Path):
    model = SentenceTransformer(MODEL_NAME)
    for era in eras:
        csv_name = f"{era}_{concept}.csv"
        csv_path = data_base / csv_name
        if not csv_path.exists():
            print(f"[WARN] Missing data file: {csv_path} — skipping era {era}")
            continue
        items = []
        texts = read_csv_lines(csv_path)
        if not texts:
            print(f"[WARN] No lines in {csv_path}; skipping.")
            continue
        print(f"[INFO] Encoding {len(texts)} texts for {concept} / {era} ...")
        embs = model.encode(texts, show_progress_bar=True)
        for i, (t, e) in enumerate(zip(texts, embs)):
            items.append({
                "id": f"{concept}_{era}_{i}",
                "text": t,
                "era": era,
                # convert to list for JSON serializable
                "embedding": e.tolist() if hasattr(e, "tolist") else list(e)
            })
        out_dir = out_base / concept
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / f"{era}.json"
        with out_path.open("w", encoding="utf8") as f:
            json.dump({"items": items, "meta": {"concept": concept, "era": era, "count": len(items)}}, f, ensure_ascii=False, indent=2)
        print(f"[OK] Wrote {out_path}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--concept", required=True, help="concept name (e.g. freedom)")
    parser.add_argument("--eras", required=True, help="comma-separated list of eras (e.g. 1900s,1950s,2020s)")
    parser.add_argument("--data-dir", default="data", help="data folder")
    parser.add_argument("--out-dir", default="embeddings", help="embeddings output folder")
    args = parser.parse_args()
    eras = [e.strip() for e in args.eras.split(",") if e.strip()]
    build_embeddings_for(args.concept, eras, Path(args.out_dir), Path(args.data_dir))

if __name__ == "__main__":
    main()
