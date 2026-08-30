const { test, expect } = require('@playwright/test');

test.describe.configure({ mode: 'serial' });

function chatPayload(overrides = {}) {
  return {
    messages: [{ role: 'user', content: 'Return the deterministic answer.' }],
    temperature: 0,
    stream: false,
    ...overrides,
  };
}

function parseSse(text) {
  const events = [];
  for (const block of text.split(/\r?\n\r?\n/)) {
    const line = block.split(/\r?\n/).find((item) => item.startsWith('data:'));
    if (!line) continue;
    const data = line.slice(5).trim();
    if (data === '[DONE]') {
      events.push('DONE');
      continue;
    }
    events.push(JSON.parse(data));
  }
  return events;
}

function aggregateSseContent(events) {
  const parts = [];
  for (const event of events) {
    if (!event || typeof event !== 'object') continue;
    for (const choice of event.choices || []) {
      const content = choice?.delta?.content;
      if (typeof content === 'string') parts.push(content);
    }
  }
  return parts.join('');
}

test('external client sees coherent health, discovery, identity and status without private paths', async ({ request }) => {
  const health = await request.get('/health');
  expect(health.ok()).toBeTruthy();

  const modelsResponse = await request.get('/v1/models');
  expect(modelsResponse.ok()).toBeTruthy();
  const models = await modelsResponse.json();
  const modelKeys = models.data.map((item) => item.key || item.id);
  expect(modelKeys).toEqual(
    expect.arrayContaining(['e2e-switchable', 'e2e-alt'])
  );

  const identityResponse = await request.get('/v1/runtime/identity');
  expect(identityResponse.ok()).toBeTruthy();
  const identity = await identityResponse.json();
  expect(identity.protocol_version).toBe('local-llm-identity-v1');
  expect(identity.default_model).toBe('e2e-switchable');
  expect(Object.keys(identity.models)).toEqual(
    expect.arrayContaining(['e2e-switchable', 'e2e-alt'])
  );
  const publicIdentity = JSON.stringify(identity);
  expect(publicIdentity).not.toContain('/e2e/');
  expect(publicIdentity).not.toContain('LOCAL_LLM_E2E_ROOT');

  const statusResponse = await request.get('/status');
  expect(statusResponse.ok()).toBeTruthy();
  const status = await statusResponse.json();
  expect(status.default_model).toBe('e2e-switchable');
  expect(Object.keys(status.models)).toEqual(
    expect.arrayContaining(['e2e-switchable', 'e2e-alt'])
  );
});

test('default and explicit model routing are observable through the public HTTP response', async ({ request }) => {
  const defaultResponse = await request.post('/v1/chat/completions', {
    data: chatPayload(),
  });
  expect(defaultResponse.ok()).toBeTruthy();
  const defaultPayload = await defaultResponse.json();
  expect(defaultPayload.model).toBe('org/e2e-switchable');
  expect(defaultPayload.choices[0].message.content).toBe('42');

  const alternateResponse = await request.post('/v1/chat/completions', {
    data: chatPayload({ model: 'e2e-alt' }),
  });
  expect(alternateResponse.ok()).toBeTruthy();
  const alternatePayload = await alternateResponse.json();
  expect(alternatePayload.model).toBe('org/e2e-alt');
  expect(alternatePayload.choices[0].message.content).toBe('84');
});

test('unknown routing and malformed input fail explicitly without poisoning the next request', async ({ request }) => {
  const unknown = await request.post('/v1/chat/completions', {
    data: chatPayload({ model: 'does-not-exist' }),
  });
  expect(unknown.status()).toBe(404);
  expect(await unknown.text()).not.toContain('42');

  const malformed = await request.post('/v1/chat/completions', {
    data: { temperature: 0, stream: false },
  });
  expect(malformed.status()).toBe(400);
  expect((await malformed.text()).toLowerCase()).toContain('messages');

  const recovered = await request.post('/v1/chat/completions', {
    data: chatPayload(),
  });
  expect(recovered.ok()).toBeTruthy();
  expect((await recovered.json()).choices[0].message.content).toBe('42');
});

test('task and media policy fail closed while a compatible local vision request succeeds', async ({ request }) => {
  const imageContent = [
    { type: 'image_url', image_url: { url: 'data:image/png;base64,AAAA' } },
    { type: 'text', text: 'Describe this fixture image.' },
  ];

  const unsupported = await request.post('/v1/chat/completions', {
    data: chatPayload({
      model: 'e2e-switchable',
      messages: [{ role: 'user', content: imageContent }],
    }),
  });
  expect(unsupported.status()).toBe(400);
  const unsupportedPayload = await unsupported.json();
  expect(unsupportedPayload.detail.code).toBe('unsupported_modality');

  const vision = await request.post('/v1/chat/completions', {
    data: chatPayload({
      model: 'e2e-alt',
      messages: [{ role: 'user', content: imageContent }],
    }),
  });
  expect(vision.ok()).toBeTruthy();
  expect((await vision.json()).choices[0].message.content).toBe('84');

  const remote = await request.post('/v1/chat/completions', {
    data: chatPayload({
      model: 'e2e-alt',
      messages: [
        {
          role: 'user',
          content: [
            { type: 'image_url', image_url: { url: 'https://example.com/private.png' } },
            { type: 'text', text: 'Do not fetch this remote image.' },
          ],
        },
      ],
    }),
  });
  expect(remote.ok()).toBeFalsy();
  expect([400, 403, 422]).toContain(remote.status());
  expect((await remote.text()).toLowerCase()).toContain('remote');
});

test('streaming hidden reasoning is filtered at the real socket HTTP boundary', async ({ request }) => {
  const response = await request.post('/v1/chat/completions', {
    data: chatPayload({
      model: 'e2e-switchable',
      stream: true,
      enable_thinking: true,
      show_thinking: false,
      response_format: { type: 'json_object' },
    }),
  });

  expect(response.ok()).toBeTruthy();
  expect(response.headers()['content-type']).toContain('text/event-stream');
  const body = await response.text();
  const events = parseSse(body);
  expect(aggregateSseContent(events)).toBe('{"answer":42}');
  expect(events.at(-1)).toBe('DONE');
  expect(body).not.toContain('private reasoning');
  expect(body).not.toContain('<think>');
});

test('backend failure is produced by the server stack and the next inference recovers', async ({ request }) => {
  const failed = await request.post('/v1/chat/completions', {
    data: chatPayload({
      messages: [{ role: 'user', content: 'Trigger the fixture. [backend-error]' }],
    }),
  });
  expect(failed.status()).toBe(500);
  const failurePayload = await failed.json();
  expect(String(failurePayload.detail)).toContain('deterministic fixture backend failure');
  expect(JSON.stringify(failurePayload)).not.toContain('/e2e/');

  const recovered = await request.post('/v1/chat/completions', {
    data: chatPayload({ messages: [{ role: 'user', content: 'Recover now.' }] }),
  });
  expect(recovered.ok()).toBeTruthy();
  expect((await recovered.json()).choices[0].message.content).toBe('42');
});

test('multipart transcription reaches an explicit transcription-capable resident runtime', async ({ request }) => {
  const response = await request.post('/v1/audio/transcriptions', {
    multipart: {
      model: 'e2e-alt',
      language: 'it',
      file: {
        name: 'fixture.wav',
        mimeType: 'audio/wav',
        buffer: Buffer.from('RIFFdeterministic-e2e-audio'),
      },
    },
  });

  expect(response.ok()).toBeTruthy();
  const payload = await response.json();
  expect(payload.model).toBe('org/e2e-alt');
  expect(payload.text).toBe('deterministic transcript');
  expect(payload.language).toBe('it');
  expect(payload.duration_seconds ?? payload.duration).toBe(1.25);
});

test('residency admin API preserves explicit pinning and keeps eviction non-automatic', async ({ request }) => {
  const pinned = await request.post('/api/v1/residency/pin', {
    data: { model: 'e2e-alt', pinned: true },
  });
  expect(pinned.ok()).toBeTruthy();
  expect((await pinned.json()).pinned).toBe(true);

  const preview = await request.post('/api/v1/residency/eviction/preview', {
    data: { mode: 'lru', limit: 3, protect_resident_default: true },
  });
  expect(preview.ok()).toBeTruthy();
  const previewPayload = await preview.json();
  expect(previewPayload.automatic).toBe(false);
  expect(previewPayload.reclamation_claim).toBe(false);
  expect(previewPayload.candidates.map((item) => item.key)).not.toContain('e2e-alt');
  expect(previewPayload.candidates.map((item) => item.key)).not.toContain('e2e-switchable');

  const unpinned = await request.post('/api/v1/residency/pin', {
    data: { model: 'e2e-alt', pinned: false },
  });
  expect(unpinned.ok()).toBeTruthy();
  expect((await unpinned.json()).pinned).toBe(false);
});

test('resource, scheduler, policy and evidence admin surfaces are reachable and privacy-safe', async ({ request }) => {
  for (const path of [
    '/api/v1/resources',
    '/api/v1/scheduler',
    '/api/v1/policies',
    '/api/v1/evidence',
  ]) {
    const response = await request.get(path);
    expect(response.ok(), `${path} should be available`).toBeTruthy();
    const text = await response.text();
    expect(text).not.toContain('LOCAL_LLM_E2E_ROOT');
    expect(text).not.toContain('private reasoning');
  }
});

test('evaluation catalog and execution work for an API-only consumer', async ({ request }) => {
  const catalogResponse = await request.get('/api/v1/evaluation/test-sets');
  expect(catalogResponse.ok()).toBeTruthy();
  const catalog = await catalogResponse.json();
  expect(catalog.test_sets.map((item) => item.id)).toContain('general-purpose');

  const runResponse = await request.post('/api/v1/evaluation/runs', {
    data: {
      model: 'e2e-switchable',
      test_set_id: 'general-purpose',
      test_set_version: '1.0.0',
      sample_count: 10,
      seed: 0,
      reasoning_policy: 'off',
      retain_content: false,
    },
  });
  expect(runResponse.ok()).toBeTruthy();
  const run = await runResponse.json();
  expect(run.report.manifest.test_set_id).toBe('general-purpose');
  expect(run.report.manifest.test_set_version).toBe('1.0.0');
  expect(run.report.manifest.sample_ids).toHaveLength(10);
  expect(run.report.manifest.seed).toBe(0);
  expect(run.report.manifest.content_retained).toBe(false);
  expect(run.report.results).toHaveLength(10);
});
