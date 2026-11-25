# Contributing

Start with a small change that someone can run or verify. Report the problem, show expected and actual behavior, and include a minimal public or synthetic example. Do not include credentials, personal data, or restricted research inputs.

## Local checks

```sh
python -m pip install ".[test]"
python -m pytest -q
node web/test-core.mjs
```

Use a virtual environment with Python 3.10 or later. Explain the checks you ran in your pull request. For new behavior, add a focused test with an explicit expected result. Keep unrelated changes in a separate pull request.

## Small tasks

- Add a fixture for a rectilinear 2D Latitude/Longitude grid in the browser tests.
- Document one tested QGIS import, with bounds and a small synthetic input.
- Design an explicit longitude-normalization option with tests for dateline behavior.

Discuss larger changes in an issue before implementing them. Respect contributors, describe disagreements in terms of the code or evidence, and credit sources and contributors. Maintainer responses depend on availability; no response time is promised.
