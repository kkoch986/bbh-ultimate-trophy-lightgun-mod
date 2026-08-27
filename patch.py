#!/usr/bin/env python3
"""
Big Buck Hunter: Ultimate Trophy - Light Gun Mod Patch
Hides the on-screen weapon and reticle so the game works better with a real
light gun / arcade cabinet setup.

What it does:
- Disables the on-screen Shotgun2D, Shotgun and Crossbow GameObjects.
- Disables each weapon's visual holder and all renderer components under it.
- Disables the CursorWindow reticle GameObject and its controlling script.

The script auto-detects the game install directory on Windows, Linux and
Batocera. You can also run it from inside the game folder.
"""

import os
import sys
import shutil
from pathlib import Path

GAME_NAME = "BigBuckHunter_UltimateTrophy"
BACKUP_SUFFIX = ".original"
WEAPON_ROOTS = ["Shotgun2D", "Shotgun", "Crossbow"]
WEAPON_NAME_PATTERNS = {
    "shotgun", "shotgun2d", "crossbow", "crossbow_rig", "crossbow_bolt",
    "bolt_blue", "bolt_green", "bolt_orange", "bolt_yellow",
    "bbh_gun", "bbh_gungreytest", "gun", "muzzle", "barrel",
}


def candidate_game_dirs():
    """Yield possible absolute paths to the game root directory."""
    # Current working directory
    yield Path.cwd()

    # Directory containing this script
    yield Path(__file__).parent

    # Same parent as this script (when mod folder lives next to BBH.exe)
    yield Path(__file__).parent.parent

    # Standard Linux Steam library
    home = Path.home()
    yield home / ".local" / "share" / "Steam" / "steamapps" / "common" / GAME_NAME

    # Batocera Flatpak Steam
    batocera_base = Path("/userdata/saves/flatpak/data/.var/app/com.valvesoftware.Steam")
    yield batocera_base / ".local/share/Steam/steamapps/common" / GAME_NAME
    yield batocera_base / "data/Steam/steamapps/common" / GAME_NAME

    # Batocera system Steam (add-ons)
    yield Path("/userdata/system/add-ons/steam/.local/share/Steam/steamapps/common") / GAME_NAME


def find_game_dir():
    """Return the game root directory, or None if not found."""
    for candidate in candidate_game_dirs():
        if (candidate / "BBH.exe").is_file() and (candidate / "BBH_Data").is_dir():
            return candidate
    return None


def ensure_unitypy():
    try:
        import UnityPy
        return UnityPy
    except ImportError:
        import subprocess
        print("UnityPy not found. Installing into a temporary venv...")
        venv = Path(__file__).parent / ".venv"
        if not venv.exists():
            subprocess.check_call([sys.executable, "-m", "venv", str(venv)])
        pip = venv / ("Scripts/pip.exe" if os.name == "nt" else "bin/pip")
        subprocess.check_call([str(pip), "install", "UnityPy"])
        py = venv / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
        os.execv(str(py), [str(py), __file__])


def load_bundle(path: Path):
    import UnityPy
    env = UnityPy.load(str(path))
    by_path = {obj.path_id: obj for obj in env.objects}
    return env, by_path


def get_name(obj):
    try:
        data = obj.read()
        return getattr(data, "name", "") or getattr(data, "m_Name", "")
    except Exception:
        return ""


def go_children(go_obj, by_path):
    """Yield child GameObjects of a GameObject by walking its Transform."""
    data = go_obj.read()
    for comp_pair in data.m_Component:
        comp = comp_pair.component.read()
        if comp_pair.component.type.name == "Transform":
            for child_ptr in comp.m_Children:
                child_t = by_path.get(child_ptr.path_id)
                if child_t:
                    child_go = child_t.read().m_GameObject.read()
                    yield by_path[child_go.object_reader.path_id]
                    yield from go_children(by_path[child_go.object_reader.path_id], by_path)
            break


def disable_gameobject(obj, by_path):
    """Disable a GameObject and persist the change."""
    data = obj.read()
    if data.m_IsActive:
        data.m_IsActive = False
        obj.save_typetree(data)
        return True
    return False


def disable_renderers_under(go_obj, by_path):
    """Disable all MeshRenderer/SkinnedMeshRenderer/SpriteRenderer under a GO."""
    changed = False
    renderer_types = {"MeshRenderer", "SkinnedMeshRenderer", "SpriteRenderer"}
    for child in [go_obj, *go_children(go_obj, by_path)]:
        child_data = child.read()
        for comp_pair in child_data.m_Component:
            comp_type = comp_pair.component.type.name
            if comp_type in renderer_types:
                rend_obj = by_path.get(comp_pair.component.path_id)
                if not rend_obj:
                    continue
                rend = rend_obj.read()
                if rend.m_Enabled:
                    rend.m_Enabled = 0
                    rend_obj.save_typetree(rend)
                    changed = True
    return changed


def patch_weapon_bundle(bundle_path: Path):
    env, by_path = load_bundle(bundle_path)
    modified = False

    renderer_types = {"MeshRenderer", "SkinnedMeshRenderer", "SpriteRenderer"}

    # Phase 1: Identify GOs that have MonoBehaviours (logic controllers)
    logic_go_ids = set()
    for obj in env.objects:
        if obj.type.name != "GameObject":
            continue
        go_data = obj.read()
        for comp_pair in go_data.m_Component:
            if comp_pair.component.type.name == "MonoBehaviour":
                logic_go_ids.add(obj.path_id)
                break

    # Phase 2: Disable renderers on ALL weapon-related GOs
    # (but never disable the GO itself if it has a MonoBehaviour)
    weapon_gos = []
    for obj in env.objects:
        if obj.type.name != "GameObject":
            continue
        name = get_name(obj)
        if not name:
            continue
        name_lower = name.lower().strip()
        if name_lower in WEAPON_NAME_PATTERNS or name in WEAPON_ROOTS:
            weapon_gos.append((obj, name))

    print(f"  Found {len(weapon_gos)} weapon-related GameObject(s)")
    print(f"  {len(logic_go_ids)} GO(s) have MonoBehaviours (keeping active)")

    for go_obj, name in weapon_gos:
        is_logic = go_obj.path_id in logic_go_ids

        # Only disable non-logic GOs
        if not is_logic:
            if disable_gameobject(go_obj, by_path):
                print(f"  Disabled visual GO '{name}'")
                modified = True

        # Always disable renderers on this GO and children
        for child in [go_obj, *go_children(go_obj, by_path)]:
            child_data = child.read()
            for comp_pair in child_data.m_Component:
                comp_type = comp_pair.component.type.name
                if comp_type in renderer_types:
                    rend_obj = by_path.get(comp_pair.component.path_id)
                    if not rend_obj:
                        continue
                    rend = rend_obj.read()
                    if rend.m_Enabled:
                        rend.m_Enabled = 0
                        rend_obj.save_typetree(rend)
                        child_name = get_name(child)
                        print(f"  Disabled renderer on '{child_name}' ({comp_type})")
                        modified = True

    # Phase 3: Also disable any renderer whose owning GO name matches
    for obj in env.objects:
        if obj.type.name not in renderer_types:
            continue
        rend = obj.read()
        if not rend.m_Enabled:
            continue
        try:
            go_ref = getattr(rend, "m_GameObject", None)
            if go_ref and go_ref.path_id:
                go_obj = by_path.get(go_ref.path_id)
                if go_obj and go_obj.type.name == "GameObject":
                    go_name = get_name(go_obj).lower()
                    if go_name in WEAPON_NAME_PATTERNS or go_name in WEAPON_ROOTS:
                        rend.m_Enabled = 0
                        obj.save_typetree(rend)
                        print(f"  Disabled orphan renderer on GO '{go_name}'")
                        modified = True
        except Exception:
            pass

    if not modified:
        print("  Nothing to change.")
        return

    out = env.file.save()
    backup_path = bundle_path.with_suffix(bundle_path.suffix + BACKUP_SUFFIX)
    if not backup_path.exists():
        print(f"  Creating backup: {backup_path}")
        shutil.copy2(bundle_path, backup_path)

    with open(bundle_path, "wb") as f:
        f.write(out)
    print(f"  Wrote patched bundle: {bundle_path}")


def patch_reticle_bundle(bundle_path: Path):
    env, by_path = load_bundle(bundle_path)
    modified = False

    reticle_names = {"CursorWindow", "TargetCursorWindow", "Cursor", "Reticle",
                     "gunreticle", "ReticleHit", "TargetCursor"}

    # Only disable VISUAL components (Canvas, Image, GraphicRaycaster)
    # Never disable GOs or MonoBehaviours — they handle input logic
    visual_types = {"Canvas", "Image", "RawImage", "GraphicRaycaster"}

    for obj in env.objects:
        if obj.type.name != "GameObject":
            continue
        name = get_name(obj)
        if not name:
            continue
        name_lower = name.lower()
        if name_lower not in {n.lower() for n in reticle_names}:
            continue

        # Disable visual components on the reticle GO itself
        go_data = obj.read()
        for comp_pair in go_data.m_Component:
            ctype = comp_pair.component.type.name
            if ctype in visual_types:
                comp_obj = by_path.get(comp_pair.component.path_id)
                if not comp_obj:
                    continue
                comp = comp_obj.read()
                if comp.m_Enabled:
                    comp.m_Enabled = 0
                    comp_obj.save_typetree(comp)
                    print(f"  Disabled {ctype} on '{name}'")
                    modified = True

        # Disable visual components on children (Canvas -> Image hierarchy)
        for child in go_children(obj, by_path):
            child_data = child.read()
            for comp_pair in child_data.m_Component:
                ctype = comp_pair.component.type.name
                if ctype in visual_types:
                    comp_obj = by_path.get(comp_pair.component.path_id)
                    if not comp_obj:
                        continue
                    comp = comp_obj.read()
                    if comp.m_Enabled:
                        comp.m_Enabled = 0
                        comp_obj.save_typetree(comp)
                        child_name = get_name(child)
                        print(f"  Disabled {ctype} on child '{child_name}'")
                        modified = True

    if not modified:
        print("  Nothing to change.")
        return

    out = env.file.save()
    backup_path = bundle_path.with_suffix(bundle_path.suffix + BACKUP_SUFFIX)
    if not backup_path.exists():
        print(f"  Creating backup: {backup_path}")
        shutil.copy2(bundle_path, backup_path)

    with open(bundle_path, "wb") as f:
        f.write(out)
    print(f"  Wrote patched bundle: {bundle_path}")


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
    ensure_unitypy()

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
        print(f"\n=== Patching: {game_dir} ===")
        bundle_dir = game_dir / "BBH_Data" / "StreamingAssets" / "aa" / "StandaloneWindows64"

        if not bundle_dir.is_dir():
            print(f"WARNING: Cannot find bundle directory: {bundle_dir}")
            continue

        weapon_bundle = bundle_dir / "abd4eaaf5ee36d5445d05f049913a21d.bundle"
        reticle_bundle = bundle_dir / "4bb9c63b88eb661db8f5d56fe5a64ea1.bundle"

        if weapon_bundle.exists():
            print(f"Patching {weapon_bundle.name}...")
            patch_weapon_bundle(weapon_bundle)
        else:
            print(f"WARNING: Weapon bundle not found: {weapon_bundle}")

        if reticle_bundle.exists():
            print(f"Patching {reticle_bundle.name}...")
            patch_reticle_bundle(reticle_bundle)
        else:
            print(f"WARNING: Reticle bundle not found: {reticle_bundle}")

    print("\nDone. Original files backed up with suffix '.original'.")
    print("To revert, run: python BBH_LightGun_Mod/revert.py")


if __name__ == "__main__":
    main()
