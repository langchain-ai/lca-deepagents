// ── Page components ──────────────────────────────────────────────────────────
// Global language state: one language choice drives everything on the page —
// the page-level switch (data-page-lang-switch) AND every per-block code-tabs
// (data-code-tabs) toggle move together. Persisted in localStorage so the
// choice also carries across lessons.
document.addEventListener('DOMContentLoaded', function () {
  var codeTabWraps = document.querySelectorAll('[data-code-tabs]');
  var pageSwitchButtons = document.querySelectorAll('[data-page-lang-switch] [data-page-lang]');

  function setGlobalLang(lang) {
    pageSwitchButtons.forEach(function (btn) {
      var active = btn.getAttribute('data-page-lang') === lang;
      btn.classList.toggle('active', active);
      btn.setAttribute('aria-selected', active ? 'true' : 'false');
    });

    document.querySelectorAll('[data-lang]').forEach(function (el) {
      el.hidden = el.getAttribute('data-lang') !== lang;
    });

    codeTabWraps.forEach(function (wrap) {
      var tabs = wrap.querySelectorAll('[data-code-tab]');
      var hasLang = Array.prototype.some.call(tabs, function (tab) {
        return tab.getAttribute('data-code-tab') === lang;
      });
      if (!hasLang) return; // this block doesn't offer that language — leave it as-is

      var panels = wrap.querySelectorAll('[data-code-panel]');
      tabs.forEach(function (tab) {
        var active = tab.getAttribute('data-code-tab') === lang;
        tab.classList.toggle('active', active);
        tab.setAttribute('aria-selected', active ? 'true' : 'false');
      });
      panels.forEach(function (panel) {
        panel.classList.toggle('active', panel.getAttribute('data-code-panel') === lang);
      });
    });

    try { localStorage.setItem('lca-page-lang', lang); } catch (e) {}
  }

  codeTabWraps.forEach(function (wrap) {
    var tabs = wrap.querySelectorAll('[data-code-tab]');
    tabs.forEach(function (tab) {
      tab.addEventListener('click', function () {
        setGlobalLang(tab.getAttribute('data-code-tab'));
      });
    });
  });

  pageSwitchButtons.forEach(function (btn) {
    btn.addEventListener('click', function () {
      setGlobalLang(btn.getAttribute('data-page-lang'));
    });
  });

  if (codeTabWraps.length || pageSwitchButtons.length) {
    var stored = null;
    try { stored = localStorage.getItem('lca-page-lang'); } catch (e) {}
    setGlobalLang(stored || 'python');
  }

  // Fixed page-lang-switch: reserve its height with a spacer (it's taken out
  // of flow by position:fixed), then auto-hide on scroll-down, reappear on
  // scroll-up.
  var switchEl = document.querySelector('[data-page-lang-switch]');
  if (switchEl) {
    var spacer = document.createElement('div');
    switchEl.parentNode.insertBefore(spacer, switchEl.nextSibling);
    function syncSpacerHeight() { spacer.style.height = switchEl.offsetHeight + 'px'; }
    syncSpacerHeight();
    window.addEventListener('resize', syncSpacerHeight);

    var lastScrollY = window.scrollY;
    window.addEventListener('scroll', function () {
      var currentScrollY = window.scrollY;
      if (currentScrollY < lastScrollY || currentScrollY < 10) {
        switchEl.classList.remove('pls-hidden');
      } else if (currentScrollY > lastScrollY && currentScrollY > 100) {
        switchEl.classList.add('pls-hidden');
      }
      lastScrollY = currentScrollY;
    }, { passive: true });
  }

  var panel = document.querySelector('.lt-panel');
  if (!panel) return;

  var hasLab = false, hasQuiz = false, hasHomework = false;
  document.querySelectorAll('.lt-tab').forEach(function (t) {
    var p = t.getAttribute('data-p') || '';
    if (p.startsWith('lab')) hasLab = true;
    if (p === 'quiz') hasQuiz = true;
    if (p.startsWith('homework')) hasHomework = true;
  });

  var parts = [];
  if (hasLab) parts.push('Lab');
  if (hasQuiz) parts.push('Quiz');
  if (hasHomework) parts.push('Homework');

  var label = '↑  Back to top';
  if (parts.length) label += ': ' + parts.join(' & ');

  var btn = document.createElement('button');
  btn.className = 'back-to-top-btn';
  btn.textContent = label;
  btn.addEventListener('click', function () { window.scrollTo({ top: 0, behavior: 'instant' }); });

  var refH2 = null;
  panel.querySelectorAll('h2').forEach(function (h) {
    if (h.textContent.trim() === 'References') refH2 = h;
  });
  if (refH2) panel.insertBefore(btn, refH2);
  else panel.appendChild(btn);
});

// ── SVG fragment helpers ──────────────────────────────────────────────────────

function solidArrow(x1, x2, y, lbl, lx, a, fs) {
  fs = fs || 12.5;
  return `<line class="al" x1="${x1}" y1="${y}" x2="${x2}" y2="${y}" stroke-width="1.5" marker-end="url(#${a})"/>` +
         `<text class="at" x="${lx}" y="${y-7}" text-anchor="middle" font-size="${fs}">${lbl}</text>`;
}

function dashedArrow(x1, x2, y, lbl, lx, a, fs) {
  fs = fs || 12.5;
  return `<line class="al" x1="${x1}" y1="${y}" x2="${x2}" y2="${y}" stroke-width="1.5" stroke-dasharray="6,4" marker-end="url(#${a})"/>` +
         `<text class="at" x="${lx}" y="${y-7}" text-anchor="middle" font-size="${fs}">${lbl}</text>`;
}

function labelBox(cx, y, w, lines, fs) {
  fs = fs || 12;
  const lh = 20, pad = 12;
  const h = lines.length * lh + pad;
  let s = `<rect class="ab" x="${cx - w/2}" y="${y}" width="${w}" height="${h}" rx="4" stroke-width="1.5"/>`;
  lines.forEach((t, i) => {
    s += `<text class="abt" x="${cx}" y="${y + pad/2 + lh*(i+0.8)}" text-anchor="middle" font-size="${fs}">${t}</text>`;
  });
  return s;
}

// ── Diagram builder ──────────────────────────────────────────────────────────
// opts: { id, participants, cx, bw, bh, tby, bby, vw, vh,
//         steps, buildSteps, staticSVG (optional), stageBg (optional) }

function buildDiagram(opts) {
  const { id, participants, cx, bw, bh, tby, bby, vw, vh, steps, buildSteps, staticSVG: customStatic, stageBg, partFontSize } = opts;
  const wrap = document.getElementById(id);
  if (!wrap) return;
  const n = steps.length;
  const arrId  = `arr-${id}`;
  const arrAId = `arr-a-${id}`;
  const stepSVGs = buildSteps(arrId);

  // Static SVG: use custom if provided, otherwise generate from participants
  let staticSVG = '';
  if (customStatic !== undefined) {
    staticSVG = customStatic;
  } else {
    const ly1 = tby + bh;
    const ly2 = bby;
    participants.forEach(function(lbl, i) {
      const x = cx[i] - bw/2;
      staticSVG += `<rect x="${x}" y="${tby}" width="${bw}" height="${bh}" rx="4" fill="#161F34" stroke="#2F4B68" stroke-width="1.5"/>`;
      const pfs = partFontSize || 13;
      staticSVG += `<text x="${cx[i]}" y="${tby + bh/2 + 5}" text-anchor="middle" fill="#E5F4FF" font-size="${pfs}" font-weight="500">${lbl}</text>`;
      staticSVG += `<line x1="${cx[i]}" y1="${ly1}" x2="${cx[i]}" y2="${ly2}" stroke="#40668D" stroke-width="1.5" stroke-dasharray="5,5"/>`;
      staticSVG += `<rect x="${x}" y="${bby}" width="${bw}" height="${bh}" rx="4" fill="#161F34" stroke="#2F4B68" stroke-width="1.5"/>`;
      staticSVG += `<text x="${cx[i]}" y="${bby + bh/2 + 5}" text-anchor="middle" fill="#E5F4FF" font-size="${pfs}" font-weight="500">${lbl}</text>`;
    });
  }

  const stepGroups = stepSVGs.map(function(el, i) {
    return `<g class="step step-hidden" id="${id}-s${i}">${el}</g>`;
  }).join('');

  const svg = `<svg viewBox="0 0 ${vw} ${vh}" xmlns="http://www.w3.org/2000/svg" font-family="'IBM Plex Mono','Courier New',monospace">
<defs>
  <marker id="${arrId}" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
    <polygon points="0 0, 8 3, 0 6" fill="#40668D"/>
  </marker>
  <marker id="${arrAId}" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
    <polygon points="0 0, 8 3, 0 6" fill="#7FC8FF"/>
  </marker>
</defs>
<rect width="${vw}" height="${vh}" fill="#030710"/>
${staticSVG}
${stepGroups}
</svg>`;

  wrap.innerHTML = `
    <div class="sd-stage" id="${id}-stage" tabindex="0" style="background:${stageBg || '#030710'}">${svg}</div>
    <div class="sd-bar">
      <div class="sd-caption">
        <strong id="${id}-tag">Click &#8594; to begin</strong>
        <span id="${id}-cap">Step through the sequence one message at a time.</span>
      </div>
      <div class="sd-controls">
        <button class="sd-btn" id="${id}-prev" disabled title="Previous">&#8592;</button>
        <button class="sd-btn" id="${id}-next" title="Next">&#8594;</button>
      </div>
    </div>
    <div class="sd-dots" id="${id}-dots">${steps.map(function(_, i) { return `<div class="sd-dot" data-i="${i}"></div>`; }).join('')}</div>
    <div class="mobile-note">Best viewed on a wider screen</div>
  `;

  var tagEl   = document.getElementById(id + '-tag');
  var capEl   = document.getElementById(id + '-cap');
  var prevBtn = document.getElementById(id + '-prev');
  var nextBtn = document.getElementById(id + '-next');
  var dots    = wrap.querySelectorAll('.sd-dot');
  var stage   = document.getElementById(id + '-stage');

  // current === -1 means "overview" state: all steps fully visible
  var current = -1;

  function getStep(i) { return document.getElementById(id + '-s' + i); }

  function applyState(i, state) {
    var el = getStep(i);
    el.classList.remove('step-hidden', 'step-past', 'step-current');
    el.classList.add(state);
    var marker = state === 'step-current' ? arrAId : arrId;
    el.querySelectorAll('line[marker-end]').forEach(function(line) {
      line.setAttribute('marker-end', 'url(#' + marker + ')');
    });
  }

  function showAll() {
    for (var i = 0; i < n; i++) applyState(i, 'step-past');
    current = -1;
    tagEl.textContent = 'Overview';
    capEl.textContent = 'The complete sequence. Click → to walk through it step by step.';
    prevBtn.disabled = true;
    nextBtn.disabled = false;
    dots.forEach(function(d) { d.classList.remove('active'); });
  }

  function goTo(index) {
    if (index < 0 || index >= n) return;
    for (var i = 0; i < n; i++) {
      if      (i < index)   applyState(i, 'step-past');
      else if (i === index) applyState(i, 'step-current');
      else                  applyState(i, 'step-hidden');
    }
    current = index;
    tagEl.textContent = steps[index].tag;
    capEl.textContent = steps[index].caption;
    prevBtn.disabled = false;
    nextBtn.disabled = index === n - 1;
    dots.forEach(function(d, i) { d.classList.toggle('active', i === index); });
  }

  function advance() {
    if (current === -1) goTo(0);
    else if (current < n - 1) goTo(current + 1);
  }

  function retreat() {
    if (current <= 0) showAll();
    else goTo(current - 1);
  }

  showAll();  // start fully rendered

  prevBtn.addEventListener('click', retreat);
  nextBtn.addEventListener('click', advance);
  dots.forEach(function(d, i) { d.addEventListener('click', function() { goTo(i); }); });
  stage.addEventListener('click', advance);
  stage.addEventListener('keydown', function(e) {
    if (e.key === 'ArrowRight' || e.key === ' ') { e.preventDefault(); advance(); }
    if (e.key === 'ArrowLeft')                   { e.preventDefault(); retreat(); }
  });
  var tx = 0;
  stage.addEventListener('touchstart', function(e) { tx = e.touches[0].clientX; }, { passive: true });
  stage.addEventListener('touchend', function(e) {
    var dx = e.changedTouches[0].clientX - tx;
    if (Math.abs(dx) > 40) dx < 0 ? advance() : retreat();
  });
}

// ── Slideshow builder ─────────────────────────────────────────────────────────
// opts: { id, slides }  where each slide is { src, tag, caption }

function buildSlideshow(opts) {
  var id           = opts.id;
  var slides       = opts.slides;
  var initialSlide = opts.initialSlide || 0;
  var wrap         = document.getElementById(id);
  if (!wrap) return;
  var n       = slides.length;
  var current = 0;

  wrap.innerHTML =
    '<div class="sd-stage ss-stage" id="' + id + '-stage" tabindex="0">' +
      '<img class="ss-img" id="' + id + '-img" src="" alt="">' +
    '</div>' +
    '<div class="sd-bar">' +
      '<div class="sd-caption">' +
        '<strong id="' + id + '-tag"></strong>' +
        '<div id="' + id + '-cap" class="ss-cap"></div>' +
      '</div>' +
      '<div class="sd-controls">' +
        '<button class="sd-btn" id="' + id + '-prev" disabled title="Previous">&#8592;</button>' +
        '<button class="sd-btn" id="' + id + '-next" title="Next">&#8594;</button>' +
      '</div>' +
    '</div>' +
    '<div class="sd-dots" id="' + id + '-dots">' +
      slides.map(function(_, i) { return '<div class="sd-dot" data-i="' + i + '"></div>'; }).join('') +
    '</div>' +
    '<div class="mobile-note">Tap image to advance</div>';

  var imgEl   = document.getElementById(id + '-img');
  var tagEl   = document.getElementById(id + '-tag');
  var capEl   = document.getElementById(id + '-cap');
  var prevBtn = document.getElementById(id + '-prev');
  var nextBtn = document.getElementById(id + '-next');
  var dots    = wrap.querySelectorAll('.sd-dot');
  var stage   = document.getElementById(id + '-stage');

  function goTo(i) {
    if (i < 0 || i >= n) return;
    current      = i;
    imgEl.src    = slides[i].src;
    imgEl.alt    = slides[i].tag;
    tagEl.textContent = slides[i].tag;
    capEl.innerHTML = '';
    slides[i].caption.split(/\n\s*\n/).forEach(function(para) {
      var p = document.createElement('p');
      p.textContent = para.trim();
      if (p.textContent) capEl.appendChild(p);
    });
    prevBtn.disabled  = i === 0;
    nextBtn.disabled  = i === n - 1;
    dots.forEach(function(d, j) { d.classList.toggle('active', j === i); });
  }

  function advance() { goTo(current + 1); }
  function retreat() { goTo(current - 1); }

  goTo(initialSlide);

  prevBtn.addEventListener('click', retreat);
  nextBtn.addEventListener('click', advance);
  dots.forEach(function(d, i) { d.addEventListener('click', function() { goTo(i); }); });
  stage.addEventListener('click', advance);
  stage.addEventListener('keydown', function(e) {
    if (e.key === 'ArrowRight' || e.key === ' ') { e.preventDefault(); advance(); }
    if (e.key === 'ArrowLeft')                   { e.preventDefault(); retreat(); }
  });
  var tx = 0;
  stage.addEventListener('touchstart', function(e) { tx = e.touches[0].clientX; }, { passive: true });
  stage.addEventListener('touchend', function(e) {
    var dx = e.changedTouches[0].clientX - tx;
    if (Math.abs(dx) > 40) dx < 0 ? advance() : retreat();
  });
}
