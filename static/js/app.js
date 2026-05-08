// Maison Aleta — storefront UI helpers
(function () {
  'use strict';

  // Add-to-cart form: rewrite the action URL based on the chosen variant
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
  });

  // Auto-dismiss flash messages
  document.querySelectorAll('.flash__item').forEach((el) => {
    setTimeout(() => {
      el.style.transition = 'opacity .4s ease';
      el.style.opacity = '0';
      setTimeout(() => el.remove(), 500);
    }, 4000);
  });
})();
