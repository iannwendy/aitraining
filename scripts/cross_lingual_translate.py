#!/usr/bin/env python3
"""
Cross-lingual Translation Pipeline - NLLB-200 Translation

Downloads English Reddit depression data from HuggingFace, filters off-topic posts,
translates to Vietnamese using NLLB-200-600M, and adds metadata.

Dataset: ShreyaR/DepressionDetection
Columns: clean_text, is_depression (binary 0/1)
Output: data/translated/reddit_dep_en.csv (filtered English)
        data/translated/reddit_dep_translated.csv (English-Vietnamese pairs + metadata)
"""

import argparse
import hashlib
from datetime import datetime
from pathlib import Path

import pandas as pd
import torch
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
from tqdm import tqdm

# Configuration
HF_DATASET = "ShreyaR/DepressionDetection"
TRANSLATED_DIR = Path("data/translated")
OUTPUT_EN_PATH = TRANSLATED_DIR / "reddit_dep_en.csv"
OUTPUT_TRANSLATED_PATH = TRANSLATED_DIR / "reddit_dep_translated.csv"

# Off-topic keywords to exclude (case-insensitive)
OFF_TOPIC_KEYWORDS = [
    "minecraft", "fortnite", "gaming", "esports", "video game",
    "politics", "news", "election", "trump", "biden",
    "sports", "football", "basketball", "soccer"
]

# Global model instances (lazy loaded)
_tokenizer = None
_model = None


def is_off_topic(text: str) -> bool:
    """Check if text contains off-topic keywords."""
    if pd.isna(text):
        return True
    text_lower = str(text).lower()
    return any(keyword in text_lower for keyword in OFF_TOPIC_KEYWORDS)


def download_dataset():
    """Download dataset from HuggingFace using the datasets library."""
    print(f"Loading dataset from HuggingFace: {HF_DATASET}")

    from datasets import load_dataset

    # Load dataset from HuggingFace
    dataset = load_dataset(HF_DATASET, split="train")

    # Convert to pandas DataFrame
    df = dataset.to_pandas()
    print(f"Downloaded {len(df)} samples")
    print(f"Dataset columns: {df.columns.tolist()}")
    print(f"Label distribution before filtering:")
    if 'is_depression' in df.columns:
        print(df['is_depression'].value_counts())
    elif 'label' in df.columns:
        print(df['label'].value_counts())

    return df


def filter_dataset(df: pd.DataFrame) -> pd.DataFrame:
    """Filter out off-topic posts."""
    print(f"\nFiltering off-topic posts...")

    # Determine which column is the label
    if 'is_depression' in df.columns:
        label_col = 'is_depression'
        text_col = 'clean_text'
    elif 'label' in df.columns:
        label_col = 'label'
        text_col = 'text'
    else:
        raise ValueError(f"Could not find label column. Available: {df.columns.tolist()}")

    # Identify depression and normal posts
    depression_df = df[df[label_col] == 1].copy()
    normal_df = df[df[label_col] == 0].copy()

    print(f"  Depression posts (label=1): {len(depression_df)}")
    print(f"  Normal posts (label=0): {len(normal_df)}")

    # Filter off-topic from normal posts
    normal_off_topic = normal_df[normal_df[text_col].apply(is_off_topic)]
    normal_filtered = normal_df[~normal_df[text_col].apply(is_off_topic)]

    print(f"  Normal off-topic posts excluded: {len(normal_off_topic)}")
    print(f"  Normal posts after filtering: {len(normal_filtered)}")

    # Target: 2000-2500 total samples with ~2:1 normal:depression ratio
    # Target total: 2250 (middle of range) => depression ~750, normal ~1500
    TARGET_TOTAL = 2250
    target_depression_count = TARGET_TOTAL // 3  # ~750
    target_normal_count = target_depression_count * 2  # ~1500

    # Sample depression posts if we have more than target
    if len(depression_df) > target_depression_count:
        depression_filtered = depression_df.sample(n=target_depression_count, random_state=42)
        print(f"  Depression posts sampled to {len(depression_filtered)} for target total")
    else:
        depression_filtered = depression_df.copy()
        print(f"  Using all {len(depression_filtered)} depression posts")

    # Sample normal posts to achieve 2:1 ratio
    if len(normal_filtered) > target_normal_count:
        normal_sampled = normal_filtered.sample(n=target_normal_count, random_state=42)
        print(f"  Normal posts sampled to {len(normal_sampled)} for 2:1 ratio")
    else:
        normal_sampled = normal_filtered
        print(f"  Using all {len(normal_sampled)} normal posts")

    # Combine and create output format
    result_df = pd.concat([depression_filtered, normal_sampled], ignore_index=True)

    # Rename columns to output format (matching spec: clean_text, is_depression)
    result_df = result_df.rename(columns={
        text_col: 'clean_text',
        label_col: 'is_depression'
    })

    # Select only required columns
    result_df = result_df[['clean_text', 'is_depression']]

    # Shuffle
    result_df = result_df.sample(frac=1, random_state=42).reset_index(drop=True)

    return result_df


def get_device():
    """Detect available device."""
    if torch.cuda.is_available():
        return "cuda"
    elif torch.backends.mps.is_available():
        return "mps"
    return "cpu"


def load_nllb_model():
    """Load NLLB-200-distilled-600M model (publicly available)."""
    global _tokenizer, _model
    if _tokenizer is None:
        print("Loading NLLB-200-distilled-600M...")
        device = get_device()
        print(f"Using device: {device}")

        # Using distilled version which is publicly accessible
        _tokenizer = AutoTokenizer.from_pretrained("facebook/nllb-200-distilled-600M")
        _model = AutoModelForSeq2SeqLM.from_pretrained("facebook/nllb-200-distilled-600M")
        _model = _model.to(device)
        _model.eval()
        print("Model loaded!")
    return _tokenizer, _model, get_device()


def translate_batch(texts, tokenizer, model, device, batch_size=16, max_length=128):
    """Translate batch of texts from English to Vietnamese."""
    translations = []

    # Get the token ID for Vietnamese (Latin script)
    vie_token_id = tokenizer.convert_tokens_to_ids("vie_Latn")

    for i in tqdm(range(0, len(texts), batch_size), desc="Translating"):
        batch = texts[i:i+batch_size]
        inputs = tokenizer(batch, return_tensors="pt", truncation=True,
                          max_length=max_length, padding=True)
        inputs = {k: v.to(device) for k, v in inputs.items()}

        # Force Vietnamese as target language using forced_bos_token_id
        outputs = model.generate(
            **inputs,
            forced_bos_token_id=vie_token_id,
            max_length=max_length,
            num_beams=3,
            length_penalty=0.6
        )

        for output in outputs:
            translated = tokenizer.decode(output, skip_special_tokens=True)
            translations.append(translated)

    return translations


def translate_dataset(input_path: Path, output_path: Path):
    """Translate dataset and save with metadata."""
    df = pd.read_csv(input_path)
    print(f"Loaded {len(df)} samples from {input_path}")

    # Load model
    tokenizer, model, device = load_nllb_model()

    # Get original texts
    original_texts = df['clean_text'].tolist()

    # Translate
    print(f"Translating {len(df)} samples from English to Vietnamese...")
    translations = translate_batch(original_texts, tokenizer, model, device)

    # Create output dataframe with metadata
    result_df = pd.DataFrame()
    result_df['text'] = translations
    result_df['original_text'] = original_texts
    result_df['text_hash'] = df['clean_text'].apply(
        lambda x: hashlib.sha256(str(x).encode()).hexdigest()
    )
    result_df['translation_model'] = 'nllb-200-distilled-600M'
    result_df['translation_version'] = '1.0'
    result_df['translation_date'] = datetime.now().isoformat()
    result_df['is_machine_translated'] = True
    result_df['source_dataset'] = 'reddit_depression_kaggle'
    result_df['source_label'] = df['is_depression']
    result_df['label'] = df['is_depression']  # Keep label column

    # Save
    output_path.parent.mkdir(parents=True, exist_ok=True)
    result_df.to_csv(output_path, index=False)
    print(f"Saved translated dataset to {output_path}")

    return result_df


def main():
    """Main pipeline."""
    parser = argparse.ArgumentParser(description="Cross-lingual translation pipeline")
    parser.add_argument('--translate', action='store_true',
                        help='Run translation step (requires NLLB model)')
    parser.add_argument('--skip-download', action='store_true',
                        help='Skip download, use existing reddit_dep_en.csv')
    args = parser.parse_args()

    TRANSLATED_DIR.mkdir(parents=True, exist_ok=True)

    # Step 1: Download and filter (always run unless skipped)
    if not args.skip_download and not OUTPUT_EN_PATH.exists():
        print("=" * 60)
        print("Step 1: Downloading and Filtering Dataset")
        print("=" * 60)

        # Download
        df = download_dataset()

        # Filter
        filtered_df = filter_dataset(df)

        # Save English dataset
        filtered_df.to_csv(OUTPUT_EN_PATH, index=False)

        print(f"\n{'=' * 60}")
        print(f"Output saved to: {OUTPUT_EN_PATH}")
        print(f"Total samples: {len(filtered_df)}")
        print(f"Label distribution:")
        print(filtered_df['is_depression'].value_counts())
        print(f"{'=' * 60}")
    else:
        print(f"Using existing {OUTPUT_EN_PATH}")

    # Step 2: Translate to Vietnamese (if --translate flag is passed)
    if args.translate:
        print("\n" + "=" * 60)
        print("Step 2: Translating to Vietnamese (NLLB-200)")
        print("=" * 60)

        if not OUTPUT_EN_PATH.exists():
            print(f"Error: {OUTPUT_EN_PATH} not found. Run without --translate first.")
            return

        translate_dataset(OUTPUT_EN_PATH, OUTPUT_TRANSLATED_PATH)

        # Verify output
        print("\nVerification:")
        result_df = pd.read_csv(OUTPUT_TRANSLATED_PATH)
        print(f"  Rows: {len(result_df)}")
        print(f"  Columns: {result_df.columns.tolist()}")
        print("\nSample rows:")
        for i in range(min(3, len(result_df))):
            print(f"\n--- Sample {i+1} ---")
            print(f"English: {result_df['original_text'].iloc[i][:100]}...")
            print(f"Vietnamese: {result_df['text'].iloc[i][:100]}...")
    else:
        print("\nSkipping translation. Use --translate to run NLLB-200 translation.")


if __name__ == "__main__":
    main()
