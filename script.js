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

// Preselect the contact form's Event Type from a ?event_type= query param,
// so a link like /contact/?event_type=corporate lands with that option
// already chosen. Only sets it when the value is one of the form's own
// options, so an unrecognized param just leaves the default in place.
(() => {
  const eventType = new URLSearchParams(window.location.search).get('event_type');
  const select = document.getElementById('event-type');
  if (!eventType || !select) return;
  if ([...select.options].some((o) => o.value === eventType)) {
    select.value = eventType;
  }
})();

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

// Sticky mobile CTA: on the home page's full-bleed hero, stay hidden
// until the visitor scrolls past it, so landing shows only the hero's
// own two buttons instead of four competing for thumb space. Other
// pages (hero-light, much shorter) keep the bar visible immediately.
const tallHero = document.querySelector('.hero');
const stickyBar = document.querySelector('.sticky-mobile-cta');
if (tallHero && stickyBar) {
  document.body.classList.add('has-tall-hero');
  const toggleStickyBar = () => {
    stickyBar.classList.toggle('past-hero', window.scrollY > tallHero.offsetHeight - 80);
  };
  toggleStickyBar();
  window.addEventListener('scroll', toggleStickyBar, { passive: true });
}

// Autoplay-in-view, muted, looping videos (home service cards, About's
// Nosirrot reels): play only while scrolled into view, pause out of view,
// and under reduced motion never call play() at all — the video just
// shows its poster, same as every other reduced-motion fallback here.
const autoplayVideos = document.querySelectorAll('[data-autoplay-inview]');
if (autoplayVideos.length && !window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
  const autoplayObserver = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        entry.target.play().catch(() => {});
      } else {
        entry.target.pause();
      }
    });
  }, { threshold: 0.25 });
  autoplayVideos.forEach((v) => autoplayObserver.observe(v));
}

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
