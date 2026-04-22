# Contributing to roku-tui

This guide outlines the professional standards and workflows for maintaining and contributing to the **roku-tui** project. Following these habits ensures a stable codebase and a clean, professional release history.

## Development Workflow

We follow a "Feature Branch" workflow to ensure the `main` branch remains stable and production-ready at all times.

### 1. Work on a Branch
Never commit major changes directly to `main`. Create a descriptive branch for your work:
```bash
git checkout -b feat/my-new-feature
# or
git checkout -b fix/issue-description
```

### 2. Quality Control
Before merging any code, ensure it passes all local checks. Our pre-commit hooks handle this, but you should run them manually during development:
```bash
uv run ruff check . --fix
uv run ruff format .
uv run mypy .
uv run pytest
```

### 3. Merge to Main
Once your work is complete and tested, merge it into `main`. (In a team setting, this would be done via a Pull Request).
```bash
git checkout main
git merge feat/my-new-feature
git push origin main
```

---

## Versioning Strategy (SemVer)

We use [Semantic Versioning](https://semver.org/). While in the `0.x.y` phase, we follow these rules:

- **MAJOR (x.0.0):** Breaking changes that fundamentally alter the CLI or database.
- **MINOR (0.x.0):** New features or significant improvements (e.g., adding Headless Mode).
- **PATCH (0.x.y):** Bug fixes, documentation tweaks, and internal chores.

---

## The Release Ceremony

When the codebase is stable and you are ready to share a new version, follow these steps precisely. **Do not cut a release for every single commit.** Let features and fixes accumulate.

1. **Sync Main:** Ensure your local `main` is up to date and passing tests.
   ```bash
   git checkout main
   git pull origin main
   uv run pytest
   ```
2. **Bump Version:** Update the version string in TWO files:
   - `pyproject.toml`
   - `roku_tui/__init__.py`
3. **Commit the Bump:**
   ```bash
   git add pyproject.toml roku_tui/__init__.py
   git commit -m "chore: release v0.x.y"
   ```
4. **Tag the Release:**
   ```bash
   git tag v0.x.y
   ```
5. **Push Everything:**
   ```bash
   git push origin main --tags
   ```

---

## Professional Release Notes

After pushing a tag, GitHub Actions will build the binaries. Once complete, go to the [Releases](https://github.com/hirekarl/roku_tui/releases) page and edit the release description.

**Template:**
```markdown
## What's New
* **Feature Name:** Brief description of what it does and why it matters.

## Bug Fixes
* Description of the fix and what issue it solved.

## Under the Hood
* Internal refactorings or dependency updates.
```

---

## Habits for Success

*   **Be Patient:** Wait until you have a meaningful "chunk" of work before tagging a release.
*   **Trust the CI:** If the GitHub Action build fails, fix the code on a branch, merge it, and *then* update the tag.
*   **Commit Often, Release Seldom:** Small, atomic commits are great. Frequent releases are noisy.
