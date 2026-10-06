# RFC 0001: ui-heuristic-auditor design

- **Status:** Accepted (M1 implemented)
- **Author:** EquinoxWN
- **Created:** 2026

## Problem

Usability and accessibility reviews are slow, manual and inconsistent: a reviewer opens a page,
resizes the window, squints at contrast, and writes notes nobody can reproduce. Problems that only
exist at one screen size (a menu button with no label that only appears on phones) are easy to
miss. Automated checkers exist, but they usually look at one viewport, return raw results without
evidence of where on the screen the problem is, and are not wired into CI. The goal is a tool that
captures any page at mobile and desktop sizes, finds problems with evidence (screenshot, element,
position) and a suggested fix, and can fail a build when serious problems appear. Later milestones
add a vision model for Nielsen's heuristics and measure the tool's own accuracy.

## Goals

- Playwright opens a URL in headless Chromium at a phone and a desktop viewport and saves a
  full-page screenshot and the rendered DOM for each.
- axe-core runs deterministic WCAG 2.x A and AA checks in each viewport; results are merged into one
  finding per rule and element, listing the viewports where it occurs and its box on each screenshot.
- Every finding has a severity, the WCAG references, the offending HTML and axe's suggested fix.
- A JSON report and a Markdown summary are written; the CLI can fail on a chosen severity so it can
  gate CI.
- Later: a vision LLM reviews screenshots against Nielsen's 10 heuristics with schema-validated
  output (M2), AI and deterministic findings are merged (M2), an HTML report overlays findings on
  the screenshots (M3), precision and recall on a labeled set of seeded pages (M3).

## Non-goals

- Crawling a whole site; one URL per run.
- Proving a page is accessible. Automated rules catch a subset of WCAG failures; manual review is
  still needed, and the report says so.
- Auditing pages behind a login in M1.

## Proposed design

![architecture](../architecture.png)

```
URL ─► check scheme (http/https only)
     ─► for each viewport (mobile 390x844 touch, desktop 1440x900):
          new browser context ─► goto (timeout) ─► full-page screenshot + DOM
          inject verified axe-core 4.13.0 ─► axe.run(WCAG A/AA tags) ─► violations + element boxes
     ─► merge: one finding per (rule, element), viewports listed, worst impact first
     ─► report.json + summary.md ─► exit 1 if any finding is at or above --fail-on
```

| Part | M1 implementation |
|---|---|
| Browser | Playwright 1.63 (sync API), one headless Chromium per run, a fresh context per viewport with `is_mobile`, touch and device scale factor 1 so screenshot pixels equal CSS pixels |
| Rules | axe-core 4.13.0 with `runOnly` tags `wcag2a`, `wcag2aa`, `wcag21a`, `wcag21aa`, `wcag22aa` (best-practice rules excluded) |
| Supply chain | axe-core is downloaded from the npm registry at first use and checked against npm's published sha512 integrity before it is cached; only `package/axe.min.js` is read from the tarball |
| Evidence | For each element: CSS selector, HTML (first 500 characters), failure summary (the fix), and its box in page coordinates per viewport |
| Output | `screenshot-<viewport>.png`, `dom-<viewport>.html`, `axe-<viewport>.json`, `report.json` (schema 1), `summary.md` |
| CLI | `ui-audit URL --out DIR [--viewports mobile,desktop] [--fail-on serious] [--timeout 30]`; exit 0 clean, 1 findings at threshold, 2 errors |

## Alternatives considered

| Option | Why not (yet) |
|---|---|
| Lighthouse or pa11y | Both run axe-style checks, but each wraps its own browser and reporting; owning the Playwright session is what makes multi-viewport capture, element boxes and (M2) the vision review fit into one pipeline. |
| An `axe-playwright-python` style wrapper package | Convenient, but it bundles a copy of axe-core whose version and integrity are the wrapper's choice. Fetching the pinned release and verifying npm's hash keeps the exact rules auditable. See ADR 0002. |
| Selenium | Works, but Playwright's per-context device emulation, auto-waiting and bundled browsers make viewport capture simpler and more reproducible. |
| Run every axe rule, including best practices | More findings, but best-practice rules are opinions that change between versions; WCAG A/AA rules map to a standard and make the "clean page has zero findings" test meaningful. See ADR 0003. |
| Ask a vision model for everything | Flexible, but non-deterministic and unmeasured; deterministic checks come first so M3 can measure what the model adds on top. |

## Measurement plan

- M1: 19 tests against real headless Chromium and a local fixture site: screenshot sizes and full
  page height, DOM capture, a clean page with zero findings, all six seeded problems found on the
  right elements, viewport-specific problems attributed only to their viewport, boxes inside the
  screenshot, severity filtering and ordering, refused URL schemes, load timeouts, the CLI as a
  subprocess, and axe-core integrity checks. One real public page is audited in CI.
- M2: vision LLM findings validated against a JSON schema, merged with axe findings.
- M3: precision and recall per heuristic on a labeled set of pages with seeded UX problems.

## Milestones

- **M1 (done):** multi-viewport capture, verified axe-core, merged findings with evidence, JSON and
  Markdown reports, CI gate, 19 tests.
- **M2:** vision review against Nielsen's heuristics (Claude API, schema-validated JSON with
  bounding boxes), merge and de-duplication with deterministic findings.
- **M3:** HTML report overlaying findings on screenshots, labeled evaluation set, proof table.

## Risks and open questions

- Automated WCAG checks find only part of the problems; the report must not be read as "accessible".
- Pages that load content after the `load` event may be audited too early; M2 can wait for network
  idle or a selector.
- Chromium is a large download (about 700 MB on disk locally); CI installs it with its system
  libraries on every run.
