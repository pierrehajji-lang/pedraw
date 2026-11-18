// Animations du portfolio : apparitions, copie de l'email, effet 3D « Projet suivant ».
document.documentElement.classList.add('js');

// 1) Apparitions : au chargement (data-delay en secondes) ou quand l'élément entre à l'écran.
const show = (el) => {
  const d = parseFloat(el.dataset.delay || 0);
  setTimeout(() => el.classList.add('in'), d * 1000);
};
const io = new IntersectionObserver((entries) => {
  entries.forEach((e) => {
    if (!e.isIntersecting) return;
    show(e.target);
    io.unobserve(e.target);
  });
}, { threshold: 0.15 });

const startPage = () => document.querySelectorAll('.rise, .drop').forEach((el) => {
  if (el.dataset.delay !== undefined) show(el); else io.observe(el);
});

// 0) Vidéo d'intro : voile flou après 2 s, puis elle s'en va au premier défilement.
const intro = document.getElementById('intro-video');
if (intro) {
  document.documentElement.classList.add('intro-lock');
  // Écran en hauteur (téléphone) : vidéo verticale ; sinon vidéo horizontale.
  const v = intro.querySelector('video');
  const tall = matchMedia('(orientation: portrait)').matches;
  v.poster = tall ? 'assets/img/intro-poster-mobile.jpg' : 'assets/img/intro-poster.jpg';
  v.src = tall ? 'assets/intro-mobile.mp4' : 'assets/intro.mp4';
  const dimTimer = setTimeout(() => intro.classList.add('dim'), 3000);
  const leave = () => {
    if (intro.classList.contains('out')) return;
    clearTimeout(dimTimer);
    // Un seul titre à l'écran : celui de la vidéo glisse à la place de celui de la page, caché en attendant.
    const pageTitle = document.querySelector('.top-title .mega');
    const introTitle = intro.querySelector('.mega');
    pageTitle.classList.remove('drop');
    pageTitle.style.visibility = 'hidden';
    const dy = pageTitle.getBoundingClientRect().top - introTitle.getBoundingClientRect().top;
    const now = new DOMMatrix(getComputedStyle(introTitle).transform).m42; // position actuelle (si le titre montait encore)
    introTitle.style.transform = `translateY(${now + dy}px)`;
    intro.classList.add('out');
    document.documentElement.classList.remove('intro-lock');
    startPage();
    setTimeout(() => { pageTitle.style.visibility = ''; intro.remove(); }, 1000); // fin du glissement
  };
  addEventListener('wheel', leave, { passive: true });
  addEventListener('touchmove', leave, { passive: true });
  addEventListener('keydown', (e) => { if ([' ', 'ArrowDown', 'PageDown', 'Enter'].includes(e.key)) leave(); });
  intro.addEventListener('click', leave);
} else startPage();
// Lignes de listes : décalées les unes après les autres.
document.querySelectorAll('.services li, .xp li').forEach((li, i, all) => {
  li.dataset.delay = (Array.prototype.indexOf.call(li.parentNode.children, li) * 0.08).toFixed(2);
  io.observe(li);
});

// 2) Bouton « Copier l'email ».
document.querySelectorAll('.btn-copy').forEach((b) => {
  const label = b.querySelector('span');
  b.addEventListener('click', async () => {
    try { await navigator.clipboard.writeText(b.dataset.email); } catch (e) { return; }
    label.textContent = 'Copié !';
    setTimeout(() => (label.textContent = "Copier l'email"), 1600);
  });
});

// 3) « Projet suivant » : la carte se redresse en 3D pendant le défilement.
const next = document.querySelector('.next-inner');
if (next) {
  const tick = () => {
    const r = next.getBoundingClientRect();
    // p = 0 quand le bloc entre par le bas, 1 quand il arrive au milieu de l'écran
    const p = Math.min(1, Math.max(0, (innerHeight - r.top) / (innerHeight * 0.6)));
    next.style.transform = `perspective(1200px) scale(${0.8 + 0.2 * p}) rotateX(${-60 * (1 - p)}deg)`;
  };
  addEventListener('scroll', tick, { passive: true });
  addEventListener('resize', tick);
  tick();
}
