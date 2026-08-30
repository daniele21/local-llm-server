const crypto = require('node:crypto');
const { test, expect } = require('@playwright/test');

const OVERVIEW_VISUAL_DIGEST = 'a2eac8e9abf5ba7a1f5a566cedf7fa6ef119ba3ae06a6ccda9bc0f2da023927b';
const EVALUATION_VISUAL_DIGEST = '__EVALUATION_FORM_BOOTSTRAP_DIGEST__';

test.use({
  viewport: { width: 1440, height: 1000 },
  colorScheme: 'dark',
  reducedMotion: 'reduce',
});

async function openStudio(page, route = '/overview') {
  await page.route('https://fonts.googleapis.com/**', (route) => route.abort());
  await page.route('https://fonts.gstatic.com/**', (route) => route.abort());
  await page.goto(route, { waitUntil: 'domcontentloaded' });
  await expect(page.getByRole('link', { name: 'Playground' })).toBeVisible();
}

async function imageDigest(locator) {
  const image = await locator.screenshot({ animations: 'disabled' });
  return crypto.createHash('sha256').update(image).digest('hex');
}

test('evaluation keeps scenario setup primary and advanced evidence controls disclosed on demand', async ({ page }) => {
  await openStudio(page, '/evaluations');

  const form = page.locator('[data-evaluation-form][data-product-semantics="true"]');
  await expect(form).toBeVisible();
  await expect(form.locator('[data-evaluation-model]')).toBeVisible();
  await expect(form.locator('[data-evaluation-test-set]')).toBeVisible();
  await expect(form.locator('[data-evaluation-samples]')).toBeVisible();

  const advanced = form.locator('[data-evaluation-advanced]');
  await expect(advanced.getByText('Advanced run settings', { exact: true })).toBeVisible();
  await expect(form.locator('[data-evaluation-seed]')).toBeHidden();
  await expect(form.locator('[data-evaluation-retain-content]')).toBeHidden();

  const library = page.locator('[data-evaluation-library]');
  await expect(library).toBeVisible();
  await expect(library.locator('[data-evaluation-import-file]')).toBeHidden();

  const evidenceContract = page.locator('[data-evaluation-contract-disclosure]');
  await expect(evidenceContract).toBeVisible();
  await expect(evidenceContract.getByText('Evidence-grade', { exact: true })).toBeHidden();

  const runButton = form.locator('[data-evaluation-start]');
  await expect(runButton).toHaveAttribute('data-variant', 'primary');
  await expect(runButton).toBeEnabled();

  await advanced.locator('summary').click();
  await expect(form.locator('[data-evaluation-seed]')).toBeVisible();
  await expect(form.locator('[data-evaluation-retain-content]')).toBeVisible();
});

test('evaluation result uses semantic evidence values and progressively disclosed run identity', async ({ page }) => {
  await openStudio(page, '/evaluations');

  const form = page.locator('[data-evaluation-form][data-product-semantics="true"]');
  await expect(form).toBeVisible();
  const samples = form.locator('[data-evaluation-samples]');
  await samples.selectOption({ index: 0 });
  await form.locator('[data-evaluation-start]').click();

  const result = page.locator('[data-evaluation-result]');
  await expect(result.getByRole('heading', { name: 'Evaluation result' })).toBeVisible({ timeout: 15_000 });
  const evidenceValues = result.locator('.evaluation-metric-card.ds-evidence-value');
  await expect(evidenceValues).toHaveCount(4);
  await expect(evidenceValues.first().locator('.ds-evidence-value__kind')).toBeVisible();

  const identity = result.locator('[data-evaluation-identity-disclosure]');
  await expect(identity).toBeVisible();
  await expect(identity.getByText('Runtime fingerprint', { exact: true })).toBeHidden();
  await identity.locator('summary').click();
  await expect(identity.getByText('Runtime fingerprint', { exact: true })).toBeVisible();
});

test('models and overview reuse canonical resource and evidence semantics', async ({ page }) => {
  await openStudio(page, '/models');
  const budget = page.locator('.control-plane-models__budget.ds-resource-budget');
  await expect(budget).toBeVisible();
  await expect(budget.locator('.ds-resource-budget__track')).toBeVisible();
  await expect(budget.locator('.ds-resource-budget__legend')).toBeVisible();
  await expect(page.locator('[data-model-action-status].ds-action-feedback')).toBeVisible();

  await page.getByRole('link', { name: 'Overview' }).click();
  const details = page.locator('.overview-evidence-details');
  await details.locator('summary').click();
  await expect(details.locator('.ds-metric.ds-evidence-value').first()).toBeVisible();
  await expect(details.locator('.ds-evidence-value__kind').first()).toBeVisible();
});

test('stable overview decision surface matches its targeted visual digest', async ({ page }) => {
  await openStudio(page, '/overview');
  await expect(page.locator('.overview-readiness-strip')).toBeVisible();
  const surface = page.locator('#overview-tab');
  const digest = await imageDigest(surface);
  expect(digest).toBe(OVERVIEW_VISUAL_DIGEST);
});

test('stable evaluation setup form matches its targeted visual digest', async ({ page }) => {
  await openStudio(page, '/evaluations');
  const form = page.locator('[data-evaluation-form][data-product-semantics="true"]');
  await expect(form).toBeVisible();
  const digest = await imageDigest(form);
  expect(digest).toBe(EVALUATION_VISUAL_DIGEST);
});
