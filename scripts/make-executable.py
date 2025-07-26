#!/usr/bin/env python3
"""
Make Scripts Executable
Sets appropriate permissions on all setup scripts
"""

import os
import stat
from pathlib import Path


def make_executable(file_path: Path):
    """Make a file executable"""
    current_permissions = file_path.stat().st_mode
    new_permissions = current_permissions | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH
    file_path.chmod(new_permissions)
    print(f"Made executable: {file_path}")


def main():
    """Make all scripts executable"""
    root_dir = Path(__file__).parent.parent
    scripts_dir = root_dir / "scripts"
    
    # Scripts to make executable
    script_files = [
        root_dir / "setup.py",
        scripts_dir / "start-dev.py",
        scripts_dir / "stop-dev.py",
        scripts_dir / "start-docker.py",
        scripts_dir / "stop-docker.py",
        scripts_dir / "install-deps.py",
        scripts_dir / "health-check.py",
        scripts_dir / "make-executable.py"
    ]
    
    for script_file in script_files:
        if script_file.exists():
            try:
                make_executable(script_file)
            except Exception as e:
                print(f"Error making {script_file} executable: {e}")
        else:
            print(f"Script not found: {script_file}")
    
    print("All scripts have been made executable!")


if __name__ == "__main__":
    main()