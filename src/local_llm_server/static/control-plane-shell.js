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

        ensureSkipLink(main);

        const legacyButtons = new Map(
            [...nav.querySelectorAll('.nav-item[data-tab]')].map((button) => [button.dataset.tab, button])
        );
        const tourButton = nav.querySelector('.start-tour-btn');

        const sectionLabel = document.createElement('div');
        sectionLabel.className = 'control-plane-section-label';
        sectionLabel.textContent = 'Control plane';
        sectionLabel.setAttribute('aria-hidden', 'true');
        nav.insertBefore(sectionLabel, nav.firstChild);

        const tablist = document.createElement('div');
        tablist.className = 'control-plane-tablist';
        tablist.setAttribute('role', 'tablist');
        tablist.setAttribute('aria-label', 'Control plane views');
        tablist.setAttribute('aria-orientation', 'vertical');
        nav.insertBefore(tablist, tourButton || null);

        NAV.forEach((item) => {
            let button = legacyButtons.get(item.id);
            if (!button) {
                button = document.createElement('button');
                button.type = 'button';
                button.className = 'nav-item';
                button.dataset.tab = item.id;
                button.dataset.controlPlane = 'true';
                button.textContent = item.label;
            } else {
                replaceButtonLabel(button, item.label);
            }
            configureTabButton(button, item);
            tablist.appendChild(button);
        });

        ensureView(main, 'overview-tab', overviewMarkup());
        ensureView(main, 'endpoints-tab', endpointsMarkup());
        ensureView(main, 'benchmark-tab', benchmarkMarkup());
        ensureView(main, 'settings-tab', settingsMarkup());
        configurePanels(main);

        const activePanel = document.querySelector('.app-main .tab-panel--active');
        const activeId = activePanel?.id && NAV.some((item) => item.id === activePanel.id)
            ? activePanel.id
            : 'overview-tab';
        activate(activeId, { focus: false });
    }

    function ensureSkipLink(main) {
        if (document.querySelector('[data-control-plane-skip-link]')) return;
        if (!main.id) main.id = 'control-plane-main';
        main.tabIndex = -1;
        const link = document.createElement('a');
        link.href = `#${main.id}`;
        link.className = 'ds-skip-link';
        link.dataset.controlPlaneSkipLink = 'true';
        link.textContent = 'Skip to main content';
        link.addEventListener('click', () => {
            window.setTimeout(() => main.focus({ preventScroll: true }), 0);
        });
        document.body.prepend(link);
    }

    function configureTabButton(button, item) {
        button.type = 'button';
        button.id = `control-plane-tab-${item.id}`;
        button.setAttribute('role', 'tab');
        button.setAttribute('aria-controls', item.id);
        button.setAttribute('aria-selected', 'false');
        button.tabIndex = -1;
        button.dataset.controlPlane = 'true';

        button.querySelectorAll('svg').forEach((icon) => {
            icon.setAttribute('aria-hidden', 'true');
            icon.setAttribute('focusable', 'false');
        });

        if (button.dataset.controlPlaneA11yBound !== 'true') {
            button.dataset.controlPlaneA11yBound = 'true';
            button.addEventListener('click', () => activate(item.id, { focus: false }));
            button.addEventListener('keydown', handleTabKeydown);
        }
    }

    function handleTabKeydown(event) {
        const buttons = orderedTabButtons();
        const current = buttons.indexOf(event.currentTarget);
        if (current < 0 || buttons.length === 0) return;

        let next = null;
        if (event.key === 'ArrowDown' || event.key === 'ArrowRight') {
            next = (current + 1) % buttons.length;
        } else if (event.key === 'ArrowUp' || event.key === 'ArrowLeft') {
            next = (current - 1 + buttons.length) % buttons.length;
        } else if (event.key === 'Home') {
            next = 0;
        } else if (event.key === 'End') {
            next = buttons.length - 1;
        }

        if (next === null) return;
        event.preventDefault();
        const button = buttons[next];
        activate(button.dataset.tab, { focus: true });
    }

    function orderedTabButtons() {
        const tablist = document.querySelector('.control-plane-tablist');
        if (!tablist) return [];
        return NAV
            .map((item) => tablist.querySelector(`.nav-item[data-tab="${item.id}"]`))
            .filter(Boolean);
    }

    function replaceButtonLabel(button, label) {
        const icon = button.querySelector('svg');
        button.textContent = '';
        if (icon) button.appendChild(icon);
        button.appendChild(document.createTextNode(label));
        button.dataset.controlPlane = 'true';
    }

    function activate(panelId, { focus = false } = {}) {
        const nav = document.querySelector('.sidebar-nav');
        const main = document.querySelector('.app-main');
        if (!nav || !main) return;
        const selected = nav.querySelector(`.nav-item[data-tab="${panelId}"]`);
        if (!selected) return;

        orderedTabButtons().forEach((button) => {
            const active = button === selected;
            button.classList.toggle('nav-item--active', active);
            button.setAttribute('aria-selected', active ? 'true' : 'false');
            button.tabIndex = active ? 0 : -1;
        });

        main.querySelectorAll('.tab-panel').forEach((panel) => {
            const active = panel.id === panelId;
            panel.classList.toggle('tab-panel--active', active);
            panel.hidden = !active;
            panel.setAttribute('aria-hidden', active ? 'false' : 'true');
        });

        if (focus) selected.focus();
    }

    function configurePanels(main) {
        main.querySelectorAll('.tab-panel').forEach((panel) => {
            panel.setAttribute('role', 'tabpanel');
            panel.tabIndex = 0;
            const button = document.querySelector(`.control-plane-tablist .nav-item[data-tab="${panel.id}"]`);
            if (button?.id) panel.setAttribute('aria-labelledby', button.id);
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
