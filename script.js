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

// GA4 event tracking — tag any element with data-ga-event="name" and it
// fires automatically on click. Forms fire on submit instead of click.
// Call links (tel:) and booking-tool links (calendly.com, cal.com,
// calendar.google.com) are auto-tagged even without a data attribute.
document.querySelectorAll('a[href^="tel:"]:not([data-ga-event])').forEach((a) => {
  a.dataset.gaEvent = 'call_tap';
});
document.querySelectorAll('a[href*="calendly.com"]:not([data-ga-event]), a[href*="cal.com"]:not([data-ga-event]), a[href*="calendar.google.com"]:not([data-ga-event])').forEach((a) => {
  a.dataset.gaEvent = 'book_a_call_click';
});

document.addEventListener('click', (e) => {
  const el = e.target.closest('[data-ga-event]');
  if (!el || el.tagName === 'FORM') return;
  if (typeof gtag === 'function') {
    gtag('event', el.dataset.gaEvent, {
      event_category: 'engagement',
      event_label: el.dataset.gaLabel || el.textContent.trim().slice(0, 100),
    });
  }
});

document.querySelectorAll('form').forEach((form) => {
  form.addEventListener('submit', () => {
    if (typeof gtag === 'function') {
      gtag('event', form.dataset.gaEvent || 'form_submit', {
        event_category: 'engagement',
        event_label: form.dataset.gaLabel || form.id || 'form',
      });
    }
  });
});

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
