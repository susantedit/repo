"""
Rewrites all 2024 commits to use the correct GitHub email via git fast-export + fast-import.
"""
import subprocess
import os

REPO = os.path.dirname(os.path.abspath(__file__))
WRONG_EMAIL = b"user@example.com"
RIGHT_EMAIL = b"susantedit@gmail.com"
RIGHT_NAME  = b"susantedit"

def main():
    print("Exporting commit history...")
    export = subprocess.run(
        ["git", "fast-export", "--all"],
        cwd=REPO, capture_output=True
    )
    if export.returncode != 0:
        print("fast-export failed:", export.stderr.decode())
        return

    data = export.stdout

    # Replace wrong author/committer lines containing the placeholder email
    data = data.replace(
        b"author User <user@example.com>",
        b"author " + RIGHT_NAME + b" <" + RIGHT_EMAIL + b">"
    )
    data = data.replace(
        b"committer User <user@example.com>",
        b"committer " + RIGHT_NAME + b" <" + RIGHT_EMAIL + b">"
    )

    print("Importing corrected history...")
    # Delete existing refs so fast-import can rewrite them
    subprocess.run(["git", "update-ref", "-d", "refs/heads/main"], cwd=REPO, capture_output=True)

    imp = subprocess.run(
        ["git", "fast-import", "--force", "--quiet"],
        input=data, cwd=REPO, capture_output=True
    )
    if imp.returncode != 0:
        print("fast-import failed:", imp.stderr.decode())
        return

    # Reset working tree to new HEAD
    subprocess.run(["git", "reset", "--hard", "HEAD"], cwd=REPO, capture_output=True)
    subprocess.run(["git", "checkout", "main"], cwd=REPO, capture_output=True)
    subprocess.run(["git", "reset", "--hard", "HEAD"], cwd=REPO, capture_output=True)

    # Verify
    result = subprocess.run(
        ["git", "log", "--format=%ae"],
        cwd=REPO, capture_output=True, text=True
    )
    emails = set(result.stdout.strip().splitlines())
    print("Emails in repo now:", emails)

    if b"user@example.com".decode() not in emails:
        print("✅ All commits now use correct email!")
    else:
        print("⚠️  Some commits still have the old email.")

    print("\nForce-pushing to remote...")
    push = subprocess.run(
        ["git", "push", "--force"],
        cwd=REPO, capture_output=True, text=True
    )
    print(push.stdout)
    print(push.stderr)
    print("Done! GitHub should show contributions within a few minutes.")

if __name__ == "__main__":
    main()
