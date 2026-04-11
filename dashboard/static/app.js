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


// ── Billing Error Modal ──────────────────────────────────────────────

function showBillingModal(message, billingUrl) {
    // Remove any existing modal
    const existing = document.getElementById('billing-modal');
    if (existing) existing.remove();

    const modal = document.createElement('div');
    modal.id = 'billing-modal';
    modal.className = 'fixed inset-0 z-[100] bg-black/60 flex items-center justify-center p-4';
    modal.innerHTML = `
        <div class="bg-white rounded-xl shadow-2xl max-w-lg w-full p-6">
            <div class="flex items-start gap-4">
                <div class="w-12 h-12 rounded-full bg-red-100 flex items-center justify-center flex-shrink-0">
                    <svg class="w-6 h-6 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z"/>
                    </svg>
                </div>
                <div class="flex-1">
                    <h2 class="text-lg font-semibold text-gray-900">Anthropic API Credits Low</h2>
                    <p class="text-sm text-gray-600 mt-2">${message || 'Your Claude API balance is too low to run this request.'}</p>
                    <div class="mt-4 p-4 bg-gray-50 rounded-lg">
                        <div class="text-xs font-semibold text-gray-500 uppercase mb-2">How to fix</div>
                        <ol class="text-sm text-gray-700 space-y-1.5 list-decimal list-inside">
                            <li>Click the button below to open Anthropic billing</li>
                            <li>Click "Add to balance" and charge $5-10</li>
                            <li>Come back to the dashboard and try again</li>
                        </ol>
                    </div>
                    <div class="mt-5 flex gap-3">
                        <a href="${billingUrl || 'https://console.anthropic.com/settings/billing'}" target="_blank"
                            class="flex-1 inline-flex items-center justify-center px-4 py-2.5 bg-gray-900 text-white rounded-lg text-sm font-medium hover:bg-gray-800">
                            <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"/></svg>
                            Open Anthropic Billing
                        </a>
                        <button onclick="document.getElementById('billing-modal').remove()"
                            class="px-4 py-2.5 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50">
                            Close
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `;
    document.body.appendChild(modal);
    modal.addEventListener('click', (e) => { if (e.target === modal) modal.remove(); });
}


// ── Shared API Fetch Helper ──────────────────────────────────────────
// Automatically handles the 402 billing-error response and pops the modal.

async function apiFetch(url, options = {}) {
    const resp = await fetch(url, options);
    let data = null;
    try { data = await resp.clone().json(); } catch (e) { /* not JSON */ }

    if (resp.status === 402 && data && data.status === 'billing_error') {
        showBillingModal(data.message, data.billing_url);
        return { ok: false, status: 402, data, billingError: true };
    }

    return {
        ok: resp.ok,
        status: resp.status,
        data: data,
        billingError: false,
    };
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

    const result = await apiFetch('/api/regenerate/' + scriptId, { method: 'POST' });
    if (result.billingError) {
        if (card) card.style.opacity = '1';
        return;
    }
    const data = result.data || {};
    if (data.status === 'success') {
        showToast('Script regenerated!');
        window.location.reload();
    } else {
        showToast('Error: ' + (data.message || 'Failed'));
        if (card) card.style.opacity = '1';
    }
}
