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

// Accept configuration written before the category-prefix migration.
const legacySkillNames = Object.freeze({
  "dev-done-flow": "workflow-dev-done-flow",
  "grill-me-cn": "review-grill-me-cn",
  "humanizer": "academic-humanizer",
  "idea-hook-forge": "academic-idea-hook-forge",
  "lit-speed-read": "academic-lit-speed-read",
  "llm-research-grill": "academic-llm-research-grill",
  "paddleocr-vl": "document-paddleocr-vl",
  "paper-weaver": "academic-paper-weaver",
  "parallel-executor-with-trellis": "workflow-parallel-executor-with-trellis",
  "prompt-amplifier": "writing-prompt-amplifier",
  "ref-classify": "academic-ref-classify",
  "ref-rename": "academic-ref-rename",
  "rethlas": "math-rethlas",
  "tavily-search": "web-tavily-search",
  "topic-refiner": "academic-topic-refiner",
  "trans-criptase": "agent-trans-criptase",
  "trellis-task-orchestrator": "workflow-trellis-task-orchestrator",
  "write-research-grill": "academic-write-research-grill"
});

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
    "academic-humanizer",
    "academic-idea-hook-forge",
    "academic-lit-speed-read",
    "academic-llm-research-grill",
    "academic-paper-weaver",
    "academic-radar",
    "academic-ref-classify",
    "academic-ref-rename",
    "academic-search",
    "academic-topic-refiner",
    "academic-write-research-grill",
    "agent-trans-criptase",
    "document-paddleocr-vl",
    "math-rethlas",
    "media-transcript",
    "review-grill-me-cn",
    "web-tavily-search",
    "workflow-dev-done-flow",
    "workflow-parallel-executor-with-trellis",
    "workflow-trellis-task-orchestrator",
    "writing-prompt-amplifier",
    "writing-style"
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
  const requestedSkills = Array.isArray(config.include)
    ? config.include.map((skill) => legacySkillNames[skill] ?? skill)
    : null;
  const toInstall = requestedSkills
    ? available.filter((skill) => requestedSkills.includes(skill))
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
