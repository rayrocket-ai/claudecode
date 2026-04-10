// ── Toast Notifications ──────────────────────────────────────────────

function showToast(message, duration = 3000) {
    const toast = document.getElementById('toast');
    const msg = document.getElementById('toast-message');
    if (!toast || !msg) return;
    msg.textContent = message;
    toast.classList.remove('hidden');
    clearTimeout(toast._timeout);
    toast._timeout = setTimeout(() => {
        toast.classList.add('hidden');
    }, duration);
}


// ── Script Card Interactions ─────────────────────────────────────────

function toggleBody(scriptId) {
    const body = document.getElementById('body-' + scriptId);
    const arrow = document.getElementById('body-arrow-' + scriptId);
    if (body.classList.contains('hidden')) {
        body.classList.remove('hidden');
        arrow.classList.add('rotate-180');
    } else {
        body.classList.add('hidden');
        arrow.classList.remove('rotate-180');
    }
}


function toggleEdit(scriptId) {
    const view = document.getElementById('view-' + scriptId);
    const edit = document.getElementById('edit-' + scriptId);
    view.classList.toggle('hidden');
    edit.classList.toggle('hidden');
}


async function saveScript(scriptId) {
    const data = {
        title: document.getElementById('edit-title-' + scriptId).value,
        hook: document.getElementById('edit-hook-' + scriptId).value,
        body: document.getElementById('edit-body-' + scriptId).value,
        cta: document.getElementById('edit-cta-' + scriptId).value,
        personal_tie_in: document.getElementById('edit-tien-' + scriptId).value,
        visual_suggestions: document.getElementById('edit-visuals-' + scriptId).value,
    };

    try {
        const resp = await fetch('/api/scripts/' + scriptId, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data),
        });
        if (resp.ok) {
            showToast('Script saved!');
            window.location.reload();
        } else {
            showToast('Failed to save');
        }
    } catch (e) {
        showToast('Network error');
    }
}


async function copyScript(scriptId) {
    try {
        const resp = await fetch('/api/scripts/' + scriptId + '/copy');
        const text = await resp.text();
        await navigator.clipboard.writeText(text);
        showToast('Script copied to clipboard!');
    } catch (e) {
        showToast('Failed to copy');
    }
}


async function regenerateScript(scriptId) {
    if (!confirm('Regenerate this script? The current version will be replaced.')) return;

    const card = document.getElementById('script-' + scriptId);
    if (card) card.style.opacity = '0.5';

    try {
        const resp = await fetch('/api/regenerate/' + scriptId, { method: 'POST' });
        const data = await resp.json();
        if (data.status === 'success') {
            showToast('Script regenerated!');
            window.location.reload();
        } else {
            showToast('Error: ' + (data.message || 'Failed'));
            if (card) card.style.opacity = '1';
        }
    } catch (e) {
        showToast('Network error');
        if (card) card.style.opacity = '1';
    }
}
