#!/usr/bin/env node
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const projectRoot = path.resolve(__dirname, "..", "..", "..", "..");
const packageRoot = path.resolve(__dirname, "..");
const skillsRoot = path.join(packageRoot, "skills");
const publishableSkillsPath = path.join(__dirname, "publishable-skills.json");

function readJson(filePath, fallback) {
  if (!fs.existsSync(filePath)) {
    return fallback;
  }
  try {
    return JSON.parse(fs.readFileSync(filePath, "utf8"));
  } catch {
    return fallback;
  }
}

function readPublishableSkills() {
  const fallback = [
    "grill-me-cn",
    "idea-hook-forge",
    "lit-speed-read",
    "llm-research-grill",
    "paper-weaver",
    "parallel-executor-with-trellis",
    "prompt-amplifier",
    "ref-classify",
    "ref-rename",
    "tavily-search",
    "topic-refiner",
    "trellis-task-orchestrator",
    "write-research-grill"
  ];
  const parsed = readJson(publishableSkillsPath, { skills: fallback });
  return Array.isArray(parsed.skills) ? parsed.skills : fallback;
}

function getAvailableSkills(publishableSkills) {
  return publishableSkills.filter((name) => {
    const skillMd = path.join(skillsRoot, name, "SKILL.md");
    return fs.existsSync(skillMd);
  });
}

function readProjectConfig() {
  return readJson(path.join(projectRoot, "skills.json"), {});
}

function detectTargets() {
  const candidates = [
    { key: "claude", dir: ".claude/skills" },
    { key: "codex", dir: ".codex/skills" },
    { key: "agents", dir: ".agents/skills" }
  ];
  return candidates.filter((candidate) =>
    fs.existsSync(path.join(projectRoot, candidate.dir.split("/")[0]))
  );
}

function copyDir(src, dest) {
  fs.mkdirSync(dest, { recursive: true });
  for (const entry of fs.readdirSync(src, { withFileTypes: true })) {
    const sourcePath = path.join(src, entry.name);
    const targetPath = path.join(dest, entry.name);
    if (entry.isDirectory()) {
      copyDir(sourcePath, targetPath);
    } else {
      fs.copyFileSync(sourcePath, targetPath);
    }
  }
}

function main() {
  const config = readProjectConfig();
  const publishableSkills = readPublishableSkills();
  const available = getAvailableSkills(publishableSkills);
  const toInstall = Array.isArray(config.include)
    ? available.filter((skill) => config.include.includes(skill))
    : available;

  const allTargets = [
    { key: "claude", dir: ".claude/skills" },
    { key: "codex", dir: ".codex/skills" },
    { key: "agents", dir: ".agents/skills" }
  ];

  const targets = Array.isArray(config.targets)
    ? allTargets.filter((target) => config.targets.includes(target.key))
    : detectTargets();

  if (targets.length === 0) {
    console.log("[fifine-skills] No AI tool directories found (.claude / .codex / .agents). Skipping.");
    return;
  }

  if (toInstall.length === 0) {
    console.log("[fifine-skills] No publishable skills matched the current config. Skipping.");
    return;
  }

  console.log(`[fifine-skills] Installing ${toInstall.length} skill(s) to: ${targets.map((target) => target.dir).join(", ")}`);

  for (const skill of toInstall) {
    const src = path.join(skillsRoot, skill);
    for (const target of targets) {
      const dest = path.join(projectRoot, target.dir, skill);
      copyDir(src, dest);
      console.log(`  ${skill} -> ${target.dir}/${skill}`);
    }
  }

  console.log("[fifine-skills] Done.");
}

main();
