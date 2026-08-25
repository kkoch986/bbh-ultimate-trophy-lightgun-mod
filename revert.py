#!/usr/bin/env python3
"""
Revert the Big Buck Hunter light-gun mod patch.
Restores the original asset bundles from their backups.
"""

import sys
from pathlib import Path

BUNDLE_DIR = Path("BBH_Data/StreamingAssets/aa/StandaloneWindows64")
BACKUP_SUFFIX = ".original"
BUNDLES = [
    "abd4eaaf5ee36d5445d05f049913a21d.bundle",
    "4bb9c63b88eb661db8f5d56fe5a64ea1.bundle",
]


def main():
    if not BUNDLE_DIR.is_dir():
        print(f"ERROR: Cannot find bundle directory: {BUNDLE_DIR}")
        print("Make sure you run this script from the game root.")
        sys.exit(1)

    for filename in BUNDLES:
        bundle_path = BUNDLE_DIR / filename
        backup_path = bundle_path.with_suffix(bundle_path.suffix + BACKUP_SUFFIX)
        if not backup_path.exists():
            print(f"No backup found for {filename}, skipping.")
            continue
        print(f"Restoring {filename}...")
        backup_path.replace(bundle_path)

    print("\nDone. Original bundles restored.")


if __name__ == "__main__":
    main()
