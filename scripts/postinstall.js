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

// Accept both pre-namespace and previous category-prefix names.
const legacySkillNames = Object.freeze({
  "dev-done-flow": "skills-workflow-dev",
  "grill-me-cn": "skills-review-plan",
  "humanizer": "skills-writing-humanizer",
  "idea-hook-forge": "skills-research-hook-forge",
  "lit-speed-read": "skills-research-quick-read",
  "llm-research-grill": "skills-review-research",
  "paddleocr-vl": "skills-convert-document",
  "paper-weaver": "skills-research-deep-read",
  "parallel-executor-with-trellis": "skills-workflow-parallel",
  "prompt-amplifier": "skills-writing-prompt",
  "ref-classify": "skills-library-classify",
  "ref-rename": "skills-library-rename",
  "rethlas": "skills-math-proof",
  "tavily-search": "skills-web-search",
  "topic-refiner": "skills-research-topic",
  "trans-criptase": "skills-session-trans-criptase",
  "trellis-task-orchestrator": "skills-workflow-trellis",
  "write-research-grill": "skills-review-writing",
  "academic-topic-refiner": "skills-research-topic",
  "academic-radar": "skills-research-radar",
  "academic-search": "skills-research-search",
  "academic-lit-speed-read": "skills-research-quick-read",
  "academic-paper-weaver": "skills-research-deep-read",
  "academic-idea-hook-forge": "skills-research-hook-forge",
  "ai-research-writing-skill": "skills-writing-research-paper",
  "research-paper-writing": "skills-writing-paper-sections",
  "academic-humanizer": "skills-writing-humanizer",
  "writing-style": "skills-writing-style",
  "writing-prompt-amplifier": "skills-writing-prompt",
  "academic-llm-research-grill": "skills-review-research",
  "academic-write-research-grill": "skills-review-writing",
  "review-grill-me-cn": "skills-review-plan",
  "academic-ref-classify": "skills-library-classify",
  "academic-ref-rename": "skills-library-rename",
  "workflow-dev-done-flow": "skills-workflow-dev",
  "workflow-parallel-executor-with-trellis": "skills-workflow-parallel",
  "workflow-trellis-task-orchestrator": "skills-workflow-trellis",
  "agent-trans-criptase": "skills-session-trans-criptase",
  "handoff": "skills-session-handoff",
  "document-paddleocr-vl": "skills-convert-document",
  "media-transcript": "skills-convert-media",
  "web-tavily-search": "skills-web-search",
  "math-rethlas": "skills-math-proof"
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
    "skills-writing-research-paper",
    "skills-writing-humanizer",
    "skills-research-hook-forge",
    "skills-research-quick-read",
    "skills-review-research",
    "skills-research-deep-read",
    "skills-research-radar",
    "skills-library-classify",
    "skills-library-rename",
    "skills-research-search",
    "skills-research-topic",
    "skills-review-writing",
    "skills-session-trans-criptase",
    "skills-convert-document",
    "skills-session-handoff",
    "skills-math-proof",
    "skills-convert-media",
    "skills-writing-paper-sections",
    "skills-review-plan",
    "skills-web-search",
    "skills-workflow-dev",
    "skills-workflow-parallel",
    "skills-workflow-trellis",
    "skills-writing-prompt",
    "skills-writing-style"
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
