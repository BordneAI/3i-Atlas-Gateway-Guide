// scripts/validate_kb.js
//
// Sanity checks for the 3i/ATLAS KB:
// - JSON well-formed
// - tier fields only use allowed values
// - strict referential scanner v1.0.1 (Option A)

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
const CITATION_KEYS = new Set(["source_id", "source_ids", "sources", "citations"]);
const QUARANTINE_CONTAINER_KEYS = new Set([
  "quarantine", "_quarantine", "_quarantined", "quarantined_nodes"
]);
const ALLOWED_EXTERNAL_IDS = new Set();

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

function candidateId(id) {
  if (typeof id !== "string") return false;
  if (id.startsWith("_")) return false;
  if (!/^[A-Z0-9][A-Z0-9_-]{5,79}$/.test(id)) return false;
  return id.includes("-") || id.includes("_");
}

function isNonEmptyString(value) {
  return typeof value === "string" && value.trim().length > 0;
}

function isSourceRecord(key, value) {
  if (!candidateId(key)) return false;
  if (!value || typeof value !== "object" || Array.isArray(value)) return false;

  const hasRequiredStrings = (
    isNonEmptyString(value.tier) &&
    isNonEmptyString(value.title) &&
    (isNonEmptyString(value.type) || isNonEmptyString(value.publisher))
  );
  if (!hasRequiredStrings) return false;

  const hasUrls = Array.isArray(value.urls) &&
    value.urls.every((u) => typeof u === "string" && u.trim().length > 0);
  const hasPath = isNonEmptyString(value.path);
  const hasLegacyLocator = Array.isArray(value.urls);
  return hasUrls || hasPath || hasLegacyLocator;
}

function pushWarning(warnings, key, entry) {
  warnings[key].push(entry);
}

function extractRegistryAndQuarantine(sources, warnings) {
  const registryKeys = new Set();
  const topLevelKeys = Object.keys(sources || {});

  for (const key of topLevelKeys) {
    if (key === "_quarantined" || key === "_quarantined_meta") continue;
    const val = sources[key];
    if (isSourceRecord(key, val)) {
      registryKeys.add(key);
    } else if (candidateId(key) && val && typeof val === "object" && !Array.isArray(val)) {
      pushWarning(warnings, "source_record_missing_required_fields", { key });
    }
  }

  const quarantineKeys = new Set();
  const q = sources ? sources._quarantined : undefined;
  if (Array.isArray(q)) {
    for (const item of q) {
      if (typeof item === "string" && candidateId(item) && registryKeys.has(item)) {
        quarantineKeys.add(item);
      } else {
        pushWarning(warnings, "quarantine_container_schema_violation", {
          kind: "list_entry",
          value: item
        });
      }
    }
  } else if (q && typeof q === "object") {
    for (const [key, val] of Object.entries(q)) {
      if (isSourceRecord(key, val)) {
        quarantineKeys.add(key);
      } else {
        pushWarning(warnings, "quarantine_container_schema_violation", {
          kind: "object_entry",
          key
        });
      }
    }
  } else if (q !== undefined) {
    pushWarning(warnings, "quarantine_container_schema_violation", {
      kind: "container_type",
      value_type: typeof q
    });
  }

  return { registryKeys, quarantineKeys };
}

function scanKbCitations(kb, quarantineKeys, warnings) {
  const citedValidIds = new Set();
  const occurrences = [];

  function walk(node, path, noSurfaceAncestor, quarantineAncestor) {
    if (Array.isArray(node)) {
      node.forEach((child, idx) => {
        walk(child, `${path}[${idx}]`, noSurfaceAncestor, quarantineAncestor);
      });
      return;
    }
    if (!node || typeof node !== "object") return;

    const localNoSurface = noSurfaceAncestor || node.do_not_surface === true;
    for (const [key, value] of Object.entries(node)) {
      const nextPath = path ? `${path}.${key}` : key;
      const localQuarantine = quarantineAncestor || QUARANTINE_CONTAINER_KEYS.has(key);

      if (CITATION_KEYS.has(key)) {
        if (key === "source_id") {
          if (typeof value !== "string") {
            pushWarning(warnings, "citation_field_wrong_type", { path: nextPath, expected: "string" });
          } else if (candidateId(value)) {
            citedValidIds.add(value);
            occurrences.push({
              id: value,
              path: nextPath,
              surfaced: !localNoSurface && !localQuarantine
            });
          } else {
            pushWarning(warnings, "free_text_in_citation_fields", { path: nextPath, value });
          }
        } else if (Array.isArray(value)) {
          value.forEach((item, idx) => {
            const itemPath = `${nextPath}[${idx}]`;
            if (typeof item !== "string") {
              pushWarning(warnings, "non_string_in_citation_array", { path: itemPath });
              return;
            }
            if (candidateId(item)) {
              citedValidIds.add(item);
              occurrences.push({
                id: item,
                path: itemPath,
                surfaced: !localNoSurface && !localQuarantine
              });
            } else {
              pushWarning(warnings, "free_text_in_citation_fields", { path: itemPath, value: item });
            }
          });
        } else {
          pushWarning(warnings, "citation_field_wrong_type", { path: nextPath, expected: "array|string" });
        }
      }

      walk(value, nextPath, localNoSurface, localQuarantine);
    }
  }

  walk(kb, "knowledge_base_merged_v2", false, false);

  const quarantinedInSurfaced = new Set();
  for (const occ of occurrences) {
    if (quarantineKeys.has(occ.id) && occ.surfaced) {
      quarantinedInSurfaced.add(occ.id);
    }
  }

  return {
    citedValidIds,
    occurrences,
    quarantinedInSurfaced
  };
}

function main() {
  console.log("🔍 Validating KB JSON files, tiers, and strict referential integrity...");

  const loadedByName = {};
  KB_FILES.forEach((file) => {
    if (!fs.existsSync(path.join(ROOT, file))) {
      console.warn(`⚠️  KB file missing (skipping): ${file}`);
      return;
    }

    console.log(`✅ Checking ${file}...`);
    const data = readJson(file);
    if (data) {
      loadedByName[file] = data;
      checkTierField(data, path.basename(file, ".json"));
    }
  });

  // strict referential scanner v1.0.1
  const sources = loadedByName["sources.json"];
  const kb = loadedByName["knowledge_base_merged_v2.json"];
  if (sources && kb) {
    const warnings = {
      citation_field_wrong_type: [],
      non_string_in_citation_array: [],
      free_text_in_citation_fields: [],
      quarantine_container_schema_violation: [],
      source_record_missing_required_fields: [],
      duplicate_source_ids_detected: []
    };

    const { registryKeys, quarantineKeys } = extractRegistryAndQuarantine(sources, warnings);
    const { citedValidIds, quarantinedInSurfaced } = scanKbCitations(kb, quarantineKeys, warnings);

    const missingIds = [...citedValidIds]
      .filter((id) => !registryKeys.has(id) && !quarantineKeys.has(id) && !ALLOWED_EXTERNAL_IDS.has(id))
      .sort();
    const quarantinedInSurfacedList = [...quarantinedInSurfaced].sort();

    const warningCounts = Object.fromEntries(
      Object.entries(warnings).map(([k, v]) => [k, v.length])
    );
    const scannerSummary = {
      missing_ids: missingIds,
      quarantined_in_surfaced: quarantinedInSurfacedList,
      schema_warnings: warningCounts
    };
    console.log(`🧭 Strict referential summary: ${JSON.stringify(scannerSummary)}`);

    if (missingIds.length > 0) {
      console.error(`❌ missing_ids detected: ${missingIds.join(", ")}`);
      process.exitCode = 1;
    }
    if (quarantinedInSurfacedList.length > 0) {
      console.error(`❌ quarantined_in_surfaced detected: ${quarantinedInSurfacedList.join(", ")}`);
      process.exitCode = 1;
    }
  } else {
    console.warn("⚠️  Strict referential scanner skipped (sources.json or knowledge_base_merged_v2.json missing).");
  }

  if (process.exitCode && process.exitCode !== 0) {
    console.error("❌ KB validation failed.");
    process.exit(process.exitCode);
  } else {
    console.log("✅ KB validation passed.");
  }
}

main();
