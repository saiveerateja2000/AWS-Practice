async function fetchJson(url){
  const resp = await fetch(url);
  const data = await resp.json();
  return {status: resp.status, requestId: resp.headers.get('X-Request-ID'), data};
}
function renderJson(target, items){
  const el = document.getElementById(target);
  el.textContent = JSON.stringify(items, null, 2);
}
window.fetchJson = fetchJson;
window.renderJson = renderJson;
