// Chain view connectors: drawn between card edges after layout, redrawn on resize.
// Hover or focus a card to highlight everything upstream and downstream of it.
(function () {
  const chain = document.getElementById('chain');
  const svg = document.getElementById('wires');
  const NS = 'http://www.w3.org/2000/svg';
  const paths = [];

  function draw() {
    svg.textContent = '';
    paths.length = 0;
    if (getComputedStyle(svg).display === 'none') return;
    const box = chain.getBoundingClientRect();
    // spread several lines leaving (or entering) one card along its edge, in edge order
    const outs = {}, ins = {};
    EDGES.forEach((e, i) => { (outs[e.from] = outs[e.from] || []).push(i); (ins[e.to] = ins[e.to] || []).push(i); });
    const port = (r, list, i) => {
      const n = list.length, k = list.indexOf(i);
      const top = r.top + 22, bot = Math.max(top, r.bottom - 14);
      return n === 1 ? Math.min(top, bot) : top + (bot - top) * k / (n - 1);
    };
    // product -> rows: one neutral trunk, one graded tick per row
    const bus = EDGES.map((e, i) => [e, i]).filter(([e]) => e.bus);
    const rowsBox = document.querySelector('.rows').getBoundingClientRect();
    if (bus.length) {
      const pr = document.getElementById(bus[0][0].from).getBoundingClientRect();
      const sx = rowsBox.left - box.left - 26;
      const py = pr.top + 30 - box.top;
      const ys = bus.map(([e]) => {
        const r = document.getElementById(e.to).getBoundingClientRect();
        return r.top + 22 - box.top;
      });
      const trunk = document.createElementNS(NS, 'path');
      trunk.setAttribute('d', `M${pr.right - box.left},${py} H${sx} M${sx},${Math.min(py, ...ys)} V${Math.max(py, ...ys)}`);
      trunk.setAttribute('class', 'rm-ln trunk');
      svg.appendChild(trunk);
      bus.forEach(([e], k) => {
        const r = document.getElementById(e.to).getBoundingClientRect();
        add(e, `M${sx},${ys[k]} H${r.left - box.left}`);
      });
    }
    EDGES.forEach((e, i) => {
      if (e.bus) return;
      const a = document.getElementById(e.from), b = document.getElementById(e.to);
      if (!a || !b) return;
      const ra = a.getBoundingClientRect(), rb = b.getBoundingClientRect();
      const x1 = ra.right - box.left, y1 = port(ra, outs[e.from].filter(j => !EDGES[j].bus), i) - box.top;
      const x2 = rb.left - box.left, y2 = port(rb, ins[e.to], i) - box.top;
      const dx = Math.max(24, (x2 - x1) / 2);
      add(e, `M${x1},${y1} C${x1 + dx},${y1} ${x2 - dx},${y2} ${x2},${y2}`);
    });

    function add(e, d) {
      const p = document.createElementNS(NS, 'path');
      p.setAttribute('d', d);
      p.setAttribute('class', 'rm-ln e ' + e.grade);
      const t = document.createElementNS(NS, 'title');
      t.textContent = e.label;
      p.appendChild(t);
      svg.appendChild(p);
      paths.push({ el: p, e });
    }
  }

  function linked(id) {
    const keep = new Set([id]);
    const walk = (dir) => {
      let frontier = [id];
      while (frontier.length) {
        const next = [];
        for (const n of frontier)
          for (const e of EDGES) {
            const [src, dst] = dir ? [e.from, e.to] : [e.to, e.from];
            if (src === n && !keep.has(dst)) { keep.add(dst); next.push(dst); }
          }
        frontier = next;
      }
    };
    walk(true); walk(false);
    return keep;
  }

  function focus(id) {
    const keep = linked(id);
    chain.classList.add('focus');
    document.querySelectorAll('.rm-card').forEach(c => c.classList.toggle('on', keep.has(c.id)));
    paths.forEach(({ el, e }) => el.classList.toggle('on', keep.has(e.from) && keep.has(e.to)));
  }
  function clear() {
    chain.classList.remove('focus');
    document.querySelectorAll('.rm-card.on, .e.on').forEach(n => n.classList.remove('on'));
  }

  document.querySelectorAll('.rm-card').forEach(c => {
    c.tabIndex = 0;
    c.addEventListener('mouseenter', () => focus(c.id));
    c.addEventListener('mouseleave', clear);
    c.addEventListener('focus', () => focus(c.id));
    c.addEventListener('blur', clear);
  });
  new ResizeObserver(draw).observe(chain);
  document.querySelectorAll('details').forEach(d => d.addEventListener('toggle', draw));
  draw();
})();

// Picture viewer: a thumbnail opens its full evidence figure (caption, provenance, date, footnote).
(() => {
  const box = document.getElementById('lightbox');
  if (!box) return;
  const body = box.querySelector('.body');
  document.addEventListener('click', ev => {
    const btn = ev.target.closest('[data-fig]');
    if (btn) {
      const tpl = document.getElementById(btn.dataset.fig);
      if (!tpl) return;
      body.replaceChildren(tpl.content.cloneNode(true));
      box.showModal();
      return;
    }
    if (ev.target.closest('[data-close]') || ev.target === box) box.close();
    else if (box.open && ev.target.closest('.rm-lightbox a[href^="#"]')) box.close();
  });
})();
