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

// Accept pre-namespace and previous category-prefix names while publishing
// only the current fifine-* namespace. The retired AI research writing skill
// is intentionally absent and is not redirected to another skill.
const legacySkillNames = Object.freeze({
  "dev-done-flow": "fifine-dev-done-flow",
  "grill-me-cn": "fifine-grill-me-cn",
  "humanizer": "fifine-live-humanizer",
  "idea-hook-forge": "fifine-idea-hook-forge",
  "lit-speed-read": "fifine-lit-speed-read",
  "llm-research-grill": "fifine-llm-research-grill",
  "paddleocr-vl": "fifine-paddleocr-vl",
  "paper-weaver": "fifine-paper-weaver",
  "parallel-executor-with-trellis": "fifine-parallel-executor-with-trellis",
  "prompt-amplifier": "fifine-prompt-amplifier",
  "ref-classify": "fifine-ref-classify",
  "ref-rename": "fifine-ref-rename",
  "rethlas": "fifine-rethlas",
  "tavily-search": "fifine-tavily-search",
  "topic-refiner": "fifine-topic-refiner",
  "trans-criptase": "fifine-trans-criptase",
  "trellis-task-orchestrator": "fifine-trellis-task-orchestrator",
  "write-research-grill": "fifine-write-research-grill",
  "academic-topic-refiner": "fifine-topic-refiner",
  "fifine-radar": "fifine-research-radar",
  "fifine-search": "fifine-research-search",
  "academic-radar": "fifine-research-radar",
  "academic-search": "fifine-research-search",
  "academic-lit-speed-read": "fifine-lit-speed-read",
  "academic-paper-weaver": "fifine-paper-weaver",
  "academic-idea-hook-forge": "fifine-idea-hook-forge",
  "research-paper-writing": "fifine-research-paper-writing",
  "academic-humanizer": "fifine-live-humanizer",
  "writing-style": "fifine-writing-style",
  "writing-prompt-amplifier": "fifine-prompt-amplifier",
  "academic-llm-research-grill": "fifine-llm-research-grill",
  "academic-write-research-grill": "fifine-write-research-grill",
  "review-grill-me-cn": "fifine-grill-me-cn",
  "academic-ref-classify": "fifine-ref-classify",
  "academic-ref-rename": "fifine-ref-rename",
  "workflow-dev-done-flow": "fifine-dev-done-flow",
  "workflow-parallel-executor-with-trellis": "fifine-parallel-executor-with-trellis",
  "workflow-trellis-task-orchestrator": "fifine-trellis-task-orchestrator",
  "agent-trans-criptase": "fifine-trans-criptase",
  "handoff": "fifine-handoff",
  "document-paddleocr-vl": "fifine-paddleocr-vl",
  "media-transcript": "fifine-media-transcript",
  "web-tavily-search": "fifine-tavily-search",
  "math-rethlas": "fifine-rethlas",
  "skills-writing-humanizer": "fifine-live-humanizer",
  "skills-research-hook-forge": "fifine-idea-hook-forge",
  "skills-research-quick-read": "fifine-lit-speed-read",
  "skills-review-research": "fifine-llm-research-grill",
  "skills-research-deep-read": "fifine-paper-weaver",
  "skills-research-radar": "fifine-research-radar",
  "skills-library-classify": "fifine-ref-classify",
  "skills-library-rename": "fifine-ref-rename",
  "skills-research-search": "fifine-research-search",
  "skills-research-topic": "fifine-topic-refiner",
  "skills-review-writing": "fifine-write-research-grill",
  "skills-session-trans-criptase": "fifine-trans-criptase",
  "skills-convert-document": "fifine-paddleocr-vl",
  "skills-session-handoff": "fifine-handoff",
  "skills-math-proof": "fifine-rethlas",
  "skills-convert-media": "fifine-media-transcript",
  "skills-review-plan": "fifine-grill-me-cn",
  "skills-writing-paper-sections": "fifine-research-paper-writing",
  "skills-web-search": "fifine-tavily-search",
  "skills-workflow-dev": "fifine-dev-done-flow",
  "skills-workflow-parallel": "fifine-parallel-executor-with-trellis",
  "skills-workflow-trellis": "fifine-trellis-task-orchestrator",
  "skills-writing-prompt": "fifine-prompt-amplifier",
  "skills-writing-style": "fifine-writing-style"
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
    "fifine-live-humanizer",
    "fifine-idea-hook-forge",
    "fifine-lit-speed-read",
    "fifine-llm-research-grill",
    "fifine-paper-weaver",
    "fifine-research-radar",
    "fifine-ref-classify",
    "fifine-ref-rename",
    "fifine-research-search",
    "fifine-topic-refiner",
    "fifine-write-research-grill",
    "fifine-trans-criptase",
    "fifine-paddleocr-vl",
    "fifine-handoff",
    "fifine-rethlas",
    "fifine-media-transcript",
    "fifine-research-paper-writing",
    "fifine-grill-me-cn",
    "fifine-tavily-search",
    "fifine-dev-done-flow",
    "fifine-parallel-executor-with-trellis",
    "fifine-trellis-task-orchestrator",
    "fifine-prompt-amplifier",
    "fifine-writing-style"
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
