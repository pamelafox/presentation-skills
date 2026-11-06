#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Post Q&A entries from markdown writeups as comments to a GitHub Discussion."""

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path


def parse_discussion_url(url: str) -> tuple[str, str, int]:
    """Parse a GitHub discussion URL to extract org, repo info, and discussion number.

    Handles both formats:
    - https://github.com/orgs/ORG/discussions/NUMBER
    - https://github.com/OWNER/REPO/discussions/NUMBER
    """
    # Org discussion pattern
    org_match = re.match(r"https://github\.com/orgs/([^/]+)/discussions/(\d+)", url)
    if org_match:
        org = org_match.group(1)
        number = int(org_match.group(2))
        # For org discussions, we need to find the .github repo or similar
        # The discussions repo is typically named after the org or is .github
        return org, "discussions", number

    # Repo discussion pattern
    repo_match = re.match(r"https://github\.com/([^/]+)/([^/]+)/discussions/(\d+)", url)
    if repo_match:
        owner = repo_match.group(1)
        repo = repo_match.group(2)
        number = int(repo_match.group(3))
        return owner, repo, number

    raise ValueError(f"Could not parse discussion URL: {url}")


def get_discussion_id(owner: str, repo: str, number: int) -> str:
    """Get the GraphQL node ID for a discussion."""
    query = """
    query($owner: String!, $repo: String!, $number: Int!) {
      repository(owner: $owner, name: $repo) {
        discussion(number: $number) {
          id
          title
        }
      }
    }
    """
    result = subprocess.run(
        [
            "gh",
            "api",
            "graphql",
            "-f",
            f"query={query}",
            "-f",
            f"owner={owner}",
            "-f",
            f"repo={repo}",
            "-F",
            f"number={number}",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    data = json.loads(result.stdout)
    discussion = data["data"]["repository"]["discussion"]
    print(f"Found discussion: {discussion['title']}")
    return discussion["id"]


def post_comment(discussion_id: str, body: str) -> str:
    """Post a comment to a discussion and return the comment URL."""
    mutation = """
    mutation($discussionId: ID!, $body: String!) {
      addDiscussionComment(input: {discussionId: $discussionId, body: $body}) {
        comment {
          url
        }
      }
    }
    """
    result = subprocess.run(
        [
            "gh",
            "api",
            "graphql",
            "-f",
            f"query={mutation}",
            "-f",
            f"discussionId={discussion_id}",
            "-f",
            f"body={body}",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    data = json.loads(result.stdout)
    return data["data"]["addDiscussionComment"]["comment"]["url"]


def parse_writeup(content: str) -> list[dict]:
    """Parse a writeup markdown file into Q&A sections.

    Returns a list of dicts with 'title' and 'body' keys.
    Each ## heading starts a new Q&A, and ### subheadings are included in the body.
    """
    sections = []
    current_section = None

    lines = content.split("\n")
    i = 0

    while i < len(lines):
        line = lines[i]

        # Skip the main title (# heading)
        if line.startswith("# ") and not line.startswith("## "):
            i += 1
            continue

        # New Q&A section
        if line.startswith("## "):
            # Save previous section if exists
            if current_section:
                current_section["body"] = current_section["body"].strip()
                if current_section["body"]:  # Only add if has content
                    sections.append(current_section)

            title = line[3:].strip()
            current_section = {"title": title, "body": ""}
            i += 1
            continue

        # Subsection - include in current section's body
        if line.startswith("### ") and current_section:
            current_section["body"] += f"\n**{line[4:].strip()}**\n"
            i += 1
            continue

        # Regular content - add to current section
        if current_section:
            current_section["body"] += line + "\n"

        i += 1

    # Don't forget the last section
    if current_section:
        current_section["body"] = current_section["body"].strip()
        if current_section["body"]:
            sections.append(current_section)

    return sections


def format_comment(date: str, title: str, body: str) -> str:
    """Format a Q&A as a discussion comment."""
    return f"**{date}: {title}**\n\n{body}"


def main():
    parser = argparse.ArgumentParser(
        description="Post Q&A entries from writeups to a GitHub Discussion"
    )
    parser.add_argument("writeup_path", help="Path to the markdown writeup file")
    parser.add_argument("discussion_url", help="GitHub discussion URL")
    parser.add_argument("date", help="Date string to prefix comments (e.g., 2026/01/06)")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Parse and display without posting",
    )
    args = parser.parse_args()

    # Read writeup
    writeup_path = Path(args.writeup_path)
    if not writeup_path.exists():
        print(f"Error: Writeup file not found: {writeup_path}", file=sys.stderr)
        sys.exit(1)

    content = writeup_path.read_text()
    sections = parse_writeup(content)

    if not sections:
        print("No Q&A sections found in writeup", file=sys.stderr)
        sys.exit(1)

    print(f"Found {len(sections)} Q&A sections")

    # Parse discussion URL
    owner, repo, number = parse_discussion_url(args.discussion_url)

    if args.dry_run:
        print("\n=== DRY RUN - Would post the following comments ===\n")
        for i, section in enumerate(sections, 1):
            comment = format_comment(args.date, section["title"], section["body"])
            print(f"--- Comment {i} ---")
            print(comment)
            print()
        return

    # Get discussion ID
    discussion_id = get_discussion_id(owner, repo, number)

    # Post each section as a comment
    for i, section in enumerate(sections, 1):
        comment = format_comment(args.date, section["title"], section["body"])
        print(f"Posting comment {i}/{len(sections)}: {section['title'][:50]}...")
        url = post_comment(discussion_id, comment)
        print(f"  Posted: {url}")

    print(f"\nDone! Posted {len(sections)} comments.")


if __name__ == "__main__":
    main()
