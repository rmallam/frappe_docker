#!/usr/bin/env python3
import argparse
import json
import os
import sys
import urllib.request
from typing import List, Set

def get_repos_from_org(org: str) -> List[str]:
    """Fetches all repository clone URLs from a GitHub organization."""
    repos = []
    page = 1
    while True:
        url = f"https://api.github.com/orgs/{org}/repos?page={page}&per_page=100"
        try:
            headers = {"Accept": "application/vnd.github.v3+json"}
            # Authenticate if GITHUB_TOKEN is present to avoid rate limits
            token = os.environ.get("GITHUB_TOKEN")
            if token:
                headers["Authorization"] = f"token {token}"
            
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req) as response:
                data = json.loads(response.read().decode())
                if not data:
                    break
                # Only include repos that look like Frappe apps (optional: check for hooks.py)
                for repo in data:
                    if not repo["archived"] and not repo["fork"]:
                        repos.append(repo["clone_url"])
                page += 1
        except Exception as e:
            print(f"Error fetching repos from org {org}: {e}", file=sys.stderr)
            break
    return repos

def main():
    parser = argparse.ArgumentParser(description="Discover and list Frappe app URLs.")
    parser.add_argument("--org", help="GitHub Organization to scan")
    parser.add_argument("--apps", help="Space-separated list of Git URLs or app names")
    
    args = parser.parse_args()
    
    all_apps: Set[str] = set()
    
    # 1. Process manual list
    if args.apps:
        # Split by space and clean
        manual_apps = [a.strip() for a in args.apps.split() if a.strip()]
        for app in manual_apps:
            # If it doesn't start with http/git, assume it's a standard Frappe app name
            # but usually it's better to provide the full URL for clarity
            if app.startswith(("http://", "https://", "git@")):
                all_apps.add(app)
            else:
                # Fallback for standard apps if needed, but get-app handles names too
                all_apps.add(app)
    
    # 2. Process GitHub Organization
    if args.org:
        org_apps = get_repos_from_org(args.org)
        all_apps.update(org_apps)
    
    # Output space-separated list for xargs
    if all_apps:
        print(" ".join(sorted(list(all_apps))))

if __name__ == "__main__":
    main()
