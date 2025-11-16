"""
Batch Rename Script: RefleXion -> VerifiMind
Updates all occurrences across the entire project
"""

import os
import re
from pathlib import Path


def replace_in_file(file_path: Path, replacements: dict):
    """Replace all occurrences in a file"""
    try:
        # Read file
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        original_content = content

        # Apply all replacements
        for old, new in replacements.items():
            content = content.replace(old, new)

        # Only write if changes were made
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        return False
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False


def main():
    """Main renaming function"""

    # Define replacements (order matters!)
    replacements = {
        "RefleXion™": "VerifiMind™",
        "RefleXion": "VerifiMind",
        "REFLEXION": "VERIFIMIND",
        "reflexion": "verifimind",
    }

    # Project root
    project_root = Path(__file__).parent

    # File extensions to process
    extensions = ['.py', '.md', '.txt', '.json', '.xml', '.bat']

    # Directories to skip
    skip_dirs = {'venv', '.venv', 'env', '__pycache__', '.git', 'node_modules'}

    print("=" * 80)
    print("RENAMING PROJECT: RefleXion -> VerifiMind")
    print("=" * 80)
    print()

    files_processed = 0
    files_updated = 0

    # Process all files
    for file_path in project_root.rglob('*'):
        # Skip directories and non-matching extensions
        if file_path.is_dir():
            continue

        # Skip directories we don't want to process
        if any(skip_dir in file_path.parts for skip_dir in skip_dirs):
            continue

        # Check if file extension matches
        if file_path.suffix not in extensions:
            continue

        # Skip this script itself
        if file_path.name == 'rename_to_verifimind.py':
            continue

        files_processed += 1

        # Process file
        if replace_in_file(file_path, replacements):
            files_updated += 1
            print(f"[OK] Updated: {file_path.relative_to(project_root)}")

    print()
    print("=" * 80)
    print("RENAMING COMPLETE")
    print("=" * 80)
    print(f"Files processed: {files_processed}")
    print(f"Files updated: {files_updated}")
    print()
    print("Next steps:")
    print("1. Rename the project directory from 'RefleXion Project 2025' to 'VerifiMind Project 2025'")
    print("2. Test the system: python launch.py")
    print("3. Verify all functionality works")
    print()


if __name__ == "__main__":
    main()
