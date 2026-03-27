// Theme toggle (dark/light)
(function () {
  const btn = document.getElementById('theme-toggle');
  const stored = localStorage.getItem('betscore-theme') || 'dark';
  document.documentElement.setAttribute('data-theme', stored);
  updateIcon(stored);

  if (btn) {
    btn.addEventListener('click', () => {
      const current = document.documentElement.getAttribute('data-theme') || 'dark';
      const next = current === 'dark' ? 'light' : 'dark';
      document.documentElement.setAttribute('data-theme', next);
      localStorage.setItem('betscore-theme', next);
      updateIcon(next);
    });
  }

  function updateIcon(theme) {
    if (!btn) return;
    const icon = btn.querySelector('i');
    if (icon) {
      icon.className = theme === 'dark' ? 'fa-solid fa-sun' : 'fa-solid fa-moon';
    }
  }
})();
