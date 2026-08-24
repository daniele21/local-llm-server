(() => {
    const noticeSelector = '[data-evaluation-migration-notice]';

    function createNotice() {
        const notice = document.createElement('section');
        notice.className = 'ds-card evaluation-context';
        notice.dataset.evaluationMigrationNotice = 'true';
        notice.innerHTML = `
            <span class="evaluation-eyebrow">Evaluation ownership transition</span>
            <h3>New evaluation work moves to Performance Lab</h3>
            <p>
                This Local LLM Server surface remains available for the current EV-3 evidence wave and legacy history.
                New post-cutover evaluation evidence belongs in Performance Lab.
            </p>
            <a
                class="ds-button ds-button--small"
                href="https://github.com/daniele21/performance-lab"
                target="_blank"
                rel="noreferrer"
            >Open Performance Lab</a>`;
        return notice;
    }

    function mountNotice() {
        const view = document.getElementById('benchmark-tab');
        if (!view || view.dataset.evaluationUi !== 'true' || view.querySelector(noticeSelector)) return;

        const notice = createNotice();
        const header = view.querySelector('.control-plane-header');
        if (header) header.insertAdjacentElement('afterend', notice);
        else view.prepend(notice);
    }

    function boot() {
        mountNotice();
        const observer = new MutationObserver(mountNotice);
        observer.observe(document.body, {
            attributes: true,
            childList: true,
            subtree: true,
            attributeFilter: ['data-evaluation-ui'],
        });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', boot, { once: true });
    } else {
        boot();
    }
})();
