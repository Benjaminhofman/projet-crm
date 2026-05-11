// ── Déconnexion ───────────────────────────────────────────────────────────────

function logout() {
    sessionStorage.removeItem('crm_token');
    window.location.replace('/login.html');
}

// ── Injection bouton Déconnexion ───────────────────────────────────────────────

function injectLogoutButton() {
    if (document.getElementById('logout-btn')) return; // déjà injecté

    // index.html  → div interne droit du header (à côté du menu nav + search)
    // pages std   → .header directement (flex space-between, bouton va à droite)
    // client.html → .top-bar (pas de .header)
    const container =
        document.querySelector('.header > div') ||
        document.querySelector('.header')       ||
        document.querySelector('.top-bar');

    if (!container) return;

    const btn = document.createElement('button');
    btn.id          = 'logout-btn';
    btn.textContent = '🚪 Déconnexion';
    btn.onclick     = logout;
    btn.style.cssText = [
        'background:#e74c3c',
        'color:white',
        'border:none',
        'padding:8px 14px',
        'border-radius:6px',
        'cursor:pointer',
        'font-size:14px',
        'font-weight:600',
        'white-space:nowrap',
        'transition:background 0.2s',
        'flex-shrink:0',
    ].join(';');
    btn.onmouseover = () => btn.style.background = '#c0392b';
    btn.onmouseout  = () => btn.style.background = '#e74c3c';

    container.appendChild(btn);
}

// ── Vérification auth ─────────────────────────────────────────────────────────

async function checkAuth() {
    const token = sessionStorage.getItem('crm_token');
    if (!token) {
        window.location.replace('/login.html');
        return;
    }
    try {
        const res  = await fetch('/api/auth/verify', {
            headers: { 'Authorization': 'Bearer ' + token }
        });
        const data = await res.json();
        if (!data.valid) {
            sessionStorage.removeItem('crm_token');
            window.location.replace('/login.html');
        } else {
            injectLogoutButton();
        }
    } catch {
        // Erreur réseau transitoire — on ne redirige pas pour ne pas bloquer l'accès
    }
}
