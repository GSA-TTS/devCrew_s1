"""
Git Scanner for scanning commit history and branches.

Provides author attribution and historical secret detection.
"""

import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from .pattern_manager import PatternManager
from .secret_scanner import SecretFinding, SecretScanner


@dataclass
class CommitInfo:
    """Information about a git commit."""

    sha: str
    author_name: str
    author_email: str
    date: str
    message: str


@dataclass
class CommitScan:
    """Results of scanning a single commit."""

    commit: CommitInfo
    findings: List[SecretFinding] = field(default_factory=list)
    files_changed: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "commit": {
                "sha": self.commit.sha,
                "author_name": self.commit.author_name,
                "author_email": self.commit.author_email,
                "date": self.commit.date,
                "message": self.commit.message[:100],
            },
            "findings": [f.to_dict() for f in self.findings],
            "files_changed": self.files_changed,
        }


@dataclass
class BranchScan:
    """Results of scanning a branch."""

    branch_name: str
    commit_scans: List[CommitScan] = field(default_factory=list)
    total_commits: int = 0
    scan_timestamp: str = ""

    def __post_init__(self) -> None:
        """Set timestamp."""
        if not self.scan_timestamp:
            self.scan_timestamp = datetime.utcnow().isoformat()

    @property
    def total_findings(self) -> int:
        """Total findings across all commits."""
        return sum(len(cs.findings) for cs in self.commit_scans)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "branch_name": self.branch_name,
            "total_commits": self.total_commits,
            "total_findings": self.total_findings,
            "scan_timestamp": self.scan_timestamp,
            "commit_scans": [cs.to_dict() for cs in self.commit_scans if cs.findings],
        }


class GitScanner:
    """Scanner for git history."""

    def __init__(
        self,
        repo_path: str | Path,
        pattern_manager: Optional[PatternManager] = None,
    ) -> None:
        """Initialize git scanner."""
        self.repo_path = Path(repo_path)
        self.secret_scanner = SecretScanner(pattern_manager)
        self._validate_repo()

    def _validate_repo(self) -> None:
        """Validate that path is a git repository."""
        git_dir = self.repo_path / ".git"
        if not git_dir.exists():
            raise ValueError(f"Not a git repository: {self.repo_path}")

    def _run_git(self, args: List[str]) -> str:
        """Run a git command and return output."""
        cmd = ["git", "-C", str(self.repo_path)] + args
        result = subprocess.run(  # nosec B603 B607
            cmd,
            capture_output=True,
            text=True,
            timeout=60,
        )
        return result.stdout

    def get_commits(
        self,
        branch: Optional[str] = None,
        limit: int = 100,
        since: Optional[str] = None,
        until: Optional[str] = None,
    ) -> List[CommitInfo]:
        """Get list of commits."""
        args = [
            "log",
            "--format=%H|%an|%ae|%aI|%s",
            f"-{limit}",
        ]

        if branch:
            args.append(branch)

        if since:
            args.append(f"--since={since}")

        if until:
            args.append(f"--until={until}")

        output = self._run_git(args)
        commits = []

        for line in output.strip().split("\n"):
            if not line:
                continue
            parts = line.split("|", 4)
            if len(parts) >= 5:
                commits.append(
                    CommitInfo(
                        sha=parts[0],
                        author_name=parts[1],
                        author_email=parts[2],
                        date=parts[3],
                        message=parts[4],
                    )
                )

        return commits

    def get_commit_diff(self, sha: str) -> str:
        """Get the diff for a commit."""
        output = self._run_git(["show", "--no-color", sha])
        return output

    def get_commit_files(self, sha: str) -> List[str]:
        """Get list of files changed in a commit."""
        output = self._run_git(["show", "--name-only", "--format=", sha])
        return [f for f in output.strip().split("\n") if f]

    def get_file_at_commit(self, sha: str, file_path: str) -> Optional[str]:
        """Get file content at a specific commit."""
        try:
            output = self._run_git(["show", f"{sha}:{file_path}"])
            return output
        except subprocess.SubprocessError:
            return None

    def scan_commit(self, sha: str) -> CommitScan:
        """Scan a single commit for secrets."""
        # Get commit info
        output = self._run_git(
            ["log", "-1", "--format=%H|%an|%ae|%aI|%s", sha]
        )
        parts = output.strip().split("|", 4)
        commit = CommitInfo(
            sha=parts[0],
            author_name=parts[1],
            author_email=parts[2],
            date=parts[3],
            message=parts[4] if len(parts) > 4 else "",
        )

        # Get diff and scan
        diff = self.get_commit_diff(sha)
        files = self.get_commit_files(sha)

        findings = self.secret_scanner.scan_content(
            diff, f"commit:{sha}"
        )

        # Update file paths in findings
        for finding in findings:
            finding.file_path = f"commit:{sha}"

        return CommitScan(
            commit=commit,
            findings=findings,
            files_changed=files,
        )

    def scan_commits(
        self,
        commits: Optional[List[str]] = None,
        branch: Optional[str] = None,
        limit: int = 100,
    ) -> List[CommitScan]:
        """Scan multiple commits."""
        if commits:
            return [self.scan_commit(sha) for sha in commits]

        commit_infos = self.get_commits(branch=branch, limit=limit)
        return [self.scan_commit(c.sha) for c in commit_infos]

    def scan_branch(
        self,
        branch: str = "HEAD",
        limit: int = 100,
        since: Optional[str] = None,
    ) -> BranchScan:
        """Scan an entire branch for secrets."""
        commits = self.get_commits(branch=branch, limit=limit, since=since)

        commit_scans = []
        for commit in commits:
            scan = self.scan_commit(commit.sha)
            if scan.findings:
                commit_scans.append(scan)

        return BranchScan(
            branch_name=branch,
            commit_scans=commit_scans,
            total_commits=len(commits),
        )

    def get_branches(self) -> List[str]:
        """Get list of all branches."""
        output = self._run_git(["branch", "-a", "--format=%(refname:short)"])
        return [b.strip() for b in output.strip().split("\n") if b.strip()]

    def scan_all_branches(self, limit_per_branch: int = 50) -> Dict[str, BranchScan]:
        """Scan all branches."""
        branches = self.get_branches()
        results = {}

        for branch in branches:
            try:
                results[branch] = self.scan_branch(branch, limit=limit_per_branch)
            except Exception:
                continue

        return results

    def get_authors_with_secrets(
        self, branch_scan: BranchScan
    ) -> Dict[str, List[SecretFinding]]:
        """Group findings by author."""
        authors: Dict[str, List[SecretFinding]] = {}

        for commit_scan in branch_scan.commit_scans:
            author = commit_scan.commit.author_email
            if author not in authors:
                authors[author] = []
            authors[author].extend(commit_scan.findings)

        return authors

    def find_secret_introduction(
        self, file_path: str, pattern_name: str
    ) -> Optional[CommitInfo]:
        """Find the commit that introduced a secret."""
        # Get file history
        output = self._run_git(
            ["log", "--follow", "--format=%H|%an|%ae|%aI|%s", "--", file_path]
        )

        for line in output.strip().split("\n"):
            if not line:
                continue

            parts = line.split("|", 4)
            sha = parts[0]

            # Check if this commit introduced the secret
            content = self.get_file_at_commit(sha, file_path)
            if content:
                findings = self.secret_scanner.scan_content(content, file_path)
                if any(f.pattern_name == pattern_name for f in findings):
                    return CommitInfo(
                        sha=parts[0],
                        author_name=parts[1],
                        author_email=parts[2],
                        date=parts[3],
                        message=parts[4] if len(parts) > 4 else "",
                    )

        return None

    def blame_line(self, file_path: str, line_number: int) -> Optional[CommitInfo]:
        """Get commit info for a specific line."""
        try:
            output = self._run_git(
                ["blame", "-L", f"{line_number},{line_number}", "--porcelain", file_path]
            )
            lines = output.strip().split("\n")
            if lines:
                sha = lines[0].split()[0]
                # Get full commit info
                return self.get_commits(limit=1)[0] if sha else None
        except Exception:
            return None

        return None
