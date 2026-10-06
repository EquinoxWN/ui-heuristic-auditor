# ADR 0003: Run only WCAG A and AA rules in the deterministic pass

- **Status:** Accepted

## Context

By default axe-core runs WCAG rules plus "best practice" rules such as "all content should be in a
landmark region". Best-practice rules are useful advice, but they are not requirements, their set
changes between axe releases, and they make it hard to say what a clean result means. The
auditor's accuracy will be measured in M3, which needs a stable definition of a finding.

## Decision

The deterministic pass calls `axe.run` with `runOnly` tags `wcag2a`, `wcag2aa`, `wcag21a`,
`wcag21aa` and `wcag22aa`. Every finding therefore maps to a WCAG success criterion, recorded in its
`wcag` field.

## Consequences

- A page that passes has no automatically detectable WCAG A/AA violations, and the clean fixture
  test asserts exactly zero findings.
- Usability problems that are not WCAG violations (confusing layout, weak hierarchy) are not
  reported by this pass; that is the job of the M2 heuristic review.
- Adding best-practice rules later is a one-line change, behind an explicit option.
