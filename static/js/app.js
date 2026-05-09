// LiveBoutique — storefront UI helpers
(function () {
  'use strict';

  // --- Add-to-cart form: rewrite the action URL based on the chosen variant
  // and reflect the selected variant's price in the product detail header.
  document.querySelectorAll('[data-add-to-cart]').forEach((form) => {
    const radios = form.querySelectorAll('input[name="variant"]');
    const priceValue = document.querySelector('[data-price-value]');

    function sync() {
      const selected = form.querySelector('input[name="variant"]:checked');
      if (!selected) return;
      const url = selected.dataset.addUrl;
      if (url) form.setAttribute('action', url);
      if (priceValue && selected.dataset.price) {
        const num = parseFloat(selected.dataset.price);
        if (!Number.isNaN(num)) {
          priceValue.textContent = num.toLocaleString(undefined, {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2,
          });
        }
      }
    }

    radios.forEach((r) => r.addEventListener('change', sync));
    sync();

    // Analytics: emit add_to_cart on submit (keyed off PostHog if configured).
    form.addEventListener('submit', () => {
      const selected = form.querySelector('input[name="variant"]:checked');
      const sku = selected ? selected.value : null;
      if (window.posthog && sku) {
        window.posthog.capture('add_to_cart', { variant_id: sku });
      }
    });
  });

  // --- PDP image gallery (click thumb to swap main image; tabbable) ---
  document.querySelectorAll('[data-gallery]').forEach((root) => {
    const main = root.querySelector('[data-gallery-image]');
    const thumbs = root.querySelectorAll('[data-gallery-thumb]');
    thumbs.forEach((thumb) => {
      thumb.addEventListener('click', () => {
        if (!main) return;
        main.src = thumb.dataset.src;
        main.alt = thumb.dataset.alt || main.alt;
        thumbs.forEach((t) => {
          t.classList.toggle('pdp__thumb--active', t === thumb);
          t.setAttribute('aria-selected', t === thumb ? 'true' : 'false');
        });
      });
    });

    // Touch-swipe on the main image for mobile gallery navigation.
    if (main && thumbs.length > 1) {
      let startX = 0;
      main.addEventListener('touchstart', (e) => {
        startX = e.touches[0].clientX;
      }, { passive: true });
      main.addEventListener('touchend', (e) => {
        const dx = (e.changedTouches[0] || {}).clientX - startX;
        if (Math.abs(dx) < 40) return;
        const active = root.querySelector('.pdp__thumb--active');
        const list = Array.from(thumbs);
        const idx = list.indexOf(active);
        if (idx === -1) return;
        const next = list[(idx + (dx < 0 ? 1 : -1) + list.length) % list.length];
        next.click();
      }, { passive: true });
    }
  });

  // --- Auto-dismiss flash messages ---
  document.querySelectorAll('.flash__item').forEach((el) => {
    setTimeout(() => {
      el.style.transition = 'opacity .4s ease';
      el.style.opacity = '0';
      setTimeout(() => el.remove(), 500);
    }, 4000);
  });

  // --- Analytics: begin_checkout / purchase ---
  if (document.body.classList || true) {
    const path = window.location.pathname;
    if (window.posthog) {
      if (/^\/checkout\/$/.test(path)) {
        window.posthog.capture('begin_checkout');
      }
      if (/\/checkout\/\d+\/success\//.test(path)) {
        const match = path.match(/\/checkout\/(\d+)\/success\//);
        window.posthog.capture('purchase', { order_id: match ? match[1] : null });
      }
    }
  }
})();
