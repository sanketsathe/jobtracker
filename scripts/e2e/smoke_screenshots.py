import argparse
import datetime
import os
import subprocess
import sys
import time
from pathlib import Path
from urllib.error import URLError
from urllib.parse import urlparse
from urllib.request import urlopen

from playwright.sync_api import sync_playwright


def wait_for_server(url, timeout=20, server_proc=None):
    start = time.time()
    while time.time() - start < timeout:
        if server_proc and server_proc.poll() is not None:
            return False
        try:
            with urlopen(url, timeout=2) as response:
                if response.status < 500:
                    return True
        except URLError:
            time.sleep(0.5)
        except Exception:
            time.sleep(0.5)
    return False


def print_server_log_tail(log_path, lines=40):
    if not log_path.exists():
        return
    try:
        content = log_path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return
    if not content:
        return
    tail = content[-lines:]
    print("Server log tail:")
    for line in tail:
        print(line)


def relative_to_root(path, root):
    try:
        return path.relative_to(root)
    except ValueError:
        return path


def update_evidence_log(log_path, feature, out_dir, screenshot_paths, repo_root):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    out_dir_rel = relative_to_root(out_dir, repo_root)
    screenshot_rel_paths = [relative_to_root(path, repo_root) for path in screenshot_paths]

    if not log_path.exists():
        log_path.parent.mkdir(parents=True, exist_ok=True)
        log_path.write_text("# Evidence Log\n\n", encoding="utf-8")

    lines = [
        f"## Run {timestamp}",
        "",
        f"- Command: FEATURE={feature} make screenshot",
        f"- Output: {out_dir_rel}/",
        "- Screenshots:",
    ]
    lines.extend([f"  - {path}" for path in screenshot_rel_paths])
    lines.append("")

    with log_path.open("a", encoding="utf-8") as handle:
        handle.write("\n" + "\n".join(lines))


def main():
    parser = argparse.ArgumentParser(description="Capture smoke-test screenshots with Playwright.")
    parser.add_argument("--feature", required=True, help="Feature slug used for evidence folder names.")
    parser.add_argument(
        "--base-url",
        default="http://127.0.0.1:8001",
        help="Base URL for the local Django server.",
    )
    parser.add_argument(
        "--out-dir",
        default=None,
        help="Output directory for screenshots (defaults to docs/evidence/YYYY-MM-DD/<feature>/).",
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[2]
    today = datetime.date.today().isoformat()
    feature_slug = args.feature
    out_dir = Path(args.out_dir) if args.out_dir else repo_root / "docs" / "evidence" / today / feature_slug
    out_dir.mkdir(parents=True, exist_ok=True)

    parsed = urlparse(args.base_url)
    scheme = parsed.scheme or "http"
    host = parsed.hostname or "127.0.0.1"
    port = parsed.port or 8001
    base_url = f"{scheme}://{host}:{port}"
    login_url = f"{base_url}/accounts/login/"

    env = os.environ.copy()
    env.setdefault("DJANGO_SETTINGS_MODULE", "config.settings_e2e")
    env.setdefault("DJANGO_SECRET_KEY", "e2e-dev-secret")
    env.setdefault("E2E_USERNAME", "e2e")
    env.setdefault("E2E_PASSWORD", "e2e-pass")

    username = env["E2E_USERNAME"]
    password = env["E2E_PASSWORD"]
    settings_module = env["DJANGO_SETTINGS_MODULE"]

    subprocess.run(
        [sys.executable, "manage.py", "migrate", "--noinput", f"--settings={settings_module}"],
        check=True,
        cwd=repo_root,
        env=env,
    )
    subprocess.run(
        [sys.executable, "manage.py", "seed_e2e_user", f"--settings={settings_module}"],
        check=True,
        cwd=repo_root,
        env=env,
    )

    log_path = out_dir / "server.log"
    server_log = log_path.open("w", encoding="utf-8")
    server_proc = subprocess.Popen(
        [
            sys.executable,
            "manage.py",
            "runserver",
            f"{host}:{port}",
            "--noreload",
            f"--settings={settings_module}",
        ],
        cwd=repo_root,
        env=env,
        stdout=server_log,
        stderr=subprocess.STDOUT,
    )

    screenshot_paths = []
    evidence_log = repo_root / "docs" / "features" / feature_slug / "evidence.md"
    try:
        if not wait_for_server(login_url, timeout=25, server_proc=server_proc):
            server_log.flush()
            print_server_log_tail(log_path)
            raise RuntimeError("Django server did not become ready in time.")

        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            page = browser.new_page(viewport={"width": 1280, "height": 720})

            page.goto(login_url, wait_until="networkidle")
            login_path = out_dir / "01-login.png"
            page.screenshot(path=str(login_path), full_page=True)
            screenshot_paths.append(login_path)

            page.fill("input[name='username']", username)
            page.fill("input[name='password']", password)
            page.click("button[type='submit']")

            try:
                page.wait_for_url("**/applications/**", timeout=10000)
            except Exception:
                pass

            page.wait_for_selector("h1", timeout=5000)
            dashboard_path = out_dir / "02-dashboard.png"
            page.screenshot(path=str(dashboard_path), full_page=True)
            screenshot_paths.append(dashboard_path)

            page.goto(f"{base_url}/applications/new/", wait_until="networkidle")
            page.wait_for_selector("h1", timeout=5000)
            new_app_path = out_dir / "03-new-application.png"
            page.screenshot(path=str(new_app_path), full_page=True)
            screenshot_paths.append(new_app_path)

            browser.close()

        update_evidence_log(evidence_log, feature_slug, out_dir, screenshot_paths, repo_root)

    finally:
        server_proc.terminate()
        try:
            server_proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            server_proc.kill()
            server_proc.wait(timeout=5)
        server_log.close()

    print("Screenshots saved:")
    for path in screenshot_paths:
        print(f"- {relative_to_root(path, repo_root)}")
    print(f"Evidence log updated: {relative_to_root(evidence_log, repo_root)}")


if __name__ == "__main__":
    main()
