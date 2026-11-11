# Releasing openqdata

Releases use version tags on commits already merged into `main`. A branch for every release is unnecessary; use a maintenance branch only when an older release line needs independent fixes. The current workflow accepts only commits belonging to `main`.

## One-time publishing setup

Create a PyPI account, enable two-factor authentication, and register a pending Trusted Publisher at <https://pypi.org/manage/account/publishing/>:

| Field | Value |
| --- | --- |
| PyPI project | `openqdata` |
| GitHub owner | `hansbuehler` |
| Repository | `openqdata` |
| Workflow filename | `release.yml` |
| Environment | `pypi` |

The GitHub `pypi` environment must require approval from `hansbuehler` and allow deployment from tags matching `v*`. Allow self-review so the repository owner can approve a release they initiated. Administrator bypass remains available. These environment rules are repository settings, not settings defined by the workflow YAML. Trusted Publishing obtains a short-lived credential through GitHub OIDC; no PyPI API-token secret is required.

A pending publisher creates the PyPI project on its first successful upload; it does not reserve the name in advance. See [PyPI's setup instructions](https://docs.pypi.org/trusted-publishers/creating-a-project-through-oidc/).

## Make a release

1. Update both `[project].version` in `pyproject.toml` and `openqdata.__version__` in `src/openqdata/__init__.py` to the same unused version.
2. Merge the change into `main` and let the offline CI checks pass.
3. Tag that commit with `v` followed by the exact package version. For example, for version `0.2.0`:

   ```sh
   git switch main
   git pull --ff-only
   git tag -a v0.2.0 -m 'openqdata 0.2.0'
   git push origin v0.2.0
   ```

4. In GitHub Actions, the `release` workflow reruns the offline tests and import checks on Python 3.12, 3.13 and 3.14. It then verifies main-branch ancestry and the version/tag match, builds a source distribution and wheel, validates their metadata and README with `twine check --strict`, and installs the wheel for an isolated import check.
5. Review the results and the `distributions` artifact. Approve the waiting `pypi` deployment to upload those exact artifacts. The publishing job cannot run before all test and build checks succeed.

After publication, users can install the release with:

```sh
python -m pip install openqdata==0.2.0
```

PyPI releases cannot be overwritten with different files; changes require a new version. Building a release does not access licensed caches or regenerate data. The distributions contain the package, documentation and synthetic offline test inputs; benchmark extensions and datasets remain separately distributed.

## Test the workflow without publishing

Use **Actions → release → Run workflow**, selecting `main`. This runs the tests, version consistency check, build, metadata validation and installed-wheel check. Publishing is skipped for branch runs. A run selected against a version tag instead follows the normal publishing path, including environment approval.

The workflow follows the [Python Packaging User Guide](https://packaging.python.org/en/latest/guides/publishing-package-distribution-releases-using-github-actions-ci-cd-workflows/): only the publishing job receives `id-token: write`, and it downloads the validated artifacts without checking out or rebuilding the source.
