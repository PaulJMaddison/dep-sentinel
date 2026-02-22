from __future__ import annotations

import os
from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass
from fnmatch import fnmatch
from pathlib import Path

from depaudit.model import Dependency, ScanResult
from depaudit.parsers.registry import discover_parsers

_DEFAULT_IGNORES = (
    ".git",
    "node_modules",
    ".venv",
    "venv",
    "target",
    "dist",
    "build",
    "bin",
    "obj",
    ".mypy_cache",
    ".ruff_cache",
    ".pytest_cache",
)


@dataclass(frozen=True)
class _IgnoreRule:
    pattern: str
    directory_only: bool
    negated: bool

    @classmethod
    def parse(cls, raw_line: str) -> _IgnoreRule | None:
        line = raw_line.strip()
        if not line or line.startswith("#"):
            return None

        negated = line.startswith("!")
        if negated:
            line = line[1:]
        directory_only = line.endswith("/")
        if directory_only:
            line = line[:-1]
        if not line:
            return None
        return cls(pattern=line, directory_only=directory_only, negated=negated)

    def matches(self, rel_posix: str, is_dir: bool) -> bool:
        pattern = self.pattern

        if self.directory_only:
            if "/" in pattern:
                if rel_posix == pattern or rel_posix.startswith(f"{pattern}/"):
                    return True
            parts = rel_posix.split("/")
            return any(fnmatch(part, pattern) for part in parts[:-1] if not is_dir) or any(
                fnmatch(part, pattern) for part in parts
            )

        if "/" in pattern:
            return fnmatch(rel_posix, pattern)

        parts = rel_posix.split("/")
        return any(fnmatch(part, pattern) for part in parts)


class RepoScanner:
    def __init__(self, repo_root: Path):
        self.repo_root = repo_root.resolve()
        self._rules = self._load_gitignore_rules()

    def collect_candidate_files(self) -> list[Path]:
        candidates: list[Path] = []
        for root, dirs, files in os.walk(self.repo_root, topdown=True):
            root_path = Path(root)
            rel_root = root_path.relative_to(self.repo_root)

            keep_dirs: list[str] = []
            for dirname in sorted(dirs):
                rel_dir = (rel_root / dirname).as_posix()
                if self._is_ignored(rel_dir, is_dir=True):
                    continue
                keep_dirs.append(dirname)
            dirs[:] = keep_dirs

            for filename in sorted(files):
                rel_file = (rel_root / filename).as_posix()
                if self._is_ignored(rel_file, is_dir=False):
                    continue
                candidates.append(root_path / filename)
        return candidates

    def scan(self, max_workers: int | None = None) -> ScanResult:
        files = self.collect_candidate_files()
        dependencies: list[Dependency] = []
        errors: list[str] = []
        package_roots: set[str] = set()

        parsers = discover_parsers()
        parse_jobs: list[tuple[int, str, object, Path]] = []
        for parser_index, parser in enumerate(parsers):
            parser_name = parser.__class__.__name__
            matches = sorted(parser.detect(files), key=lambda path: path.as_posix())
            for manifest in matches:
                package_roots.add(manifest.parent.relative_to(self.repo_root).as_posix() or ".")
                parse_jobs.append((parser_index, parser_name, parser, manifest))

        if parse_jobs:
            worker_count = max_workers if max_workers is not None else min(32, len(parse_jobs))
            future_map: dict[Future[list[Dependency]], tuple[int, str, Path]] = {}
            with ThreadPoolExecutor(max_workers=worker_count) as pool:
                for parser_index, parser_name, parser, manifest in parse_jobs:
                    future = pool.submit(parser.parse, manifest)
                    future_map[future] = (parser_index, parser_name, manifest)

                for future, (_, _parser_name, manifest) in sorted(
                    future_map.items(), key=lambda item: (item[1][0], item[1][2].as_posix())
                ):
                    try:
                        dependencies.extend(future.result())
                    except Exception as exc:  # pragma: no cover - explicit defensive behavior
                        rel_path = manifest.relative_to(self.repo_root).as_posix()
                        short_message = _short_error_message(exc)
                        errors.append(f"{rel_path}: {short_message}")

        return ScanResult.from_parts(
            repo_root=self.repo_root,
            dependencies=dependencies,
            errors=sorted(errors),
            stats={
                "files_scanned": len(files),
                "dependencies_found": len(dependencies),
                "parse_errors": len(errors),
                "package_roots": len(package_roots),
            },
        )

    def _load_gitignore_rules(self) -> list[_IgnoreRule]:
        rules = [
            _IgnoreRule(pattern=name, directory_only=True, negated=False)
            for name in _DEFAULT_IGNORES
        ]
        gitignore = self.repo_root / ".gitignore"
        if not gitignore.exists():
            return rules

        try:
            content = gitignore.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            return rules

        for line in content.splitlines():
            parsed = _IgnoreRule.parse(line)
            if parsed is not None:
                rules.append(parsed)
        return rules

    def _is_ignored(self, rel_posix: str, is_dir: bool) -> bool:
        ignored = False
        for rule in self._rules:
            if rule.matches(rel_posix, is_dir):
                ignored = not rule.negated
        return ignored


def scan_repo(repo_root: Path, max_workers: int | None = None) -> ScanResult:
    return RepoScanner(repo_root).scan(max_workers=max_workers)


def _short_error_message(exc: Exception) -> str:
    message = str(exc).strip().splitlines()[0] if str(exc).strip() else ""
    exc_name = exc.__class__.__name__
    if not message:
        return exc_name
    if message.startswith(exc_name):
        return message
    return f"{exc_name}: {message}"
