"""
Vendorpy CLI - A tool for automating Cloudflare Python Workers vendoring.

This CLI tool automates the process of vendoring Python packages for Cloudflare Workers.
It generates the requirements.txt file with the appropriate pruned packages and
handles the vendoring process.
"""

import subprocess
import sys
from pathlib import Path
import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from vendorpy.utils import (
    CLOUDFLARE_BUILT_IN_PACKAGES,
    create_pyodide_env,
    create_virtual_env,
    install_packages_to_vendor,
)

app = typer.Typer(
    help="Vendorpy - A tool for automating Cloudflare Python Workers vendoring",
    add_completion=False,
)
console = Console()


@app.command()
def vendor(
    vendor_file: Path = typer.Option(  # noqa: B008
        "vendor.txt",
        "--vendor-file",
        "-v",
        help="Path to the vendor.txt file containing packages to vendor",
        exists=True,
    ),
    requirements_file: Path = typer.Option(  # noqa: B008
        "requirements.txt",
        "--requirements-file",
        "-r",
        help="Path to the requirements.txt file to generate",
    ),
    vendor_dir: Path = typer.Option(  # noqa: B008
        "src/vendor",
        "--vendor-dir",
        "-d",
        help="Directory to install vendored packages to",
    ),
    python_version: str = typer.Option(  # noqa: B008
        "3.12",
        "--python-version",
        "-p",
        help="Python version to use for vendoring (must be 3.12 for Cloudflare Workers)",
    ),
    skip_built_in: bool = typer.Option(  # noqa: B008
        True,
        "--skip-built-in/--include-built-in",
        help="Skip built-in Cloudflare packages in requirements.txt",
    ),
):
    """
    Vendor Python packages for Cloudflare Workers.

    This command automates the process of vendoring Python packages for Cloudflare Workers.
    It generates the requirements.txt file with the appropriate pruned packages and
    handles the vendoring process.
    """
    try:
        # Create vendor directory if it doesn't exist
        vendor_dir.mkdir(parents=True, exist_ok=True)

        # Generate requirements.txt with pruned packages
        if skip_built_in:
            console.print(
                Panel.fit(
                    "Generating requirements.txt with pruned built-in packages",
                    title="[bold green]Step 1: Requirements Generation[/bold green]",
                )
            )
            generate_requirements(requirements_file)

        # Create virtual environments and vendor packages
        console.print(
            Panel.fit(
                "Setting up Python environment for vendoring",
                title="[bold green]Step 2: Environment Setup[/bold green]",
            )
        )

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            # Create Python virtual environment
            task1 = progress.add_task("Creating Python virtual environment...", total=1)
            venv_path = create_virtual_env(python_version)
            progress.update(task1, completed=1)

            # Create Pyodide virtual environment
            task2 = progress.add_task(
                "Creating Pyodide virtual environment...", total=1
            )
            pyodide_venv_path = create_pyodide_env(venv_path)
            progress.update(task2, completed=1)

            # Install packages to vendor directory
            task3 = progress.add_task(
                "Installing packages to vendor directory...", total=1
            )
            install_packages_to_vendor(pyodide_venv_path, vendor_file, vendor_dir)
            progress.update(task3, completed=1)

        console.print(
            Panel.fit(
                f"✅ Successfully vendored packages from {vendor_file} to {vendor_dir}",
                title="[bold green]Vendoring Complete[/bold green]",
            )
        )

        console.print("\n[bold]Next steps:[/bold]")
        console.print("1. Make sure your wrangler.toml includes the vendor directory:")
        console.print(
            """
[[rules]]
globs = ["vendor/**"]
type = "Data"
fallthrough = true
        """,
            style="green",
        )
        console.print("2. Import your vendored packages in your code")
        console.print("3. Run 'wrangler dev' to test your worker")

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e!s}")
        sys.exit(1)


def generate_requirements(requirements_file: Path) -> None:
    """Generate requirements.txt with pruned built-in packages."""

    # Build the uv export command with all the prune flags
    cmd = [
        "uv",
        "export",
        "--format",
        "requirements-txt",
        "-o",
        str(requirements_file),
        "--locked",
        "--frozen",
        "--no-dev",
        "--prune",
    ]

    # Add all built-in packages as prune flags
    for package in CLOUDFLARE_BUILT_IN_PACKAGES:
        cmd.extend(["--prune", package])

    try:
        # Using subprocess with a fixed command list is safe as we're not using shell=True
        # and not accepting user input for the command itself
        subprocess.run(cmd, check=True, capture_output=True, text=True)  # nosec B603
        console.print(f"✅ Generated {requirements_file} with pruned built-in packages")
    except subprocess.CalledProcessError as e:
        console.print(f"[bold red]Error generating requirements.txt:[/bold red] {e}")
        raise


@app.command()
def list_built_in():
    """List all built-in packages available in Cloudflare Workers."""
    console.print(
        Panel.fit(
            "\n".join(f"- {pkg}" for pkg in sorted(CLOUDFLARE_BUILT_IN_PACKAGES)),
            title="[bold green]Cloudflare Workers Built-in Packages[/bold green]",
        )
    )


def main():
    """Main entry point for the CLI."""
    app()


if __name__ == "__main__":
    main()
