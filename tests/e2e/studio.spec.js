const { test, expect } = require('@playwright/test');

async function openStudio(page) {
  await page.route('https://fonts.googleapis.com/**', (route) => route.abort());
  await page.route('https://fonts.gstatic.com/**', (route) => route.abort());
  await page.goto('/', { waitUntil: 'domcontentloaded' });
  await expect(page.getByRole('tab', { name: 'Playground' })).toBeVisible();
}

async function openPlayground(page) {
  await openStudio(page);
  await page.getByRole('tab', { name: 'Playground' }).click();
  await expect(page.locator('#chat-tab')).toBeVisible();

  const panel = page.locator('#advanced-params-panel');
  if (await panel.evaluate((element) => element.classList.contains('collapsible--collapsed'))) {
    await page.locator('#advanced-params-trigger').click();
  }

  await page.waitForFunction(() => {
    const control = document.querySelector('#param-enable-thinking');
    return Boolean(window.localLlmThinkingControls)
      && control?.dataset?.thinkingMode === 'switchable';
  });
  await expect(page.locator('#param-enable-thinking')).toBeEnabled();
  await expect(page.locator('#param-show-thinking')).toBeEnabled();
}

async function sendMessage(page, text = 'What is 17 + 25?') {
  const requestPromise = page.waitForRequest((request) => {
    const url = new URL(request.url());
    return request.method() === 'POST' && url.pathname === '/v1/chat/completions';
  });
  await page.locator('#chat-textarea').fill(text);
  await page.locator('#send-chat-btn').click();
  const request = await requestPromise;
  await expect(page.locator('#typing-status')).toBeHidden();
  return request.postDataJSON();
}

test('control-plane tabs support keyboard roving focus', async ({ page }) => {
  await openStudio(page);
  const tabs = page.getByRole('tab');
  await expect(tabs).toHaveCount(7);

  const overview = page.getByRole('tab', { name: 'Overview' });
  const models = page.getByRole('tab', { name: 'Models & Runtimes' });
  await overview.click();
  await overview.focus();
  await page.keyboard.press('ArrowDown');

  await expect(models).toBeFocused();
  await expect(models).toHaveAttribute('aria-selected', 'true');
  await expect(page.locator('#registry-tab')).toBeVisible();
});

test('switchable thinking sends an explicit OFF request', async ({ page }) => {
  await openPlayground(page);
  await page.locator('#param-enable-thinking').setChecked(false, { force: true });
  await page.locator('#param-show-thinking').setChecked(false, { force: true });

  const payload = await sendMessage(page);
  expect(payload.enable_thinking).toBe(false);
  expect(payload.show_thinking).toBe(false);
  await expect(page.locator('#chat-messages-container')).toContainText('42');
  await expect(page.locator('#chat-messages-container')).not.toContainText('private reasoning');
});

test('thinking can execute while reasoning stays hidden', async ({ page }) => {
  await openPlayground(page);
  await page.locator('#param-enable-thinking').setChecked(true, { force: true });
  await page.locator('#param-show-thinking').setChecked(false, { force: true });

  const payload = await sendMessage(page);
  expect(payload.enable_thinking).toBe(true);
  expect(payload.show_thinking).toBe(false);
  await expect(page.locator('#chat-messages-container')).toContainText('42');
  await expect(page.locator('#chat-messages-container')).not.toContainText('private reasoning');
});

test('structured JSON never mixes hidden reasoning into application output', async ({ page }) => {
  await openPlayground(page);
  await page.locator('#param-enable-thinking').setChecked(true, { force: true });
  await page.locator('#param-show-thinking').setChecked(false, { force: true });
  await page.locator('#param-force-json').setChecked(true, { force: true });

  const payload = await sendMessage(page, 'Return one JSON object.');
  expect(payload.enable_thinking).toBe(true);
  expect(payload.show_thinking).toBe(false);
  expect(payload.response_format).toEqual({ type: 'json_object' });
  await expect(page.locator('#chat-messages-container')).toContainText('{"answer":42}');
  await expect(page.locator('#chat-messages-container')).not.toContainText('private reasoning');
});

test('typed API failures render a useful UI error instead of object coercion', async ({ page }) => {
  await openPlayground(page);
  await page.route('**/v1/chat/completions', async (route) => {
    await route.fulfill({
      status: 502,
      contentType: 'application/json',
      body: JSON.stringify({
        detail: {
          code: 'invalid_model_output',
          message: 'Structured output is invalid model JSON.',
          retryable: false,
          details: {},
        },
      }),
    });
  });

  await page.locator('#chat-textarea').fill('Return JSON.');
  await page.locator('#send-chat-btn').click();
  await expect(page.locator('#chat-messages-container')).toContainText('Structured output is invalid model JSON.');
  await expect(page.locator('#chat-messages-container')).not.toContainText('[object Object]');
});

test('general-purpose evaluation sends and records reasoning OFF', async ({ page }) => {
  await openStudio(page);
  await page.getByRole('tab', { name: 'Benchmark & Evaluation' }).click();

  const testSet = page.locator('[data-evaluation-test-set]');
  const samples = page.locator('[data-evaluation-samples]');
  const policy = page.locator('[data-evaluation-reasoning-policy]');
  await expect(testSet).toBeVisible();
  await testSet.selectOption('general-purpose::1.0.0');
  await samples.selectOption('10');
  await expect(policy).toHaveValue('off');

  const requestPromise = page.waitForRequest((request) => {
    const url = new URL(request.url());
    return request.method() === 'POST' && url.pathname === '/api/v1/evaluation/runs';
  });
  await page.locator('[data-evaluation-start]').click();
  const request = await requestPromise;
  const payload = request.postDataJSON();

  expect(payload).toMatchObject({
    model: 'e2e-switchable',
    test_set_id: 'general-purpose',
    test_set_version: '1.0.0',
    sample_count: 10,
    seed: 0,
    reasoning_policy: 'off',
  });

  await expect(page.locator('[data-evaluation-reasoning-profile]')).toContainText(
    'off requested → off effective'
  );
});
