// Keep preview credentials in this tab, never in a URL or a third-party cookie.
(() => {
  const initial = document.querySelector('meta[name="tab-session"]').content;
  let ticket = initial;
  try { ticket = sessionStorage.getItem('hubsoc-tab') || initial; } catch {}
  const headers = () => ({'X-Hubsoc-Session': ticket});
  async function render(response) {
    const doc = new DOMParser().parseFromString(await response.text(), 'text/html');
    const meta = doc.querySelector('meta[name="tab-session"]');
    if (meta) {
      ticket = meta.content;
      try { sessionStorage.setItem('hubsoc-tab', ticket); } catch {}
    }
    document.dispatchEvent(new Event('hubsoc:before-render'));
    document.body.replaceWith(doc.body);
    document.dispatchEvent(new Event('hubsoc:render'));
    if (document.querySelector('[role="alert"]')?.textContent.trim()) document.querySelector('#auth').showModal();
  }
  const ready = ticket === initial ? Promise.resolve() : fetch(location.href,{headers:headers()}).then(render);
  document.addEventListener('submit', async e => {
    if (e.target.method !== 'post') return;
    e.preventDefault();
    const data = new FormData(e.target, e.submitter);
    try {
      await ready;
      const response = await fetch(location.href,{method:'POST',body:data,headers:headers()});
      if (!response.ok && !response.headers.get('Content-Type')?.includes('application/json') && response.status !== 403) { alert(response.status===413?'Файл слишком большой (максимум 25 МБ).':'Не удалось сохранить. Проверь формат файла и поля формы.'); return; }
      if (!response.headers.get('Content-Type')?.includes('application/json')) return await render(response);
      const result = await response.json();
      ticket = result.ticket;
      history.replaceState(null,'',result.destination);
      await render(await fetch(location.href,{headers:headers()}));
    } catch { alert('Не удалось связаться с сайтом. Обновите страницу.'); }
  });
})();
