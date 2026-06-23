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
  for (const line of match[1].split(/\r?\n/)) {
    if (!line.trim()) {
      continue;
    }
    const parsed = line.match(/^([A-Za-z0-9_-]+):\s*(.*)$/);
    if (!parsed) {
      fail(`Unsupported frontmatter line in ${path.relative(repoRoot, filePath)}: ${line}`);
      continue;
    }
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
