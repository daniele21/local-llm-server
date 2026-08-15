(() => {
    const NAV = [
        { id: 'overview-tab', label: 'Overview', kind: 'new' },
        { id: 'registry-tab', label: 'Models & Runtimes', kind: 'legacy' },
        { id: 'endpoints-tab', label: 'Endpoints', kind: 'new' },
        { id: 'chat-tab', label: 'Playground', kind: 'legacy' },
        { id: 'benchmark-tab', label: 'Benchmark & Evaluation', kind: 'new' },
        { id: 'logs-tab', label: 'System / Diagnostics', kind: 'legacy' },
        { id: 'settings-tab', label: 'Settings', kind: 'new' },
    ];

    function boot() {
        const nav = document.querySelector('.sidebar-nav');
        const main = document.querySelector('.app-main');
        if (!nav || !main || nav.dataset.controlPlaneReady === 'true') return;
        nav.dataset.controlPlaneReady = 'true';

        const legacyButtons = new Map(
            [...nav.querySelectorAll('.nav-item[data-tab]')].map((button) => [button.dataset.tab, button])
        );
        const tourButton = nav.querySelector('.start-tour-btn');

        const sectionLabel = document.createElement('div');
        sectionLabel.className = 'control-plane-section-label';
        sectionLabel.textContent = 'Control plane';
        nav.insertBefore(sectionLabel, nav.firstChild);

        NAV.forEach((item) => {
            let button = legacyButtons.get(item.id);
            if (!button) {
                button = document.createElement('button');
                button.type = 'button';
                button.className = 'nav-item';
                button.dataset.tab = item.id;
                button.dataset.controlPlane = 'true';
                button.textContent = item.label;
                button.addEventListener('click', () => activate(item.id, button));
                nav.insertBefore(button, tourButton || null);
            } else {
                replaceButtonLabel(button, item.label);
            }
        });

        ensureView(main, 'overview-tab', overviewMarkup());
        ensureView(main, 'endpoints-tab', endpointsMarkup());
        ensureView(main, 'benchmark-tab', benchmarkMarkup());
        ensureView(main, 'settings-tab', settingsMarkup());

        // Keep the existing working default route rather than forcing a new
        // page on users during an incremental shell migration.
        const activePanel = document.querySelector('.tab-panel--active');
        const activeButton = activePanel
            ? nav.querySelector(`.nav-item[data-tab="${activePanel.id}"]`)
            : null;
        if (activeButton) activeButton.classList.add('nav-item--active');
    }

    function replaceButtonLabel(button, label) {
        const icon = button.querySelector('svg');
        button.textContent = '';
        if (icon) button.appendChild(icon);
        button.appendChild(document.createTextNode(label));
        button.dataset.controlPlane = 'true';
    }

    function activate(panelId, button) {
        document.querySelectorAll('.sidebar-nav .nav-item').forEach((item) => {
            item.classList.toggle('nav-item--active', item === button);
        });
        document.querySelectorAll('.app-main .tab-panel').forEach((panel) => {
            panel.classList.toggle('tab-panel--active', panel.id === panelId);
        });
    }

    function ensureView(main, id, markup) {
        if (document.getElementById(id)) return;
        const section = document.createElement('section');
        section.id = id;
        section.className = 'tab-panel control-plane-view';
        section.innerHTML = markup;
        const footer = main.querySelector('.app-footer');
        main.insertBefore(section, footer || null);
    }

    function overviewMarkup() {
        return `
            <div class="control-plane-header">
                <div>
                    <h2>Overview</h2>
                    <p>Operational entry point for local AI health, resident runtimes and evidence. Only currently available sources are surfaced.</p>
                </div>
                <span class="ds-status" data-status="ready">Shell active</span>
            </div>
            <div class="control-plane-grid">
                <article class="ds-card control-plane-card">
                    <h3>Server health</h3>
                    <p>The live connection state and active backend remain source-backed in the persistent sidebar while this panel is migrated.</p>
                </article>
                <article class="ds-card control-plane-card">
                    <h3>Resident runtimes</h3>
                    <p>Current runtime count and identities remain visible in the sidebar and Models & Runtimes view.</p>
                </article>
                <article class="ds-card control-plane-card">
                    <h3>Resource pressure</h3>
                    <div class="ds-empty control-plane-unavailable">Unavailable until B1/B2 resource contracts are connected.</div>
                </article>
            </div>`;
    }

    function endpointsMarkup() {
        return `
            <div class="control-plane-header">
                <div>
                    <h2>Endpoints</h2>
                    <p>Current public integration surfaces. Capability-driven compatibility will be added after C2.</p>
                </div>
            </div>
            <div class="control-plane-grid--two control-plane-grid">
                <article class="ds-card control-plane-card">
                    <h3>OpenAI-compatible API</h3>
                    <p>The existing chat-completions surface remains the production-compatible request path during canonical-contract migration.</p>
                    <div class="control-plane-actions">
                        <a class="ds-button ds-link" href="/docs" target="_blank" rel="noreferrer">Open Swagger</a>
                        <a class="ds-button ds-link" href="/example" target="_blank" rel="noreferrer">Integration examples</a>
                    </div>
                </article>
                <article class="ds-card control-plane-card">
                    <h3>Task compatibility</h3>
                    <div class="ds-empty control-plane-unavailable">Capability-driven model/endpoint matching unavailable until C2 is integrated.</div>
                </article>
            </div>`;
    }

    function benchmarkMarkup() {
        return `
            <div class="control-plane-header">
                <div>
                    <h2>Benchmark & Evaluation</h2>
                    <p>Reproducible model/runtime comparison will live here once metric and execution identity contracts are available.</p>
                </div>
            </div>
            <div class="ds-empty">No benchmark engine is connected yet. No synthetic performance values are displayed.</div>`;
    }

    function settingsMarkup() {
        return `
            <div class="control-plane-header">
                <div>
                    <h2>Settings</h2>
                    <p>Product policy and control-plane preferences. Existing runtime configuration remains under Models & Runtimes during migration.</p>
                </div>
            </div>
            <div class="control-plane-grid--two control-plane-grid">
                <article class="ds-card control-plane-card">
                    <h3>Privacy defaults</h3>
                    <ul>
                        <li>Remote model code is fail-closed unless explicitly enabled.</li>
                        <li>Remote HTTP(S) media policy exists; request-path enforcement is still being connected.</li>
                        <li>Temporary WAV files owned by local preprocessing are cleaned deterministically.</li>
                    </ul>
                </article>
                <article class="ds-card control-plane-card">
                    <h3>Resource policy</h3>
                    <div class="ds-empty control-plane-unavailable">Budget, headroom and residency policy controls are unavailable until B1/B2/B6.</div>
                </article>
            </div>`;
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', boot, { once: true });
    } else {
        boot();
    }
})();
