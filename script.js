// Sticky nav style on scroll
window.addEventListener('scroll', () => {
  document.querySelector('nav').classList.toggle('scrolled', window.scrollY > 60);
});

// Mobile nav toggle
function toggleNav() {
  document.getElementById('navMobile').classList.toggle('open');
}

// Copy email to clipboard
function copyEmail() {
  navigator.clipboard.writeText('joshtorrison@gmail.com');
  const btn = event.target;
  const orig = btn.textContent;
  btn.textContent = 'Copied!';
  setTimeout(() => btn.textContent = orig, 2000);
}

// Rotating hero text
const rotatingTerms = ['Wedding DJ', 'Event DJ', 'Corporate DJ', 'Party DJ'];
let termIndex = 0;
const rotatingEl = document.querySelector('.rotating-text');
if (rotatingEl) {
  setInterval(() => {
    rotatingEl.classList.add('fade');
    setTimeout(() => {
      termIndex = (termIndex + 1) % rotatingTerms.length;
      rotatingEl.textContent = rotatingTerms[termIndex];
      rotatingEl.classList.remove('fade');
    }, 500);
  }, 2800);
}
