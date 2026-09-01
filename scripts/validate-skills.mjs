import fs from "node:fs";
import path from "node:path";

const repoRoot = process.cwd();
const skillsRoot = path.join(repoRoot, "skills");
const errors = [];

function fail(message) {
  errors.push(message);
}

function readText(filePath) {
  return fs.readFileSync(filePath, "utf8");
}

function parseFrontmatter(filePath) {
  const text = readText(filePath);
  const match = text.match(/^---\r?\n([\s\S]*?)\r?\n---\r?\n?/);
  if (!match) {
    fail(`Missing YAML frontmatter: ${path.relative(repoRoot, filePath)}`);
    return null;
  }
  const fields = {};
  let currentField = null;
  for (const line of match[1].split(/\r?\n/)) {
    if (!line.trim()) {
      continue;
    }
    const parsed = line.match(/^([A-Za-z0-9_-]+):\s*(.*)$/);
    if (!parsed) {
      if (currentField && /^\s+-\s+\S/.test(line)) {
        continue;
      }
      fail(`Unsupported frontmatter line in ${path.relative(repoRoot, filePath)}: ${line}`);
      continue;
    }
    currentField = parsed[1];
    fields[parsed[1]] = parsed[2];
  }
  return fields;
}

function parseOpenAiYaml(filePath) {
  const text = readText(filePath);
  const lines = text.split(/\r?\n/);
  const result = {};
  let inInterface = false;
  for (const line of lines) {
    if (/^interface:\s*$/.test(line)) {
      inInterface = true;
      result.interface = {};
      continue;
    }
    if (!inInterface) {
      continue;
    }
    if (!/^  /.test(line)) {
      if (line.trim()) {
        inInterface = false;
      }
      continue;
    }
    const match = line.trim().match(/^([A-Za-z0-9_]+):\s*"?(.+?)"?$/);
    if (match) {
      result.interface[match[1]] = match[2];
    }
  }
  return result;
}

function walkDirectories(root, names, found = []) {
  if (!fs.existsSync(root)) {
    return found;
  }
  for (const entry of fs.readdirSync(root, { withFileTypes: true })) {
    if (!entry.isDirectory()) {
      continue;
    }
    const fullPath = path.join(root, entry.name);
    if (names.includes(entry.name)) {
      found.push(path.relative(repoRoot, fullPath));
    }
    walkDirectories(fullPath, names, found);
  }
  return found;
}

function walkFiles(root, fileName, found = []) {
  if (!fs.existsSync(root)) {
    return found;
  }
  for (const entry of fs.readdirSync(root, { withFileTypes: true })) {
    const fullPath = path.join(root, entry.name);
    if (entry.isDirectory()) {
      walkFiles(fullPath, fileName, found);
    } else if (entry.isFile() && entry.name === fileName) {
      found.push(path.relative(repoRoot, fullPath));
    }
  }
  return found;
}

if (!fs.existsSync(skillsRoot) || !fs.statSync(skillsRoot).isDirectory()) {
  fail("Missing skills/ directory.");
}

const skillDirs = fs.existsSync(skillsRoot)
  ? fs.readdirSync(skillsRoot, { withFileTypes: true }).filter((entry) => entry.isDirectory())
  : [];

if (skillDirs.length === 0) {
  fail("skills/ must contain at least one skill directory.");
}

const kebabCase = /^[a-z0-9]+(?:-[a-z0-9]+)*$/;
const skillList = [];

for (const entry of skillDirs) {
  const dirName = entry.name;
  const dirPath = path.join(skillsRoot, dirName);
  const skillMd = path.join(dirPath, "SKILL.md");
  const yamlPath = path.join(dirPath, "agents", "openai.yaml");

  if (!fs.existsSync(skillMd)) {
    fail(`Missing SKILL.md: skills/${dirName}`);
    continue;
  }

  const frontmatter = parseFrontmatter(skillMd);
  if (!frontmatter) {
    continue;
  }

  if (!("name" in frontmatter) || !("description" in frontmatter)) {
    fail(`Frontmatter must contain name and description: skills/${dirName}/SKILL.md`);
  }

  if (!kebabCase.test(frontmatter.name || "")) {
    fail(`Frontmatter name must be lowercase kebab-case: skills/${dirName}/SKILL.md`);
  }

  if ((frontmatter.name || "") !== dirName) {
    fail(`Frontmatter name must match directory name: skills/${dirName}/SKILL.md`);
  }

  if (!fs.existsSync(yamlPath)) {
    fail(`Missing agents/openai.yaml: skills/${dirName}`);
  } else {
    const yaml = parseOpenAiYaml(yamlPath);
    if (!yaml.interface?.display_name || !yaml.interface?.short_description) {
      fail(`agents/openai.yaml must contain interface.display_name and interface.short_description: skills/${dirName}`);
    } else if (yaml.interface.display_name !== dirName) {
      fail(`agents/openai.yaml interface.display_name must match directory name: skills/${dirName}`);
    }
  }

  skillList.push({
    name: dirName,
    path: `skills/${dirName}`,
    description: frontmatter.description || ""
  });
}

const skillsJsonPath = path.join(repoRoot, "skills.json");
if (!fs.existsSync(skillsJsonPath)) {
  fail("Missing skills.json.");
} else {
  try {
    const parsed = JSON.parse(readText(skillsJsonPath));
    if (!Array.isArray(parsed.skills)) {
      fail("skills.json must contain a skills array.");
    } else {
      for (const item of parsed.skills) {
        if (!item.path || !fs.existsSync(path.join(repoRoot, item.path))) {
          fail(`skills.json path does not exist: ${item.path}`);
        }
      }
    }
  } catch (error) {
    fail(`Invalid JSON in skills.json: ${error.message}`);
  }
}

const forbiddenDirs = [
  "node_modules",
  ".venv",
  "__pycache__",
  ".cache",
  ".paddlex",
  "dist",
  "build"
];

const foundForbidden = walkDirectories(repoRoot, forbiddenDirs);
for (const forbidden of foundForbidden) {
  fail(`Forbidden directory present: ${forbidden}`);
}

const forbiddenPublishDirs = [
  ".agents",
  ".claude",
  ".codex",
  ".claude-plugin",
  ".git",
  ".github",
  ".pytest_cache",
  ".trellis",
  "__pycache__",
  ".cache",
  "dist",
  "build",
  "node_modules",
  "test",
  "tests"
];

const foundForbiddenPublishDirs = walkDirectories(skillsRoot, forbiddenPublishDirs);
for (const forbidden of foundForbiddenPublishDirs) {
  fail(`Non-publishable directory present in skills payload: ${forbidden}`);
}

const expectedSkillFiles = new Set(skillDirs.map((entry) => `skills/${entry.name}/SKILL.md`));
const foundSkillFiles = walkFiles(skillsRoot, "SKILL.md");
for (const skillFile of foundSkillFiles) {
  if (!expectedSkillFiles.has(skillFile)) {
    fail(`Nested SKILL.md is not allowed in publishable skills: ${skillFile}`);
  }
}

const forbiddenPublishFiles = [
  "AGENTS.md",
  "CLAUDE.md",
  "GEMINI.md",
  "Goal.md",
  ".mcp.json",
  ".gitignore",
  ".gitattributes",
  "embed-config.json"
];

const forbiddenRootPublishDirs = [
  "data",
  "index"
];

for (const skillDir of skillDirs) {
  for (const dirName of forbiddenRootPublishDirs) {
    const dirPath = path.join(skillsRoot, skillDir.name, dirName);
    if (fs.existsSync(dirPath) && fs.statSync(dirPath).isDirectory()) {
      fail(`Generated state directory present in skills payload: skills/${skillDir.name}/${dirName}`);
    }
  }

  for (const fileName of forbiddenPublishFiles) {
    const filePath = path.join(skillsRoot, skillDir.name, fileName);
    if (fs.existsSync(filePath)) {
      fail(`Non-publishable file present in skills payload: skills/${skillDir.name}/${fileName}`);
    }
  }
}

if (errors.length > 0) {
  console.error("Skill validation failed:");
  for (const error of errors) {
    console.error(`- ${error}`);
  }
  process.exit(1);
}

console.log("Skill validation passed.");
for (const skill of skillList.sort((a, b) => a.name.localeCompare(b.name))) {
  console.log(`- ${skill.name}: ${skill.path}`);
}
