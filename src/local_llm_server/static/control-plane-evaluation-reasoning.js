(() => {
    const TEST_SETS = '/api/v1/evaluation/test-sets';
    const RUNS = '/api/v1/evaluation/runs';
    const HISTORY = '/api/v1/evaluation/history';
    const policies = new Map();
    const historyProfiles = new Map();
    let latestRunProfile = null;

    const baseFetch = window.fetch.bind(window);

    function pathOf(input) {
        try {
            const raw = typeof input === 'string' ? input : input?.url;
            return raw ? new URL(raw, window.location.origin).pathname : '';
        } catch (_) {
            return '';
        }
    }

    function normalizeProfile(value) {
        if (!value || typeof value !== 'object') return null;
        const requested = String(value.requested || '').trim();
        const effective = String(value.effective || '').trim();
        const runtimeMode = String(value.runtime_mode || '').trim();
        if (!requested || !effective || !runtimeMode) return null;
        return { requested, effective, runtimeMode, requestOverride: value.request_override ?? null };
    }

    function selectedDatasetKey() {
        const option = document.querySelector('[data-evaluation-test-set]')?.selectedOptions?.[0];
        if (!option) return '';
        return `${String(option.dataset.id || '')}::${String(option.dataset.version || '')}`;
    }

    function reasoningSelect() {
        return document.querySelector('[data-evaluation-reasoning-policy]');
    }

    function ingestPolicies(payload) {
        (Array.isArray(payload?.test_sets) ? payload.test_sets : []).forEach((item) => {
            policies.set(`${item.id}::${item.version}`, String(item.default_reasoning_policy || 'runtime_default'));
        });
    }

    function applyDatasetDefault() {
        const select = reasoningSelect();
        if (!select) return;
        const policy = policies.get(selectedDatasetKey()) || 'runtime_default';
        select.value = policy;
        const help = document.querySelector('[data-evaluation-reasoning-help]');
        if (help) {
            help.textContent = policy === 'off'
                ? 'Dataset default: reasoning OFF. The manifest still records the actual effective runtime state.'
                : 'Dataset default: use the runtime thinking configuration and record the resulting effective state.';
        }
    }

    function ensureReasoningField() {
        const form = document.querySelector('[data-evaluation-form]');
        if (!form || reasoningSelect()) return;
        const sampleGrid = form.querySelector('.evaluation-field-grid');
        if (!sampleGrid) return;

        const label = document.createElement('label');
        label.className = 'ds-field';
        label.dataset.evaluationReasoningField = 'true';
        label.innerHTML = `
            <span>Reasoning policy</span>
            <select data-evaluation-reasoning-policy>
                <option value="off">Off</option>
                <option value="on">On</option>
                <option value="runtime_default">Runtime default</option>
            </select>
            <small data-evaluation-reasoning-help>Requested and effective thinking state are persisted in the run manifest.</small>`;
        sampleGrid.insertAdjacentElement('afterend', label);

        document.querySelector('[data-evaluation-test-set]')?.addEventListener('change', applyDatasetDefault);
        applyDatasetDefault();
    }

    async function refreshPolicies() {
        try {
            const response = await baseFetch(TEST_SETS, { headers: { Accept: 'application/json' } });
            if (!response.ok) return;
            ingestPolicies(await response.json());
            ensureReasoningField();
            applyDatasetDefault();
        } catch (_) {
            // The evaluation view owns service-unavailable messaging. Keep this overlay passive.
        }
    }

    function decorateLatestResult() {
        if (!latestRunProfile) return;
        const manifest = document.querySelector('[data-evaluation-result] .evaluation-manifest');
        if (!manifest || manifest.querySelector('[data-evaluation-reasoning-profile]')) return;
        const row = document.createElement('div');
        row.dataset.evaluationReasoningProfile = 'true';
        row.innerHTML = `<span>Reasoning</span><strong>${escapeHtml(latestRunProfile.requested)} requested → ${escapeHtml(latestRunProfile.effective)} effective <small>(${escapeHtml(latestRunProfile.runtimeMode)})</small></strong>`;
        manifest.appendChild(row);
    }

    function decorateHistory() {
        document.querySelectorAll('[data-evaluation-history] tbody tr').forEach((row) => {
            const runId = row.querySelector('code[title]')?.getAttribute('title') || '';
            const summary = historyProfiles.get(runId);
            if (!summary) return;
            const cells = row.querySelectorAll('td');
            if (cells.length < 6) return;
            const profile = normalizeProfile(summary.reasoning_profile);
            const identityKnown = Boolean(summary.runtime_fingerprint) && Boolean(profile);
            const identityCell = cells[5];
            updateHistoryIdentityCell(identityCell, identityKnown);
            const modelCell = cells[1];
            if (profile && !modelCell.querySelector('[data-history-reasoning-profile]')) {
                const detail = document.createElement('small');
                detail.dataset.historyReasoningProfile = 'true';
                detail.style.display = 'block';
                detail.textContent = `Reasoning ${profile.requested} → ${profile.effective}`;
                modelCell.appendChild(detail);
            }
        });

        const detailManifest = document.querySelector('[data-evaluation-history-detail] .evaluation-manifest');
        if (detailManifest && !detailManifest.querySelector('[data-evaluation-reasoning-profile]')) {
            const heading = document.querySelector('[data-evaluation-history-detail] .evaluation-eyebrow');
            const runText = heading?.parentElement?.querySelector('h3')?.textContent || '';
            for (const [runId, summary] of historyProfiles) {
                if (!runId.startsWith(runText.replace('…', ''))) continue;
                const profile = normalizeProfile(summary.reasoning_profile);
                if (!profile) break;
                const row = document.createElement('div');
                row.dataset.evaluationReasoningProfile = 'true';
                row.innerHTML = `<span>Reasoning</span><strong>${escapeHtml(profile.requested)} → ${escapeHtml(profile.effective)} (${escapeHtml(profile.runtimeMode)})</strong>`;
                detailManifest.appendChild(row);
                break;
            }
        }
    }

    function updateHistoryIdentityCell(identityCell, identityKnown) {
        const status = identityKnown ? 'ready' : 'warning';
        const label = identityKnown ? 'Evidence-grade' : 'Exploratory';
        const markup = `<span class="ds-status" data-status="${status}">${label}</span>`;
        if (identityCell.innerHTML === markup) return false;
        identityCell.innerHTML = markup;
        return true;
    }

    window.fetch = async function evaluationReasoningFetch(input, options = {}) {
        const path = pathOf(input);
        let rewritten = options;
        if (path === RUNS && String(options.method || 'GET').toUpperCase() === 'POST' && typeof options.body === 'string') {
            try {
                const payload = JSON.parse(options.body);
                const select = reasoningSelect();
                if (select?.value) payload.reasoning_policy = select.value;
                rewritten = { ...options, body: JSON.stringify(payload) };
            } catch (_) {
                // Preserve the original request; the server remains the validator.
            }
        }

        const response = await baseFetch(input, rewritten);
        if (response.ok && (path === TEST_SETS || path === RUNS || path === HISTORY)) {
            response.clone().json().then((payload) => {
                if (path === TEST_SETS) {
                    ingestPolicies(payload);
                    ensureReasoningField();
                    applyDatasetDefault();
                } else if (path === RUNS) {
                    latestRunProfile = normalizeProfile(payload?.report?.manifest?.reasoning_profile);
                    setTimeout(decorateLatestResult, 0);
                } else if (path === HISTORY) {
                    historyProfiles.clear();
                    (Array.isArray(payload?.runs) ? payload.runs : []).forEach((run) => {
                        if (run?.run_id) historyProfiles.set(String(run.run_id), run);
                    });
                    setTimeout(decorateHistory, 0);
                }
            }).catch(() => {});
        }
        return response;
    };

    const observer = new MutationObserver(() => {
        ensureReasoningField();
        decorateLatestResult();
        decorateHistory();
    });

    function boot() {
        observer.observe(document.body, { childList: true, subtree: true });
        ensureReasoningField();
        refreshPolicies();
    }

    function escapeHtml(value) {
        return String(value)
            .replaceAll('&', '&amp;')
            .replaceAll('<', '&lt;')
            .replaceAll('>', '&gt;')
            .replaceAll('"', '&quot;')
            .replaceAll("'", '&#039;');
    }

    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot, { once: true });
    else boot();

    window.localLlmEvaluationReasoning = {
        applyDatasetDefault,
        normalizeProfile,
        updateHistoryIdentityCell,
    };
})();
