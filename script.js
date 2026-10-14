// Old one-page anchor -> new page. #booking was the homepage's booking
// section before the multi-page rebuild; booking now lives at /contact/.
if (window.location.hash === '#booking') {
  window.location.replace('/contact/');
}

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
  navigator.clipboard.writeText('josh@denvereventdj.com');
  const btn = event.target;
  const orig = btn.textContent;
  btn.textContent = 'Copied!';
  setTimeout(() => btn.textContent = orig, 2000);
}

// GA4 event tracking — tag any element with data-ga-event="name" and it
// fires automatically on click. Forms fire on successful AJAX submit only
// (see below), never on click. Call links (tel:), email links (mailto:),
// and booking-tool links (calendly.com, cal.com, calendar.google.com) are
// auto-tagged even without a data attribute.
document.querySelectorAll('a[href^="tel:"]:not([data-ga-event])').forEach((a) => {
  a.dataset.gaEvent = 'call_tap';
});
document.querySelectorAll('a[href^="mailto:"]:not([data-ga-event])').forEach((a) => {
  a.dataset.gaEvent = 'email_click';
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

// Formspree submission over AJAX so generate_lead fires only on a
// genuinely successful submit, never on every click of the button and
// never on a Formspree-side rejection. Each form lives in a
// .booking-form-wrap with a sibling .form-success and .form-error.
document.querySelectorAll('.booking-form-wrap').forEach((wrap) => {
  const form = wrap.querySelector('form');
  const successBox = wrap.querySelector('.form-success');
  const errorBox = wrap.querySelector('.form-error');
  if (!form) return;

  form.addEventListener('submit', (e) => {
    e.preventDefault();
    errorBox && errorBox.classList.remove('visible');
    const submitBtn = form.querySelector('button[type="submit"]');
    if (submitBtn) submitBtn.disabled = true;

    fetch(form.action, {
      method: 'POST',
      body: new FormData(form),
      headers: { Accept: 'application/json' },
    })
      .then((response) => {
        if (response.ok) {
          form.reset();
          form.style.display = 'none';
          successBox && successBox.classList.add('visible');
          if (typeof gtag === 'function') {
            gtag('event', form.dataset.gaEvent || 'generate_lead', {
              event_category: 'engagement',
              event_label: form.dataset.gaLabel || 'form',
            });
          }
        } else {
          throw new Error('Formspree rejected the submission');
        }
      })
      .catch(() => {
        errorBox && errorBox.classList.add('visible');
        if (submitBtn) submitBtn.disabled = false;
      });
  });
});

// Rotating hero text — skipped entirely under reduced motion.
const rotatingTerms = ['Wedding DJ', 'Event DJ', 'Corporate DJ', 'Party DJ'];
let termIndex = 0;
const rotatingEl = document.querySelector('.rotating-text');
const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
if (rotatingEl && !prefersReducedMotion) {
  setInterval(() => {
    rotatingEl.classList.add('fade');
    setTimeout(() => {
      termIndex = (termIndex + 1) % rotatingTerms.length;
      rotatingEl.textContent = rotatingTerms[termIndex];
      rotatingEl.classList.remove('fade');
    }, 500);
  }, 2800);
}
