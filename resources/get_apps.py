#!/usr/bin/env python3
import argparse
import json
import os
import sys
import urllib.request
from typing import List, Set

def normalize_url(url: str) -> str:
    """Normalizes a git URL for comparison by stripping whitespace, trailing slashes, and .git extensions."""
    if not url:
        return ""
    url = url.strip().lower()
    if url.endswith("/"):
        url = url[:-1]
    if url.endswith(".git"):
        url = url[:-4]
    return url

def get_repos_from_org(org: str) -> List[str]:
    """Fetches all repository clone URLs from a GitHub organization with basic error handling."""
    repos = []
    if not org:
        return repos
    
    page = 1
    while True:
        url = f"https://api.github.com/orgs/{org}/repos?page={page}&per_page=100"
        try:
            headers = {"Accept": "application/vnd.github.v3+json"}
            # Use GITHUB_TOKEN or GH_BUILD_KEY for authentication
            token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_BUILD_KEY")
            if token:
                headers["Authorization"] = f"token {token}"
            
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req) as response:
                if response.status != 200:
                    break
                data = json.loads(response.read().decode())
                if not data:
                    break
                for repo in data:
                    # Filter for active Frappe-like repositories (primitive check)
                    if not repo["archived"] and not repo["disabled"]:
                        repos.append(repo["clone_url"])
                page += 1
        except Exception as e:
            print(f"Error fetching repos from org {org} (Page {page}): {e}", file=sys.stderr)
            break
    return repos

def main():
    parser = argparse.ArgumentParser(description="Discover and list Frappe app URLs uniquely.")
    parser.add_argument("--org", help="GitHub Organization to scan")
    parser.add_argument("--apps", help="Space-separated list of Git URLs or app names")
    
    args = parser.parse_args()
    
    seen_normalized: Set[str] = set()
    output_apps: List[str] = []
    
    def process_app(app_input: str):
        if not app_input:
            return
        # If it looks like a URL, normalize and add
        if "github.com" in app_input or "gitlab.com" in app_input or app_input.startswith(("http", "git@")):
            norm = normalize_url(app_input)
            if norm and norm not in seen_normalized:
                seen_normalized.add(norm)
                output_apps.append(app_input)
        else:
            # It's an app name (e.g. 'erpnext'). Add it if not seen.
            norm = app_input.strip().lower()
            if norm and norm not in seen_normalized:
                seen_normalized.add(norm)
                output_apps.append(app_input)

    # 1. Process Organization first (if provided)
    if args.org:
        for repo_url in get_repos_from_org(args.org):
            process_app(repo_url)
    
    # 2. Process Manual List (overrides/augments org)
    if args.apps:
        for app in args.apps.split():
            process_app(app)
    
    # Final output: space-separated list of unique strings
    if output_apps:
        print(" ".join(output_apps))

if __name__ == "__main__":
    main()
