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

Install
-------
1. Make sure the "BBH_LightGun_Mod" folder is next to BBH.exe.
2. Open a terminal in the game folder.
3. Run:
       python BBH_LightGun_Mod/patch.py
   The script will back up the original bundles before patching.

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
