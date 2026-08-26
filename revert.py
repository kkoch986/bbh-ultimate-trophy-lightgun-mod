#!/usr/bin/env python3
"""
Revert the Big Buck Hunter light-gun mod patch.
Restores the original asset bundles from their backups.

Auto-detects the game install directory on Windows, Linux and Batocera.
"""

import sys
from pathlib import Path

GAME_NAME = "BigBuckHunter_UltimateTrophy"
BACKUP_SUFFIX = ".original"
BUNDLES = [
    "abd4eaaf5ee36d5445d05f049913a21d.bundle",
    "4bb9c63b88eb661db8f5d56fe5a64ea1.bundle",
]


def candidate_game_dirs():
    """Yield possible absolute paths to the game root directory."""
    yield Path.cwd()
    yield Path(__file__).parent
    yield Path(__file__).parent.parent

    home = Path.home()
    yield home / ".local" / "share" / "Steam" / "steamapps" / "common" / GAME_NAME

    batocera_base = Path("/userdata/saves/flatpak/data/.var/app/com.valvesoftware.Steam")
    yield batocera_base / ".local/share/Steam/steamapps/common" / GAME_NAME
    yield batocera_base / "data/Steam/steamapps/common" / GAME_NAME

    yield Path("/userdata/system/add-ons/steam/.local/share/Steam/steamapps/common") / GAME_NAME


def find_all_game_dirs():
    """Return all valid game root directories."""
    seen = set()
    found = []
    for candidate in candidate_game_dirs():
        resolved = candidate.expanduser().resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        if resolved.is_dir() and (resolved / "BBH.exe").is_file() and (resolved / "BBH_Data").is_dir():
            found.append(resolved)
    return found


def main():
    if len(sys.argv) > 1:
        game_dirs = [Path(sys.argv[1]).expanduser().resolve()]
    else:
        game_dirs = find_all_game_dirs()

    if not game_dirs:
        print("ERROR: Cannot find Big Buck Hunter: Ultimate Trophy install directory.")
        print("Tried the following locations:")
        for candidate in candidate_game_dirs():
            print(f"  - {candidate}")
        print("\nRun this script from the game folder, or pass the path as an argument:")
        print(f"  python {Path(__file__).name} /path/to/{GAME_NAME}")
        sys.exit(1)

    for game_dir in game_dirs:
        print(f"\n=== Reverting: {game_dir} ===")
        bundle_dir = game_dir / "BBH_Data" / "StreamingAssets" / "aa" / "StandaloneWindows64"

        if not bundle_dir.is_dir():
            print(f"WARNING: Cannot find bundle directory: {bundle_dir}")
            continue

        for filename in BUNDLES:
            bundle_path = bundle_dir / filename
            backup_path = bundle_path.with_suffix(bundle_path.suffix + BACKUP_SUFFIX)
            if not backup_path.exists():
                print(f"No backup found for {filename}, skipping.")
                continue
            print(f"Restoring {filename}...")
            backup_path.replace(bundle_path)

    print("\nDone. Original bundles restored.")


if __name__ == "__main__":
    main()
