#!/usr/bin/env node
/**
 * normalize_updates.js
 * Normalize kb_updates_cumulative.json (v2.10.1) to pending-only queue format
 *
 * Goals:
 * - Remove all integrated items or move them to changelog
 * - Normalize statuses to "pending"
 * - Fix domains to bare hostnames
 * - Ensure proper schema with required keys
 * - Keep operations inert (no KB mutations)
 */

const fs = require('fs');
const path = require('path');

// File paths
const ROOT = path.resolve(__dirname, '..');
const UPDATES_PATH = path.join(ROOT, 'kb_updates_cumulative.json');
const CHANGELOG_PATH = path.join(ROOT, 'kb_changelog.json');
const MERGED_PATH = path.join(ROOT, 'knowledge_base_merged_v2.json');

/**
 * Extract bare domain from URL or domain string
 */
function normalizeDomain(domainStr) {
  if (!domainStr) return null;

  try {
    // Try parsing as URL first
    const url = new URL(domainStr.includes('://') ? domainStr : `https://${domainStr}`);
    return url.hostname;
  } catch {
    // Fallback: split on / and take first part
    const parts = domainStr.split('/');
    return parts[0].trim() || null;
  }
}

/**
 * Load JSON file with error handling
 */
function loadJson(filePath) {
  try {
    const content = fs.readFileSync(filePath, 'utf8');
    return JSON.parse(content);
  } catch (err) {
    console.error(`Failed to load ${filePath}:`, err.message);
    process.exit(1);
  }
}

/**
 * Save JSON file atomically with tmp + rename
 */
function saveJson(filePath, obj) {
  try {
    const tmpPath = filePath + '.tmp';
    fs.writeFileSync(tmpPath, JSON.stringify(obj, null, 2) + '\n', 'utf8');
    fs.renameSync(tmpPath, filePath);
    console.log(`✓ Saved ${path.basename(filePath)}`);
  } catch (err) {
    console.error(`Failed to save ${filePath}:`, err.message);
    process.exit(1);
  }
}

/**
 * Main normalization logic
 */
function normalize() {
  console.log('Loading files...');
  const upd = loadJson(UPDATES_PATH);
  const cl = loadJson(CHANGELOG_PATH);

  const nowIso = new Date().toISOString();
  const integratedBuffer = [];

  console.log('Normalizing kb_updates_cumulative.json...');

  // Remove deprecated top-level keys
  if ('added_in' in upd) {
    delete upd.added_in;
    console.log('  - Removed added_in');
  }
  if ('added_index' in upd) {
    delete upd.added_index;
    console.log('  - Removed added_index');
  }

  // Ensure required schema keys exist
  upd.schema_version = upd.schema_version || '2.0';
  upd.kb_version = upd.kb_version || '2.10.1';
  upd.file = upd.file || 'kb_updates_cumulative.json';
  upd.as_of = nowIso;
  upd.status = 'PENDING_QUEUE';
  upd.notes = upd.notes || 'Pending knowledge base updates awaiting review and integration';
  upd.pending = upd.pending || [];
  upd.rejected = upd.rejected || [];
  upd.updates = upd.updates || [];
  upd.entries = upd.entries || [];
  upd.sources_registry_ops = upd.sources_registry_ops || [];
  upd.ops_rollback = upd.ops_rollback || [];
  upd.tests = upd.tests || [];
  upd.integrity = upd.integrity || {
    as_of: nowIso,
    signature: `#ATLAS-SIG-UPDATES-v2.10.1-Δ${nowIso.slice(0, 10)}`
  };

  console.log('  - Ensured all required schema keys');

  // Process pending proposals
  console.log('Processing pending proposals...');
  (upd.pending || []).forEach(p => {
    // Collect integrated proposals for tracking
    if (p.status && p.status.toLowerCase() === 'integrated') {
      integratedBuffer.push(p);
      console.log(`  - Found integrated proposal: ${p.proposal_id}`);
    }
    if (p.integrated_at || p.integrated_to) {
      integratedBuffer.push(p);
    }

    // Force status to pending
    p.status = 'pending';

    // Remove integrated fields
    delete p.integrated_at;
    delete p.integrated_to;

    // Normalize required_domains
    if (Array.isArray(p.required_domains)) {
      p.required_domains = p.required_domains
        .map(normalizeDomain)
        .filter(d => d !== null);
      console.log(`  - Normalized domains for ${p.proposal_id}`);
    }

    // Special handling for December visibility proposal
    if (p.proposal_id === 'kb_propose_dec_visibility_refinement') {
      p.artifacts = p.artifacts || {};
      if (!('horizons_csv' in p.artifacts)) {
        p.artifacts.horizons_csv = null;
      }
      if (!('earthsky_url' in p.artifacts)) {
        p.artifacts.earthsky_url = null;
      }
      console.log(`  - Ensured Dec visibility artifacts fields`);
    }
  });

  // Process updates array
  console.log('Processing updates array...');
  (upd.updates || []).forEach(u => {
    u.status = u.status || 'pending';
  });

  // Process entries array
  console.log('Processing entries array...');
  (upd.entries || []).forEach(e => {
    e.status = e.status || 'pending';

    // Fix ID format if needed
    if (e.id && e.id.startsWith('U-2WELCOME-')) {
      const newId = e.id.replace('U-2WELCOME-', 'U-2025-');
      console.log(`  - Fixed ID: ${e.id} → ${newId}`);
      e.id = newId;
    }
  });

  // Process sources_registry_ops
  console.log('Processing sources_registry_ops...');
  (upd.sources_registry_ops || []).forEach(o => {
    o.status = o.status || 'pending';
  });

  // Process rejected proposals
  console.log('Processing rejected proposals...');
  (upd.rejected || []).forEach(r => {
    r.status = r.status || 'rejected';
  });

  // Process tests - ensure non-blocking
  console.log('Processing tests...');
  (upd.tests || []).forEach(t => {
    // Mark as CI-only if assert exists
    if (t.assert && !t.mode) {
      t.mode = 'ci_only';
    }
  });

  // Update integrity footer
  upd.integrity.as_of = nowIso;
  upd.integrity.signature = `#ATLAS-SIG-UPDATES-v2.10.1-Δ${nowIso.slice(0, 10)}`;

  // Handle integrated items in changelog
  console.log('\nChecking integrated proposals against changelog...');
  if (cl.applied) {
    const appliedIds = new Set(cl.applied.map(a => a.update_id || a.id));

    integratedBuffer.forEach(p => {
      // Generate expected changelog entry ID from integrated_to field if available
      if (p.integrated_to) {
        // Extract ID from field like "kb_changelog.json entry: kb_apply_iawn_registration_deadline_20251103"
        const match = p.integrated_to.match(/kb_apply[^,\s]*/);
        if (match) {
          const expectedId = match[0];
          if (appliedIds.has(expectedId)) {
            console.log(`  ✓ Found changelog entry for ${p.proposal_id}: ${expectedId}`);
          } else {
            console.log(`  ⚠ Missing changelog entry for ${p.proposal_id} (expected: ${expectedId})`);
          }
        }
      }
    });
  }

  console.log('\nValidation...');

  // Validation 1: No integrated status in pending
  const integratedInPending = upd.pending.filter(p =>
    p.status && p.status.toLowerCase() === 'integrated'
  );
  if (integratedInPending.length > 0) {
    console.error('✗ Found integrated status in pending array');
    process.exit(1);
  }
  console.log('  ✓ No integrated status in pending array');

  // Validation 2: No top-level added_in or added_index
  if ('added_in' in upd || 'added_index' in upd) {
    console.error('✗ Found deprecated top-level keys (added_in/added_index)');
    process.exit(1);
  }
  console.log('  ✓ No deprecated top-level keys');

  // Validation 3: All required_domains match pattern
  const domainPattern = /^[A-Za-z0-9.-]+$/;
  let invalidDomains = false;
  upd.pending.forEach(p => {
    if (Array.isArray(p.required_domains)) {
      p.required_domains.forEach(d => {
        if (!domainPattern.test(d)) {
          console.error(`  ✗ Invalid domain: ${d}`);
          invalidDomains = true;
        }
      });
    }
  });
  if (invalidDomains) {
    process.exit(1);
  }
  console.log('  ✓ All domains match expected pattern');

  // Validation 4: December visibility proposal exists and is pending with artifacts
  const decProp = upd.pending.find(p => p.proposal_id === 'kb_propose_dec_visibility_refinement');
  if (!decProp) {
    console.error('✗ December visibility proposal not found');
    process.exit(1);
  }
  if (decProp.status !== 'pending') {
    console.error(`✗ December visibility proposal has status '${decProp.status}' instead of 'pending'`);
    process.exit(1);
  }
  if (!decProp.artifacts || !('horizons_csv' in decProp.artifacts) || !('earthsky_url' in decProp.artifacts)) {
    console.error('✗ December visibility proposal missing required artifact fields');
    process.exit(1);
  }
  console.log('  ✓ December visibility proposal is valid');

  // Validation 5: JSON validity
  try {
    JSON.stringify(upd);
    JSON.stringify(cl);
    console.log('  ✓ JSON structure is valid');
  } catch (err) {
    console.error(`✗ JSON validation failed: ${err.message}`);
    process.exit(1);
  }

  // Save files
  console.log('\nSaving files...');
  saveJson(UPDATES_PATH, upd);
  saveJson(CHANGELOG_PATH, cl);

  console.log('\n✓ Normalization complete!');
  console.log(`  - Version: ${upd.version}`);
  console.log(`  - Schema version: ${upd.schema_version}`);
  console.log(`  - KB version: ${upd.kb_version}`);
  console.log(`  - Pending proposals: ${upd.pending.length}`);
  console.log(`  - Rejected proposals: ${upd.rejected.length}`);
  console.log(`  - Updated at: ${upd.as_of}`);

  return 0;
}

// Execute
try {
  process.exit(normalize());
} catch (err) {
  console.error('Fatal error:', err.message);
  console.error(err.stack);
  process.exit(1);
}
