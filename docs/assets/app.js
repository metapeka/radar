(function () {
  'use strict';

  /* ---------- боковое меню ---------- */
  var sidebar = document.getElementById('sidebar');
  var menuBtn = document.getElementById('menuBtn');

  function closeMenu(returnFocus) {
    sidebar.classList.remove('open');
    menuBtn.setAttribute('aria-expanded', 'false');
    menuBtn.setAttribute('aria-label', 'Открыть меню');
    document.body.style.overflow = '';
    if (returnFocus) menuBtn.focus();
  }

  if (menuBtn) {
    menuBtn.addEventListener('click', function () {
      var open = !sidebar.classList.contains('open');
      sidebar.classList.toggle('open', open);
      menuBtn.setAttribute('aria-expanded', String(open));
      menuBtn.setAttribute('aria-label', open ? 'Закрыть меню' : 'Открыть меню');
      document.body.style.overflow = open ? 'hidden' : '';
      if (open) {
        var first = sidebar.querySelector('a');
        if (first) first.focus();
      }
    });
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && sidebar.classList.contains('open')) closeMenu(true);
    });
    document.addEventListener('click', function (e) {
      if (window.innerWidth > 860) return;
      if (!sidebar.contains(e.target) && !menuBtn.contains(e.target)) closeMenu(false);
    });
  }

  /* ---------- прогресс чтения ---------- */
  var bar = document.getElementById('progress');
  if (bar) {
    var onScroll = function () {
      var h = document.documentElement;
      var max = h.scrollHeight - h.clientHeight;
      bar.style.width = (max > 0 ? (h.scrollTop / max) * 100 : 0) + '%';
    };
    document.addEventListener('scroll', onScroll, { passive: true });
    window.addEventListener('resize', onScroll);
    onScroll();
  }

  /* ---------- ссылки на заголовки ---------- */
  document.querySelectorAll('article h2[id], article h3[id]').forEach(function (h) {
    var a = document.createElement('a');
    a.className = 'anchor';
    a.href = '#' + h.id;
    a.setAttribute('aria-label', 'Ссылка на раздел: ' + h.textContent.trim());
    a.textContent = '#';
    h.appendChild(a);
  });

  /* ---------- чек-листы ---------- */
  var KEY = 'checks:' + location.pathname;
  var boxes = Array.prototype.slice.call(document.querySelectorAll('article input[type=checkbox]'));
  if (boxes.length) {
    var saved = {};
    try { saved = JSON.parse(localStorage.getItem(KEY) || '{}'); } catch (e) { saved = {}; }

    var summary = document.createElement('div');
    summary.className = 'check-summary';
    summary.innerHTML = '<span>Сделано <b>0</b> из ' + boxes.length + '</span>' +
      '<button type="button" id="checkReset">Сбросить</button>';
    document.body.appendChild(summary);

    var counter = summary.querySelector('b');
    var reset = summary.querySelector('#checkReset');

    function paint() {
      var done = 0;
      boxes.forEach(function (b, i) {
        if (b.checked) done++;
        var li = b.closest('li');
        if (li) li.classList.toggle('done', b.checked);
      });
      counter.textContent = String(done);
      summary.hidden = false;
    }
    function store() {
      var state = {};
      boxes.forEach(function (b, i) { if (b.checked) state[i] = 1; });
      try { localStorage.setItem(KEY, JSON.stringify(state)); } catch (e) { /* приватный режим */ }
    }

    boxes.forEach(function (b, i) {
      b.disabled = false;
      if (saved[i]) b.checked = true;
      b.addEventListener('change', function () { store(); paint(); });
    });
    reset.addEventListener('click', function () {
      boxes.forEach(function (b) { b.checked = false; });
      try { localStorage.removeItem(KEY); } catch (e) {}
      paint();
    });
    paint();
  }

  /* ---------- поиск ---------- */
  var modal = document.getElementById('searchModal');
  var input = document.getElementById('searchInput');
  var results = document.getElementById('searchResults');
  var items = window.SEARCH_INDEX || [];
  var sel = -1;
  var lastFocus = null;

  function focusables() {
    return modal.querySelectorAll('a[href],button,input,[tabindex]:not([tabindex="-1"])');
  }
  function openSearch() {
    lastFocus = document.activeElement;
    modal.hidden = false;
    var shell = document.querySelector('.shell');
    if (shell) shell.inert = true;
    input.value = '';
    input.focus();
    render('');
  }
  function closeSearch() {
    modal.hidden = true;
    sel = -1;
    var shell = document.querySelector('.shell');
    if (shell) shell.inert = false;
    if (lastFocus && document.contains(lastFocus)) lastFocus.focus();
    lastFocus = null;
  }
  function esc(s) {
    return String(s).replace(/[&<>"]/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c];
    });
  }
  function score(item, q) {
    var s = 0;
    if (item.t.toLowerCase().indexOf(q) === 0) s += 60;
    if (item.t.toLowerCase().indexOf(q) > -1) s += 30;
    if ((item.h || []).join(' ').toLowerCase().indexOf(q) > -1) s += 18;
    if ((item.x || '').toLowerCase().indexOf(q) > -1) s += 8;
    return s;
  }
  function snippet(item, q) {
    var x = item.x || '';
    var i = x.toLowerCase().indexOf(q);
    if (i < 0) return x.slice(0, 110);
    var start = Math.max(0, i - 45);
    return (start > 0 ? '…' : '') + x.slice(start, start + 130).trim() + '…';
  }
  function render(q) {
    q = q.trim().toLowerCase();
    var list = q
      ? items.map(function (it) { return { it: it, s: score(it, q) }; })
          .filter(function (r) { return r.s > 0; })
          .sort(function (a, b) { return b.s - a.s; })
          .slice(0, 12).map(function (r) { return r.it; })
      : items.slice(0, 10);
    if (!list.length) {
      results.innerHTML = '<div class="no-res">Ничего не найдено. Попробуйте «бэкап», «сессия», «2FA», «MVT».</div>';
      sel = -1;
      return;
    }
    results.innerHTML = list.map(function (it, i) {
      return '<a class="sr-item" role="option" aria-selected="false" data-i="' + i + '" href="' + it.u + '">' +
        '<div class="sr-path">' + esc(it.g || '') + '</div>' +
        '<div class="sr-title">' + esc(it.t) + '</div>' +
        '<div class="sr-snip">' + esc(snippet(it, q || it.t.toLowerCase())) + '</div></a>';
    }).join('');
    sel = -1;
  }
  function move(d) {
    var nodes = results.querySelectorAll('.sr-item');
    if (!nodes.length) return;
    if (sel > -1) {
      nodes[sel].classList.remove('sel');
      nodes[sel].setAttribute('aria-selected', 'false');
    }
    sel = (sel + d + nodes.length) % nodes.length;
    nodes[sel].classList.add('sel');
    nodes[sel].setAttribute('aria-selected', 'true');
    nodes[sel].scrollIntoView({ block: 'nearest' });
  }

  var searchBtn = document.getElementById('searchBtn');
  if (searchBtn && modal) {
    searchBtn.addEventListener('click', openSearch);
    modal.addEventListener('click', function (e) { if (e.target === modal) closeSearch(); });
    input.addEventListener('input', function () { render(input.value); });
    input.addEventListener('keydown', function (e) {
      if (e.key === 'ArrowDown') { e.preventDefault(); move(1); }
      else if (e.key === 'ArrowUp') { e.preventDefault(); move(-1); }
      else if (e.key === 'Enter') {
        var nodes = results.querySelectorAll('.sr-item');
        if (nodes.length) window.location.href = nodes[sel > -1 ? sel : 0].getAttribute('href');
      }
    });
    modal.addEventListener('keydown', function (e) {
      if (e.key !== 'Tab') return;
      var f = focusables();
      if (!f.length) return;
      var first = f[0], last = f[f.length - 1];
      if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
      else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
    });
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && !modal.hidden) closeSearch();
      var tag = (document.activeElement && document.activeElement.tagName) || '';
      if (e.key === '/' && !/^(INPUT|TEXTAREA|SELECT)$/.test(tag)) {
        e.preventDefault();
        openSearch();
      }
    });
  }
})();
