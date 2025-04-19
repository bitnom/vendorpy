# vendorpy

[![Release](https://img.shields.io/github/v/release/bitnom/vendorpy)](https://img.shields.io/github/v/release/bitnom/vendorpy)
[![Build status](https://img.shields.io/github/actions/workflow/status/bitnom/vendorpy/main.yml?branch=main)](https://github.com/bitnom/vendorpy/actions/workflows/main.yml?query=branch%3Amain)
[![codecov](https://codecov.io/gh/bitnom/vendorpy/branch/main/graph/badge.svg)](https://codecov.io/gh/bitnom/vendorpy)
[![Commit activity](https://img.shields.io/github/commit-activity/m/bitnom/vendorpy)](https://img.shields.io/github/commit-activity/m/bitnom/vendorpy)
[![License](https://img.shields.io/github/license/bitnom/vendorpy)](https://img.shields.io/github/license/bitnom/vendorpy)

# Cloudflare Python Workers Vendoring CLI Tool

Vendorpy is a command-line tool that automates the process of vendoring Python packages for Cloudflare Workers. It simplifies the vendoring process by handling the creation of virtual environments, generating requirements.txt with pruned built-in packages, and installing vendored packages.

- **Github repository**: <https://github.com/bitnom/vendorpy/>
- **Documentation** <https://bitnom.github.io/vendorpy/>

## Installation

```bash
pip install vendorpy
```

## Usage

### Vendor Packages

To vendor packages for Cloudflare Workers:

1. Create a `vendor.txt` file with the packages you want to vendor:

```
jinja2
markupsafe
# Add other packages you need to vendor
```

2. Run the vendorpy command:

```bash
vendorpy vendor --vendor-file vendor.txt --vendor-dir src/vendor
```

This will:
- Generate a `requirements.txt` file with all built-in Cloudflare packages pruned
- Create the necessary virtual environments
- Install the vendored packages to the specified directory

### List Built-in Packages

To see all built-in packages available in Cloudflare Workers:

```bash
vendorpy list-built-in
```

### Check if a Package is Built-in

To check if a specific package is built-in or needs to be vendored:

```bash
vendorpy isbuiltin <package_name>
```

For example:

```bash
vendorpy isbuiltin fastapi  # Built-in package
vendorpy isbuiltin flask    # Not built-in, needs vendoring
```

### Command Options

```
Options:
  -v, --vendor-file PATH          Path to the vendor.txt file containing
                                  packages to vendor  [default: vendor.txt]
  -r, --requirements-file PATH    Path to the requirements.txt file to
                                  generate  [default: requirements.txt]
  -d, --vendor-dir PATH           Directory to install vendored packages to
                                  [default: src/vendor]
  -p, --python-version TEXT       Python version to use for vendoring (must be
                                  3.12 for Cloudflare Workers)  [default: 3.12]
  --skip-built-in / --include-built-in
                                  Skip built-in Cloudflare packages in
                                  requirements.txt  [default: skip-built-in]
  --help                          Show this message and exit.
```

## Getting started with development

### 1. Clone Repository

```bash
git clone https://github.com/bitnom/vendorpy.git
```

### 2. Set Up Your Development Environment

Then, install the environment and the pre-commit hooks with

```bash
make install
```

This will also generate your `uv.lock` file

### 3. Run the pre-commit hooks

Initially, the CI/CD pipeline might be failing due to formatting issues. To resolve those run:

```bash
uv run pre-commit run -a
```

### 4. Commit the changes

Lastly, commit the changes made by the two steps above to your repository.

```bash
git add .
git commit -m 'Fix formatting issues'
git push origin main
```

The CI/CD pipeline will be triggered when you open a pull request, merge to main, or when you create a new release.

To finalize the set-up for publishing to PyPI, see [here](https://fpgmaas.github.io/cookiecutter-uv/features/publishing/#set-up-for-pypi).
For activating the automatic documentation with MkDocs, see [here](https://fpgmaas.github.io/cookiecutter-uv/features/mkdocs/#enabling-the-documentation-on-github).
To enable the code coverage reports, see [here](https://fpgmaas.github.io/cookiecutter-uv/features/codecov/).

## Releasing a new version

- Create an API Token on [PyPI](https://pypi.org/).
- Add the API Token to your projects secrets with the name `PYPI_TOKEN` by visiting [this page](https://github.com/bitnom/vendorpy/settings/secrets/actions/new).
- Create a [new release](https://github.com/bitnom/vendorpy/releases/new) on Github.
- Create a new tag in the form `*.*.*`.

For more details, see [here](https://fpgmaas.github.io/cookiecutter-uv/features/cicd/#how-to-trigger-a-release).

---

Repository initiated with [fpgmaas/cookiecutter-uv](https://github.com/fpgmaas/cookiecutter-uv).
