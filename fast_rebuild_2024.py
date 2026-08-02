"""
Uses git fast-import to create all 2024 "HIRE ME !" contribution commits
in one shot — much faster than individual git commit calls.
"""
import os
import subprocess
from datetime import datetime, timedelta

TEXT = "HIRE ME !"
START_DATE = datetime(2024, 1, 7)
COMMITS_PER_DAY = 10  # darkest green on GitHub requires 10+

FONT = {
    "H": ["#..#", "#..#", "####", "#..#", "#..#", "#..#", "#..#"],
    "I": ["####", "..#.", "..#.", "..#.", "..#.", "..#.", "####"],
    "R": ["###.", "#..#", "###.", "#.#.", "#..#", "#..#", "#..#"],
    "E": ["####", "#...", "###.", "#...", "#...", "#...", "####"],
    "M": ["#..#", "####", "#..#", "#..#", "#..#", "#..#", "#..#"],
    " ": ["....", "....", "....", "....", "....", "....", "...."],
    "!": [".#..", ".#..", ".#..", ".#..", ".#..", ".....", ".#.."],
}

REPO = os.path.dirname(os.path.abspath(__file__))


def build_dates():
    columns = []
    for ch in TEXT:
        columns.append(FONT[ch])
        columns.append(["...."] * 7)
    columns.pop()  # remove trailing spacer

    dates = []
    for ci, col in enumerate(columns):
        for ri, cell in enumerate(col):
            if "#" in cell:
                d = START_DATE + timedelta(weeks=ci, days=ri)
                dates.extend([d] * COMMITS_PER_DAY)
    return sorted(dates)


def get_current_head():
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=REPO, capture_output=True, text=True
    )
    return result.stdout.strip()


def get_current_data_txt_blob():
    """Get the current blob hash of data.txt from HEAD."""
    result = subprocess.run(
        ["git", "ls-tree", "HEAD", "data.txt"],
        cwd=REPO, capture_output=True, text=True
    )
    line = result.stdout.strip()
    if line:
        # format: "100644 blob <hash>\tdata.txt"
        return line.split()[2]
    return None


def main():
    dates = build_dates()
    total = len(dates)
    print(f"Building fast-import stream for {total} commits ({TEXT})...")
    print(f"Date range: {dates[0].strftime('%Y-%m-%d')} -> {dates[-1].strftime('%Y-%m-%d')}")
    print(f"Commits per day: {COMMITS_PER_DAY} (darkest green)")

    parent_sha = get_current_head()
    print(f"Parent commit: {parent_sha[:10]}")

    # Read current data.txt content so we can append to it
    data_txt_path = os.path.join(REPO, "data.txt")
    with open(data_txt_path, "rb") as f:
        base_content = f.read()

    # Build the fast-import stream
    # We accumulate the file content as we go
    content = base_content
    stream_parts = []

    for i, d in enumerate(dates):
        ts = int(d.timestamp())
        date_str = d.strftime("%Y-%m-%dT%H:%M:%S")
        line = ("Commit at " + date_str + "\n").encode()
        content = content + line

        blob_data = content
        blob_len = len(blob_data)

        stream_parts.append(f"blob\nmark :{i+1}\ndata {blob_len}\n")
        stream_parts.append(None)  # placeholder for binary data
        blob_bytes_list = [(i, blob_data)]

        commit_str = (
            f"commit refs/heads/main\n"
            f"author User <user@example.com> {ts} +0000\n"
            f"committer User <user@example.com> {ts} +0000\n"
            f"data 14\ngraph-greener!\n"
            f"from {parent_sha}\n"
            f"M 100644 :{i+1} data.txt\n\n"
        )
        parent_sha = f":{i+1+total}"  # will be resolved after import... need different approach

    # The above approach with mark references is complex.
    # Instead, let's build the entire stream at once properly.
    print("Generating fast-import stream...")

    stream = bytearray()
    mark = 1
    commit_marks = []
    content = base_content

    for i, d in enumerate(dates):
        ts = int(d.timestamp())
        date_str = d.strftime("%Y-%m-%dT%H:%M:%S")
        line = ("Commit at " + date_str + "\n").encode("utf-8")
        content = content + line
        blob_data = bytes(content)

        # blob
        blob_mark = mark
        mark += 1
        blob_header = f"blob\nmark :{blob_mark}\ndata {len(blob_data)}\n".encode()
        stream += blob_header
        stream += blob_data
        stream += b"\n"

        # commit
        commit_mark = mark
        mark += 1
        commit_marks.append(commit_mark)

        author_line = f"author User <user@example.com> {ts} +0000\n".encode()
        committer_line = f"committer User <user@example.com> {ts} +0000\n".encode()
        msg = b"graph-greener!"
        msg_len = len(msg)

        if i == 0:
            from_line = f"from {get_current_head()}\n".encode()
        else:
            from_line = f"from :{commit_marks[i-1]}\n".encode()

        commit_header = f"commit refs/heads/main\nmark :{commit_mark}\n".encode()
        stream += commit_header
        stream += author_line
        stream += committer_line
        stream += f"data {msg_len}\n".encode()
        stream += msg
        stream += b"\n"
        stream += from_line
        stream += f"M 100644 :{blob_mark} data.txt\n".encode()
        stream += b"\n"

        if (i + 1) % 100 == 0:
            print(f"  Stream built: {i+1}/{total}")

    print(f"Stream size: {len(stream) // 1024} KB")
    print("Running git fast-import...")

    proc = subprocess.run(
        ["git", "fast-import", "--force"],
        input=stream,
        cwd=REPO,
        capture_output=True
    )

    if proc.returncode != 0:
        print("ERROR:", proc.stderr.decode())
        return

    print(proc.stderr.decode())

    # Update working tree
    subprocess.run(["git", "checkout", "main", "--", "data.txt"], cwd=REPO, capture_output=True)
    subprocess.run(["git", "reset", "--hard", "HEAD"], cwd=REPO, capture_output=True)

    # Verify
    result = subprocess.run(
        ["git", "log", "--format=%ad", "--date=format:%Y-%m-%d"],
        cwd=REPO, capture_output=True, text=True
    )
    count_2024 = result.stdout.count("2024")
    print(f"2024 commits in log: {count_2024}")
    print(f"Expected: {total}")

    print("\nForce-pushing to remote...")
    push = subprocess.run(["git", "push", "--force"], cwd=REPO, capture_output=True, text=True)
    print(push.stdout)
    print(push.stderr)
    print("\nDone! Check your GitHub contribution graph for 2024.")


if __name__ == "__main__":
    main()
