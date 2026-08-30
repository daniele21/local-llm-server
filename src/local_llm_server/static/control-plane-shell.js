(() => {
    const NAV = [
        { id: 'overview-tab', label: 'Overview', route: '/overview', kind: 'new' },
        { id: 'registry-tab', label: 'Models & Runtimes', route: '/models', kind: 'legacy' },
        { id: 'endpoints-tab', label: 'Endpoints', route: '/endpoints', kind: 'new' },
        { id: 'chat-tab', label: 'Playground', route: '/playground', kind: 'legacy' },
        { id: 'benchmark-tab', label: 'Benchmark & Evaluation', route: '/evaluations', kind: 'new' },
        { id: 'logs-tab', label: 'System / Diagnostics', route: '/system', kind: 'legacy' },
        { id: 'settings-tab', label: 'Settings', route: '/settings', kind: 'new' },
    ];
    const DETAIL_WAIT_ATTEMPTS = 100;
    const DETAIL_WAIT_MS = 50;
    let restoringDetail = false;

    function boot() {
        const nav = document.querySelector('.sidebar-nav');
        const main = document.querySelector('.app-main');
        if (!nav || !main || nav.dataset.controlPlaneReady === 'true') return;
        nav.dataset.controlPlaneReady = 'true';
        nav.setAttribute('aria-label', 'Control plane');

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

        const navigation = document.createElement('div');
        navigation.className = 'control-plane-navigation';
        navigation.dataset.controlPlaneNavigation = 'true';
        nav.insertBefore(navigation, tourButton || null);

        NAV.forEach((item) => {
            const legacy = legacyButtons.get(item.id);
            const link = createNavigationLink(item, legacy);
            navigation.appendChild(link);
            legacy?.remove();
        });

        ensureView(main, 'overview-tab', overviewMarkup());
        ensureView(main, 'endpoints-tab', endpointsMarkup());
        ensureView(main, 'benchmark-tab', benchmarkMarkup());
        ensureView(main, 'settings-tab', settingsMarkup());
        configurePanels(main);
        bindDetailRoutes();

        const route = resolveLocation(window.location.pathname);
        if (window.location.pathname === '/') {
            window.history.replaceState(null, '', route.path);
        }
        activate(route.panelId);
        restoreRoutedDetail(route);

        window.addEventListener('pageshow', (event) => {
            if (!event.persisted) return;
            const current = resolveLocation(window.location.pathname);
            activate(current.panelId);
            restoreRoutedDetail(current);
        });

        window.localLlmControlPlane = {
            navigate(panelId) {
                const item = NAV.find((entry) => entry.id === panelId);
                if (item) window.location.assign(item.route);
            },
            routeForPanel(panelId) {
                return NAV.find((entry) => entry.id === panelId)?.route || null;
            },
            opaqueIdFor: encodeOpaque,
        };
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

    function createNavigationLink(item, legacy) {
        const link = document.createElement('a');
        link.href = item.route;
        link.className = legacy?.className || 'nav-item';
        link.classList.remove('nav-item--active');
        link.dataset.tab = item.id;
        link.dataset.controlPlane = 'true';
        link.removeAttribute('role');
        link.removeAttribute('aria-selected');
        link.removeAttribute('aria-controls');
        link.removeAttribute('tabindex');

        const icon = legacy?.querySelector('svg')?.cloneNode(true);
        if (icon) {
            icon.setAttribute('aria-hidden', 'true');
            icon.setAttribute('focusable', 'false');
            link.appendChild(icon);
        }
        link.appendChild(document.createTextNode(item.label));
        return link;
    }

    function activate(panelId) {
        const nav = document.querySelector('.sidebar-nav');
        const main = document.querySelector('.app-main');
        if (!nav || !main) return;
        const selected = nav.querySelector(`.nav-item[data-tab="${panelId}"]`);
        if (!selected) return;

        navigationLinks().forEach((link) => {
            const active = link === selected;
            link.classList.toggle('nav-item--active', active);
            if (active) link.setAttribute('aria-current', 'page');
            else link.removeAttribute('aria-current');
        });

        main.querySelectorAll('.tab-panel').forEach((panel) => {
            const active = panel.id === panelId;
            panel.classList.toggle('tab-panel--active', active);
            panel.hidden = !active;
            panel.setAttribute('aria-hidden', active ? 'false' : 'true');
        });

        const item = NAV.find((entry) => entry.id === panelId);
        if (item) document.title = `Local LLM Studio · ${item.label}`;
    }

    function navigationLinks() {
        const navigation = document.querySelector('.control-plane-navigation');
        if (!navigation) return [];
        return NAV
            .map((item) => navigation.querySelector(`.nav-item[data-tab="${item.id}"]`))
            .filter(Boolean);
    }

    function configurePanels(main) {
        main.querySelectorAll('.tab-panel').forEach((panel) => {
            panel.removeAttribute('role');
            panel.removeAttribute('aria-labelledby');
            panel.removeAttribute('tabindex');
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

    function resolveLocation(pathname) {
        const normalized = pathname === '/' ? '/overview' : pathname.replace(/\/+$/, '') || '/overview';
        const exact = NAV.find((item) => item.route === normalized);
        if (exact) return { panelId: exact.id, path: exact.route, detail: null };

        const modelMatch = normalized.match(/^\/models\/([^/]+)$/);
        if (modelMatch) {
            return {
                panelId: 'registry-tab',
                path: normalized,
                detail: { type: 'model', opaqueId: modelMatch[1] },
            };
        }

        const evaluationMatch = normalized.match(/^\/evaluations\/([^/]+)$/);
        if (evaluationMatch) {
            return {
                panelId: 'benchmark-tab',
                path: normalized,
                detail: { type: 'evaluation', opaqueId: evaluationMatch[1] },
            };
        }

        return { panelId: 'overview-tab', path: '/overview', detail: null };
    }

    function bindDetailRoutes() {
        if (document.documentElement.dataset.controlPlaneDetailRoutesBound === 'true') return;
        document.documentElement.dataset.controlPlaneDetailRoutesBound = 'true';
        document.addEventListener('click', (event) => {
            if (restoringDetail) return;
            const target = event.target instanceof Element ? event.target : null;
            if (!target) return;

            const modelControl = target.closest('[data-open-model]');
            if (modelControl?.dataset?.openModel) {
                event.preventDefault();
                event.stopImmediatePropagation();
                window.location.assign(`/models/${encodeOpaque(modelControl.dataset.openModel)}`);
                return;
            }

            const evaluationControl = target.closest('[data-evaluation-inspect]');
            if (evaluationControl?.dataset?.evaluationInspect) {
                event.preventDefault();
                event.stopImmediatePropagation();
                window.location.assign(`/evaluations/${encodeOpaque(evaluationControl.dataset.evaluationInspect)}`);
                return;
            }

            if (target.closest('[data-evaluation-history-close]')) {
                event.preventDefault();
                event.stopImmediatePropagation();
                window.location.assign('/evaluations');
            }
        }, true);
    }

    function restoreRoutedDetail(route) {
        if (!route.detail) return;
        const decoded = decodeOpaque(route.detail.opaqueId);
        if (!decoded) {
            showRouteRecovery(route.panelId, 'This detail link is invalid. Use the section navigation to choose an available item.');
            return;
        }
        const attribute = route.detail.type === 'model' ? 'data-open-model' : 'data-evaluation-inspect';
        waitForControl(attribute, decoded, 0, (control) => {
            if (!control) {
                const kind = route.detail.type === 'model' ? 'model/runtime' : 'evaluation run';
                showRouteRecovery(route.panelId, `The linked ${kind} is unavailable in the current source state.`);
                return;
            }
            restoringDetail = true;
            try {
                control.click();
            } finally {
                restoringDetail = false;
            }
        });
    }

    function waitForControl(attribute, value, attempt, done) {
        const control = [...document.querySelectorAll(`[${attribute}]`)]
            .find((element) => element.getAttribute(attribute) === value);
        if (control) {
            done(control);
            return;
        }
        if (attempt >= DETAIL_WAIT_ATTEMPTS) {
            done(null);
            return;
        }
        window.setTimeout(() => waitForControl(attribute, value, attempt + 1, done), DETAIL_WAIT_MS);
    }

    function showRouteRecovery(panelId, message) {
        const panel = document.getElementById(panelId);
        if (!panel || panel.querySelector('[data-route-recovery]')) return;
        const notice = document.createElement('div');
        notice.className = 'ds-empty control-plane-unavailable';
        notice.dataset.routeRecovery = 'true';
        notice.setAttribute('role', 'status');
        notice.textContent = message;
        panel.prepend(notice);
    }

    function encodeOpaque(value) {
        const bytes = new TextEncoder().encode(String(value));
        let binary = '';
        bytes.forEach((byte) => { binary += String.fromCharCode(byte); });
        return btoa(binary).replaceAll('+', '-').replaceAll('/', '_').replace(/=+$/u, '');
    }

    function decodeOpaque(value) {
        try {
            const normalized = String(value).replaceAll('-', '+').replaceAll('_', '/');
            const padded = normalized.padEnd(Math.ceil(normalized.length / 4) * 4, '=');
            const binary = atob(padded);
            const bytes = Uint8Array.from(binary, (character) => character.charCodeAt(0));
            return new TextDecoder().decode(bytes) || null;
        } catch (_) {
            return null;
        }
    }

    function overviewMarkup() {
        return `
            <div class="control-plane-header">
                <div>
                    <h2>Overview</h2>
                    <p>See whether local AI is ready, what is resident, and what constrains the next action.</p>
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