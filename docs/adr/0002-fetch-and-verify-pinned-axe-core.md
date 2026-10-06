# ADR 0002: Fetch the pinned axe-core release and verify npm's integrity hash before running it

- **Status:** Accepted

## Context

axe-core is JavaScript that the auditor injects into every page it audits, so whoever controls that
file controls what runs in the browser and what the report says. Python wrappers bundle their own
copy of axe-core at a version they choose; vendoring the 500 KB minified file into this repo hides
its origin in a large blob; installing it with npm would add a Node.js toolchain to a Python project.

## Decision

The auditor pins axe-core by version (4.13.0) and by the sha512 integrity that npm publishes for
that exact tarball. On first use it downloads the tarball from the npm registry, verifies the hash,
reads only `package/axe.min.js` (never extracting other paths), and caches it in `.tmp/cache`.
Upgrading means changing the version and the integrity string together, in one reviewable line.

## Consequences

- A tampered or substituted download fails with `IntegrityError` before any byte runs in a page;
  tests check the rejection and that only `axe.min.js` is read, even from a tarball containing a
  path-traversal entry.
- The first run needs network access to registry.npmjs.org; later runs use the cache.
- Dependabot does not see this pin, so axe-core upgrades are a manual step: change `AXE_VERSION`
  and `TARBALL_INTEGRITY` in `axe.py` together.
