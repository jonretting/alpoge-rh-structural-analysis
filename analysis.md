# Structural Analysis of the Alpoge RH Proof

**Date**: November 22, 2026
**Method**: Full dependency DAG trace from Main.lean through all 175,187 modules
**Author**: Jonathan Michael Retting, Independent Researcher, Los Angeles, CA
**License**: CC-BY-4.0 (https://creativecommons.org/licenses/by/4.0/)

## Motivation

The Alpoge proof of the Riemann Hypothesis is 175,187 Lean 4 source files totaling roughly 17 million lines and 1 GB of source code. Several people have noted that no one yet understands the mathematical content of the proof in human-readable terms. Number theorists are working on it, but the sheer volume makes it hard to find the signal.

This analysis takes a structural approach: build the dependency graph, trace the proof chain backward from the conclusion, identify the bottlenecks, and strip away verification machinery until only the mathematical idea remains.

## Phase 1: The Dependency Graph

### Method

Parsed all 175,187 `.lean` files for `import` statements. Built a directed acyclic graph (edges from importer to importee). Computed transitive closure from `Main.lean`.

### Findings

Every single file is reachable from Main.lean. Zero dead code. This is unusual for a codebase of this size (large software projects typically have 5-30% unreachable modules). The proof generator was architecturally tight.

The DAG has 43 layers of depth, with a diamond-shaped distribution:

```
Depth  0-4:        37 modules    (root + assembly)
Depth  5-9:    30,995 modules    (framework + definitions)
Depth 10-14:   70,892 modules    (peak mass, 40% of proof)
Depth 15-19:   40,375 modules    (deep verification)
Depth 20-29:   25,853 modules    (specialized machinery)
Depth 30-43:    7,035 modules    (deepest inductive steps)
```

### Bottleneck Ranking

The module with the most dependents is the most structurally important. If you wanted to understand the proof, start here:

| Rank | Module | Dependents | What it does |
|------|--------|-----------|-------------|
| 1 | CTSmallCone | 3,088 | Constant term decomposition: the vocabulary of tower descent |
| 2 | SiegelWeilAnisotropicHermitian | 2,972 | Siegel-Weil formula (integral = Eisenstein series) |
| 3 | DiscreteSeriesHermitianUnique | 2,518 | Uniqueness of discrete series representations |
| 4 | ExistsNormLeHeightPow | 2,460 | Existence of height bounds |
| 5 | UniformisationConclusion | 2,390 | Toroidal compactification (uniformization) |

## Phase 2: The Proof Chain

Traced backward from `Main.lean` through the proof terms.

### Main.lean (11 lines, 5 theorems)

```lean
theorem riemannHypothesis : RiemannHypothesis := rhOfAll
theorem riemannZeta_eq_zero_re : RiemannZetaZerosOnLine := rhOfAll
theorem LFunction_ne_zero_of_half_lt_re : DirichletLNonvanishingRightOfHalf := allChi
theorem LFunction_eq_zero_re : DirichletLZerosOnLine := claimAll.2.1
theorem LFunction_eq_zero_re_of_isPrimitive : PrimitiveDirichletLZerosOnLine := critAll
```

Everything reduces to two terms: `rhOfAll` and `allChi`.

### MainTheorems.lean (7 lines)

```lean
theorem allChi : UpperTheory.EveryCharacter := UpperTheory.FinalTheorems.everyCharacter
theorem rhOfAll : RiemannHypothesis := Formalism.VW.rh_of_every allChi
```

RH equals "every Dirichlet character's L-function has no zeros to the right of Re(s) = 1/2" plus a functional equation argument.

### CritLine.lean (32 lines)

This is where RH actually happens. The argument:

1. Assume a zero exists at s with Re(s) != 1/2.
2. If Re(s) < 1/2: the completed L-function satisfies Lambda(chi, s) = epsilon * Lambda(chi^-1, 1-s). A zero at s forces a zero at 1-s, but Re(1-s) > 1/2. This contradicts `EveryCharacter`.
3. If Re(s) > 1/2: `EveryCharacter` directly says this cannot happen.
4. Therefore Re(s) = 1/2.

The functional equation s <-> (1-s) is a mirror at Re(s) = 1/2. If nothing lives on the right side, the mirror guarantees nothing lives on the left side. All zeros must sit on the mirror itself. This is 32 lines of Lean.

### EveryCharacter (the definition)

```lean
def UpperTheory.EveryCharacter : Prop :=
  forall (N : nat) [NeZero N] (chi : DirichletCharacter C N) (s : C),
    1 / 2 < s.re -> (chi != 1 or s != 1) -> DirichletCharacter.LFunction chi s != 0
```

Translation: "No Dirichlet L-function has a zero to the right of Re(s) = 1/2."

This is what the other 17 million lines prove.

### MainConclusion.lean

```lean
theorem UpperTheory.FinalTheorems.everyCharacter : UpperTheory.EveryCharacter :=
  UpperTheory.FinalTheorems.everyCharacter_of_row ...
```

This calls into the theta correspondence tower, which lives in the 141,928-file `Development/` directory.

## Phase 3: The Core Strategy

### CTSmallCone.lean (363 lines, all definitions, zero proofs)

The #1 bottleneck file defines about 30 propositions that form the proof's vocabulary. Here are the most important ones:

| Definition | Role |
|-----------|------|
| IsPair | Base configuration for theta pairs |
| cone | The integral construction (over stabilizer K x ideles with character twist) |
| TowerA / TowerB | Tower descent: reduce dimension by 2 at each step |
| CTSmallCone / CTBigCone | Constant term decompositions (small/big part of the integral split) |
| CTSmallZero / CTBigZero | Zero-value constant term specializations |
| PolZero / PolRe / PolAll | Induction chain for the proportionality constant |
| EndA / EndB | Base cases at the bottom of the tower |
| LocA / LocB | Local descent relations (linking adjacent tower levels) |

This file is all vocabulary and zero proofs. It names the things you need to track as you go down the tower. The 3,088 files that depend on it are all checking that these named things behave correctly at each level.

### How the Tower Works

The inductive backbone:

1. TowerA(p+1, q+1) -> TowerB(p+1, q+1) via theta lift at this level
2. TowerB(p+1, q+1) -> TowerA(p, q) via dimension descent by 2
3. Repeat until p = 0, q = 0
4. At the base: EndA / EndB are true by direct construction
5. Chain everything back up: each level's nonvanishing follows from the level below

The 43-layer depth corresponds to roughly 21 levels of tower descent (each level requires two DAG steps: theta lift + descent).

## Phase 4: The Kernel

### What the proof discovered

Strip away 17 million lines of verification. What remains is a strategy:

1. To prove RH, it suffices to prove `EveryCharacter` (no L-function zeros in the right half-plane). The functional equation does the rest in 32 lines.
2. To prove `EveryCharacter`, build a tower of Hermitian spaces connected by theta lifts. At each level, decompose the integral into a constant term (the predictable part from lower levels) and a remainder. Show the remainder is nonzero.
3. Descend dimensions 2 at a time. At dimension 0, nonvanishing is trivial.
4. Chain back up. Done.

### The intellectual predecessor

This is a direct descendant of Stepanov's method (1969).

Stepanov proved the Weil conjecture for curves over finite fields by constructing an auxiliary polynomial that vanishes at every F_q-rational point, then bounding the degree of what remains. The idea: take away the part you can predict, see what is left.

Alpoge's proof does the same thing for the integers. At each tower level, the constant term is the predictable part. Remove it. The remainder must be nonzero for the induction to close. The theta lift is what makes the removal work for number fields instead of function fields.

The idea is maybe a page of mathematics. Checking that it works at every level of the tower, for every Hermitian space dimension, for every Dirichlet character, is the other 17 million lines.

### The numbers

| Component | Lines | Percentage |
|-----------|-------|-----------|
| Mathematical content (Layers 1-3) | 406 | 0.0024% |
| Verification machinery (Layer 4) | ~17,000,000 | 99.9976% |

## What This Analysis Does Not Do

This is a structural reading of the dependency graph. It identifies where the mathematical idea lives and how the proof is organized. It does not:

- Verify the correctness of the proof (the Lean checker and multiple independent checkers have done this)
- Explain why the theta tower descent works at every level (this is the deep mathematical content that number theorists are currently working to understand)
- Answer why the integers have a structure that forces all zeros onto a single line (the proof shows they cannot escape the line; it does not say what makes escape impossible)

The last question is, in my view, the most interesting one. The proof is a "that" answer. The "why" answer would be shorter and deeper, and it is still open.

---

**Author:** Jonathan Michael Retting, Independent Researcher, Los Angeles, CA
**License:** CC-BY-4.0 (https://creativecommons.org/licenses/by/4.0/)
