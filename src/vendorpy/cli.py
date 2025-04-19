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
from rich.table import Table

from vendorpy.utils import (
    CLOUDFLARE_BUILT_IN_PACKAGES,
    configure_wrangler_for_vendor,
    create_pyodide_env,
    create_virtual_env,
    create_vendor_file,
    detect_packages_to_vendor,
    install_packages_to_vendor,
)

app = typer.Typer(
    help="Vendorpy - A tool for automating Cloudflare Python Workers vendoring",
    add_completion=False,
)
console = Console()


@app.command()
def auto_vendor(
    requirements_file: Path = typer.Option(  # noqa: B008
        "requirements.txt",
        "--requirements-file",
        "-r",
        help="Path to the requirements.txt file to generate",
    ),
    vendor_file: Path = typer.Option(  # noqa: B008
        "vendor.txt",
        "--vendor-file",
        "-v",
        help="Path to the vendor.txt file to generate",
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
):
    """
    Automatically detect and vendor packages for Cloudflare Workers.

    This command automatically detects which packages need to be vendored by analyzing your
    project dependencies and comparing them with Cloudflare's built-in packages. It then
    handles the entire vendoring process in a single step.
    """
    try:
        console.print(
            Panel.fit(
                "Detecting packages that need to be vendored",
                title="[bold green]Step 1: Package Detection[/bold green]",
            )
        )

        # Detect packages to vendor
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Analyzing project dependencies...", total=1)

            try:
                package_results = detect_packages_to_vendor()
                vendor_packages = package_results["vendor"]
                built_in_packages = package_results["built_in"]
                progress.update(task, completed=1)
            except Exception as e:
                progress.update(
                    task,
                    completed=1,
                    description=f"Failed to analyze dependencies: {e}",
                )
                raise

        # Display results in a table
        table = Table(title="Package Analysis Results")
        table.add_column("Package Type", style="cyan")
        table.add_column("Count", style="green")
        table.add_column("Packages", style="yellow")

        table.add_row(
            "Need Vendoring",
            str(len(vendor_packages)),
            ", ".join(vendor_packages) if vendor_packages else "None",
        )
        table.add_row(
            "Built-in (No Vendoring Required)",
            str(len(built_in_packages)),
            ", ".join(built_in_packages) if built_in_packages else "None",
        )

        console.print(table)

        # If there are no packages to vendor, notify and exit
        if not vendor_packages:
            console.print(
                Panel.fit(
                    "No packages need to be vendored! All your dependencies are already built into Cloudflare Workers.",
                    title="[bold green]No Action Required[/bold green]",
                )
            )
            return

        # Create vendor.txt file
        console.print(
            Panel.fit(
                f"Creating {vendor_file} with {len(vendor_packages)} packages that need vendoring",
                title="[bold green]Step 2: Vendor File Creation[/bold green]",
            )
        )
        create_vendor_file(vendor_packages, vendor_file)
        console.print(f"✅ Created {vendor_file}")

        # Generate requirements.txt with pruned packages
        console.print(
            Panel.fit(
                "Generating requirements.txt with pruned built-in packages",
                title="[bold green]Step 3: Requirements Generation[/bold green]",
            )
        )
        generate_requirements(requirements_file)

        # Create virtual environments and vendor packages
        console.print(
            Panel.fit(
                "Setting up Python environment for vendoring",
                title="[bold green]Step 4: Environment Setup[/bold green]",
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
                f"✅ Successfully vendored {len(vendor_packages)} packages to {vendor_dir}",
                title="[bold green]Vendoring Complete[/bold green]",
            )
        )

        # Configure wrangler.toml or wrangler.jsonc
        console.print(
            Panel.fit(
                "Configuring wrangler for vendoring",
                title="[bold green]Step 5: Wrangler Configuration[/bold green]",
            )
        )

        config_result = configure_wrangler_for_vendor()

        if config_result is None:
            console.print(
                Panel.fit(
                    "No wrangler.toml or wrangler.jsonc found in the current directory.\n\n"
                    "Please manually configure your wrangler file to include the vendor directory:\n"
                    """
[[rules]]
globs = ["vendor/**"]
type = "Data"
fallthrough = true
                    """,
                    title="[bold yellow]Manual Configuration Required[/bold yellow]",
                )
            )
        else:
            success, message = config_result
            if success:
                console.print(f"✅ {message}")
            else:
                console.print(
                    Panel.fit(
                        f"{message}\n\n"
                        "Please manually add the following to your wrangler configuration:\n"
                        """
[[rules]]
globs = ["vendor/**"]
type = "Data"
fallthrough = true
                        """,
                        title="[bold yellow]Manual Configuration Required[/bold yellow]",
                    )
                )

        console.print("\n[bold]Next steps:[/bold]")
        console.print("1. Import your vendored packages in your code")
        console.print("2. Run 'wrangler dev' to test your worker")

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e!s}")
        sys.exit(1)


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


@app.command()
def isbuiltin(
    package_name: str = typer.Argument(..., help="Name of the package to check"),  # noqa: B008
    add_to_vendor: bool = typer.Option(  # noqa: B008
        False,
        "--add",
        "-a",
        help="Add the package to vendor.txt if it's not built-in",
    ),
    vendor_file: Path = typer.Option(  # noqa: B008
        "vendor.txt",
        "--vendor-file",
        "-v",
        help="Path to the vendor.txt file",
    ),
):
    """Check if a package is built-in or needs to be vendored.

    If the package is not built-in, it can be automatically added to vendor.txt with the --add flag.
    """
    try:
        # Validate package name
        if not package_name or not package_name.strip():
            console.print("[bold red]Error:[/bold red] Package name cannot be empty.")
            sys.exit(1)

        # Normalize package name (convert to lowercase and replace dashes with underscores)
        normalized_name = package_name.lower().replace("-", "_")

        # Check if the package is in the built-in packages list
        is_built_in = any(
            pkg.lower().replace("-", "_") == normalized_name
            for pkg in CLOUDFLARE_BUILT_IN_PACKAGES
        )

        if is_built_in:
            try:
                # Find the exact package name with correct casing
                exact_name = next(
                    pkg
                    for pkg in CLOUDFLARE_BUILT_IN_PACKAGES
                    if pkg.lower().replace("-", "_") == normalized_name
                )
                console.print(
                    Panel.fit(
                        f"[bold green]✓ {exact_name}[/bold green] is a built-in package in Cloudflare Workers.\n\n"
                        "You can use it directly without vendoring.\n\n"
                        "Add it to your requirements.txt file:"
                        f"\n  {exact_name}",
                        title="[bold green]Built-in Package[/bold green]",
                    )
                )
            except StopIteration:
                # This should not happen, but handle it just in case
                console.print(
                    Panel.fit(
                        f"[bold green]✓ {package_name}[/bold green] is a built-in package in Cloudflare Workers.\n\n"
                        "You can use it directly without vendoring.\n\n"
                        "Add it to your requirements.txt file:"
                        f"\n  {package_name}",
                        title="[bold green]Built-in Package[/bold green]",
                    )
                )
        else:
            console.print(
                Panel.fit(
                    f"[bold yellow]! {package_name}[/bold yellow] is NOT a built-in package in Cloudflare Workers.\n\n"
                    "You need to vendor this package.",
                    title="[bold yellow]Package Needs Vendoring[/bold yellow]",
                )
            )

            # Check if we should add the package to vendor.txt
            if add_to_vendor:
                try:
                    # Create vendor.txt if it doesn't exist
                    if not vendor_file.exists():
                        vendor_file.parent.mkdir(parents=True, exist_ok=True)
                        vendor_file.touch()
                        console.print(f"Created {vendor_file} file.")

                    # Check if the package is already in vendor.txt
                    with open(vendor_file, "r") as f:
                        vendor_packages = [
                            line.strip()
                            for line in f
                            if line.strip() and not line.strip().startswith("#")
                        ]

                    if package_name in vendor_packages:
                        console.print(
                            f"Package {package_name} is already in {vendor_file}."
                        )
                    else:
                        # Add the package to vendor.txt
                        with open(vendor_file, "a") as f:
                            # Add a newline if the file doesn't end with one
                            if vendor_file.exists() and vendor_file.stat().st_size > 0:
                                with open(vendor_file, "r") as check_f:
                                    content = check_f.read()
                                    if content and not content.endswith("\n"):
                                        f.write("\n")

                            f.write(f"{package_name}\n")
                        console.print(
                            f"[bold green]✓ Added {package_name} to {vendor_file}[/bold green]"
                        )
                except Exception as e:
                    console.print(
                        f"[bold red]Error adding package to vendor.txt:[/bold red] {e!s}"
                    )
            else:
                console.print("\nTo add this package to your vendor.txt file:")
                console.print(
                    f"  [bold]vendorpy isbuiltin {package_name} --add[/bold]",
                    style="blue",
                )
                console.print("\nOr manually add it to your vendor.txt file and run:")
                console.print("  [bold]vendorpy vendor[/bold]", style="blue")
    except Exception as e:
        console.print(f"[bold red]Error checking package:[/bold red] {e!s}")
        sys.exit(1)


def main():
    """Main entry point for the CLI."""
    app()


if __name__ == "__main__":
    main()
