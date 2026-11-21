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

/* ---------- фильтр таблиц по платформам ---------- */
(function () {
  var MAP = [
    { key: "mac", re: /mac\s*os/i, label: "macOS" },
    { key: "win", re: /^win/i, label: "Windows" },
    { key: "linux", re: /linux/i, label: "Linux" },
    { key: "ios", re: /^ios/i, label: "iOS" },
    { key: "android", re: /^andr/i, label: "Android" }
  ];

  function textOf(el) { return (el.textContent || "").trim(); }

  document.querySelectorAll("article table").forEach(function (table) {
    var headCells = table.querySelectorAll("thead th");
    if (!headCells.length) headCells = table.querySelectorAll("tr:first-child th");
    if (!headCells.length) return;

    var cols = {};
    headCells.forEach(function (th, i) {
      var t = textOf(th);
      MAP.forEach(function (p) { if (p.re.test(t)) cols[p.key] = i; });
    });
    if (Object.keys(cols).length < 3) return;

    var bodyRows = Array.prototype.slice.call(table.querySelectorAll("tbody tr"));
    if (!bodyRows.length) return;

    var box = document.createElement("div");
    box.className = "table-filter";
    box.setAttribute("role", "group");
    box.setAttribute("aria-label", "Фильтр по платформе");

    var status = document.createElement("span");
    status.className = "table-filter-count";
    status.setAttribute("aria-live", "polite");

    function apply(key) {
      var shown = 0;
      bodyRows.forEach(function (row) {
        var cells = row.children;
        var hide = false;
        if (key && cells[cols[key]] !== undefined) {
          var v = textOf(cells[cols[key]]);
          hide = (v === "—" || v === "-" || v === "");
        }
        row.hidden = hide;
        if (!hide) shown++;
      });
      status.textContent = "показано " + shown + " из " + bodyRows.length;
      box.querySelectorAll("button").forEach(function (b) {
        b.setAttribute("aria-pressed", String(b.dataset.key === key));
      });
    }

    function addButton(key, label) {
      var b = document.createElement("button");
      b.type = "button";
      b.dataset.key = key;
      b.textContent = label;
      b.setAttribute("aria-pressed", "false");
      b.addEventListener("click", function () {
        apply(b.getAttribute("aria-pressed") === "true" || key === "" ? "" : key);
      });
      box.appendChild(b);
    }

    addButton("", "Все");
    MAP.forEach(function (p) { if (cols[p.key] !== undefined) addButton(p.key, p.label); });
    box.appendChild(status);
    table.parentNode.insertBefore(box, table);
    apply("");
  });
})();

/* ---------- профили риска ---------- */
(function () {
  var root = document.documentElement;
  var order = { basic: 0, elevated: 1, targeted: 2 };
  var btns = Array.prototype.slice.call(document.querySelectorAll('.profile-switch button'));
  if (!btns.length) return;

  var groups = {
    elevated: Array.prototype.slice.call(document.querySelectorAll('.profile.elevated')),
    targeted: Array.prototype.slice.call(document.querySelectorAll('.profile.targeted'))
  };
  var hint = document.querySelector('.profile-hint');

  function countFor(p) {
    if (p === 'basic') return 0;
    if (p === 'elevated') return groups.elevated.length;
    return groups.elevated.length + groups.targeted.length;
  }
  function firstBlock(p) {
    if (p === 'targeted' && groups.targeted.length) return groups.targeted[0];
    if (groups.elevated.length) return groups.elevated[0];
    return groups.targeted.length ? groups.targeted[0] : null;
  }

  btns.forEach(function (b) {
    var n = countFor(b.dataset.profile);
    var cnt = document.createElement('span');
    cnt.className = 'cnt';
    cnt.textContent = String(n);
    b.appendChild(cnt);
    b.dataset.count = String(n);
    if (!n) b.title = 'На этой странице нет отдельных пунктов для этого профиля';
  });

  function updateHint() {
    if (!hint) return;
    var e = groups.elevated.length, t = groups.targeted.length;
    if (!e && !t) { hint.textContent = 'Дополнительных блоков на странице нет'; return; }
    var parts = [];
    if (e) parts.push('повышенный — ' + e);
    if (t) parts.push('целевой — ' + t);
    hint.textContent = 'На странице: ' + parts.join(', ');
  }

  function toast(msg, target) {
    var old = document.querySelector('.toast');
    if (old) old.remove();
    var el = document.createElement('div');
    el.className = 'toast';
    el.setAttribute('role', 'status');
    var span = document.createElement('span');
    span.textContent = msg;
    el.appendChild(span);
    if (target) {
      var btn = document.createElement('button');
      btn.type = 'button';
      btn.textContent = 'Показать';
      btn.addEventListener('click', function () {
        target.scrollIntoView({ block: 'start' });
        el.remove();
      });
      el.appendChild(btn);
    }
    document.body.appendChild(el);
    setTimeout(function () { if (el.parentNode) el.remove(); }, 7000);
  }

  function apply(p, persist, announce) {
    if (!(p in order)) p = 'basic';
    root.dataset.profile = p;
    btns.forEach(function (b) {
      b.setAttribute('aria-pressed', String(b.dataset.profile === p));
    });
    if (persist) {
      try { localStorage.setItem('profile', p); } catch (e) {}
    }
    if (announce) {
      var n = countFor(p);
      if (!n) {
        toast('Для профиля «' + (p === 'elevated' ? 'повышенный' : 'целевой') +
              '» на этой странице отдельных пунктов нет');
      } else {
        var block = firstBlock(p);
        toast('Профиль изменён: добавлено блоков — ' + n, block);
      }
    }
  }

  function revealHash() {
    if (!location.hash) return;
    var id;
    try { id = decodeURIComponent(location.hash.slice(1)); } catch (e) { return; }
    var el = document.getElementById(id);
    if (!el) return;
    var box = el.closest('.profile');
    if (!box) return;
    var need = box.classList.contains('targeted') ? 'targeted' : 'elevated';
    if (order[need] > order[root.dataset.profile || 'basic']) apply(need, true, false);
  }

  apply(root.dataset.profile || 'basic', false, false);
  updateHint();
  revealHash();

  btns.forEach(function (b) {
    b.addEventListener('click', function () { apply(b.dataset.profile, true, true); });
  });
  window.addEventListener('hashchange', revealHash);
})();

/* ---------- таймлайн: развернуть всё ---------- */
(function () {
  var items = Array.prototype.slice.call(document.querySelectorAll('details.tl'));
  if (!items.length) return;
  var btn = document.querySelector('[data-tl-toggle]');

  function allOpen() {
    return items.every(function (d) { return d.open; });
  }

  function label() {
    if (!btn) return;
    btn.textContent = allOpen() ? 'Свернуть всё' : 'Развернуть всё';
    btn.setAttribute('aria-pressed', String(allOpen()));
  }

  if (btn) {
    btn.addEventListener('click', function () {
      var open = !allOpen();
      items.forEach(function (d) { d.open = open; });
      label();
    });
    items.forEach(function (d) { d.addEventListener('toggle', label); });
    label();
  }

  window.addEventListener('beforeprint', function () {
    items.forEach(function (d) {
      d.dataset.wasOpen = d.open ? '1' : '0';
      d.open = true;
    });
  });

  window.addEventListener('afterprint', function () {
    items.forEach(function (d) {
      if (d.dataset.wasOpen === '0') d.open = false;
    });
  });
})();
