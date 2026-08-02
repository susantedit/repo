import os
import subprocess
from datetime import datetime, timedelta

TEXT = "HIRE ME !"
START_DATE = datetime(2024, 1, 7)
COMMITS_PER_DAY = 10  # darkest green on GitHub

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
FILENAME = "data.txt"

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

def make_commit(d):
    filepath = os.path.join(REPO, FILENAME)
    with open(filepath, "a") as f:
        f.write("Commit at " + d.isoformat() + "\n")
    subprocess.run(["git", "add", FILENAME], cwd=REPO, capture_output=True)
    env = os.environ.copy()
    ds = d.strftime("%Y-%m-%dT%H:%M:%S")
    env["GIT_AUTHOR_DATE"] = ds
    env["GIT_COMMITTER_DATE"] = ds
    subprocess.run(["git", "commit", "-m", "graph-greener!"], cwd=REPO, env=env, capture_output=True)

def main():
    dates = build_dates()
    total = len(dates)
    first = dates[0].strftime("%Y-%m-%d")
    last = dates[-1].strftime("%Y-%m-%d")
    print("Making " + str(total) + " commits for HIRE ME !")
    print("Date range: " + first + " -> " + last)
    print("Commits per day: " + str(COMMITS_PER_DAY) + " (darkest green)")
    print("")

    for i, d in enumerate(dates, 1):
        make_commit(d)
        if i % 100 == 0 or i == total:
            print("[" + str(i) + "/" + str(total) + "] committed " + d.strftime("%Y-%m-%d"))

    print("")
    print("Done! Force-pushing to remote...")
    subprocess.run(["git", "push", "--force"], cwd=REPO)
    print("All done! Check your GitHub contribution graph.")

if __name__ == "__main__":
    main()
