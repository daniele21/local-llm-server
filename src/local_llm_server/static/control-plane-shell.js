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
        // page on users during the incremental shell migration.
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
                    <p>Operational entry point for local AI health, residency, scheduling and runtime evidence.</p>
                </div>
                <span class="ds-status" data-status="loading">Loading sources</span>
            </div>
            <div class="ds-empty">Loading source-backed Overview state…</div>`;
    }

    function endpointsMarkup() {
        return `
            <div class="control-plane-header">
                <div>
                    <h2>Endpoints</h2>
                    <p>Task-aware integration surfaces derived from current runtime capability descriptors.</p>
                </div>
            </div>
            <div class="ds-empty">Loading capability-backed endpoint compatibility…</div>`;
    }

    function benchmarkMarkup() {
        return `
            <div class="control-plane-header">
                <div>
                    <h2>Benchmark & Evaluation</h2>
                    <p>Reproducible local evaluation, persisted run history and compatibility-aware comparison.</p>
                </div>
            </div>
            <div class="ds-empty">Loading evaluation sources…</div>`;
    }

    function settingsMarkup() {
        return `
            <div class="control-plane-header">
                <div>
                    <h2>Settings</h2>
                    <p>Effective product policy and control-plane configuration state.</p>
                </div>
            </div>
            <div class="ds-empty">Loading source-backed policy state…</div>`;
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', boot, { once: true });
    } else {
        boot();
    }
})();
