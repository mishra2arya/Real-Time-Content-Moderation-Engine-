"""Dataset ingestion, preprocessing, stratified splitting, and statistics generation.

Supports ingesting real large-scale datasets (such as 200K+ Jigsaw/Civil Comments CSV/JSONL files)
or generating a comprehensive representative curation across all moderation policy categories.
Zero heavy dependencies (uses standard library csv, json, random, math).
"""

import argparse
import csv
import json
import os
import random
import sys
from typing import Dict, List, Tuple

# Ensure repository root is on sys.path
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from app.moderation.preprocessing import clean_text


def generate_curated_examples() -> List[Dict[str, any]]:
    """Generate a rich, balanced curated dataset covering diverse moderation categories and edge cases."""
    toxic_templates = [
        # Threats
        ("I will hunt you down and destroy you", 1, "threat"),
        ("I'm going to find your house and beat you up", 1, "threat"),
        ("You deserve to be shot and killed", 1, "threat"),
        ("I will put a bullet in your head if you speak again", 1, "threat"),
        ("Someone needs to eliminate you from this earth", 1, "threat"),
        ("I'll break your neck if I ever see you", 1, "threat"),
        ("Watch your back, your days are numbered", 1, "threat"),
        ("I am going to murder your entire family", 1, "threat"),
        # Severe Toxicity
        ("Go kill yourself right now nobody cares about you", 1, "severe_toxicity"),
        ("Drop dead and burn in hell forever", 1, "severe_toxicity"),
        ("You are a waste of oxygen, just go die", 1, "severe_toxicity"),
        ("I hope you suffer and die a painful death", 1, "severe_toxicity"),
        ("Do the world a favor and jump off a bridge", 1, "severe_toxicity"),
        (
            "You should drown yourself you miserable piece of filth",
            1,
            "severe_toxicity",
        ),
        # Identity Attack
        (
            "All people from your country are filthy vermin and thieves",
            1,
            "identity_attack",
        ),
        ("Your religion is pure cancer and should be eradicated", 1, "identity_attack"),
        ("Subhumans like you don't deserve human rights", 1, "identity_attack"),
        (
            "Go back to where you came from, we don't want your kind here",
            1,
            "identity_attack",
        ),
        (
            "People of your race are genetically inferior degenerates",
            1,
            "identity_attack",
        ),
        (
            "You disgusting minority scum should get out of our community",
            1,
            "identity_attack",
        ),
        # Insults & Harassment
        ("You are the most pathetic clown I have ever seen", 1, "insult"),
        ("Nobody loves you, you stupid worthless idiot", 1, "insult"),
        ("You have the brain of an absolute moron, shut up", 1, "insult"),
        ("You absolute imbecile, your opinion is completely trash", 1, "insult"),
        ("You are an ugly, repulsive loser with zero future", 1, "insult"),
        ("Shut your disgusting mouth you illiterate freak", 1, "insult"),
        ("Why are you so dumb? You are an embarrassment to humanity", 1, "insult"),
        ("Get lost you toxic piece of garbage", 1, "insult"),
        # Obfuscated / Leetspeak attacks
        ("y0u are a c0mplete 1d10t and a l0ser", 1, "insult"),
        ("1 w!ll f!nd y0u and destr0y y0u", 1, "threat"),
        ("g0 d!e y0u st00pid pers0n", 1, "severe_toxicity"),
        ("u absolute sh!thead moron", 1, "insult"),
        ("I h4te everything about you, disgusting trash", 1, "insult"),
    ]

    benign_templates = [
        # Normal conversation & greetings
        ("Hello! How are you doing today? Hope you have a great week!", 0, "benign"),
        (
            "Good morning everyone! Looking forward to collaborating on this project.",
            0,
            "benign",
        ),
        ("Thank you so much for your assistance, I truly appreciate it.", 0, "benign"),
        (
            "Can anyone recommend a good book or documentary on modern history?",
            0,
            "benign",
        ),
        ("The weather today is absolutely beautiful and sunny outside.", 0, "benign"),
        ("Congratulations on your graduation and new job offer!", 0, "benign"),
        ("What is the best recipe for homemade chocolate chip cookies?", 0, "benign"),
        (
            "I really enjoyed reading this article, very informative and well written.",
            0,
            "benign",
        ),
        (
            "Happy birthday! May all your dreams and wishes come true this year.",
            0,
            "benign",
        ),
        (
            "Let's schedule a brief follow-up call to review the quarterly roadmap.",
            0,
            "benign",
        ),
        # Technical & Computing discourse (containing trigger words used benignly)
        ("Please kill the background process using kill -9 on Linux.", 0, "benign"),
        (
            "We need to terminate the thread before executing the shutdown hook.",
            0,
            "benign",
        ),
        (
            "The execution of this algorithm takes approximately 48 milliseconds.",
            0,
            "benign",
        ),
        (
            "Let's drop the staging database table before running database migrations.",
            0,
            "benign",
        ),
        (
            "The garbage collector will clean up unreferenced memory objects.",
            0,
            "benign",
        ),
        (
            "Make sure to kill all dangling container instances after test completion.",
            0,
            "benign",
        ),
        (
            "We should destroy the staging cluster to save infrastructure cloud costs.",
            0,
            "benign",
        ),
        (
            "The crash dump file was generated after the memory segmentation fault.",
            0,
            "benign",
        ),
        # Colloquial slang / Gaming (apparent trigger words used positively)
        ("That guitar solo was absolutely sick! Incredible performance!", 0, "benign"),
        ("You completely killed it on stage tonight, outstanding show!", 0, "benign"),
        (
            "This game is insanely addictive, our team is dominating the lobby.",
            0,
            "benign",
        ),
        ("The movie villain was super wicked and had fantastic acting.", 0, "benign"),
        (
            "We crushed our sales targets this quarter thanks to everyone's dedication.",
            0,
            "benign",
        ),
        # Heated but civil debate / constructive critique
        (
            "I strongly disagree with your policy proposal, here is the economic data.",
            0,
            "benign",
        ),
        (
            "This argument lacks empirical evidence and suffers from circular logic.",
            0,
            "benign",
        ),
        (
            "While I understand your perspective, the latest study contradicts that conclusion.",
            0,
            "benign",
        ),
        (
            "The product design has several critical flaws that need immediate attention.",
            0,
            "benign",
        ),
        (
            "Your methodology has serious sampling bias that invalidates the results.",
            0,
            "benign",
        ),
        (
            "We must hold politicians accountable for budgetary mismanagement.",
            0,
            "benign",
        ),
    ]

    records: List[Dict[str, any]] = []

    prefixes = [
        "",
        "Honestly, ",
        "In my opinion, ",
        "Look, ",
        "To be fair, ",
        "I just wanted to say that ",
        "Everyone knows that ",
        "Listen here: ",
        "Actually, ",
        "By the way, ",
    ]
    suffixes = [
        "",
        ".",
        "!",
        "...",
        "!!",
        " - that is all.",
        " #truth",
        " IMO.",
        " have some respect.",
        " what do you think?",
    ]

    for text, label, category in toxic_templates:
        for p in prefixes:
            for s in suffixes[:4]:
                sample = f"{p}{text}{s}".strip()
                records.append({"text": sample, "label": label, "category": category})

    for text, label, category in benign_templates:
        for p in prefixes:
            for s in suffixes[:4]:
                sample = f"{p}{text}{s}".strip()
                records.append({"text": sample, "label": label, "category": category})

    random.seed(42)
    random.shuffle(records)
    return records


def stratified_split(
    records: List[Dict[str, any]],
    test_size: float = 0.15,
    val_size: float = 0.15,
    seed: int = 42,
) -> Tuple[List[Dict[str, any]], List[Dict[str, any]], List[Dict[str, any]]]:
    """Perform deterministic stratified split across binary labels."""
    random.seed(seed)
    positives = [r for r in records if r["label"] == 1]
    negatives = [r for r in records if r["label"] == 0]

    random.shuffle(positives)
    random.shuffle(negatives)

    def split_group(items: List[Dict]) -> Tuple[List[Dict], List[Dict], List[Dict]]:
        n = len(items)
        n_test = int(round(n * test_size))
        n_val = int(round(n * val_size))
        test = items[:n_test]
        val = items[n_test : n_test + n_val]
        train = items[n_test + n_val :]
        return train, val, test

    pos_train, pos_val, pos_test = split_group(positives)
    neg_train, neg_val, neg_test = split_group(negatives)

    train = pos_train + neg_train
    val = pos_val + neg_val
    test = pos_test + neg_test

    random.shuffle(train)
    random.shuffle(val)
    random.shuffle(test)

    return train, val, test


def prepare_dataset(
    input_file: str = None,
    output_dir: str = "data/processed",
    test_size: float = 0.15,
    val_size: float = 0.15,
    seed: int = 42,
    text_col: str = "text",
    label_col: str = "label",
) -> Tuple[List[Dict], List[Dict], List[Dict], Dict]:
    """Ingest, clean, split dataset, and calculate comprehensive metrics."""
    os.makedirs(output_dir, exist_ok=True)
    random.seed(seed)

    raw_records: List[Dict[str, any]] = []

    if input_file and os.path.exists(input_file):
        print(f"Ingesting external dataset from {input_file}...")
        if input_file.endswith(".jsonl"):
            with open(input_file, "r", encoding="utf-8") as fp:
                for line in fp:
                    if line.strip():
                        raw_records.append(json.loads(line))
        else:
            with open(input_file, "r", encoding="utf-8") as fp:
                reader = csv.DictReader(fp)
                for row in reader:
                    raw_records.append(row)
        print(f"Loaded {len(raw_records):,} raw records from file.")
    else:
        print("No external dataset provided. Generating curated moderation dataset...")
        raw_records = generate_curated_examples()
        print(f"Generated {len(raw_records):,} curated examples.")

    raw_count = len(raw_records)

    # 1. Cleaning & Deduplication
    seen_texts = set()
    cleaned_records: List[Dict[str, any]] = []
    duplicate_count = 0

    for r in raw_records:
        raw_text = r.get(text_col, r.get("cleaned_text", ""))
        label_val = r.get(label_col, 0)
        try:
            label = 1 if int(float(label_val)) > 0 else 0
        except (ValueError, TypeError):
            label = 0

        clean = clean_text(str(raw_text))
        if not clean:
            continue

        if clean in seen_texts:
            duplicate_count += 1
            continue

        seen_texts.add(clean)
        cleaned_records.append(
            {
                "cleaned_text": clean,
                "label": label,
                "category": r.get("category", "toxic" if label == 1 else "benign"),
            }
        )

    total_clean = len(cleaned_records)

    # 2. Length statistics
    char_lens = [len(r["cleaned_text"]) for r in cleaned_records]
    word_lens = [len(r["cleaned_text"].split()) for r in cleaned_records]

    char_lens.sort()
    word_lens.sort()

    p95_idx = int(0.95 * len(char_lens)) if char_lens else 0
    p95_char = char_lens[p95_idx] if char_lens else 0
    max_char = char_lens[-1] if char_lens else 0
    avg_char = sum(char_lens) / len(char_lens) if char_lens else 0.0

    p95_word_idx = int(0.95 * len(word_lens)) if word_lens else 0
    p95_word = word_lens[p95_word_idx] if word_lens else 0
    max_word = word_lens[-1] if word_lens else 0
    avg_word = sum(word_lens) / len(word_lens) if word_lens else 0.0

    # 3. Stratified Split
    train, val, test = stratified_split(
        cleaned_records,
        test_size=test_size,
        val_size=val_size,
        seed=seed,
    )

    # 4. Save to CSV
    def save_csv(path: str, rows: List[Dict]):
        with open(path, "w", newline="", encoding="utf-8") as fp:
            writer = csv.DictWriter(
                fp, fieldnames=["cleaned_text", "label", "category"]
            )
            writer.writeheader()
            writer.writerows(rows)

    train_path = os.path.join(output_dir, "train.csv")
    val_path = os.path.join(output_dir, "val.csv")
    test_path = os.path.join(output_dir, "test.csv")

    save_csv(train_path, train)
    save_csv(val_path, val)
    save_csv(test_path, test)

    # 5. Class Distribution
    toxic_count = sum(1 for r in cleaned_records if r["label"] == 1)
    non_toxic_count = sum(1 for r in cleaned_records if r["label"] == 0)

    stats = {
        "total_raw_examples": int(raw_count),
        "total_clean_examples": int(total_clean),
        "training_examples": int(len(train)),
        "validation_examples": int(len(val)),
        "test_examples": int(len(test)),
        "duplicate_count": int(duplicate_count),
        "number_of_labels": 2,
        "class_distribution": {
            "non_toxic (0)": int(non_toxic_count),
            "toxic (1)": int(toxic_count),
        },
        "avg_char_length": float(round(avg_char, 2)),
        "p95_char_length": int(p95_char),
        "max_char_length": int(max_char),
        "avg_word_length": float(round(avg_word, 2)),
        "p95_word_length": int(p95_word),
        "max_word_length": int(max_word),
        "seed": seed,
    }

    stats_path = os.path.join(output_dir, "dataset_stats.json")
    with open(stats_path, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2)

    # Print summary report
    print("\n" + "=" * 55)
    print("DATASET PREPARATION STATISTICS REPORT")
    print("=" * 55)
    print(f"Total raw examples:       {stats['total_raw_examples']:,}")
    print(f"Duplicate count:          {stats['duplicate_count']:,}")
    print(f"Total clean examples:     {stats['total_clean_examples']:,}")
    print(f"Training examples:        {stats['training_examples']:,} (70%)")
    print(f"Validation examples:      {stats['validation_examples']:,} (15%)")
    print(f"Test examples:            {stats['test_examples']:,} (15%)")
    print(f"Number of labels:         {stats['number_of_labels']}")
    print(f"Class distribution:       {stats['class_distribution']}")
    print(f"Average character length: {stats['avg_char_length']}")
    print(f"P95 character length:     {stats['p95_char_length']}")
    print(f"Max character length:     {stats['max_char_length']}")
    print(f"Average word length:      {stats['avg_word_length']}")
    print(f"P95 word length:          {stats['p95_word_length']}")
    print(f"Max word length:          {stats['max_word_length']}")
    print(f"Stats saved to:           {stats_path}")
    print("=" * 55 + "\n")

    return train, val, test, stats


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Prepare dataset for moderation training."
    )
    parser.add_argument(
        "--input", type=str, default=None, help="Input CSV or JSONL file."
    )
    parser.add_argument(
        "--output_dir", type=str, default="data/processed", help="Output directory."
    )
    parser.add_argument("--seed", type=int, default=42, help="Random seed.")
    args = parser.parse_args()

    prepare_dataset(input_file=args.input, output_dir=args.output_dir, seed=args.seed)
