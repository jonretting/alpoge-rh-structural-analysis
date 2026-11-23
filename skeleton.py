#!/usr/bin/env python3
# Author:  Jonathan Michael Retting
# License: CC-BY-4.0 (https://creativecommons.org/licenses/by/4.0/)
"""
Dependency analysis of the Alpoge RH proof.
Parses import statements from all .lean files, builds a DAG,
traces the transitive closure from Main.lean, and reports structure.

Usage:
    python skeleton.py /path/to/proof/src
    python skeleton.py /path/to/proof/src --json output.json
"""
import os
import sys
import json
from collections import defaultdict, deque
from pathlib import Path


def parse_imports(filepath):
    """Extract import statements from a .lean file."""
    imports = []
    try:
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            for line in f:
                line = line.strip()
                if line.startswith('import '):
                    mod = line[7:].strip()
                    if mod:
                        imports.append(mod)
                elif line and not line.startswith('--') and not line.startswith('#') and not line.startswith('/-'):
                    if not line.startswith('open') and not line.startswith('set_option'):
                        break
    except Exception:
        pass
    return imports


def main():
    if len(sys.argv) < 2:
        print("Usage: python skeleton.py /path/to/proof/src [--json output.json]")
        sys.exit(1)

    root = Path(sys.argv[1])
    json_out = None
    if '--json' in sys.argv:
        idx = sys.argv.index('--json')
        if idx + 1 < len(sys.argv):
            json_out = sys.argv[idx + 1]

    if not root.exists():
        print(f"Error: {root} does not exist")
        sys.exit(1)

    # Phase 1: Parse all .lean files
    print(f"Parsing .lean files in {root} ...")
    graph = {}
    file_lines = {}
    file_sizes = {}

    for dirpath, dirnames, filenames in os.walk(root):
        for fn in filenames:
            if not fn.endswith('.lean'):
                continue
            fp = os.path.join(dirpath, fn)
            rel = os.path.relpath(fp, root).replace(os.sep, '/')
            mod = rel[:-5].replace('/', '.')

            graph[mod] = parse_imports(fp)
            file_sizes[mod] = os.path.getsize(fp)
            try:
                with open(fp, 'rb') as f:
                    file_lines[mod] = sum(1 for _ in f)
            except Exception:
                file_lines[mod] = 0

    print(f"Found {len(graph):,} modules")

    # Phase 2: BFS from Main.lean
    print("Tracing dependency closure from Main.lean ...")
    visited = set()
    queue = deque([("Main", 0)])
    depths = {}
    external_imports = set()

    while queue:
        mod, depth = queue.popleft()
        if mod in visited:
            continue
        visited.add(mod)
        depths[mod] = depth

        for imp in graph.get(mod, []):
            if imp.startswith("Mathlib") or imp.startswith("Init") or imp.startswith("Lean") or imp.startswith("Batteries"):
                external_imports.add(imp)
            elif imp not in visited:
                queue.append((imp, depth + 1))

    reachable = visited
    unreachable = set(graph.keys()) - reachable
    max_depth = max(depths.values()) if depths else 0

    reachable_lines = sum(file_lines.get(m, 0) for m in reachable)
    total_lines = sum(file_lines.values())

    # Phase 3: Count dependents per module
    dependent_counts = defaultdict(int)
    for mod in reachable:
        for imp in graph.get(mod, []):
            if imp in reachable:
                dependent_counts[imp] += 1

    bottlenecks = sorted(dependent_counts.items(), key=lambda x: x[1], reverse=True)[:25]

    # Report
    print(f"\n{'='*60}")
    print(f"DEPENDENCY ANALYSIS")
    print(f"{'='*60}")
    print(f"\n  Total modules:            {len(graph):>10,}")
    print(f"  Reachable from Main.lean: {len(reachable):>10,}  ({len(reachable)*100/len(graph):.1f}%)")
    print(f"  Unreachable:              {len(unreachable):>10,}  ({len(unreachable)*100/len(graph):.1f}%)")
    print(f"\n  Total lines:              {total_lines:>10,}")
    print(f"  Reachable lines:          {reachable_lines:>10,}")
    print(f"  External (Mathlib) imports:{len(external_imports):>10,}")
    print(f"  Max dependency depth:     {max_depth:>10}")

    print(f"\n{'='*60}")
    print(f"TOP BOTTLENECK MODULES (most depended-upon)")
    print(f"{'='*60}\n")

    for mod, count in bottlenecks:
        lines = file_lines.get(mod, 0)
        d = depths.get(mod, '?')
        print(f"  {count:>6} dependents  {lines:>7,} lines  depth={d}  {mod}")

    # Depth histogram
    print(f"\n{'='*60}")
    print(f"DEPTH DISTRIBUTION")
    print(f"{'='*60}\n")

    depth_hist = defaultdict(int)
    for d in depths.values():
        depth_hist[d] += 1

    for d in sorted(depth_hist.keys())[:25]:
        bar = '#' * min(depth_hist[d] // 100, 60)
        print(f"  depth {d:>3}: {depth_hist[d]:>7,} modules  {bar}")
    if max_depth > 25:
        print(f"  ... (depths 25-{max_depth} omitted)")

    # Weight by top-level namespace
    print(f"\n{'='*60}")
    print(f"TOP-LEVEL NAMESPACE BREAKDOWN")
    print(f"{'='*60}\n")

    ns_stats = defaultdict(lambda: {'total': 0, 'reachable': 0, 'lines': 0})
    for mod in graph:
        top = mod.split('.')[0]
        ns_stats[top]['total'] += 1
        ns_stats[top]['lines'] += file_lines.get(mod, 0)
        if mod in reachable:
            ns_stats[top]['reachable'] += 1

    print(f"  {'Namespace':<30} {'Total':>8} {'Reachable':>10} {'Lines':>10}")
    print(f"  {'-'*30} {'-'*8} {'-'*10} {'-'*10}")
    for ns in sorted(ns_stats.keys(), key=lambda t: ns_stats[t]['lines'], reverse=True):
        s = ns_stats[ns]
        print(f"  {ns:<30} {s['total']:>8,} {s['reachable']:>10,} {s['lines']:>10,}")

    if json_out:
        results = {
            'total_modules': len(graph),
            'reachable_modules': len(reachable),
            'unreachable_modules': len(unreachable),
            'total_lines': total_lines,
            'reachable_lines': reachable_lines,
            'external_imports': len(external_imports),
            'max_depth': max_depth,
            'bottlenecks': [(m, c) for m, c in bottlenecks],
        }
        with open(json_out, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\nResults saved to {json_out}")


if __name__ == '__main__':
    main()
