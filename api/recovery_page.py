"""Small same-origin activation page; tokens arrive only in URL fragments."""

RECOVERY_HTML = """<!doctype html>
<html lang="ru"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Подтверждение почты — фестивальчики</title>
<style>
body{font:16px/1.6 system-ui,sans-serif;background:#f1f5f9;color:#334155;margin:0;padding:24px;min-height:85vh;display:grid;place-items:center}
main{max-width:440px;background:white;padding:32px;border-radius:20px;box-shadow:0 4px 20px #0001}
h1{font-size:24px;line-height:1.3}button{font:inherit;min-height:48px;width:100%;background:#1e293b;color:white;border:0;border-radius:12px;padding:12px;cursor:pointer}button:disabled{opacity:.6}button:focus-visible{outline:3px solid #64748b;outline-offset:3px}#status{overflow-wrap:anywhere}
</style></head><body><main>
<h1>Почта снова работает</h1>
<p>Подтвердите свой адрес и войдите в кабинет судьи. Ссылка одноразовая, без срока истечения. Новый запрос кода заменяет её.</p>
<button id="confirm" type="button">Подтвердить почту и войти</button>
<p id="status" role="status" aria-live="polite"></p>
<noscript>Включите JavaScript для подтверждения почты.</noscript>
</main><script>
const params = new URLSearchParams(location.hash.slice(1));
const email = params.get('email');
const code = params.get('code');
history.replaceState(null, '', location.pathname);
const button = document.getElementById('confirm');
const status = document.getElementById('status');
if (!email || !code) { button.disabled = true; status.textContent = 'Откройте полную ссылку из письма.'; }
button.addEventListener('click', async () => {
  button.disabled = true; status.textContent = 'Подтверждаем адрес…';
  try {
    const response = await fetch('/api/v1/auth/verify-code', {
      method:'POST', headers:{'Content-Type':'application/json'},
      body:JSON.stringify({email,code})
    });
    const data = await response.json();
    if (!response.ok) throw new Error('Ссылка уже использована или заменена новым кодом. Запросите код в боте /link_email.');
    localStorage.setItem('token', data.access_token);
    location.replace('/dashboard');
  } catch (error) {
    status.textContent = error instanceof Error ? error.message : 'Не удалось подтвердить адрес. Попробуйте ещё раз.';
    button.disabled = false;
  }
});
</script></body></html>"""
