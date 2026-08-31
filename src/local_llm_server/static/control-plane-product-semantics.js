(() => {
    let scheduled = false;

    function scheduleRefinement() {
        if (scheduled) return;
        scheduled = true;
        window.requestAnimationFrame(() => {
            scheduled = false;
            refineProductSurfaces();
        });
    }

    function refineProductSurfaces() {
        refineEvaluation();
        refineModels();
        refineOverviewEvidence();
    }

    function refineEvaluation() {
        const view = document.getElementById('benchmark-tab');
        if (!view) return;

        const form = view.querySelector('[data-evaluation-form]');
        if (form && form.dataset.productSemantics !== 'true') {
            form.dataset.productSemantics = 'true';
            refineEvaluationForm(view, form);
        }

        const layout = view.querySelector('.evaluation-layout');
        if (layout) layout.classList.add('evaluation-layout--refined');

        const library = view.querySelector('.evaluation-layout > .evaluation-context:not([data-evaluation-library])');
        if (library) replaceWithDisclosure(library, {
            summary: datasetLibrarySummary(library),
            className: 'evaluation-context evaluation-refinement__library',
            marker: 'evaluationLibrary',
        });

        const contract = view.querySelector('.evaluation-contract-card:not([data-evaluation-contract-disclosure])');
        if (contract) replaceWithDisclosure(contract, {
            summary: 'How evaluation evidence works',
            className: 'evaluation-context evaluation-contract-card evaluation-refinement__contract',
            marker: 'evaluationContractDisclosure',
        });

        const result = view.querySelector('[data-evaluation-result]');
        if (result) refineEvaluationResult(result);

        view.querySelectorAll('.evaluation-comparison-deltas').forEach((grid) => {
            grid.classList.add('ds-evidence-grid');
            grid.querySelectorAll('.evaluation-comparison-delta').forEach((card) => {
                decorateEvidenceValue(card, inferKind(card.querySelector('strong')?.textContent));
            });
        });

        view.querySelectorAll('.evaluation-history-detail-card .evaluation-manifest').forEach((manifest) => {
            wrapIdentityManifest(manifest, 'Run identity & reproducibility');
        });
    }

    function refineEvaluationForm(view, form) {
        const startButton = form.querySelector('[data-evaluation-start]');
        if (startButton) {
            startButton.classList.remove('ds-button--primary');
            startButton.setAttribute('data-variant', 'primary');
        }

        const seed = form.querySelector('[data-evaluation-seed]')?.closest('.ds-field');
        const retention = form.querySelector('.evaluation-retention-option');
        const note = form.querySelector('.evaluation-note');
        if (!seed && !retention && !note) return;

        const details = document.createElement('details');
        details.className = 'ds-disclosure evaluation-refinement__advanced';
        details.dataset.evaluationAdvanced = 'true';
        const summary = document.createElement('summary');
        summary.innerHTML = '<span>Advanced run settings</span><small>Seed · retained content · scorer contract</small>';
        const body = document.createElement('div');
        body.className = 'evaluation-refinement__advanced-body';
        details.append(summary, body);

        if (seed) body.appendChild(seed);
        if (retention) body.appendChild(retention);
        if (note) body.appendChild(note);

        const fieldGrid = form.querySelector('.evaluation-field-grid');
        if (fieldGrid) fieldGrid.classList.add('evaluation-primary-fields');

        if (startButton) form.insertBefore(details, startButton);
        else form.appendChild(details);

        const heading = form.querySelector('h3');
        if (heading) heading.textContent = 'Run an evaluation';
        const eyebrow = form.querySelector('.evaluation-eyebrow');
        if (eyebrow) eyebrow.textContent = 'Scenario setup';

        const resultHost = view.querySelector('[data-evaluation-result]');
        if (resultHost) resultHost.setAttribute('aria-live', 'polite');
    }

    function datasetLibrarySummary(library) {
        const count = library.querySelector('.evaluation-library-summary strong')?.textContent?.trim();
        return count ? `Dataset library · ${count} versions` : 'Dataset library';
    }

    function replaceWithDisclosure(element, { summary, className, marker }) {
        const details = document.createElement('details');
        details.className = `ds-card ds-disclosure ${className}`;
        details.dataset[marker] = 'true';
        const summaryNode = document.createElement('summary');
        summaryNode.textContent = summary;
        const body = document.createElement('div');
        body.className = 'evaluation-refinement__disclosure-body';
        while (element.firstChild) body.appendChild(element.firstChild);
        details.append(summaryNode, body);
        element.replaceWith(details);
        return details;
    }

    function refineEvaluationResult(result) {
        const metrics = result.querySelector('.evaluation-metrics');
        if (metrics) {
            metrics.classList.add('ds-evidence-grid');
            metrics.querySelectorAll('.evaluation-metric-card').forEach((card) => {
                decorateEvidenceValue(card, inferKind(card.querySelector('strong')?.textContent));
            });
        }

        const manifest = directChild(result, '.evaluation-manifest');
        if (manifest) wrapIdentityManifest(manifest, 'Run identity & reproducibility');

        result.querySelectorAll('.evaluation-running').forEach((feedback) => {
            feedback.classList.add('ds-action-feedback');
            feedback.dataset.status = 'loading';
        });

        result.querySelectorAll(':scope > .control-plane-unavailable').forEach((feedback) => {
            feedback.classList.remove('ds-empty');
            feedback.classList.add('ds-action-feedback');
            feedback.dataset.status = 'error';
        });
    }

    function wrapIdentityManifest(manifest, summaryText) {
        if (!manifest || manifest.closest('[data-evaluation-identity-disclosure]')) return;
        const details = document.createElement('details');
        details.className = 'ds-disclosure evaluation-refinement__identity';
        details.dataset.evaluationIdentityDisclosure = 'true';
        const summary = document.createElement('summary');
        summary.textContent = summaryText;
        manifest.before(details);
        details.append(summary, manifest);
    }

    function directChild(parent, selector) {
        return [...parent.children].find((child) => child.matches(selector)) || null;
    }

    function decorateEvidenceValue(card, kind = 'observed') {
        if (!card || card.dataset.semanticEvidence === 'true') return;
        card.dataset.semanticEvidence = 'true';
        card.dataset.kind = kind;
        card.classList.add('ds-evidence-value');
        const label = card.querySelector(':scope > span, .ds-metric__label');
        const value = card.querySelector(':scope > strong, .ds-metric__value');
        const meta = card.querySelector(':scope > small, .ds-metric__source');
        if (label) label.classList.add('ds-evidence-value__label');
        if (value) value.classList.add('ds-evidence-value__value');
        if (meta) meta.classList.add('ds-evidence-value__meta');

        if (!card.querySelector('.ds-evidence-value__kind')) {
            const kindLabel = document.createElement('span');
            kindLabel.className = 'ds-evidence-value__kind';
            kindLabel.textContent = kind;
            card.appendChild(kindLabel);
        }
    }

    function inferKind(valueText, sourceText = '') {
        const value = String(valueText || '').toLowerCase();
        const source = String(sourceText || '').toLowerCase();
        if (!value || value.includes('unavailable') || value.includes('not retained')) return 'unavailable';
        if (source.includes('estimate')) return 'estimated';
        if (source.includes('configured')) return 'configured';
        return 'observed';
    }

    function refineModels() {
        const surface = document.querySelector('[data-control-plane-models]');
        if (!surface) return;
        const budget = surface.querySelector('.control-plane-models__budget');
        if (budget) budget.classList.add('ds-resource-budget');
        const track = surface.querySelector('.control-plane-models__budget-bar');
        if (track) {
            track.classList.add('ds-resource-budget__track');
            track.querySelectorAll('.control-plane-models__budget-segment').forEach((segment) => {
                segment.classList.add('ds-resource-budget__segment');
                if (segment.classList.contains('control-plane-models__budget-segment--committed')) segment.dataset.kind = 'committed';
                else if (segment.classList.contains('control-plane-models__budget-segment--reserved')) segment.dataset.kind = 'reserved';
                else if (segment.classList.contains('control-plane-models__budget-segment--remaining')) segment.dataset.kind = 'remaining';
            });
        }
        surface.querySelector('.control-plane-models__budget-legend')?.classList.add('ds-resource-budget__legend');

        const feedback = surface.querySelector('[data-model-action-status]');
        if (feedback) {
            feedback.classList.remove('ds-empty');
            feedback.classList.add('ds-action-feedback');
            feedback.dataset.status = feedbackStatus(feedback.textContent);
        }
    }

    function feedbackStatus(text) {
        const value = String(text || '').toLowerCase();
        if (value.includes('fail') || value.includes('error')) return 'error';
        if (value.includes('unavailable') || value.includes('disabled')) return 'unavailable';
        if (value.includes('loading') || value.includes('applying')) return 'loading';
        if (value.includes('warning') || value.includes('pressure') || value.includes('capacity')) return 'warning';
        return 'ready';
    }

    function refineOverviewEvidence() {
        const details = document.querySelector('.overview-evidence-details');
        if (!details) return;
        details.querySelectorAll('.ds-metric').forEach((metric) => {
            const value = metric.querySelector('.ds-metric__value')?.textContent;
            const source = metric.querySelector('.ds-metric__source')?.textContent;
            decorateEvidenceValue(metric, inferKind(value, source));
        });
    }

    function boot() {
        refineProductSurfaces();
        const observer = new MutationObserver(scheduleRefinement);
        observer.observe(document.body, { childList: true, subtree: true, characterData: true });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', boot, { once: true });
    } else {
        boot();
    }
})();
