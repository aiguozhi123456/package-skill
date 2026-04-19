#!/usr/bin/env python3
"""Skill Packager — create, add, remove sub-skills in a package. Use update.py for scan/pack.md."""

import argparse
import re
import shutil
import sys
from pathlib import Path

SKILLS_DIR = Path(__file__).resolve().parents[2]  # skills/ directory (parent of package-skill/)


def parse_frontmatter(text: str) -> dict:
    """Extract YAML frontmatter fields from a SKILL.md."""
    m = re.match(r'^---\s*\n(.*?)\n---', text, re.DOTALL)
    if not m:
        return {}
    fm = {}
    for line in m.group(1).splitlines():
        if ':' in line:
            key, _, val = line.partition(':')
            val = val.strip().strip('"').strip("'")
            fm[key.strip()] = val
    return fm


def read_skill_description(skill_path: Path) -> tuple[str, str]:
    """Return (name, description) from a skill's SKILL.md frontmatter."""
    skill_md = skill_path / "SKILL.md"
    if not skill_md.exists():
        print(f"  Warning: {skill_md} not found", file=sys.stderr)
        return skill_path.name, ""
    text = skill_md.read_text(encoding="utf-8")
    fm = parse_frontmatter(text)
    return fm.get("name", skill_path.name), fm.get("description", "")


def scan_subs(package_dir: Path) -> list[dict]:
    """Scan sub/*/SKILL.md and return list of {name, description, dir}."""
    subs = []
    sub_dir = package_dir / "sub"
    if not sub_dir.exists():
        return subs
    for child in sorted(sub_dir.iterdir()):
        if child.is_dir() and (child / "SKILL.md").exists():
            name, desc = read_skill_description(child)
            subs.append({"name": name, "description": desc, "dir": child.name})
    return subs


def write_pack_md(package_dir: Path, subs: list[dict]):
    """Write pack.md registry (also used by update.py)."""
    package_name = package_dir.name
    lines = [f"# {package_name} Registry\n"]
    lines.append(f"Auto-generated. {len(subs)} sub-skills.\n")
    for s in subs:
        lines.append(f"- **{s['name']}** — {s['description']}")
    (package_dir / "pack.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"  Updated pack.md ({len(subs)} entries)")


def generate_skill_md(package_name: str, description: str, subs: list[dict]) -> str:
    """Generate a SKILL.md for the package."""
    sub_names = ", ".join(s["name"] for s in subs)
    return f"""---
name: {package_name}
description: "This is a skill package containing: {sub_names}. {description}"
---

# {package_name.title()} Package

This is a skill package bundling {len(subs)} sub-skills: {sub_names}.

## How to Use

1. Read [pack.md](pack.md) to determine which sub-skill matches the current task
2. Read the matching sub-skill: `read_file("skills/{package_name}/sub/<sub-skill>/SKILL.md")`
3. Follow that sub-skill's instructions
"""


def cmd_create(args):
    """Create a new package from existing skills."""
    package_name = args.package
    skill_names = args.skills

    package_dir = SKILLS_DIR / package_name
    if package_dir.exists():
        print(f"Error: {package_dir} already exists", file=sys.stderr)
        sys.exit(1)

    # Validate source skills exist
    source_paths = []
    for name in skill_names:
        src = SKILLS_DIR / name
        if not src.exists():
            print(f"Error: skill '{name}' not found at {src}", file=sys.stderr)
            sys.exit(1)
        source_paths.append(src)

    # Create structure
    (package_dir / "sub").mkdir(parents=True)
    print(f"Created {package_dir}/")

    # Copy skills into sub/
    subs = []
    for src, name in zip(source_paths, skill_names):
        dest = package_dir / "sub" / name
        shutil.copytree(src, dest)
        sname, sdesc = read_skill_description(dest)
        subs.append({"name": sname, "description": sdesc, "dir": name})
        print(f"  Copied {name} -> sub/{name}/")

    # Write pack.md
    write_pack_md(package_dir, subs)

    # Write SKILL.md
    skill_md = generate_skill_md(package_name, args.description, subs)
    (package_dir / "SKILL.md").write_text(skill_md, encoding="utf-8")
    print(f"  Generated SKILL.md")

    # Remove original top-level skills
    for src in source_paths:
        shutil.rmtree(src)
        print(f"  Removed original: {src.name}/")

    print(f"\nPackage '{package_name}' created with {len(subs)} sub-skills.")
    print(f"Review and edit {package_dir / 'SKILL.md'} to refine the trigger description.")


def cmd_scan(args):
    """Scan sub-skills and update pack.md."""
    package_dir = SKILLS_DIR / args.package
    if not package_dir.exists():
        print(f"Error: package '{args.package}' not found", file=sys.stderr)
        sys.exit(1)

    subs = scan_subs(package_dir)
    write_pack_md(package_dir, subs)
    print(f"Package '{args.package}': {len(subs)} sub-skills found.")
    for s in subs:
        print(f"  - {s['name']}")


def cmd_add(args):
    """Add a skill to an existing package."""
    package_dir = SKILLS_DIR / args.package
    src = SKILLS_DIR / args.skill

    if not package_dir.exists():
        print(f"Error: package '{args.package}' not found", file=sys.stderr)
        sys.exit(1)
    if not src.exists():
        print(f"Error: skill '{args.skill}' not found", file=sys.stderr)
        sys.exit(1)

    dest = package_dir / "sub" / args.skill
    if dest.exists():
        print(f"Error: sub-skill '{args.skill}' already exists in package", file=sys.stderr)
        sys.exit(1)

    shutil.copytree(src, dest)
    print(f"Copied {args.skill} -> sub/{args.skill}/")

    # Remove original
    shutil.rmtree(src)
    print(f"Removed original: {args.skill}/")

    # Update pack.md
    subs = scan_subs(package_dir)
    write_pack_md(package_dir, subs)
    print(f"Updated pack.md ({len(subs)} entries)")
    print(f"Remember to update the package SKILL.md trigger description.")


def cmd_remove(args):
    """Remove a sub-skill from a package and restore it to top-level."""
    package_dir = SKILLS_DIR / args.package
    sub_path = package_dir / "sub" / args.skill
    dest = SKILLS_DIR / args.skill

    if not sub_path.exists():
        print(f"Error: sub-skill '{args.skill}' not found in package", file=sys.stderr)
        sys.exit(1)
    if dest.exists():
        print(f"Error: top-level '{args.skill}' already exists", file=sys.stderr)
        sys.exit(1)

    shutil.move(str(sub_path), str(dest))
    print(f"Restored {args.skill} -> skills/{args.skill}/")

    # Update pack.md
    subs = scan_subs(package_dir)
    if subs:
        write_pack_md(package_dir, subs)
    print(f"Updated pack.md ({len(subs)} entries remaining)")
    print(f"Remember to update the package SKILL.md trigger description.")


def main():
    parser = argparse.ArgumentParser(description="Skill Packager CLI")
    sub = parser.add_subparsers(dest="command")

    p_create = sub.add_parser("create", help="Create a new skill package")
    p_create.add_argument("package", help="Package name (e.g., document)")
    p_create.add_argument("-d", "--description", required=True, help="Trigger description for this package")
    p_create.add_argument("skills", nargs="+", help="Skill names to package")

    p_scan = sub.add_parser("scan", help="(Deprecated) Use update.py instead")
    p_scan.add_argument("package", help="Package name")

    p_add = sub.add_parser("add", help="Add a skill to an existing package")
    p_add.add_argument("package", help="Package name")
    p_add.add_argument("skill", help="Skill name to add")

    p_remove = sub.add_parser("remove", help="Remove sub-skill, restore to top-level")
    p_remove.add_argument("package", help="Package name")
    p_remove.add_argument("skill", help="Sub-skill name to remove")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)

    {"create": cmd_create, "scan": cmd_scan, "add": cmd_add, "remove": cmd_remove}[args.command](args)


if __name__ == "__main__":
    main()
