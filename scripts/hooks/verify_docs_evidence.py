import os
import subprocess
import sys
from pathlib import Path

UI_PATHS = (
    "templates/",
    "tracker/templates/",
    "static/",
    "tracker/static/",
)

REQUIRED_PROCESS_DOCS = (
    Path("docs/PROCESS/Definition_of_Done.md"),
    Path("docs/PROCESS/Codex_Delivery_Protocol.md"),
    Path("docs/PROCESS/Evidence_Standards.md"),
)


def get_changed_files(staged=True):
    cmd = ["git", "diff", "--name-only"]
    if staged:
        cmd.insert(2, "--cached")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        return []
    files = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    return files


def is_ui_file(path):
    normalized = path.replace("\\", "/")
    return any(normalized.startswith(prefix) for prefix in UI_PATHS)


def is_evidence_file(path):
    normalized = path.replace("\\", "/")
    if normalized.startswith("docs/evidence/"):
        return True
    if normalized.startswith("docs/features/") and normalized.endswith("/evidence.md"):
        return True
    return False


def main():
    if os.getenv("SKIP_DOCS_EVIDENCE_CHECK") == "1":
        print("Skipping docs/evidence check (SKIP_DOCS_EVIDENCE_CHECK=1).")
        return 0

    missing = [path for path in REQUIRED_PROCESS_DOCS if not path.exists()]
    if missing:
        print("Required process docs are missing:")
        for path in missing:
            print(f"- {path}")
        return 1

    changed_files = get_changed_files(staged=True)
    if not changed_files:
        changed_files = get_changed_files(staged=False)

    ui_changes = [path for path in changed_files if is_ui_file(path)]
    if not ui_changes:
        return 0

    evidence_changes = [path for path in changed_files if is_evidence_file(path)]
    if evidence_changes:
        return 0

    print("UI-related files changed without evidence updates.")
    print("Add one of the following before committing:")
    print("- A screenshot under docs/evidence/YYYY-MM-DD/<feature>/")
    print("- An update to docs/features/<feature>/evidence.md")
    print("To bypass once: SKIP_DOCS_EVIDENCE_CHECK=1 git commit ...")
    return 1


if __name__ == "__main__":
    sys.exit(main())
