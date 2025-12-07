// scripts/validate_kb.js
//
// Simple sanity checks for the 3i/ATLAS KB:
// - JSON well-formed
// - tier fields only use allowed values

const fs = require("fs");
const path = require("path");

const ROOT = process.cwd();

// KB files we want to validate
const KB_FILES = [
  "knowledge_base_merged_v2.json",
  "sources.json",
  "kb_updates_cumulative.json",
  "tags_index.json"
];

const ALLOWED_TIERS = new Set([
  "T1", "T2", "T3", "T4",
  "F0", "F1", "F2", "F3", "F4", "F5", "F6", "F7"
]);

function readJson(filePath) {
  const full = path.join(ROOT, filePath);
  const raw = fs.readFileSync(full, "utf8");
  try {
    return JSON.parse(raw);
  } catch (err) {
    console.error(`❌ ${filePath} is not valid JSON: ${err.message}`);
    process.exitCode = 1;
    return null;
  }
}

function checkTierField(obj, pathSoFar = "") {
  if (obj && typeof obj === "object") {
    if (Object.prototype.hasOwnProperty.call(obj, "tier")) {
      const val = obj.tier;
      if (!ALLOWED_TIERS.has(val)) {
        console.error(
          `❌ Invalid tier "${val}" at ${pathSoFar ? pathSoFar + "." : ""}tier`
        );
        process.exitCode = 1;
      }
    }

    if (Array.isArray(obj)) {
      obj.forEach((item, idx) =>
        checkTierField(item, `${pathSoFar}[${idx}]`)
      );
    } else {
      for (const key of Object.keys(obj)) {
        const nextPath = pathSoFar ? `${pathSoFar}.${key}` : key;
        checkTierField(obj[key], nextPath);
      }
    }
  }
}

function main() {
  console.log("🔍 Validating KB JSON files and tier fields...");

  KB_FILES.forEach((file) => {
    if (!fs.existsSync(path.join(ROOT, file))) {
      console.warn(`⚠️  KB file missing (skipping): ${file}`);
      return;
    }

    console.log(`✅ Checking ${file}...`);
    const data = readJson(file);
    if (data) {
      checkTierField(data, path.basename(file, ".json"));
    }
  });

  if (process.exitCode && process.exitCode !== 0) {
    console.error("❌ KB validation failed.");
    process.exit(process.exitCode);
  } else {
    console.log("✅ KB validation passed.");
  }
}

main();
