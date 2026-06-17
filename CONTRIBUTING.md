# Contributing to SUTRA Core

Thanks for your interest in SUTRA! We're building an AI-powered headless ERP for India's 63 million MSMEs, and every contribution matters.

## Development Setup

```bash
git clone https://github.com/ravikumarve/sutra-core.git
cd sutra-core
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env
```

## Making Changes

1. Fork the repository
2. Create a branch: `git checkout -b feat/your-feature`
3. Make your changes and add tests
4. Commit: follow [Conventional Commits](https://www.conventionalcommits.org/)
5. Open a PR with a clear description

## What We Welcome

| Area | Description | Value |
|------|-------------|-------|
| **Dialect Maps** | Hinglish vocabulary, regional colloquialisms, unit aliases | Highest impact |
| **Industry Presets** | New business-type configs (e.g., electronics, furniture) | High impact |
| **Query Optimization** | PostgreSQL EXPLAIN ANALYZE improvements | High impact |
| **Test Audio Fixtures** | Real-world Hinglish voice note transcriptions | Medium impact |
| **Bug Fixes** | With reproduction steps | Always welcome |
| **Performance** | With benchmarks in PR description | Always welcome |

## What We Avoid

- Cosmetic refactors without functional improvement
- Adding new dependencies without discussion
- Changing the agent communication protocol without an issue first
- Direct modifications to production `.env` examples

## Code Style

- **Python**: Black + isort (`make format` or `black src/ tests/`)
- **TypeScript** (dashboard): Prettier + ESLint
- **Commits**: Conventional Commits (`feat:`, `fix:`, `docs:`, `perf:`, etc.)
- **Tests**: pytest with async support for agent pipeline tests

## PR Checklist

Before submitting:

- [ ] `pytest tests/ -v` passes
- [ ] New tests added for new behavior
- [ ] Coverage maintained (75% agent pipeline, 90% financial modules)
- [ ] `AGENTS.md` updated if agent responsibilities changed
- [ ] Conventional Commit message format used
- [ ] PR description explains *what* and *why*

## Need Help?

Open a [Discussion](https://github.com/ravikumarve/sutra-core/discussions) or check existing [Issues](https://github.com/ravikumarve/sutra-core/issues).
