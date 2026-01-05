import argparse
import datetime
import tarfile
from pathlib import Path
import shutil


def parse_args():
    parser = argparse.ArgumentParser(description="Archive old evidence folders.")
    parser.add_argument("--days", type=int, default=60, help="Archive folders older than N days.")
    parser.add_argument(
        "--evidence-root",
        default="docs/evidence",
        help="Root folder containing dated evidence directories.",
    )
    parser.add_argument(
        "--archive-root",
        default="docs/archive",
        help="Root folder where archives are stored.",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    evidence_root = Path(args.evidence_root)
    archive_root = Path(args.archive_root)

    if not evidence_root.exists():
        print(f"Evidence root not found: {evidence_root}")
        return

    archive_root.mkdir(parents=True, exist_ok=True)
    cutoff = datetime.date.today() - datetime.timedelta(days=args.days)

    archived = []
    for item in sorted(evidence_root.iterdir()):
        if not item.is_dir():
            continue
        try:
            folder_date = datetime.date.fromisoformat(item.name)
        except ValueError:
            continue

        if folder_date >= cutoff:
            continue

        archive_path = archive_root / f"evidence-{item.name}.tar.gz"
        if archive_path.exists():
            print(f"Archive already exists, skipping: {archive_path}")
            continue

        with tarfile.open(archive_path, "w:gz") as tar:
            tar.add(item, arcname=item.name)

        if archive_path.exists() and archive_path.stat().st_size > 0:
            shutil.rmtree(item)
            archived.append((item.name, archive_path))
        else:
            print(f"Archive failed for {item}")

    if not archived:
        print("No evidence folders eligible for archiving.")
        return

    print("Archived evidence:")
    for name, path in archived:
        print(f"- {name} -> {path}")


if __name__ == "__main__":
    main()
