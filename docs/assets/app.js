(function () {
  var sidebar = document.getElementById('sidebar');
  var menuBtn = document.getElementById('menuBtn');

  function closeMenu() {
    sidebar.classList.remove('open');
    menuBtn.setAttribute('aria-expanded', 'false');
  }
  menuBtn.addEventListener('click', function () {
    var open = sidebar.classList.toggle('open');
    menuBtn.setAttribute('aria-expanded', String(open));
  });
  document.addEventListener('click', function (e) {
    if (window.innerWidth > 860) return;
    if (!sidebar.contains(e.target) && !menuBtn.contains(e.target)) closeMenu();
  });

  var modal = document.getElementById('searchModal');
  var input = document.getElementById('searchInput');
  var results = document.getElementById('searchResults');
  var items = (window.SEARCH_INDEX || []);
  var sel = -1;

  function openSearch() {
    modal.hidden = false;
    input.value = '';
    input.focus();
    render('');
  }
  function closeSearch() {
    modal.hidden = true;
    sel = -1;
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
    var heads = (item.h || []).join(' ').toLowerCase();
    if (heads.indexOf(q) > -1) s += 18;
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
      return '<a class="sr-item" data-i="' + i + '" href="' + it.u + '">' +
        '<div class="sr-path">' + esc(it.g || '') + '</div>' +
        '<div class="sr-title">' + esc(it.t) + '</div>' +
        '<div class="sr-snip">' + esc(snippet(it, q || it.t.toLowerCase())) + '</div></a>';
    }).join('');
    sel = -1;
  }
  function move(d) {
    var nodes = results.querySelectorAll('.sr-item');
    if (!nodes.length) return;
    if (sel > -1) nodes[sel].classList.remove('sel');
    sel = (sel + d + nodes.length) % nodes.length;
    nodes[sel].classList.add('sel');
    nodes[sel].scrollIntoView({ block: 'nearest' });
  }

  document.getElementById('searchBtn').addEventListener('click', openSearch);
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
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && !modal.hidden) closeSearch();
    var tag = (document.activeElement && document.activeElement.tagName) || '';
    if (e.key === '/' && !/^(INPUT|TEXTAREA|SELECT)$/.test(tag)) {
      e.preventDefault(); openSearch();
    }
  });
})();
