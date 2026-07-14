/* Animated deep-space background: stars, golden particles, drifting nebula. */
(function () {
  const c = document.getElementById('starfield');
  if (!c) return;
  const ctx = c.getContext('2d');
  let W, H, stars = [], dust = [], t = 0;

  function resize() {
    W = c.width = innerWidth;
    H = c.height = innerHeight;
    stars = Array.from({ length: Math.min(240, W / 6) }, () => ({
      x: Math.random() * W, y: Math.random() * H,
      r: Math.random() * 1.3 + .2,
      tw: Math.random() * Math.PI * 2,
      sp: .12 + Math.random() * .5,
    }));
    dust = Array.from({ length: 26 }, () => ({
      x: Math.random() * W, y: Math.random() * H,
      r: Math.random() * 2.2 + .8,
      vx: (Math.random() - .5) * .18, vy: -(.06 + Math.random() * .16),
      a: Math.random() * .5 + .15,
    }));
  }
  addEventListener('resize', resize); resize();

  function frame() {
    t += .008;
    ctx.clearRect(0, 0, W, H);

    // slow nebula
    const g1 = ctx.createRadialGradient(
      W * (.7 + Math.sin(t * .35) * .06), H * .2, 0,
      W * .7, H * .2, W * .5);
    g1.addColorStop(0, 'rgba(155,92,255,.055)');
    g1.addColorStop(1, 'transparent');
    ctx.fillStyle = g1; ctx.fillRect(0, 0, W, H);

    const g2 = ctx.createRadialGradient(
      W * .15, H * (.85 + Math.cos(t * .3) * .04), 0,
      W * .15, H * .85, W * .45);
    g2.addColorStop(0, 'rgba(217,178,91,.045)');
    g2.addColorStop(1, 'transparent');
    ctx.fillStyle = g2; ctx.fillRect(0, 0, W, H);

    // twinkling stars
    for (const s of stars) {
      const a = .35 + .65 * Math.abs(Math.sin(s.tw + t * s.sp * 4));
      ctx.globalAlpha = a;
      ctx.fillStyle = '#e8e4f5';
      ctx.beginPath(); ctx.arc(s.x, s.y, s.r, 0, 7); ctx.fill();
    }

    // rising golden particles
    for (const d of dust) {
      d.x += d.vx; d.y += d.vy;
      if (d.y < -8) { d.y = H + 8; d.x = Math.random() * W; }
      ctx.globalAlpha = d.a * (.6 + .4 * Math.sin(t * 2 + d.x));
      ctx.fillStyle = '#ffd700';
      ctx.shadowColor = '#d9b25b'; ctx.shadowBlur = 8;
      ctx.beginPath(); ctx.arc(d.x, d.y, d.r, 0, 7); ctx.fill();
      ctx.shadowBlur = 0;
    }
    ctx.globalAlpha = 1;
    requestAnimationFrame(frame);
  }
  frame();
})();
