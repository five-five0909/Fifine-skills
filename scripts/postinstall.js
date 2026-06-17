#!/usr/bin/env node
/**
 * Fifine-skills postinstall
 * Distributes skills to AI tool directories in the target project.
 *
 * Reads optional <project>/skills.json:
 *   { "include": ["lit-speed-read"], "targets": ["claude", "codex"] }
 */

const fs = require('fs');
const path = require('path');

// Project root = where `npm install` was run (3 levels up from node_modules/@fifine/skills/scripts/)
const projectRoot = path.resolve(__dirname, '..', '..', '..', '..');
const skillsRoot = path.resolve(__dirname, '..');
const publishableSkillsPath = path.join(__dirname, 'publishable-skills.json');

function readPublishableSkills() {
  const fallback = [
    'paper-weaver',
    'lit-speed-read',
    'grill-me-cn',
    'llm-research-grill',
    'write-research-grill',
    'prompt-amplifier',
    'tavily-search',
    'topic-refiner',
    'ref-rename',
    'ref-classify',
    'trellis-task-orchestrator',
    'parallel-executor-with-trellis',
  ];
  if (!fs.existsSync(publishableSkillsPath)) return fallback;
  try {
    const parsed = JSON.parse(fs.readFileSync(publishableSkillsPath, 'utf8'));
    return Array.isArray(parsed.skills) ? parsed.skills : fallback;
  } catch {
    return fallback;
  }
}

// Skill directories in this package (anything with a SKILL.md)
function getAvailableSkills(publishableSkills) {
  return publishableSkills.filter(name => {
    const skillMd = path.join(skillsRoot, name, 'SKILL.md');
    return fs.existsSync(skillMd);
  });
}

// Read project-level skills.json if present
function readProjectConfig() {
  const configPath = path.join(projectRoot, 'skills.json');
  if (!fs.existsSync(configPath)) return {};
  try {
    return JSON.parse(fs.readFileSync(configPath, 'utf8'));
  } catch {
    return {};
  }
}

// Detect which AI tool directories exist in the project
function detectTargets() {
  const candidates = [
    { key: 'claude', dir: '.claude/skills' },
    { key: 'codex',  dir: '.codex/skills'  },
    { key: 'agents', dir: '.agents/skills'  },
  ];
  return candidates.filter(c =>
    fs.existsSync(path.join(projectRoot, c.dir.split('/')[0]))
  );
}

function copyDir(src, dest) {
  fs.mkdirSync(dest, { recursive: true });
  for (const entry of fs.readdirSync(src, { withFileTypes: true })) {
    const s = path.join(src, entry.name);
    const d = path.join(dest, entry.name);
    if (entry.isDirectory()) copyDir(s, d);
    else fs.copyFileSync(s, d);
  }
}

function main() {
  const config = readProjectConfig();
  const publishableSkills = readPublishableSkills();
  const available = getAvailableSkills(publishableSkills);

  const toInstall = config.include
    ? available.filter(s => config.include.includes(s))
    : available;

  let targets;
  if (config.targets) {
    const allTargets = [
      { key: 'claude', dir: '.claude/skills' },
      { key: 'codex',  dir: '.codex/skills'  },
      { key: 'agents', dir: '.agents/skills'  },
    ];
    targets = allTargets.filter(t => config.targets.includes(t.key));
  } else {
    targets = detectTargets();
  }

  if (targets.length === 0) {
    console.log('[fifine-skills] No AI tool directories found (.claude / .codex / .agents). Skipping.');
    return;
  }

  if (toInstall.length === 0) {
    console.log('[fifine-skills] No publishable skills matched the current config. Skipping.');
    return;
  }

  console.log(`[fifine-skills] Installing ${toInstall.length} skill(s) to: ${targets.map(t => t.dir).join(', ')}`);

  for (const skill of toInstall) {
    const src = path.join(skillsRoot, skill);
    for (const target of targets) {
      const dest = path.join(projectRoot, target.dir, skill);
      copyDir(src, dest);
      console.log(`  ✓ ${skill} → ${target.dir}/${skill}`);
    }
  }

  console.log('[fifine-skills] Done.');
}

main();
