#!/usr/bin/env python3
"""GitHub fixture CLI: all mutations stay in a disposable local Git repository."""
import json
import os
import subprocess
import sys
from pathlib import Path


def main():
    root = Path(os.environ["MINERVA_FIXTURE_ROOT"]).resolve()
    location = root / ".git" / "fixture-github.json"
    state = json.loads(location.read_text()) if location.exists() else {"prs": [], "actions": []}
    args = sys.argv[1:]
    with (root / ".git/fixture-gh-calls.jsonl").open("a") as log:
        log.write(json.dumps(args) + "\n")
    def git(*values, cwd=None):
        return subprocess.run(["git", "-C", str(cwd or Path.cwd()), *values],
                              capture_output=True, text=True, check=True).stdout.strip()
    def save():
        location.write_text(json.dumps(state))
    def emit(value):
        if "--jq" in args or "-q" in args:
            # The shipped probes query scalar repo properties or branch lists.
            query = args[args.index("--jq" if "--jq" in args else "-q") + 1]
            if 'startswith("minerva/reconcile")' in query:
                print(json.dumps(next((p for p in value if p["headRefName"].startswith("minerva/reconcile")), None)))
            elif "headRefName" in query:
                print("\n".join(p["headRefName"] for p in value))
            elif "defaultBranchRef" in query:
                print("main")
            elif "hasIssuesEnabled" in query:
                print("false")
            elif "nameWithOwner" in query:
                print("fixture/project")
            elif query in {".state", ".number", ".url", ".autoMergeRequest"} and isinstance(value, dict):
                print(value[query[1:]] if value[query[1:]] is not None else "null")
            else:
                print("fixture: unsupported jq query " + query, file=sys.stderr)
                raise ValueError("unsupported fixture jq query")
        else:
            print(json.dumps(value))
    if args[:2] == ["auth", "status"]:
        return 0
    if args[:2] == ["repo", "view"]:
        emit({"nameWithOwner": "fixture/project", "hasIssuesEnabled": False,
              "defaultBranchRef": {"name": "main"}, "mergeCommitAllowed": True,
              "squashMergeAllowed": True, "rebaseMergeAllowed": True})
        return 0
    if args[:2] in (["issue", "list"], ["label", "list"]):
        emit([])
        return 0
    if args[:2] == ["pr", "list"]:
        prs = state["prs"]
        if "--state" in args and args[args.index("--state") + 1] != "all":
            requested = args[args.index("--state") + 1].upper()
            prs = [p for p in prs if p["state"] == requested]
        if "--head" in args:
            prs = [p for p in prs if p["headRefName"] == args[args.index("--head") + 1]]
        emit(prs)
        return 0
    branch = git("branch", "--show-current")
    if args[:2] == ["pr", "create"]:
        if any(p["headRefName"] == branch and p["state"] == "OPEN" for p in state["prs"]):
            print("fixture: duplicate open PR", file=sys.stderr)
            return 1
        number = len(state["prs"]) + 1
        pr = {"number": number, "url": f"https://example.invalid/fixture/pull/{number}",
              "state": "OPEN", "headRefName": branch, "mergedAt": None,
              "title": args[args.index("--title") + 1], "autoMergeRequest": None,
              "author": {"login": "fixture"}, "updatedAt": "2026-09-12T00:00:00Z"}
        state["prs"].append(pr)
        state["actions"].append({"action": "create", "branch": branch})
        save()
        print(pr["url"])
        return 0
    target = next((a for a in args[2:] if a.isdigit() or "pull/" in a), None)
    number = int(target.rsplit("/", 1)[-1]) if target else None
    pr = next((p for p in reversed(state["prs"]) if p["number"] == number), None) if number else None
    if not pr:
        pr = next((p for p in reversed(state["prs"]) if p["headRefName"] == branch), None)
    if not pr and args[:2] == ["pr", "view"] and len(args) > 2 and not args[2].startswith("-"):
        pr = next((p for p in reversed(state["prs"]) if p["headRefName"] == args[2]), None)
    if args[:2] == ["pr", "view"]:
        if not pr:
            return 1
        emit(pr)
        return 0
    if args[:2] == ["pr", "checks"]:
        if not pr:
            return 1
        bucket = os.environ.get("MINERVA_FIXTURE_CHECK_BUCKET", "pass")
        if "--json" in args:
            emit([{"name": "fixture-tests", "bucket": bucket,
                   "state": {"pass": "SUCCESS", "fail": "FAILURE", "pending": "QUEUED", "cancel": "CANCELLED"}.get(bucket, "UNKNOWN")}])
        return 0 if bucket == "pass" else 8 if bucket == "pending" else 1
    if args[:2] == ["run", "view"] and "--log-failed" in args:
        print("fixture-tests: AssertionError: addition must return a+b")
        return 0
    if args[:2] == ["pr", "merge"]:
        if not pr:
            return 1
        if os.environ.get("MINERVA_FIXTURE_CHECK_BUCKET", "pass") != "pass":
            print("fixture: refusing merge with non-green checks", file=sys.stderr)
            return 1
        if pr["state"] == "MERGED":
            return 0
        git("merge", "--ff-only", pr["headRefName"], cwd=root)
        git("push", "origin", "main", cwd=root)
        pr.update(state="MERGED", mergedAt="2026-09-12T00:00:00Z", autoMergeRequest={"enabled": True})
        state["actions"].append({"action": "merge", "branch": pr["headRefName"]})
        save()
        return 0
    if args[:2] == ["pr", "diff"]:
        print(git("diff", "main..." + (pr["headRefName"] if pr else branch)))
        return 0
    print(f"fixture: unsupported gh command {args}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
