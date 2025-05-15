// main.js
document.addEventListener('DOMContentLoaded', () => {
  // Mobile menu toggle
  const btn = document.getElementById('menu-btn');
  const menu = document.getElementById('mobile-menu');
  btn.addEventListener('click', () => menu.classList.toggle('hidden'));

  // Hero typing effect
  const el = document.getElementById('typing-text');
  const text = 'AI-Powered Patient Screening';
  let i = 0;
  function type() {
    el.textContent = text.substring(0, i++);
    if (i <= text.length) setTimeout(type, 100);
  }
  type();
});
