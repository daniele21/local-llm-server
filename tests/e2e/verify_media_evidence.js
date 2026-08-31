#!/usr/bin/env node

const fs = require('node:fs');
const path = require('node:path');

const reportPath = process.argv[2] || 'test-results/playwright-results.json';
const report = JSON.parse(fs.readFileSync(reportPath, 'utf8'));

const journeyTests = {
  'control-plane-status-and-navigation': [
    /control-plane routes stay in-document and survive refresh and browser history/i,
  ],
  'chat-inference-and-recovery': [
    /a failed inference does not poison the next request/i,
  ],
  'model-runtime-management': [
    /models and runtimes owns the lifecycle, resource recovery and deep-linked detail surface/i,
  ],
  'evaluation-review-and-repeatability': [
    /evaluation result uses semantic evidence values and progressively disclosed run identity/i,
    /general-purpose evaluation sends and records reasoning OFF/i,
  ],
};

function walkSuites(suites, parents = [], specs = []) {
  for (const suite of suites || []) {
    const next = suite.title ? [...parents, suite.title] : parents;
    for (const spec of suite.specs || []) {
      specs.push({ ...spec, fullTitle: [...next, spec.title].filter(Boolean).join(' ') });
    }
    walkSuites(suite.suites || [], next, specs);
  }
  return specs;
}

function existingAttachment(attachment) {
  if (!attachment?.path) return false;
  if (path.isAbsolute(attachment.path)) return fs.existsSync(attachment.path);
  const candidates = [
    path.resolve(attachment.path),
    path.resolve(path.dirname(reportPath), attachment.path),
  ];
  return candidates.some((candidate) => fs.existsSync(candidate));
}

const specs = walkSuites(report.suites || []);
const errors = [];
const manifest = {
  schema_version: 1,
  evidence_kind: 'local_llm_server_ui_e2e_media_v1',
  report: reportPath,
  journeys: {},
};

for (const [journey, patterns] of Object.entries(journeyTests)) {
  const matchingSpecs = specs.filter((spec) => patterns.some((pattern) => pattern.test(spec.fullTitle)));
  const passingResults = matchingSpecs.flatMap((spec) =>
    (spec.tests || []).flatMap((test) =>
      (test.results || [])
        .filter((result) => result.status === 'passed')
        .map((result) => ({ title: spec.fullTitle, result })),
    ),
  );

  const screenshots = passingResults.flatMap(({ result }) =>
    (result.attachments || []).filter(
      (attachment) => attachment.contentType === 'image/png' && existingAttachment(attachment),
    ),
  );
  const videos = passingResults.flatMap(({ result }) =>
    (result.attachments || []).filter(
      (attachment) => attachment.contentType?.startsWith('video/') && existingAttachment(attachment),
    ),
  );

  manifest.journeys[journey] = {
    status: passingResults.length && screenshots.length && videos.length ? 'PASS' : 'E2E_EVIDENCE_INCOMPLETE',
    mapped_tests: [...new Set(passingResults.map(({ title }) => title))],
    screenshot_count: screenshots.length,
    video_count: videos.length,
  };

  if (!passingResults.length) errors.push(`${journey}: no passing representative UI test`);
  if (!screenshots.length) errors.push(`${journey}: missing screenshot artifact`);
  if (!videos.length) errors.push(`${journey}: missing complete test video artifact`);
}

fs.mkdirSync('test-results', { recursive: true });
fs.writeFileSync('test-results/ui-e2e-media-manifest.json', `${JSON.stringify(manifest, null, 2)}\n`);

if (errors.length) {
  console.error('UI E2E media evidence: FAIL');
  for (const error of errors) console.error(`- ${error}`);
  process.exit(1);
}
console.log('UI E2E media evidence: PASS');
