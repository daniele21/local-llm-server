const { test, expect } = require('@playwright/test');

const OVERVIEW_VISUAL_FINGERPRINT = '10000001180000010000080000000001060000030600000104000001000000013061c79b0010431b0001010300000001060101810e0029810c001803000041c7000041cf0000002900000061000000010004000100860001040100010001000108010001200100010e000001060100010000000009c000010080000100000000';
const EVALUATION_VISUAL_FINGERPRINT = '00000000280000000b000000630000000040000043400000000000000000000000040000024c00000000000000000000000000002c5000000c00000000000000080000000800000000000000000000004a6882480040000000000000000000000000000013000123000000000000000000000001000260010000000100000000';

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

async function visualFingerprint(page, locator) {
  await page.evaluate(async () => {
    if (document.fonts?.ready) await document.fonts.ready;
  });
  const screenshot = await locator.screenshot({ animations: 'disabled' });
  const base64 = screenshot.toString('base64');
  return page.evaluate(async ({ encoded }) => {
    const rows = 32;
    const columns = 33;
    const image = new Image();
    image.src = `data:image/png;base64,${encoded}`;
    await image.decode();

    const canvas = document.createElement('canvas');
    canvas.width = columns;
    canvas.height = rows;
    const context = canvas.getContext('2d', { willReadFrequently: true });
    context.imageSmoothingEnabled = true;
    context.imageSmoothingQuality = 'high';
    context.drawImage(image, 0, 0, columns, rows);
    const pixels = context.getImageData(0, 0, columns, rows).data;

    const luminance = (index) => Math.round(
      (pixels[index] * 299 + pixels[index + 1] * 587 + pixels[index + 2] * 114) / 1000,
    );
    const bits = [];
    for (let row = 0; row < rows; row += 1) {
      for (let column = 0; column < columns - 1; column += 1) {
        const left = (row * columns + column) * 4;
        const right = left + 4;
        // Ignore tiny antialiasing/compositor differences while preserving visible edge changes.
        bits.push(luminance(left) - luminance(right) > 4 ? 1 : 0);
      }
    }

    let hex = '';
    for (let index = 0; index < bits.length; index += 4) {
      const nibble = bits.slice(index, index + 4).reduce((value, bit) => (value << 1) | bit, 0);
      hex += nibble.toString(16);
    }
    return hex;
  }, { encoded: base64 });
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

test('stable overview decision surface matches its targeted perceptual visual fingerprint', async ({ page }) => {
  await openStudio(page, '/overview');
  await expect(page.locator('.overview-readiness-strip')).toBeVisible();
  const surface = page.locator('#overview-tab');
  const fingerprint = await visualFingerprint(page, surface);
  expect(fingerprint).toBe(OVERVIEW_VISUAL_FINGERPRINT);
});

test('stable evaluation setup form matches its targeted perceptual visual fingerprint', async ({ page }) => {
  await openStudio(page, '/evaluations');
  const form = page.locator('[data-evaluation-form][data-product-semantics="true"]');
  await expect(form).toBeVisible();
  const fingerprint = await visualFingerprint(page, form);
  expect(fingerprint).toBe(EVALUATION_VISUAL_FINGERPRINT);
});
