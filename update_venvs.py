#!/usr/bin/env python3
"""Recompile the requirements of all projects and sync their virtual environments.

A project is any top-level folder containing a ``requirements.in`` file.
For each project, this script:

    1. Creates ``.venv`` if missing (or recreates it with ``--recreate``).
    2. Installs/upgrades ``pip`` and ``pip-tools`` into the venv.
    3. Compiles every ``requirements*.in`` to its ``.txt`` lock file
       (``requirements.in`` is the source of truth).
    4. Syncs the venv exactly to the lock files (hash-checked).
    5. Runs pylint on all Python files and pytest (if ``pytest.ini`` exists),
       like the CI workflows do.

Usage:
    python update_venvs.py [project ...] [--upgrade] [--recreate]
                           [--no-compile] [--no-checks] [--verbose]

Requires only the Python standard library. Missing venvs are created with the
interpreter running this script, so run it without an activated venv.

This script never commits or pushes; it only proposes a commit message.
"""

import argparse
import shutil
import subprocess
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
VENV_DIR_NAME = ".venv"
STEPS = ("compile", "sync", "pylint", "pytest")

OK = "ok"
CHANGED = "changed"
FAILED = "FAIL"
SKIPPED = "skipped"


def find_projects() -> list[str]:
    """Find all top-level project folders that contain a requirements.in file.

    Returns:
        list[str]: The sorted folder names of all projects.
    """
    return sorted(
        path.parent.name for path in REPO_ROOT.glob("*/requirements.in")
    )


def get_venv_python(venv_dir: Path) -> Path:
    """Get the path to the Python executable of a virtual environment.

    Args:
        venv_dir (Path): The path to the virtual environment.

    Returns:
        Path: The path to the venv's Python executable (Windows or POSIX layout).
    """
    windows_python = venv_dir / "Scripts" / "python.exe"
    if windows_python.exists():
        return windows_python
    return venv_dir / "bin" / "python"


def get_venv_version(venv_dir: Path) -> str:
    """Read the Python version of a virtual environment from its pyvenv.cfg.

    Args:
        venv_dir (Path): The path to the virtual environment.

    Returns:
        str: The version string (e.g. '3.13.1'), or an empty string if unknown.
    """
    cfg_path = venv_dir / "pyvenv.cfg"
    if not cfg_path.exists():
        return ""
    for line in cfg_path.read_text(encoding="utf-8").splitlines():
        key, _, value = line.partition("=")
        if key.strip() in ("version", "version_info"):
            return value.strip()
    return ""


def run(cmd: list[str], cwd: Path, verbose: bool) -> bool:
    """Run a command and print its output if it fails or verbose is set.

    Args:
        cmd (list[str]): The command and its arguments.
        cwd (Path): The working directory for the command.
        verbose (bool): Whether to always print the command output.

    Returns:
        bool: True if the command exited with code 0, False otherwise.
    """
    label = " ".join(["python" if Path(cmd[0]).stem == "python" else str(cmd[0]), *cmd[1:]])
    start = time.monotonic()

    if verbose:
        print(f"    $ {label}", flush=True)
        returncode = subprocess.run(cmd, cwd=cwd, check=False).returncode
        output = ""
    else:
        print(f"    $ {label} ...", end=" ", flush=True)
        result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, check=False)
        returncode = result.returncode
        output = result.stdout + result.stderr

    status = OK if returncode == 0 else FAILED
    print(f"{status} ({time.monotonic() - start:.1f}s)", flush=True)
    if output and returncode != 0:
        print(output, flush=True)
    return returncode == 0


def read_lock_files(lock_files: list[Path]) -> dict[Path, str]:
    """Read the current content of lock files to detect changes later.

    Args:
        lock_files (list[Path]): The lock files to read.

    Returns:
        dict[Path, str]: Mapping of lock file path to its content ('' if missing).
    """
    return {
        path: path.read_text(encoding="utf-8") if path.exists() else ""
        for path in lock_files
    }


def prepare_venv(project_dir: Path, args: argparse.Namespace) -> Path | None:
    """Create or recreate the project's venv and install pip-tools into it.

    Args:
        project_dir (Path): The project folder.
        args (argparse.Namespace): The parsed command-line arguments.

    Returns:
        Path | None: The path to the venv's Python executable, or None on failure.
    """
    venv_dir = project_dir / VENV_DIR_NAME

    if args.recreate and venv_dir.exists():
        print(f"    removing {venv_dir}")
        shutil.rmtree(venv_dir)

    if not venv_dir.exists():
        if not run([sys.executable, "-m", "venv", VENV_DIR_NAME], project_dir, args.verbose):
            return None
    else:
        running_version = f"{sys.version_info.major}.{sys.version_info.minor}"
        venv_version = get_venv_version(venv_dir)
        if venv_version and not venv_version.startswith(running_version + "."):
            print(
                f"    WARNING: .venv uses Python {venv_version}, this script runs "
                f"{running_version}. Use --recreate to rebuild it."
            )

    venv_python = get_venv_python(venv_dir)
    tools_cmd = [
        str(venv_python), "-m", "pip", "install", "--quiet", "--upgrade", "pip", "pip-tools"
    ]
    if not run(tools_cmd, project_dir, args.verbose):
        return None
    return venv_python


def compile_requirements(project_dir: Path, venv_python: Path, args: argparse.Namespace) -> str:
    """Compile all requirements*.in files of a project to hashed lock files.

    Args:
        project_dir (Path): The project folder.
        venv_python (Path): The venv's Python executable.
        args (argparse.Namespace): The parsed command-line arguments.

    Returns:
        str: The step status (ok, changed or FAIL).
    """
    # requirements.in first, so that other .in files can constrain against it
    in_files = sorted(
        project_dir.glob("requirements*.in"),
        key=lambda path: (path.name != "requirements.in", path.name),
    )
    lock_files = [path.with_suffix(".txt") for path in in_files]
    before = read_lock_files(lock_files)

    for in_file in in_files:
        cmd = [
            str(venv_python), "-m", "piptools", "compile", "--quiet",
            "--generate-hashes", "--strip-extras",
        ]
        if args.upgrade:
            cmd.append("--upgrade")
        cmd.append(in_file.name)
        if not run(cmd, project_dir, args.verbose):
            return FAILED

    return CHANGED if read_lock_files(lock_files) != before else OK


def sync_requirements(project_dir: Path, venv_python: Path, verbose: bool) -> str:
    """Sync the venv exactly to all requirements*.txt lock files of a project.

    Args:
        project_dir (Path): The project folder.
        venv_python (Path): The venv's Python executable.
        verbose (bool): Whether to always print the command output.

    Returns:
        str: The step status (ok or FAIL).
    """
    lock_files = sorted(path.name for path in project_dir.glob("requirements*.txt"))
    cmd = [str(venv_python), "-m", "piptools", "sync", *lock_files]
    return OK if run(cmd, project_dir, verbose) else FAILED


def run_pylint(project_dir: Path, venv_python: Path, verbose: bool) -> str:
    """Run pylint on every Python file of a project, as the CI workflow does.

    Args:
        project_dir (Path): The project folder.
        venv_python (Path): The venv's Python executable.
        verbose (bool): Whether to always print the command output.

    Returns:
        str: The step status (ok or FAIL).
    """
    py_files = sorted(
        path.relative_to(project_dir).as_posix()
        for path in project_dir.rglob("*.py")
        if VENV_DIR_NAME not in path.relative_to(project_dir).parts
    )
    status = OK
    for py_file in py_files:
        if not run([str(venv_python), "-m", "pylint", py_file], project_dir, verbose):
            status = FAILED
    return status


def run_pytest(project_dir: Path, venv_python: Path, verbose: bool) -> str:
    """Run the project's test suite if it has a pytest.ini.

    Args:
        project_dir (Path): The project folder.
        venv_python (Path): The venv's Python executable.
        verbose (bool): Whether to always print the command output.

    Returns:
        str: The step status (ok, FAIL or skipped).
    """
    if not (project_dir / "pytest.ini").exists():
        return SKIPPED
    cmd = [str(venv_python), "-m", "pytest", "tests/"]
    return OK if run(cmd, project_dir, verbose) else FAILED


def update_project(project: str, args: argparse.Namespace) -> dict[str, str]:
    """Run all update steps for a single project.

    A failing step skips the remaining steps of this project.

    Args:
        project (str): The project folder name.
        args (argparse.Namespace): The parsed command-line arguments.

    Returns:
        dict[str, str]: Mapping of column name to status, including 'python'.
    """
    project_dir = REPO_ROOT / project
    results = {"python": "?", **{step: SKIPPED for step in STEPS}}
    print(f"\n=== {project}", flush=True)

    venv_python = prepare_venv(project_dir, args)
    if venv_python is None:
        results["python"] = FAILED
        return results
    results["python"] = get_venv_version(project_dir / VENV_DIR_NAME) or "?"

    if not args.no_compile:
        results["compile"] = compile_requirements(project_dir, venv_python, args)
        if results["compile"] == FAILED:
            return results

    results["sync"] = sync_requirements(project_dir, venv_python, args.verbose)
    if results["sync"] == FAILED or args.no_checks:
        return results

    results["pylint"] = run_pylint(project_dir, venv_python, args.verbose)
    results["pytest"] = run_pytest(project_dir, venv_python, args.verbose)
    return results


def print_summary(all_results: dict[str, dict[str, str]]) -> None:
    """Print a summary table, the lock file diff stat and a commit message proposal.

    Args:
        all_results (dict[str, dict[str, str]]): Mapping of project to its step results.
    """
    columns = ("python", *STEPS)
    name_width = max(len("project"), *(len(name) for name in all_results))
    header = "project".ljust(name_width) + "".join(f"  {col:<8}" for col in columns)

    print("\n=== Summary")
    print(header)
    print("-" * len(header))
    for project, results in all_results.items():
        print(project.ljust(name_width) + "".join(f"  {results[col]:<8}" for col in columns))

    changed = [project for project, results in all_results.items() if results["compile"] == CHANGED]
    if not changed:
        return

    print("\n=== Changed lock files")
    subprocess.run(
        ["git", "diff", "--stat", "--", "*requirements*.txt"], cwd=REPO_ROOT, check=False
    )
    print("\nProposed commit message (commit it yourself):")
    print("    build(deps): recompile requirements from requirements.in")
    print(f"\n    Updates the lock files in {', '.join(changed)}.")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse the command-line arguments.

    Args:
        argv (list[str] | None): The arguments to parse (defaults to sys.argv).

    Returns:
        argparse.Namespace: The parsed arguments.
    """
    parser = argparse.ArgumentParser(description=__doc__.split("\n", maxsplit=1)[0])
    parser.add_argument(
        "projects", nargs="*",
        help="Project folders to update (default: all folders with a requirements.in).",
    )
    parser.add_argument(
        "--upgrade", action="store_true",
        help="Upgrade all pins to the newest versions allowed by requirements.in.",
    )
    parser.add_argument(
        "--recreate", action="store_true", help="Delete and recreate each .venv from scratch."
    )
    parser.add_argument(
        "--no-compile", action="store_true",
        help="Skip compiling; only sync the venvs to the existing lock files.",
    )
    parser.add_argument("--no-checks", action="store_true", help="Skip pylint and pytest.")
    parser.add_argument(
        "--verbose", action="store_true", help="Always print the output of every command."
    )
    return parser.parse_args(argv)


def main() -> None:
    """Update the venvs of the selected projects and print a summary."""
    args = parse_args()
    available = find_projects()
    projects = args.projects or available

    unknown = [project for project in projects if project not in available]
    if unknown:
        print(f"Unknown project(s): {', '.join(unknown)}. Available: {', '.join(available)}")
        sys.exit(2)

    print(f"Using Python {sys.version.split()[0]} ({sys.executable})")
    all_results = {project: update_project(project, args) for project in projects}
    print_summary(all_results)

    failed = any(FAILED in results.values() for results in all_results.values())
    sys.exit(1 if failed else 0)


if __name__ == "__main__":  # pragma: no cover
    main()
