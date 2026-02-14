import os
import sys
import subprocess
from datetime import datetime
from dotenv import load_dotenv

# Set encoding for Windows console
sys.stdout.reconfigure(encoding='utf-8')

# Load environment variables (Project root)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, "../.env"))

GIT_EXECUTABLE = os.getenv("GIT_EXECUTABLE", "git")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPO_URL = os.getenv("GITHUB_REPO_URL")

def run_git(args):
    """Runs a git command."""
    cmd = [GIT_EXECUTABLE] + args
    try:
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8'
        )
        if result.returncode != 0:
            print(f"Error running git {' '.join(args)}: {result.stderr}")
            return False
        return True
    except Exception as e:
        print(f"Exception running git: {e}")
        return False

def deploy():
    print("🚀 Starting deployment...")
    
    # 1. Check status
    print("Checking status...")
    if not run_git(["status"]):
        return

    # 2. Add changes
    print("Adding changes...")
    if not run_git(["add", "."]):
        return

    # 3. Commit
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    message = f"Auto-deploy: {timestamp}"
    print(f"Committing with message: {message}")
    if not run_git(["commit", "-m", message]):
        print("Commit failed (maybe nothing to commit?)")
        # Continue anyway to try push if there are unpushed commits
    
    # 4. Push
    print("Pushing to remote...")
    # Construct URL with token if available
    push_url = GITHUB_REPO_URL
    if GITHUB_TOKEN and GITHUB_REPO_URL.startswith("https://"):
        push_url = GITHUB_REPO_URL.replace("https://", f"https://{GITHUB_TOKEN}@")
    
    # sensitive: don't print the URL with token
    
    # We use subprocess directly here to avoid printing the token in run_git error logs if we were to modify it
    cmd = [GIT_EXECUTABLE, "push", push_url, "main"]
    try:
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8'
        )
        if result.returncode == 0:
            print("✅ Push successful!")
        else:
            print(f"❌ Push failed: {result.stderr}")
            # fallback to master?
            if "src refspec main does not match" in result.stderr:
                 print("Trying master branch...")
                 cmd = [GIT_EXECUTABLE, "push", push_url, "master"]
                 subprocess.run(cmd)

    except Exception as e:
        print(f"Exception during push: {e}")

if __name__ == "__main__":
    deploy()
