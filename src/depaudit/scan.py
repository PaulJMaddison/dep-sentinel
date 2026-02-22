from __future__ import annotations

from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass
from fnmatch import fnmatch
from pathlib import Path

from depaudit.model import Dependency, ScanResult
from depaudit.parsers.registry import discover_parsers

_DEFAULT_IGNORES = (
    ".git",
    "node_modules",
    "target",
    "bin",
    "obj",
    ".venv",
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
        for path in sorted(self.repo_root.rglob("*")):
            rel = path.relative_to(self.repo_root).as_posix()
            if self._is_ignored(rel, path.is_dir()):
                continue
            if path.is_file():
                candidates.append(path)
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

                for future, (_, parser_name, manifest) in sorted(
                    future_map.items(), key=lambda item: (item[1][0], item[1][2].as_posix())
                ):
                    try:
                        dependencies.extend(future.result())
                    except Exception as exc:  # pragma: no cover - explicit defensive behavior
                        rel_path = manifest.relative_to(self.repo_root).as_posix()
                        errors.append(f"{parser_name} failed to parse {rel_path}: {exc}")

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
        rules = [_IgnoreRule(pattern=name, directory_only=True, negated=False) for name in _DEFAULT_IGNORES]
        gitignore = self.repo_root / ".gitignore"
        if not gitignore.exists():
            return rules

        for line in gitignore.read_text(encoding="utf-8", errors="ignore").splitlines():
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
