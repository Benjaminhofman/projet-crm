// Vérifie que l'utilisateur est authentifié. Redirige vers login.html si non.
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
        }
    } catch {
        // Erreur réseau transitoire — on ne redirige pas pour ne pas bloquer l'accès
    }
}
