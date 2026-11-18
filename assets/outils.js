// Charte PDW commune à toutes les pages : mode jour / nuit, logo, choix d'unité mm / cm
(() => {
  const load = k => { try { return localStorage.getItem(k); } catch { return null; } };
  const keep = (k, v) => { try { localStorage.setItem(k, v); } catch {} };
  const root = document.documentElement;

  // ---- Mode jour / nuit : suit le réglage du Mac, sauf si on a cliqué le bouton ----
  const saved = load('pdw-theme');
  if (saved === 'light' || saved === 'dark') root.dataset.theme = saved;
  const dark = () => (root.dataset.theme || (matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light')) === 'dark';
  const SUN = '<svg class="ic" viewBox="0 0 24 24"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/></svg>';
  const MOON = '<svg class="ic" viewBox="0 0 24 24"><path d="M20 14.5A8 8 0 0 1 9.5 4a8 8 0 1 0 10.5 10.5z"/></svg>';

  // ---- Logo PDW : les fichiers d'origine (découpés de la planche), à côté de ce script ----
  const base = (document.currentScript && document.currentScript.src || '').replace(/[^/]*$/, '');
  const logo = kind => `<img class="pdw-logo" src="${base}logo-pdw-${['plein','nu'].includes(kind) ? kind : 'contour'}.png" alt="PDW">`;

  // ---- Unités : les valeurs restent en mm dans le code, l'affichage suit le choix mm / cm ----
  let unit = load('pdw-unit') === 'mm' ? 'mm' : 'cm';
  const per = () => unit === 'mm' ? 1 : 10;   // mm dans une unité affichée
  const fr = (v, d) => v.toLocaleString('fr-FR', {maximumFractionDigits: d});
  const PDW = window.PDW = {
    get unit(){ return unit; },
    get: el => (+el.value || 0) * per(),                       // valeur du champ, en mm
    set(el, mm){ const st = +el.dataset.step || 0.01; el.value = +(Math.round(mm/st)*st/per()).toFixed(4); },
    len: (mm, d = unit === 'mm' ? 1 : 2) => fr(mm/per(), d) + ' ' + unit,   // texte prêt à afficher
    setUnit(u){
      if (u === unit) return;
      const fields = [...document.querySelectorAll('[data-len]')].map(el => [el, el.value === '' ? null : PDW.get(el)]);
      unit = u; keep('pdw-unit', u);
      for (const [el, mm] of fields){ refresh(el); if (mm !== null) PDW.set(el, mm); }
      paint();
      document.dispatchEvent(new Event('pdw-unit'));
    },
  };
  const refresh = el => { for (const a of ['min','max','step']) if (el.dataset[a]) el[a] = +(el.dataset[a]/per()).toFixed(4); };
  function paint(){
    document.querySelectorAll('[data-unit]').forEach(e => e.textContent = unit);
    document.querySelectorAll('.unit-pick button').forEach(b => b.setAttribute('aria-pressed', b.dataset.u === unit));
  }

  function init(){
    document.querySelectorAll('[data-logo]').forEach(e => e.innerHTML = logo(e.dataset.logo));
    const head = document.querySelector('.top, .bar');
    if (head){
      const b = document.createElement('button');
      b.className = 'btn icon theme-btn';
      const show = () => { b.innerHTML = dark() ? SUN : MOON; b.title = dark() ? 'Passer en mode jour' : 'Passer en mode nuit'; b.setAttribute('aria-label', b.title); };
      b.onclick = () => { root.dataset.theme = dark() ? 'light' : 'dark'; keep('pdw-theme', root.dataset.theme); show(); };
      matchMedia('(prefers-color-scheme: dark)').addEventListener('change', show);
      show(); head.appendChild(b);
    }
    document.querySelectorAll('[data-unit-pick]').forEach(e => {
      e.classList.add('unit-pick'); e.setAttribute('role', 'group'); e.setAttribute('aria-label', 'Unité');
      e.innerHTML = '<button type="button" data-u="mm">mm</button><button type="button" data-u="cm">cm</button>';
      e.onclick = ev => { const u = ev.target.closest('button')?.dataset.u; u && PDW.setUnit(u); };
    });
    document.querySelectorAll('[data-len]').forEach(el => { refresh(el); if (el.dataset.mm) PDW.set(el, +el.dataset.mm); });
    paint();
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init); else init();
})();
