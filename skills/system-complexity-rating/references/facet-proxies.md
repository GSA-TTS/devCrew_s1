---
created: "2026-11-04T23:30:58Z"
updated: "2026-11-04T23:37:06Z"
---

# Facets: proxies, scoring heuristics and incomplete information

Each facet below gives what to put in three columns of the Facet profile table: Proxies, Score and Uncertainty. Use only the facets selected in the Purpose and perspectives part.

## Structural

- Rates: number and interconnection of parts; how entangled the internals are. Many parts with many interconnections tend to be more structurally complex and more failure-prone.
- Proxies: count of distinct components or subsystems; number of interfaces or dependencies; graph density; fan-in and fan-out between modules. Fallback descriptors: few, medium or many dependencies.
- Score heuristics: count distinct parts; count distinct interfaces; estimate the ratio of realized interfaces to the theoretical maximum; assess the presence of cycles, cross-cutting dependencies or tightly coupled clusters.
- Uncertainty: treat unknown or undocumented dependencies as adding to structural complexity, through a penalty on the score or an uncertainty band, because hidden coupling is itself a source of practical complexity.

## Behavioral and state-space

- Rates: how many distinct behaviours or trajectories the thing can exhibit, and how nonlinear or mode-switching those behaviours are.
- Proxies: number of possible states or modes; branching factor of decision points; number of distinct paths or scenarios (as cyclomatic complexity counts independent paths through code). Fallback descriptors: shallow, moderate or deep branching.
- Score heuristics: estimate the number of distinct states or modes; count decision points and branches; approximate the diversity of possible sequences.
- Uncertainty: when states cannot be enumerated formally, sample scenarios: count the qualitatively distinct stories or use cases the description implies and use that count as a lower bound on behavioural richness. Mark the score as a lower bound.

## Resource and algorithmic hardness

- Rates: the resource demands (time, space or other resources) and the inherent problem hardness of using, operating or solving the thing, for example a planning problem, scheduling system, optimization model or protocol.
- Proxies: asymptotic time or space complexity; known reductions to NP-hard or otherwise difficult classes; typical-case hardness metrics such as constrainedness or instance complexity.
- Score heuristics: where applicable, place it among linear-time, polynomial and super-polynomial algorithms, NP-hard reductions, and instance-level hardness such as constrainedness, which affects both solver and human performance.
- Uncertainty: without formal complexity results, use empirical or qualitative proxies: growth of time or cost with size, sensitivity to instance parameters, and how far small input changes can alter solution effort.

## Cognitive

- Rates: cognitive load and conceptual difficulty for the humans who must understand, learn or operate the thing.
- Proxies: number of concepts a user must hold at once; number of distinct concepts introduced; depth of reasoning (recall versus evaluation versus synthesis, as in Bloom-like hierarchies); depth of abstraction layers; need to integrate multiple representations; need for multi-step inference; presence of ambiguous, underspecified or novel constructs.
- Score heuristics: use established measures, namely subjective mental-effort ratings, perceived task-difficulty scales and rubric-based classifications of cognitive demand; these correlate with objective difficulty and load in education and cognitive-load research.
- Uncertainty: treat missing documentation, unclear terminology or inconsistent descriptions as raising cognitive complexity, since they inflate mental effort even when the underlying structure is simple.

## Uncertainty and variability

- Rates: ambiguity, volatility and unpredictability in the thing's behaviour or in its context. This is a property of the thing; it is distinct from the Uncertainty column, which records how sure the rating is.
- Proxies: define observables of ambiguity, volatility or unpredictability that the material shows. Fallback descriptors when they cannot be counted: for example stable, variable or volatile.
- Score heuristics: none specific to this facet. Map the proxies or descriptors to the common scale monotonically, so that more ambiguity, volatility or unpredictability never gives a lower score.
- Uncertainty: no facet-specific rule. Give a range (for example 3 to 4) or a confidence label when inputs are incomplete or noisy, as for every facet.
