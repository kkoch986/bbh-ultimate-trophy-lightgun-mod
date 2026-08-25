Big Buck Hunter: Ultimate Trophy - Light Gun Mod
==================================================

Purpose: hides the on-screen weapon and reticle so the game can be played
with a real light gun / arcade cabinet without the fake gun/cursor covering
the screen.

What is changed
---------------
In the Addressables asset bundles the patch disables:
- The on-screen weapon roots: Shotgun2D, Shotgun and Crossbow.
- Each weapon's visual holder GameObject and all renderer components below it.
- The CursorWindow reticle GameObject and its controlling script.

Because the visuals are disabled in the prefab, spawned instances will also
start disabled.

Supported platforms
-------------------
- Windows (run from the game folder).
- Linux Steam install.
- Batocera Flatpak Steam install.

The script auto-detects the game directory in the common locations. You can
also run it from inside the game folder.

Install
-------
1. Copy the "BBH_LightGun_Mod" folder next to BBH.exe in the game directory.
2. Open a terminal / SSH session.
3. Run:
       python BBH_LightGun_Mod/patch.py
   The script will back up the original bundles before patching.

On Batocera you can run from anywhere:

    python /userdata/saves/flatpak/data/.var/app/com.valvesoftware.Steam/.local/share/Steam/steamapps/common/BigBuckHunter_UltimateTrophy/BBH_LightGun_Mod/patch.py

Uninstall / Revert
------------------
Run:
    python BBH_LightGun_Mod/revert.py

Notes
-----
- A working Python 3 install is required. The script will create a small
  temporary virtual environment and install UnityPy automatically.
- This mod edits local asset bundles only; no executable or code changes.
- Use at your own risk. Online features are not tested.
