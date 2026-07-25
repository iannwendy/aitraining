"""Build a provenance-preserving English-to-Vietnamese auxiliary train set.

The source is a fixed-revision CC0 mirror of the cleaned Reddit depression
dataset. Labels are source/subreddit-derived and are therefore treated as weak
auxiliary labels, not clinical or expert annotations. Translation runs locally
with a pinned NLLB checkpoint; no text is uploaded to a translation service.

The script deliberately samples equal depression/normal pairs from matching
source-length bins. A pair enters train only if both translations pass the same
automatic quality checks. Validation, in-domain test, and VSMEC are read only
for exact-overlap rejection and are never used to select source rows.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import re
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import requests
import torch
from sentence_transformers import SentenceTransformer
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer


PROJECT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = PROJECT_DIR / "data" / "translated_en_vi"
SOURCE_DATASET_ID = "hugginglearners/reddit-depression-cleaned"
SOURCE_REVISION = "c71fde85d3a85330916731069ebbb3461816404b"
SOURCE_LICENSE = "CC0-1.0"
SOURCE_URL = (
    "https://huggingface.co/datasets/"
    f"{SOURCE_DATASET_ID}/resolve/{SOURCE_REVISION}/"
    "depression_dataset_reddit_cleaned.csv"
)
SOURCE_EXPECTED_SHA256 = "bc5fc11e77b4388c6484f580824900484c2b58f8ed4dce32c6d1cb78c48ed7e9"

TRANSLATION_MODEL_ID = "facebook/nllb-200-distilled-600M"
TRANSLATION_MODEL_REVISION = "f8d333a098d19b4fd9a8b18f94170487ad3f821d"
TRANSLATION_MODEL_LICENSE = "CC-BY-NC-4.0"
SIMILARITY_MODEL_ID = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
SIMILARITY_MODEL_REVISION = "e8f8c211226b894fcb81acc59f3b34ba3efd5f42"
SIMILARITY_MODEL_LICENSE = "Apache-2.0"

EN_NEGATIONS = {
    "no", "not", "never", "nothing", "nobody", "neither", "nor", "without",
    "cannot", "cant", "can't", "dont", "don't", "didnt", "didn't", "wont",
    "won't", "wouldnt", "wouldn't", "isnt", "isn't", "arent", "aren't",
    "wasnt", "wasn't", "werent", "weren't", "shouldnt", "shouldn't",
    "couldnt", "couldn't",
}
VI_NEGATIONS = {"không", "chẳng", "chưa", "đừng", "chả", "khỏi"}
PII_PATTERN = re.compile(
    r"https?://|www\.|\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b|"
    r"(?:\+?\d[\s().-]?){9,}|(?:u/|/u/)[A-Za-z0-9_-]+",
    flags=re.IGNORECASE,
)
LENGTH_BINS = [19, 39, 59, 79, 99, 119, 144]


def normalize_text(value: object) -> str:
    text = unicodedata.normalize("NFKC", str(value))
    return re.sub(r"\s+", " ", text).strip()


def normalized_key(value: object) -> str:
    return normalize_text(value).casefold()


def sha256_text(value: str) -> str:
    return hashlib.sha256(normalized_key(value).encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def clip_at_word_boundary(text: str, max_chars: int) -> str:
    text = normalize_text(text)
    if len(text) <= max_chars:
        return text
    clipped = text[: max_chars + 1]
    boundary = clipped.rfind(" ")
    return clipped[:boundary].strip() if boundary >= max_chars // 2 else text[:max_chars].strip()


def atomic_csv(frame: pd.DataFrame, path: Path) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    frame.to_csv(temporary, index=False)
    temporary.replace(path)


def download_source(path: Path) -> None:
    if path.exists() and sha256_file(path) == SOURCE_EXPECTED_SHA256:
        return
    response = requests.get(SOURCE_URL, timeout=120)
    response.raise_for_status()
    path.write_bytes(response.content)
    actual = sha256_file(path)
    if actual != SOURCE_EXPECTED_SHA256:
        raise ValueError(f"Source SHA-256 mismatch: expected {SOURCE_EXPECTED_SHA256}, got {actual}")


def select_length_matched_pairs(
    source: pd.DataFrame,
    *,
    per_class: int,
    seed: int,
    max_source_chars: int,
) -> tuple[pd.DataFrame, dict[str, object]]:
    required = {"clean_text", "is_depression"}
    if not required.issubset(source.columns):
        raise ValueError(f"Source columns must include {sorted(required)}")
    frame = source[["clean_text", "is_depression"]].copy()
    frame["source_row_id"] = np.arange(len(frame), dtype=int)
    frame["source_text_original"] = frame["clean_text"].fillna("").map(normalize_text)
    frame["source_key"] = frame["source_text_original"].map(normalized_key)
    frame["label"] = pd.to_numeric(frame["is_depression"], errors="coerce")

    blank = frame["source_key"].eq("")
    invalid_label = ~frame["label"].isin([0, 1])
    pii = frame["source_text_original"].str.contains(PII_PATTERN)
    too_short = frame["source_text_original"].str.len().lt(20)
    duplicate = frame["source_key"].duplicated(keep="first")
    valid_for_conflict_check = ~(blank | invalid_label)
    source_conflict_counts = (
        frame.loc[valid_for_conflict_check].groupby("source_key")["label"].nunique()
    )
    source_conflicting_keys = set(
        source_conflict_counts[source_conflict_counts > 1].index
    )
    source_label_conflict = frame["source_key"].isin(source_conflicting_keys)
    keep = ~(
        blank | invalid_label | pii | too_short | duplicate | source_label_conflict
    )
    filtered = frame.loc[keep].copy()
    filtered["label"] = filtered["label"].astype(int)
    filtered["source_text_en"] = filtered["source_text_original"].map(
        lambda text: clip_at_word_boundary(text, max_source_chars)
    )
    filtered["clipped_key"] = filtered["source_text_en"].map(normalized_key)

    conflict_counts = filtered.groupby("clipped_key")["label"].nunique()
    conflicting_keys = set(conflict_counts[conflict_counts > 1].index)
    clipped_duplicate = filtered["clipped_key"].duplicated(keep="first")
    filtered = filtered.loc[
        ~filtered["clipped_key"].isin(conflicting_keys) & ~clipped_duplicate
    ].copy()
    filtered["source_chars"] = filtered["source_text_en"].str.len()
    filtered["length_bin"] = pd.cut(
        filtered["source_chars"], bins=LENGTH_BINS, include_lowest=True
    ).astype(str)

    rng = np.random.default_rng(seed)
    pair_rows: list[dict[str, object]] = []
    for length_bin, group in filtered.groupby("length_bin", sort=True):
        normal = group[group["label"] == 0].iloc[rng.permutation((group["label"] == 0).sum())]
        depression = group[group["label"] == 1].iloc[
            rng.permutation((group["label"] == 1).sum())
        ]
        count = min(len(normal), len(depression))
        for index in range(count):
            pair_rows.append({
                "length_bin": length_bin,
                "normal_index": int(normal.index[index]),
                "depression_index": int(depression.index[index]),
            })
    if len(pair_rows) < per_class:
        raise ValueError(
            f"Only {len(pair_rows)} length-matched pairs available; requested {per_class}"
        )
    available_pair_count = len(pair_rows)
    random.Random(seed).shuffle(pair_rows)
    pair_rows = pair_rows[:per_class]

    selected_parts = []
    for pair_number, pair in enumerate(pair_rows):
        pair_id = f"pair_{pair_number:05d}"
        for index in (pair["normal_index"], pair["depression_index"]):
            row = filtered.loc[index].copy()
            row["pair_id"] = pair_id
            selected_parts.append(row)
    selected = pd.DataFrame(selected_parts).reset_index(drop=True)
    selected["source_text_sha256"] = selected["source_text_original"].map(sha256_text)
    selected["source_dataset"] = SOURCE_DATASET_ID
    selected["source_revision"] = SOURCE_REVISION
    selected["source_license"] = SOURCE_LICENSE
    selected["selection_seed"] = seed
    selected["translation_model"] = TRANSLATION_MODEL_ID
    selected["translation_model_revision"] = TRANSLATION_MODEL_REVISION
    selected["translation_model_license"] = TRANSLATION_MODEL_LICENSE

    report = {
        "source_rows": int(len(source)),
        "rejected": {
            "blank": int(blank.sum()),
            "invalid_label": int(invalid_label.sum()),
            "pii_pattern": int(pii.sum()),
            "too_short": int(too_short.sum()),
            "duplicate_normalized_source": int(duplicate.sum()),
            "source_label_conflict_rows": int(source_label_conflict.sum()),
            "clipped_label_conflict_keys": int(len(conflicting_keys)),
            "duplicate_after_clipping": int(clipped_duplicate.sum()),
        },
        "eligible_after_filters": int(len(filtered)),
        "available_length_matched_pairs": int(available_pair_count),
        "selected_pairs": int(per_class),
        "selected_rows": int(len(selected)),
        "selected_label_distribution": {
            str(int(key)): int(value)
            for key, value in selected["label"].value_counts().sort_index().items()
        },
        "selected_length_bins": {
            str(key): int(value)
            for key, value in selected.groupby("length_bin").size().items()
        },
    }
    return selected, report


def translation_device() -> torch.device:
    if torch.cuda.is_available():
        return torch.device("cuda")
    if torch.backends.mps.is_available():
        return torch.device("mps")
    return torch.device("cpu")


def translate_selected(
    selected: pd.DataFrame,
    progress_file: Path,
    *,
    batch_size: int,
) -> pd.DataFrame:
    existing = pd.read_csv(progress_file) if progress_file.exists() else pd.DataFrame()
    if not existing.empty and not {"source_text_sha256", "comment_text"}.issubset(
        existing.columns
    ):
        raise ValueError(f"Malformed translation checkpoint: {progress_file}")
    translated_by_hash: dict[str, str] = {}
    if not existing.empty:
        translated_by_hash = dict(
            zip(
                existing["source_text_sha256"].astype(str),
                existing["comment_text"].fillna("").map(normalize_text),
            )
        )
    selected_hashes = set(selected["source_text_sha256"].astype(str))
    translated_by_hash = {
        key: value
        for key, value in translated_by_hash.items()
        if key in selected_hashes and value
    }
    pending = selected.loc[~selected["source_text_sha256"].isin(translated_by_hash)].copy()

    def current_progress() -> pd.DataFrame:
        progress = selected.loc[
            selected["source_text_sha256"].isin(translated_by_hash)
        ].copy()
        progress["comment_text"] = progress["source_text_sha256"].map(
            translated_by_hash
        )
        return progress

    if pending.empty:
        return current_progress()

    device = translation_device()
    tokenizer = AutoTokenizer.from_pretrained(
        TRANSLATION_MODEL_ID,
        revision=TRANSLATION_MODEL_REVISION,
        src_lang="eng_Latn",
    )
    model = AutoModelForSeq2SeqLM.from_pretrained(
        TRANSLATION_MODEL_ID,
        revision=TRANSLATION_MODEL_REVISION,
    )
    model.to(device)
    model.eval()
    forced_bos = tokenizer.convert_tokens_to_ids("vie_Latn")
    for start in range(0, len(pending), batch_size):
        batch_frame = pending.iloc[start : start + batch_size]
        encoded = tokenizer(
            batch_frame["source_text_en"].tolist(),
            return_tensors="pt",
            padding=True,
            truncation=True,
            max_length=256,
        )
        encoded = {key: value.to(device) for key, value in encoded.items()}
        with torch.no_grad():
            generated = model.generate(
                **encoded,
                forced_bos_token_id=forced_bos,
                max_new_tokens=192,
                num_beams=2,
            )
        translations = tokenizer.batch_decode(generated, skip_special_tokens=True)
        for (_, row), translated in zip(batch_frame.iterrows(), translations):
            translated_by_hash[str(row["source_text_sha256"])] = normalize_text(
                translated
            )
        atomic_csv(current_progress(), progress_file)
        print(f"Translated {min(start + batch_size, len(pending)):,}/{len(pending):,} pending rows")

    del model
    if device.type == "mps":
        torch.mps.empty_cache()
    return current_progress()


def contains_english_negation(text: str) -> bool:
    tokens = set(re.findall(r"[a-z]+(?:'[a-z]+)?", text.casefold()))
    return bool(tokens & EN_NEGATIONS)


def contains_vietnamese_negation(text: str) -> bool:
    tokens = set(re.findall(r"\w+", normalized_key(text), flags=re.UNICODE))
    return bool(tokens & VI_NEGATIONS) or "không thể" in normalized_key(text)


def load_holdout_keys() -> dict[str, set[str]]:
    paths = {
        "train": PROJECT_DIR / "data" / "labeled" / "final_train.csv",
        "validation": PROJECT_DIR / "data" / "labeled" / "final_val.csv",
        "test": PROJECT_DIR / "data" / "labeled" / "final_test.csv",
        "cross_domain": PROJECT_DIR / "data_unified" / "cross_domain_test.csv",
    }
    return {
        name: set(pd.read_csv(path)["comment_text"].astype(str).map(normalized_key))
        for name, path in paths.items()
    }


def audit_translations(
    translated: pd.DataFrame,
    *,
    similarity_threshold: float,
    seed: int,
) -> tuple[pd.DataFrame, dict[str, object]]:
    frame = translated.copy()
    frame["translated_key"] = frame["comment_text"].map(normalized_key)
    frame["translation_blank"] = frame["translated_key"].eq("")
    frame["translation_pii_pattern"] = frame["comment_text"].str.contains(PII_PATTERN)
    frame["source_has_negation"] = frame["source_text_en"].map(contains_english_negation)
    frame["translation_has_negation"] = frame["comment_text"].map(
        contains_vietnamese_negation
    )
    frame["negation_mismatch"] = (
        frame["source_has_negation"] != frame["translation_has_negation"]
    )
    source_words = frame["source_text_en"].str.split().str.len().clip(lower=1)
    target_words = frame["comment_text"].str.split().str.len()
    frame["translation_length_ratio"] = target_words / source_words
    frame["length_ratio_rejected"] = ~frame["translation_length_ratio"].between(0.45, 2.20)

    similarity_model = SentenceTransformer(
        SIMILARITY_MODEL_ID,
        revision=SIMILARITY_MODEL_REVISION,
    )
    source_embeddings = similarity_model.encode(
        frame["source_text_en"].tolist(),
        batch_size=64,
        convert_to_numpy=True,
        normalize_embeddings=True,
        show_progress_bar=True,
    )
    target_embeddings = similarity_model.encode(
        frame["comment_text"].tolist(),
        batch_size=64,
        convert_to_numpy=True,
        normalize_embeddings=True,
        show_progress_bar=True,
    )
    frame["cross_lingual_cosine"] = np.sum(source_embeddings * target_embeddings, axis=1)
    frame["similarity_rejected"] = frame["cross_lingual_cosine"].lt(similarity_threshold)

    duplicate_any = frame["translated_key"].duplicated(keep=False)
    conflict_counts = frame.groupby("translated_key")["label"].nunique()
    conflicting_keys = set(conflict_counts[conflict_counts > 1].index)
    frame["duplicate_translation"] = duplicate_any
    frame["translation_label_conflict"] = frame["translated_key"].isin(conflicting_keys)

    split_keys = load_holdout_keys()
    for split_name, keys in split_keys.items():
        frame[f"overlap_{split_name}"] = frame["translated_key"].isin(keys)

    rejection_columns = [
        "translation_blank",
        "translation_pii_pattern",
        "negation_mismatch",
        "length_ratio_rejected",
        "similarity_rejected",
        "duplicate_translation",
        "translation_label_conflict",
        "overlap_train",
        "overlap_validation",
        "overlap_test",
        "overlap_cross_domain",
    ]
    frame["automatic_quality_pass"] = ~frame[rejection_columns].any(axis=1)
    valid_pairs = set(
        frame.groupby("pair_id")["automatic_quality_pass"]
        .all()
        .loc[lambda values: values]
        .index
    )
    accepted = frame[frame["pair_id"].isin(valid_pairs)].copy()
    accepted = accepted.sample(frac=1.0, random_state=seed).reset_index(drop=True)
    accepted["source"] = "translated_en_reddit_cc0"
    accepted["weak_label"] = "translated_source_label"
    accepted["confidence"] = "auxiliary_weak"
    accepted["depression_score"] = np.nan
    accepted["matched_keywords"] = ""
    accepted["weight"] = 1.0
    accepted["annotation_round"] = "translated_en_vi_20260725"
    accepted["translation_method"] = "local_nllb_en_to_vi"
    accepted["translation_audit_status"] = "automatic_pass_human_audit_pending"

    report = {
        "translated_rows": int(len(frame)),
        "automatic_rejections_by_reason": {
            column: int(frame[column].sum()) for column in rejection_columns
        },
        "accepted_complete_pairs": int(len(valid_pairs)),
        "accepted_rows": int(len(accepted)),
        "accepted_label_distribution": {
            str(int(key)): int(value)
            for key, value in accepted["label"].value_counts().sort_index().items()
        },
        "cross_lingual_cosine": {
            "threshold": similarity_threshold,
            "min": float(frame["cross_lingual_cosine"].min()),
            "median": float(frame["cross_lingual_cosine"].median()),
            "mean": float(frame["cross_lingual_cosine"].mean()),
            "max": float(frame["cross_lingual_cosine"].max()),
        },
        "human_translation_audit": "pending; sample exported for human review",
    }
    return accepted, report


def merge_train(accepted: pd.DataFrame, output_dir: Path, seed: int) -> dict[str, object]:
    clean = pd.read_csv(PROJECT_DIR / "data" / "labeled" / "final_train.csv")
    augmented = pd.read_csv(
        PROJECT_DIR / "data" / "augmented_v2" / "final_train_augmented.csv"
    )
    base_columns = clean.columns.tolist()
    provenance_columns = [
        "pair_id",
        "source_text_sha256",
        "source_dataset",
        "source_revision",
        "source_license",
        "translation_model",
        "translation_model_revision",
        "translation_model_license",
        "translation_method",
        "translation_audit_status",
    ]
    auxiliary = accepted[base_columns + provenance_columns].copy()
    clean_combined = pd.concat([clean, auxiliary], ignore_index=True, sort=False)

    augmented_columns = augmented.columns.tolist()
    auxiliary_augmented = auxiliary.copy()
    for column in augmented_columns:
        if column not in auxiliary_augmented.columns:
            auxiliary_augmented[column] = np.nan
    augmented_combined = pd.concat(
        [augmented, auxiliary_augmented], ignore_index=True, sort=False
    )

    clean_path = output_dir / "final_train_translated_en_vi.csv"
    combined_path = output_dir / "final_train_augmented_translated_en_vi.csv"
    clean_combined.to_csv(clean_path, index=False)
    augmented_combined.to_csv(combined_path, index=False)

    audit_size = min(220, len(accepted))
    audit_sample = accepted.sample(n=audit_size, random_state=seed)[[
        "pair_id",
        "source_text_en",
        "comment_text",
        "source_has_negation",
        "translation_has_negation",
    ]].copy()
    audit_sample["human_fidelity"] = ""
    audit_sample["human_label_preserved"] = ""
    audit_sample["human_fluency"] = ""
    audit_sample["human_notes"] = ""
    audit_sample.to_csv(output_dir / "translation_human_audit_sample.csv", index=False)

    return {
        "clean_plus_translated": {
            "path": str(clean_path.relative_to(PROJECT_DIR)),
            "rows": int(len(clean_combined)),
            "labels": {
                str(int(key)): int(value)
                for key, value in clean_combined["label"].value_counts().sort_index().items()
            },
        },
        "augmented_plus_translated": {
            "path": str(combined_path.relative_to(PROJECT_DIR)),
            "rows": int(len(augmented_combined)),
            "labels": {
                str(int(key)): int(value)
                for key, value in augmented_combined["label"].value_counts().sort_index().items()
            },
        },
        "human_audit_sample_rows": audit_size,
    }


def main() -> dict[str, object]:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--per-class", type=int, default=1100)
    parser.add_argument("--seed", type=int, default=20260725)
    parser.add_argument("--max-source-chars", type=int, default=144)
    parser.add_argument("--batch-size", type=int, default=12)
    parser.add_argument("--similarity-threshold", type=float, default=0.45)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    source_file = args.output_dir / "source_reddit_depression_cleaned.csv"
    selected_file = args.output_dir / "source_english_selected.csv"
    progress_file = args.output_dir / "translation_progress.csv"
    accepted_file = args.output_dir / "translated_vi_accepted.csv"
    report_file = args.output_dir / "translated_data_integrity_report.json"

    download_source(source_file)
    source = pd.read_csv(source_file)
    selected, selection_report = select_length_matched_pairs(
        source,
        per_class=args.per_class,
        seed=args.seed,
        max_source_chars=args.max_source_chars,
    )
    selected.to_csv(selected_file, index=False)
    translated = translate_selected(selected, progress_file, batch_size=args.batch_size)
    accepted, translation_report = audit_translations(
        translated,
        similarity_threshold=args.similarity_threshold,
        seed=args.seed,
    )
    accepted.to_csv(accepted_file, index=False)
    merge_report = merge_train(accepted, args.output_dir, args.seed)

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "protocol": (
            "fixed licensed English source; balanced source-length-matched pairs; "
            "local machine translation; complete-pair automatic quality gate; train only"
        ),
        "source": {
            "dataset_id": SOURCE_DATASET_ID,
            "revision": SOURCE_REVISION,
            "license": SOURCE_LICENSE,
            "url": SOURCE_URL,
            "file_sha256": sha256_file(source_file),
            "label_caveat": "source/subreddit-derived weak labels; not expert or clinical diagnosis",
        },
        "translation": {
            "model_id": TRANSLATION_MODEL_ID,
            "revision": TRANSLATION_MODEL_REVISION,
            "license": TRANSLATION_MODEL_LICENSE,
            "execution": "local; no source text sent to an external translation API",
            "similarity_model": SIMILARITY_MODEL_ID,
            "similarity_model_revision": SIMILARITY_MODEL_REVISION,
            "similarity_model_license": SIMILARITY_MODEL_LICENSE,
        },
        "selection": selection_report,
        "quality_audit": translation_report,
        "merged_training_sets": merge_report,
        "integrity_pass": bool(len(accepted) > 0),
    }
    report_file.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return report


if __name__ == "__main__":
    main()
