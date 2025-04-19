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

### Requirements

- Python 3.12 or higher (required for Cloudflare Workers compatibility)
- `uv` package manager (for generating requirements.txt)

## Usage

### Automatic Vendoring (Recommended)

The easiest way to vendor packages is using the `auto-vendor` command, which automatically detects which packages need to be vendored and handles the entire process in a single step:

```bash
vendorpy auto-vendor
```

This will:
1. Analyze your project dependencies using the lockfile
2. Determine which packages are built-in vs. which need vendoring
3. Create the vendor.txt file automatically
4. Generate a requirements.txt file with built-in packages pruned
5. Set up the necessary virtual environments
6. Vendor the required packages to src/vendor

Example output:
```
╭───────── Step 1: Package Detection ─────────╮
│ Detecting packages that need to be vendored │
╰─────────────────────────────────────────────╯
  Analyzing project dependencies...

                    Package Analysis Results
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━┳━━━━━━━━━━━━━━━━━━━┓
┃ Package Type                     ┃ Count ┃ Packages          ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━╇━━━━━━━━━━━━━━━━━━━┩
│ Need Vendoring                   │ 2     │ jinja2, markupsafe│
│ Built-in (No Vendoring Required) │ 1     │ fastapi           │
└──────────────────────────────────┴───────┴───────────────────┘

╭────────── Step 2: Vendor File Creation ──────────╮
│ Creating vendor.txt with 2 packages that need    │
│ vendoring                                        │
╰────────────────────────────────────────────────────╯
✅ Created vendor.txt

...
```

### Manual Vendoring Process

If you prefer more control, you can also use the individual commands:

#### 1. Check Which Packages Need Vendoring

```bash
# Check if a package is built-in or needs to be vendored
vendorpy isbuiltin <package_name>

# For example
vendorpy isbuiltin jinja2  # Not built-in, needs vendoring
vendorpy isbuiltin fastapi  # Built-in, no need to vendor
```

#### 2. Create a Vendor.txt File

Create a `vendor.txt` file with the packages that need to be vendored:

```
jinja2
markupsafe
# Add other packages that need to be vendored
```

#### 3. Run the Vendor Command

```bash
vendorpy vendor --vendor-file vendor.txt --vendor-dir src/vendor
```

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

You can also automatically add non-built-in packages to your vendor.txt file:

```bash
vendorpy isbuiltin flask --add  # Checks and adds to vendor.txt if needed
```

### Command Options

#### Auto-Vendor Command

```
Options:
  -r, --requirements-file PATH    Path to the requirements.txt file to
                                  generate  [default: requirements.txt]
  -v, --vendor-file PATH          Path to the vendor.txt file to generate
                                  [default: vendor.txt]
  -d, --vendor-dir PATH           Directory to install vendored packages to
                                  [default: src/vendor]
  -p, --python-version TEXT       Python version to use for vendoring (must be
                                  3.12 for Cloudflare Workers)  [default: 3.12]
  --help                          Show this message and exit.
```

#### Vendor Command

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

#### IsBuiltin Command

```
Options:
  -a, --add                       Add the package to vendor.txt if it's not built-in
  -v, --vendor-file PATH          Path to the vendor.txt file
                                  [default: vendor.txt]
  --help                          Show this message and exit.
```

## Cloudflare Worker Configuration

After vendoring your packages, make sure to configure your `wrangler.toml` file to include the vendor directory:

```toml
[[rules]]
globs = ["vendor/**"]
type = "Data"
fallthrough = true
```

## Error Handling and Troubleshooting

Vendorpy includes comprehensive error handling to help diagnose and resolve issues:

### Common Issues

1. **Python Version**: Ensure you have Python 3.12 installed as it's required for Cloudflare Workers compatibility.

2. **Missing Dependencies**: If you encounter errors about missing dependencies, make sure `uv` is installed:
   ```bash
   pip install uv
   ```

3. **Empty vendor.txt**: Your vendor.txt file must contain at least one package to vendor.

4. **Package Not Found**: If a package can't be found, check if it's available on PyPI or if it's a built-in package:
   ```bash
   vendorpy isbuiltin <package_name>
   ```

5. **Permission Issues**: If you encounter permission errors when creating virtual environments, try running the command with appropriate permissions.

The tool provides detailed error messages to help diagnose issues. If you encounter persistent problems, please open an issue on GitHub.

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
