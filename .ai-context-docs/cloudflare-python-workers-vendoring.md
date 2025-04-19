================================================
FILE: 06-vendoring/README.md
================================================
# Vendoring Packages: FastAPI + Jinja2 Example

*Note: You must have Python Packages enabled on your account for built-in packages to work. Request Access to our Closed Beta using [This Form](https://forms.gle/FcjjhV3YtPyjRPaL8)*

This is an example of a Python Worker that uses a built-in package (FastAPI) with a vendored package (Jinja2).

## Adding Packages

Built-in packages can be selected from [this list](https://developers.cloudflare.com/workers/languages/python/packages/#supported-packages) and added to your `requirements.txt` file. These can be used with no other explicit install step.

Vendored packages are added to your source files and need to be installed in a special manner. The Python Workers team plans to make this process automatic in the future, but for now, manual steps need to be taken.

### Vendoring Packages

[//]: # (NOTE: when updating the instructions below, be sure to also update the vendoring.yml CI workflow)

First, install Python3.12 and pip for Python 3.12.

*Currently, other versions of Python will not work - use 3.12!*

Then create a virtual environment and activate it from your shell:
```console
python3.12 -m venv .venv
source .venv/bin/activate
```

Within our virtual environment, install the pyodide CLI:
```console
.venv/bin/pip install pyodide-build
.venv/bin/pyodide venv .venv-pyodide
```

Next, add packages to your vendor.txt file. Here we'll add jinja2
```
jinja2
```

Lastly, add these packages to your source files at `src/vendor`. For any additional packages, re-run this command.
```console
.venv-pyodide/bin/pip install -t src/vendor -r vendor.txt
```

### Using Vendored packages

In your wrangler.toml, make the vendor directory available:

```toml
[[rules]]
globs = ["vendor/**"]
type = "Data"
fallthrough = true
```

Now, you can import and use the packages:

```python
import jinja2
# ... etc ...
```

### Developing and Deploying

To develop your Worker, run `wrangler dev`.

To deploy your Worker, run `wrangler deploy`.



================================================
FILE: 06-vendoring/requirements.txt
================================================
fastapi


================================================
FILE: 06-vendoring/vendor.txt
================================================
markupsafe
jinja2


================================================
FILE: 06-vendoring/wrangler.toml
================================================
name = "fastapi-worker"
main = "src/worker.py"
compatibility_flags = ["python_workers"]
compatibility_date = "2025-03-16"

[vars]
MESSAGE = "My env var"

[[rules]]
globs = ["vendor/**"]
type = "Data"
fallthrough = true



================================================
FILE: 06-vendoring/src/worker.py
================================================
import jinja2
from fastapi import FastAPI, Request

environment = jinja2.Environment()
template = environment.from_string("Hello, {{ name }}!")


async def on_fetch(request, env):
    import asgi

    return await asgi.fetch(app, request, env)


app = FastAPI()


@app.get("/")
async def root():
    message = "This is an example of FastAPI with Jinja2 - go to /hi/<name> to see a template rendered"
    return {"message": message}


@app.get("/hi/{name}")
async def say_hi(name: str):
    message = template.render(name=name)
    return {"message": message}


@app.get("/env")
async def env(req: Request):
    env = req.scope["env"]
    return {
        "message": "Here is an example of getting an environment variable: "
        + env.MESSAGE
    }




---
pcx_content_type: navigation
title: Packages
head:
  - tag: title
    content: Python packages supported in Cloudflare Workers
---

import { Render } from "~/components";

<Render file="python-workers-beta-packages" product="workers" />

To import a Python package, add the package name to the `requirements.txt` file within the same directory as your [Wrangler configuration file](/workers/wrangler/configuration/).

For example, if your Worker depends on [FastAPI](https://fastapi.tiangolo.com/), you would add the following:

```
fastapi
```

## Package versioning

In the example above, you likely noticed that there is no explicit version of the Python package declared in `requirements.txt`.

In Workers, Python package versions are set via [Compatibility Dates](/workers/configuration/compatibility-dates/) and [Compatibility Flags](/workers/configuration/compatibility-flags/). Given a particular compatibility date, a specific version of the [Pyodide Python runtime](https://pyodide.org/en/stable/project/changelog.html) is provided to your Worker, providing a specific set of Python packages pinned to specific versions.

As new versions of Pyodide and additional Python packages become available in Workers, we will publish compatibility flags and their associated compatibility dates here on this page.

## Supported Packages

A subset of the [Python packages that Pyodide supports](https://pyodide.org/en/latest/usage/packages-in-pyodide.html) are provided directly by the Workers runtime:

- aiohttp: 3.9.3
- aiohttp-tests: 3.9.3
- aiosignal: 1.3.1
- annotated-types: 0.6.0
- annotated-types-tests: 0.6.0
- anyio: 4.2.0
- async-timeout: 4.0.3
- attrs: 23.2.0
- certifi: 2024.2.2
- charset-normalizer: 3.3.2
- distro: 1.9.0
- [fastapi](/workers/languages/python/packages/fastapi): 0.110.0
- frozenlist: 1.4.1
- h11: 0.14.0
- h11-tests: 0.14.0
- hashlib: 1.0.0
- httpcore: 1.0.4
- httpx: 0.27.0
- idna: 3.6
- jsonpatch: 1.33
- jsonpointer: 2.4
- langchain: 0.1.8
- langchain-core: 0.1.25
- langchain-openai: 0.0.6
- langsmith: 0.1.5
- lzma: 1.0.0
- micropip: 0.6.0
- multidict: 6.0.5
- numpy: 1.26.4
- numpy-tests: 1.26.4
- openai: 1.12.0
- openssl: 1.1.1n
- packaging: 23.2
- pydantic: 2.6.1
- pydantic-core: 2.16.2
- pydecimal: 1.0.0
- pydoc-data: 1.0.0
- pyyaml: 6.0.1
- regex: 2023.12.25
- regex-tests: 2023.12.25
- requests: 2.31.0
- six: 1.16.0
- sniffio: 1.3.0
- sniffio-tests: 1.3.0
- sqlite3: 1.0.0
- ssl: 1.0.0
- starlette: 0.36.3

Looking for a package not listed here? Tell us what you'd like us to support by [opening a discussion on Github](https://github.com/cloudflare/workerd/discussions/new?category=python-packages).

## HTTP Client Libraries

Only HTTP libraries that are able to make requests asynchronously are supported. Currently, these include [`aiohttp`](https://docs.aiohttp.org/en/stable/index.html) and [`httpx`](https://www.python-httpx.org/). You can also use the [`fetch()` API](/workers/runtime-apis/fetch/) from JavaScript, using Python Workers' [foreign function interface](/workers/languages/python/ffi) to make HTTP requests.
