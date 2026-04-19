# Skill Packager

A tool for grouping related AI agent skills into a single package with internal dispatch. Reduces top-level skill count and trigger noise while preserving all capabilities.

## Why?

When you have too many skills installed, the agent's trigger accuracy degrades. Research shows accuracy drops from 90%+ (under 20 skills) to 20% (at 200 skills). Skill Packager lets you bundle related skills — like pdf, docx, pptx, xlsx — into one `document` package, keeping your top-level count low without losing functionality.

## How It Works

Each package is a normal skill directory with a `sub/` folder containing the bundled skills:

```
skills/
  document/                ← Package (looks like a normal skill)
    SKILL.md               ← Trigger description + dispatch instructions
    pack.md                ← Auto-generated sub-skill descriptions for matching
    sub/
      pdf/SKILL.md
      docx/SKILL.md
      pptx/SKILL.md
      xlsx/SKILL.md
```

The agent sees only one skill at the top level. When triggered, it reads `pack.md` to identify the matching sub-skill, then follows that sub-skill's instructions.

## Installation

Copy or clone into your agent's skills directory:

```bash
cp -r package-skill/ /path/to/skills/
```

Or with [ClawHub](https://clawhub.ai):

```bash
npx clawhub install package-skill
```

## Usage

### Create a Package

```bash
python skills/package-skill/scripts/create.py create <name> -d "trigger description" <skill1> [skill2 ...]
```

Example:
```bash
python skills/package-skill/scripts/create.py create document \
  -d "Document file operations — reading, creating, editing, or converting PDF, Word, PowerPoint, and Excel files." \
  pdf docx pptx xlsx
```

### Update Registry

```bash
python skills/package-skill/scripts/update.py <package-name>
```

### Add a Sub-Skill

```bash
python skills/package-skill/scripts/create.py add <package-name> <skill-name>
```

### Remove a Sub-Skill

```bash
python skills/package-skill/scripts/create.py remove <package-name> <skill-name>
```

## Design Principles

- **Sub-skills stay intact** — no content is stripped, only relocated to `sub/`
- **Package is a normal skill** — the agent treats it like any other skill
- **Dispatch is explicit** — the agent reads the sub-skill SKILL.md on demand
- **Reversible** — `remove` promotes a sub-skill back to top-level

## Compatibility

Designed for [nanobot](https://github.com/HKUDS/nanobot) and compatible with any agent framework that uses SKILL.md-based skill loading (Claude Code, Cursor, etc.).

## License

MIT
