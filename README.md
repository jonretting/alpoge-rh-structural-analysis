# Structural Analysis of the Alpoge RH Proof

What is the irreducible mathematical content of the Alpoge-Claude Lean 4 proof of the Riemann Hypothesis?

This repo contains a dependency analysis of all 175,187 source files, tracing the proof backward from `Main.lean` to identify the mathematical kernel buried inside 17 million lines of verification machinery.

## The Short Version

The proof has four layers:

| Layer | What | Lines | File |
|-------|------|-------|------|
| Conclusion | RH = all zeros on the critical line | 11 | `Main.lean` |
| Functional equation | No zeros right of line + symmetry = all on line | 32 | `CritLine.lean` |
| Strategy | Tower descent vocabulary (definitions only, zero proofs) | 363 | `CTSmallCone.lean` |
| Verification | Every tower level works correctly | ~17,000,000 | everything else |

406 lines of mathematical content. 17 million lines of verification. Compression ratio: 0.0024%.

One-sentence summary: **L-function nonvanishing propagates down a theta-lift tower by constant-term analysis, with a trivial base case at dimension zero.**

## What is in this repo

- `analysis.md`: The full structural analysis, layer by layer, with Lean code excerpts
- `skeleton.py`: Script to build the dependency DAG from the proof source. Parses imports, computes depth, finds bottlenecks. Run it yourself.
- `skeleton_analysis.json`: Pre-computed results (depth distribution, bottleneck ranking, proof chain)

## How to reproduce

```bash
# Clone the proof
git clone https://github.com/leanprover-community/riemann-hypothesis source

# Run the analysis
python skeleton.py
```

Requires Python 3.8+. No dependencies beyond the standard library.

## The Four Layers Explained

### Layer 1: Main.lean (11 lines)

Five theorems, all reducing to two proof terms: `rhOfAll` and `allChi`. Both defined in `MainTheorems.lean` (7 lines). Everything flows from one statement: `EveryCharacter`.

### Layer 2: CritLine.lean (32 lines)

This is where RH actually happens, and the argument is straightforward:

1. Suppose a zero of L(chi, s) exists with Re(s) != 1/2.
2. If Re(s) > 1/2: `EveryCharacter` directly forbids this.
3. If Re(s) < 1/2: the completed L-function satisfies Lambda(chi, s) = epsilon * Lambda(chi^-1, 1-s). A zero at s forces a zero at 1-s, which has Re(1-s) > 1/2, again forbidden.
4. Therefore Re(s) = 1/2.

The functional equation s <-> (1-s) reflects zeros across Re(s) = 1/2. If you can show no zeros exist on one side, the reflection guarantees none on the other. All zeros must sit on the mirror.

The remaining 17 million lines exist to prove one thing: `EveryCharacter`, which says no Dirichlet L-function has a zero in the right half-plane Re(s) > 1/2.

### Layer 3: CTSmallCone.lean (363 lines, all definitions, zero proofs)

This is the #1 bottleneck in the entire proof: 3,088 other modules depend on it.

It defines the vocabulary for a tower descent:

- **TowerA / TowerB**: Two types of spaces at each level, linked by theta lifts
- **CTSmallCone / CTBigCone**: A decomposition of integrals into two parts (constant term analysis)
- **PolZero / PolRe / PolAll**: An induction chain for a proportionality constant
- **EndA / EndB**: Base cases at the bottom of the tower
- **LocA / LocB**: Local relations linking adjacent tower levels

The strategy:
1. Start at the top of a tower of Hermitian spaces
2. At each level, use a theta lift (a specific integral transform) to pass information between TowerA and TowerB
3. Drop the dimension by 2 (TowerB at level n+1 -> TowerA at level n)
4. At each level, split the integral into a "big cone" (the predictable bulk) and a "small cone" (the part carrying the nonvanishing information)
5. Show nonvanishing propagates downward
6. At the bottom (dimension 0): trivially true
7. Chain everything back up

The 43-layer depth in the dependency graph corresponds to roughly 21 levels of tower descent (each level needs a theta lift step + a descent step).

### Layer 4: Everything else (17 million lines)

Every one of the remaining 175,000+ files verifies that the tower descent works correctly at each level. The integrals converge. The theta lifts are well-defined. The constant term decompositions are valid. The base cases hold.

100% of modules are reachable from Main.lean. Zero dead code. The proof generator was architecturally disciplined.

## The Intellectual Ancestry

The proof's core technique has a clear predecessor.

Stepanov (1969) proved the Weil conjecture for curves over finite fields by constructing an auxiliary polynomial that vanishes at every rational point, then bounding the degree of what remains. The key move: subtract the predictable part, bound the residual.

Alpoge's proof does the same thing for number fields. At each tower level, the "constant term" is the predictable part (what you can compute from the lower levels). Subtract it. The remainder must be nonzero for the tower to close. The theta lift is the mechanism that makes this subtraction work for number fields instead of function fields.

The idea is maybe a page of mathematics. Verifying that it works across all dimensions of Hermitian spaces, for all Dirichlet characters, at every level of the tower, is the other 17 million lines.

## Dependency Graph Statistics

| Metric | Value |
|--------|-------|
| Total modules | 175,187 |
| Reachable from Main.lean | 175,187 (100%) |
| Dead code | 0 |
| Maximum depth | 43 layers |
| Peak depth | 10 (15,539 modules) |
| Shape | Diamond (thin at top and bottom, wide in the middle) |
| Mathlib imports | 348 |

### Top 5 Bottlenecks (most dependents)

| Module | Dependents | Role |
|--------|-----------|------|
| CTSmallCone | 3,088 | Tower descent vocabulary |
| SiegelWeilAnisotropicHermitian | 2,972 | Siegel-Weil formula |
| DiscreteSeriesHermitianUnique | 2,518 | Discrete series uniqueness |
| ExistsNormLeHeightPow | 2,460 | Height bound existence |
| UniformisationConclusion | 2,390 | Toroidal compactification |

## License

**Author:** Jonathan Michael Retting, Independent Researcher, Los Angeles, CA
**License:** CC-BY-4.0 (https://creativecommons.org/licenses/by/4.0/)

The analysis is mine. The proof source is Alpoge's (see upstream repo for its terms).

## Acknowledgments

Community work that complements this analysis:
- [Jinho Noh's backbone index](https://github.com/thekeunpie-hash/rh-kernel-backbone)
- [Bartosz Naskrecski's proof atlas](https://nasqret.github.io/riemann-proof-atlas/)
- [Scott Cochran's diagrams](https://scottcochran.github.io/riemann-diagrams/)
