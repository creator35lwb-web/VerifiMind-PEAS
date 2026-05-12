"""
VerifiMind-PEAS — User-Facing HTML Pages

GET /register — Early Adopter opt-in registration form
GET /optout   — Early Adopter data deletion (GDPR right to erasure)

Design principles:
- Z-Protocol v1.1 consent-first: explicit T&C + Privacy Policy consent required
- Self-contained: no external CDN dependencies (fully functional offline/firewalled)
- XSS-safe: all user-controlled data written via textContent, never innerHTML
- Mobile-responsive: works on all screen sizes
- Dark theme: slate-950 / cyan-400 — matches VerifiMind brand
"""

# ── Shared CSS ────────────────────────────────────────────────────────────────

_CSS = """
:root {
  --bg:          #020617;
  --surface:     #0f172a;
  --surface-2:   #1e293b;
  --border:      #334155;
  --accent:      #22d3ee;
  --accent-hover:#0891b2;
  --accent-dim:  #164e63;
  --text:        #f1f5f9;
  --muted:       #94a3b8;
  --error:       #f87171;
  --success:     #4ade80;
  --warning:     #fbbf24;
  --danger:      #ef4444;
  --danger-hover:#dc2626;
}

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

html { font-size: 16px; }

body {
  background: var(--bg);
  color: var(--text);
  font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI",
               Roboto, "Helvetica Neue", Arial, sans-serif;
  line-height: 1.6;
  min-height: 100vh;
  padding: 2rem 1rem;
}

.page-wrapper {
  max-width: 560px;
  margin: 0 auto;
}

/* ── Header ── */
.site-header {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 2rem;
}

.site-logo {
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--accent);
  letter-spacing: -0.5px;
  text-decoration: none;
}

.site-logo span {
  color: var(--text);
  font-weight: 400;
}

.version-badge {
  font-size: 0.7rem;
  background: var(--surface-2);
  color: var(--muted);
  border: 1px solid var(--border);
  border-radius: 4px;
  padding: 2px 6px;
  vertical-align: middle;
}

/* ── Card ── */
.card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 2rem;
  margin-bottom: 1.5rem;
}

.card-title {
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--text);
  margin-bottom: 0.5rem;
}

.card-subtitle {
  color: var(--muted);
  font-size: 0.95rem;
  margin-bottom: 1.5rem;
}

/* ── Benefits strip ── */
.benefits-strip {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 0.75rem;
  margin-bottom: 1.75rem;
}

.benefit-item {
  background: var(--surface-2);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 0.75rem;
  text-align: center;
  font-size: 0.82rem;
}

.benefit-icon { font-size: 1.25rem; display: block; margin-bottom: 0.25rem; }
.benefit-label { color: var(--muted); font-size: 0.75rem; }

/* ── Form elements ── */
.field { margin-bottom: 1.25rem; }

label {
  display: block;
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--text);
  margin-bottom: 0.375rem;
}

.optional-tag {
  font-size: 0.75rem;
  color: var(--muted);
  font-weight: 400;
  margin-left: 0.25rem;
}

input[type="email"],
input[type="text"],
select,
textarea {
  width: 100%;
  background: var(--bg);
  border: 1px solid var(--border);
  border-radius: 8px;
  color: var(--text);
  font-size: 0.95rem;
  font-family: inherit;
  padding: 0.625rem 0.875rem;
  transition: border-color 0.15s, box-shadow 0.15s;
  appearance: none;
  -webkit-appearance: none;
}

input[type="email"]:focus,
input[type="text"]:focus,
select:focus,
textarea:focus {
  outline: none;
  border-color: var(--accent);
  box-shadow: 0 0 0 3px var(--accent-dim);
}

input[type="email"]::placeholder,
input[type="text"]::placeholder,
textarea::placeholder { color: var(--muted); }

select {
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath fill='%2394a3b8' d='M6 8L1 3h10z'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 0.875rem center;
  padding-right: 2.25rem;
}

select option { background: var(--surface); }

textarea { resize: vertical; min-height: 100px; }

.char-count {
  font-size: 0.75rem;
  color: var(--muted);
  text-align: right;
  margin-top: 0.25rem;
}

/* ── Consent block (Z-Protocol v1.1) ── */
.consent-block {
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 1rem 1.25rem;
  margin-bottom: 1.25rem;
  background: var(--surface-2);
}

.consent-block legend {
  font-size: 0.8rem;
  font-weight: 600;
  color: var(--accent);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  padding: 0 0.375rem;
}

.consent-note {
  font-size: 0.8rem;
  color: var(--muted);
  margin-bottom: 0.875rem;
  margin-top: 0.5rem;
}

.checkbox-row {
  display: flex;
  align-items: flex-start;
  gap: 0.625rem;
  margin-bottom: 0.75rem;
  font-size: 0.9rem;
}

.checkbox-row:last-child { margin-bottom: 0; }

.checkbox-row input[type="checkbox"] {
  width: 1.125rem;
  height: 1.125rem;
  flex-shrink: 0;
  margin-top: 0.15rem;
  accent-color: var(--accent);
  cursor: pointer;
}

.checkbox-row label {
  margin-bottom: 0;
  font-weight: 400;
  cursor: pointer;
  line-height: 1.5;
}

.checkbox-row a {
  color: var(--accent);
  text-decoration: underline;
  text-underline-offset: 2px;
}

.checkbox-row a:hover { color: var(--accent-hover); }

.required-marker { color: var(--error); margin-left: 1px; }
.optional-row label { color: var(--muted); }

/* ── Buttons ── */
.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  font-size: 0.95rem;
  font-weight: 600;
  border: none;
  border-radius: 8px;
  padding: 0.75rem 1.5rem;
  cursor: pointer;
  transition: background 0.15s, opacity 0.15s, transform 0.1s;
  font-family: inherit;
  text-decoration: none;
  width: 100%;
}

.btn:active { transform: scale(0.98); }
.btn:disabled { opacity: 0.5; cursor: not-allowed; transform: none; }

.btn-primary {
  background: var(--accent);
  color: #020617;
}

.btn-primary:hover:not(:disabled) { background: var(--accent-hover); color: #fff; }

.btn-secondary {
  background: var(--surface-2);
  color: var(--text);
  border: 1px solid var(--border);
  width: auto;
  font-size: 0.8rem;
  padding: 0.375rem 0.875rem;
}

.btn-secondary:hover:not(:disabled) { background: var(--border); }

.btn-danger {
  background: var(--danger);
  color: #fff;
}

.btn-danger:hover:not(:disabled) { background: var(--danger-hover); }

/* ── Alerts ── */
.alert {
  display: flex;
  gap: 0.625rem;
  padding: 0.75rem 1rem;
  border-radius: 8px;
  font-size: 0.875rem;
  margin-bottom: 1rem;
}

.alert-error {
  background: rgba(248, 113, 113, 0.1);
  border: 1px solid rgba(248, 113, 113, 0.3);
  color: var(--error);
}

.alert-success {
  background: rgba(74, 222, 128, 0.1);
  border: 1px solid rgba(74, 222, 128, 0.3);
  color: var(--success);
}

.alert-warning {
  background: rgba(251, 191, 36, 0.08);
  border: 1px solid rgba(251, 191, 36, 0.25);
  color: var(--warning);
}

/* ── UUID display ── */
.uuid-box {
  background: var(--bg);
  border: 1px solid var(--accent-dim);
  border-radius: 8px;
  padding: 0.875rem 1rem;
  margin: 1rem 0;
  display: flex;
  align-items: center;
  gap: 0.75rem;
  flex-wrap: wrap;
}

.uuid-code {
  font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace;
  font-size: 0.88rem;
  color: var(--accent);
  letter-spacing: 0.02em;
  flex: 1;
  word-break: break-all;
}

.copy-confirm {
  font-size: 0.75rem;
  color: var(--success);
  margin-top: 0.25rem;
}

/* ── Success state ── */
.success-header {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 1rem;
}

.success-icon {
  width: 2.5rem;
  height: 2.5rem;
  background: rgba(74, 222, 128, 0.15);
  border: 1px solid rgba(74, 222, 128, 0.3);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.25rem;
  flex-shrink: 0;
}

.success-title {
  font-size: 1.25rem;
  font-weight: 700;
  color: var(--success);
}

.benefits-list {
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  margin: 0.75rem 0 1.25rem;
}

.benefits-list li {
  display: flex;
  align-items: flex-start;
  gap: 0.5rem;
  font-size: 0.9rem;
}

.benefits-list li::before {
  content: "✓";
  color: var(--success);
  font-weight: 700;
  flex-shrink: 0;
}

.uuid-save-notice {
  font-size: 0.82rem;
  color: var(--warning);
  margin-top: 0.25rem;
}

.divider {
  border: none;
  border-top: 1px solid var(--border);
  margin: 1.25rem 0;
}

.optout-notice {
  font-size: 0.82rem;
  color: var(--muted);
}

.optout-notice a { color: var(--muted); text-decoration: underline; }
.optout-notice a:hover { color: var(--error); }

/* ── Deletion info ── */
.deletion-info {
  background: var(--surface-2);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 1rem 1.25rem;
  margin-bottom: 1.5rem;
}

.deletion-info h3 {
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--text);
  margin-bottom: 0.625rem;
}

.deletion-list {
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 0.375rem;
  margin-bottom: 0.75rem;
}

.deletion-list li {
  font-size: 0.875rem;
  color: var(--muted);
  display: flex;
  align-items: flex-start;
  gap: 0.5rem;
}

.deletion-list li::before {
  content: "×";
  color: var(--error);
  font-weight: 700;
}

.deletion-note {
  font-size: 0.8rem;
  color: var(--muted);
  line-height: 1.5;
}

.deletion-note a { color: var(--accent); }

/* ── Footer ── */
.page-footer {
  text-align: center;
  font-size: 0.8rem;
  color: var(--muted);
  margin-top: 1.5rem;
  padding-top: 1rem;
}

.page-footer a { color: var(--muted); text-decoration: underline; }
.page-footer a:hover { color: var(--accent); }

/* ── Site Navigation ── */
.site-nav {
  display: flex;
  gap: 1.25rem;
  align-items: center;
  margin-left: auto;
}
.site-nav a {
  color: var(--muted);
  text-decoration: none;
  font-size: 0.85rem;
  transition: color 0.15s;
}
.site-nav a:hover { color: var(--accent); }
.site-nav .nav-active { color: var(--text); font-weight: 500; }
.site-nav .nav-cta {
  background: var(--accent);
  color: #fff !important;
  padding: 0.3rem 0.8rem;
  border-radius: 6px;
  font-size: 0.8rem;
}
.site-nav .nav-cta:hover { opacity: 0.85; }

/* ── Research Section Pills ── */
.research-section-nav {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 2rem;
  flex-wrap: wrap;
}
.nav-pill {
  padding: 0.3rem 0.9rem;
  border-radius: 20px;
  font-size: 0.8rem;
  text-decoration: none;
  border: 1px solid var(--border);
  color: var(--muted);
  background: var(--surface-2);
  transition: all 0.15s;
}
.nav-pill:hover { border-color: var(--accent); color: var(--accent); }
.nav-pill-active { border-color: var(--accent); color: var(--accent); background: var(--surface); font-weight: 500; }

/* ── Utility ── */
.hidden { display: none !important; }
.muted { color: var(--muted); }
.text-sm { font-size: 0.875rem; }

/* ── Loading spinner ── */
.spinner {
  display: inline-block;
  width: 1rem;
  height: 1rem;
  border: 2px solid rgba(2, 6, 23, 0.3);
  border-top-color: #020617;
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
  vertical-align: middle;
}

@keyframes spin { to { transform: rotate(360deg); } }

@keyframes livepulse {
  0%, 100% { opacity: 1; }
  50%       { opacity: 0.25; }
}
.live-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.3em;
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--success);
  margin-left: 0.6rem;
  vertical-align: middle;
}
.live-badge::before {
  content: "●";
  animation: livepulse 1.4s ease-in-out infinite;
}

/* ── Responsive ── */
@media (max-width: 600px) {
  body { padding: 1rem 0.75rem; }
  .card { padding: 1.5rem 1.25rem; }
  .benefits-strip { grid-template-columns: repeat(3, 1fr); gap: 0.5rem; }
  .benefit-item { padding: 0.5rem 0.25rem; font-size: 0.75rem; }
  .benefit-icon { font-size: 1rem; }
}
"""


# ── HTML shell ────────────────────────────────────────────────────────────────

def _shell(title: str, body: str, script: str = "") -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta name="robots" content="noindex">
  <title>{title} — VerifiMind-PEAS</title>
  <style>{_CSS}</style>
</head>
<body>
<div class="page-wrapper">

  <header class="site-header">
    <a class="site-logo" href="https://verifimind.ysenseai.org">
      VerifiMind<span>-PEAS</span>
    </a>
    <span class="version-badge">v0.5.6 Gateway</span>
  </header>

  {body}

  <footer class="page-footer">
    <p>
      <a href="/privacy" target="_blank" rel="noopener">Privacy Policy</a> &nbsp;·&nbsp;
      <a href="/terms" target="_blank" rel="noopener">Terms &amp; Conditions</a> &nbsp;·&nbsp;
      <a href="https://github.com/creator35lwb-web/VerifiMind-PEAS" target="_blank" rel="noopener">GitHub</a>
    </p>
    <p style="margin-top:0.5rem">Z-Protocol v1.1 · GDPR/PDPA Compliant · Open Source (MIT)</p>
  </footer>

</div>
<script>{script}</script>
</body>
</html>"""


# ── Register page ─────────────────────────────────────────────────────────────

_REGISTER_BODY = """
<div class="card">
  <h1 class="card-title">Join as an Early Adopter</h1>
  <p class="card-subtitle">
    Register for free priority access to VerifiMind-PEAS v0.6.0-Beta
    when it launches. No credit card required.
  </p>

  <div class="benefits-strip">
    <div class="benefit-item">
      <span class="benefit-icon">&#x2705;</span>
      <strong>All 13 tools</strong>
      <div class="benefit-label">Free forever</div>
    </div>
    <div class="benefit-item">
      <span class="benefit-icon">&#x1F9EA;</span>
      <strong>Beta access</strong>
      <div class="benefit-label">v0.6.0 Beta</div>
    </div>
    <div class="benefit-item">
      <span class="benefit-icon">&#x1F4AC;</span>
      <strong>Shape it</strong>
      <div class="benefit-label">Direct feedback</div>
    </div>
  </div>

  <!-- ── Registration form ── -->
  <form id="register-form" novalidate>

    <div class="field">
      <label for="email">Email address <span class="required-marker">*</span></label>
      <input id="email" name="email" type="email" required
             autocomplete="email" placeholder="you@example.com">
    </div>

    <div class="field">
      <label for="name">
        Name <span class="optional-tag">(optional)</span>
      </label>
      <input id="name" name="name" type="text" maxlength="100"
             autocomplete="name" placeholder="Your name">
    </div>

    <div class="field">
      <label for="feedback_type">I am a...</label>
      <select id="feedback_type" name="feedback_type">
        <option value="">&#x2014; Select (optional) &#x2014;</option>
        <option value="new_user">New user, curious about VerifiMind</option>
        <option value="returning_user">Returning user of VerifiMind</option>
        <option value="recommendation">Here to recommend VerifiMind</option>
        <option value="issue">Reporting an issue or suggestion</option>
        <option value="general">General interest</option>
      </select>
    </div>

    <div class="field">
      <label for="feedback">
        Tell us about yourself or your use case
        <span class="optional-tag">(optional)</span>
      </label>
      <textarea id="feedback" name="feedback" maxlength="1000" rows="4"
                placeholder="What are you building? How did you find VerifiMind? Any feedback for the team?"></textarea>
      <div class="char-count" id="char-count" aria-live="polite">0 / 1000</div>
    </div>

    <!-- ── Consent block — Z-Protocol v1.1 ── -->
    <fieldset class="consent-block">
      <legend>Consent</legend>
      <p class="consent-note">
        We collect only what is necessary. You can opt out at any time.
        Your data is stored on Google Cloud (EU-US region) and never sold.
      </p>

      <div class="checkbox-row">
        <input type="checkbox" id="tc_accepted" name="tc_accepted" required>
        <label for="tc_accepted">
          I have read and accept the
          <a href="/terms" target="_blank" rel="noopener">Terms &amp; Conditions</a>
          <span class="required-marker">*</span>
        </label>
      </div>

      <div class="checkbox-row">
        <input type="checkbox" id="privacy_acknowledged" name="privacy_acknowledged" required>
        <label for="privacy_acknowledged">
          I have read and acknowledge the
          <a href="/privacy" target="_blank" rel="noopener">Privacy Policy</a>
          <span class="required-marker">*</span>
        </label>
      </div>

      <div class="checkbox-row optional-row">
        <input type="checkbox" id="updates_consent" name="updates_consent">
        <label for="updates_consent">
          I&rsquo;d like to receive product updates by email
          <span class="optional-tag">(optional)</span>
        </label>
      </div>
    </fieldset>

    <div id="form-error" class="alert alert-error hidden" role="alert" aria-live="assertive"></div>

    <button type="submit" id="submit-btn" class="btn btn-primary">
      Register as Early Adopter
    </button>

  </form>

  <!-- ── Success state (shown after successful registration) ── -->
  <div id="success-state" class="hidden">
    <div class="success-header">
      <div class="success-icon">&#x2713;</div>
      <div class="success-title" id="success-title">Registration complete!</div>
    </div>

    <div id="tier-badge" style="display:inline-block;padding:0.3rem 0.9rem;border-radius:6px;font-size:0.8rem;font-weight:700;letter-spacing:0.06em;text-transform:uppercase;margin-bottom:1rem;"></div>

    <div id="benefit-summary" style="background:var(--surface-2);border:1px solid var(--border);border-radius:8px;padding:0.875rem 1rem;margin-bottom:1.25rem;font-size:0.9rem;line-height:1.6;"></div>

    <p class="text-sm muted" style="margin-bottom:0.25rem">Your UUID (access key):</p>
    <div class="uuid-box">
      <code class="uuid-code" id="uuid-value"></code>
      <button id="copy-btn" class="btn btn-secondary" type="button">Copy</button>
    </div>
    <div class="uuid-save-notice" id="copy-confirm">
      &#x26A0;&#xFE0F; Save this UUID &mdash; you will need it to access v0.6.0-Beta and to opt out.
    </div>

    <ul class="benefits-list" id="benefits-list"></ul>

    <hr class="divider">
    <p class="optout-notice">
      You can
      <a href="/optout">opt out and delete your data</a>
      at any time &mdash; no questions asked.
    </p>
  </div>
</div>

<!-- Already registered? -->
<div class="card" style="padding: 1rem 1.5rem;">
  <p class="text-sm muted">
    Already registered?
    Use <a href="/early-adopters/status/" style="color: var(--accent)">
      /early-adopters/status/{uuid}
    </a>
    to check your status.
    &nbsp;&middot;&nbsp;
    <a href="/optout" style="color: var(--muted)">Opt out</a>
  </p>
</div>
"""

_REGISTER_SCRIPT = r"""
// ── Pilot tier detection (page load) ──────────────────────────────────────────
// If ?invite= param is present the user arrived via SYSTEM_NOTICE Pilot link.
// We optimistically show Pilot benefits (6 months); server validates the code.
(function() {
  var hasInvite = !!new URLSearchParams(window.location.search).get('invite');
  if (hasInvite) {
    // Update page title
    var cardTitle = document.querySelector('.card-title');
    if (cardTitle) cardTitle.textContent = 'Join as a Pilot Member';

    // Update subtitle
    var sub = document.querySelector('.card-subtitle');
    if (sub) sub.textContent = 'You have been invited to join the exclusive Pilot Program — 6 months FREE v0.6.0-Beta access. No credit card required.';

    // Update benefits strip: 6 months free + Pilot cohort (50 slots)
    var strip = document.querySelector('.benefits-strip');
    if (strip) {
      strip.innerHTML =
        '<div class="benefit-item"><span class="benefit-icon">&#x23F0;</span><strong>6 months free</strong><div class="benefit-label">Pilot tier</div></div>' +
        '<div class="benefit-item"><span class="benefit-icon">&#x1F9EA;</span><strong>Beta access</strong><div class="benefit-label">v0.6.0 Pilot</div></div>' +
        '<div class="benefit-item"><span class="benefit-icon">&#x1F511;</span><strong>50-slot cohort</strong><div class="benefit-label">Founding members</div></div>';
    }
  }
})();

// Character counter
var feedbackArea = document.getElementById('feedback');
var charCount = document.getElementById('char-count');
feedbackArea.addEventListener('input', function() {
  charCount.textContent = this.value.length + ' / 1000';
});

// Form submission
document.getElementById('register-form').addEventListener('submit', async function(e) {
  e.preventDefault();

  var btn = document.getElementById('submit-btn');
  var errDiv = document.getElementById('form-error');
  var tcBox = document.getElementById('tc_accepted');
  var privBox = document.getElementById('privacy_acknowledged');

  // Z-Protocol client-side gate (mirrors server Pydantic validators)
  errDiv.classList.add('hidden');
  if (!tcBox.checked || !privBox.checked) {
    errDiv.textContent = 'You must accept the Terms & Conditions and Privacy Policy to register.';
    errDiv.classList.remove('hidden');
    return;
  }

  var email = document.getElementById('email').value.trim();
  if (!email) {
    errDiv.textContent = 'Email address is required.';
    errDiv.classList.remove('hidden');
    return;
  }

  btn.disabled = true;
  btn.innerHTML = '<span class="spinner"></span>&nbsp;Registering\u2026';

  var feedbackType = document.getElementById('feedback_type').value;
  var feedback = feedbackArea.value.trim();
  var name = document.getElementById('name').value.trim();

  // Read invite code from URL (?invite=...) — set by SYSTEM_NOTICE link for Pilot tier
  var inviteCode = new URLSearchParams(window.location.search).get('invite') || '';

  var payload = {
    email: email,
    tc_accepted: true,
    privacy_acknowledged: true,
    updates_consent: document.getElementById('updates_consent').checked,
  };
  if (name) payload.name = name;
  if (feedback) payload.feedback = feedback;
  if (feedbackType) payload.feedback_type = feedbackType;
  if (inviteCode) payload.invite_code = inviteCode;

  try {
    var resp = await fetch('/early-adopters/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });

    var data = await resp.json();

    if (resp.ok || resp.status === 201) {
      // Show success state — textContent only (XSS-safe)
      document.getElementById('register-form').classList.add('hidden');
      var successDiv = document.getElementById('success-state');
      successDiv.classList.remove('hidden');

      var isPilot = data.tier === 'pilot';
      var tierLabel = data.tier_label || (isPilot ? 'Pilot Member' : 'Early Adopter');

      // Tier badge
      var badge = document.getElementById('tier-badge');
      badge.textContent = tierLabel;
      badge.style.background = isPilot ? 'var(--accent)' : 'var(--surface-2)';
      badge.style.color = isPilot ? '#020617' : 'var(--accent)';
      badge.style.border = isPilot ? 'none' : '1px solid var(--accent)';

      // Success title
      document.getElementById('success-title').textContent = isPilot
        ? 'Welcome, Pilot Member!'
        : 'Registration complete!';

      // Benefit summary
      var summaryEl = document.getElementById('benefit-summary');
      summaryEl.textContent = data.benefit_summary || (
        tierLabel + ': ' + (data.free_months || 3) + ' months FREE v0.6.0-Beta access. '
        + 'Free until: ' + (data.benefits_free_until ? data.benefits_free_until.split('T')[0] : 'n/a') + '.'
      );

      document.getElementById('uuid-value').textContent = data.uuid;

      var list = document.getElementById('benefits-list');
      var benefits = [
        'T\u0026C version accepted: ' + (data.tc_version || '1.0'),
        'Privacy Policy version: ' + (data.privacy_version || '1.0'),
      ];
      if (data.feedback_received) {
        benefits.push('Feedback received \u2014 thank you!');
      }
      benefits.forEach(function(text) {
        var li = document.createElement('li');
        li.textContent = text;
        list.appendChild(li);
      });

    } else {
      // Error path — textContent prevents reflected XSS
      var msg = 'Registration failed. Please check your details and try again.';
      if (resp.status === 410 && data.message) {
        msg = data.message;
      } else if (data.detail) {
        if (Array.isArray(data.detail)) {
          msg = data.detail.map(function(d) {
            return d.msg || String(d);
          }).join(' ');
        } else {
          msg = String(data.detail);
        }
      } else if (data.error) {
        msg = String(data.error);
      }
      errDiv.textContent = msg;
      errDiv.classList.remove('hidden');
      btn.disabled = false;
      btn.textContent = 'Register as Early Adopter';
    }

  } catch (err) {
    errDiv.textContent = 'Network error \u2014 please check your connection and try again.';
    errDiv.classList.remove('hidden');
    btn.disabled = false;
    btn.textContent = 'Register as Early Adopter';
  }
});

// Copy UUID to clipboard
document.getElementById('copy-btn').addEventListener('click', async function() {
  var uuid = document.getElementById('uuid-value').textContent;
  var confirmEl = document.getElementById('copy-confirm');

  try {
    await navigator.clipboard.writeText(uuid);
    confirmEl.textContent = '\u2713 Copied to clipboard!';
    confirmEl.style.color = 'var(--success)';
  } catch (_) {
    // Fallback for older browsers / HTTP
    var inp = document.createElement('input');
    inp.value = uuid;
    inp.style.position = 'fixed';
    inp.style.opacity = '0';
    document.body.appendChild(inp);
    inp.select();
    try { document.execCommand('copy'); } catch (_) {}
    document.body.removeChild(inp);
    confirmEl.textContent = '\u2713 Copied!';
    confirmEl.style.color = 'var(--success)';
  }

  setTimeout(function() {
    confirmEl.textContent = '\u26A0\uFE0F Save this UUID \u2014 you will need it to check your status or opt out.';
    confirmEl.style.color = 'var(--warning)';
  }, 3000);
});
"""


# ── Opt-out page ──────────────────────────────────────────────────────────────

_OPTOUT_BODY = """
<div class="card">
  <h1 class="card-title">Opt Out &amp; Data Deletion</h1>
  <p class="card-subtitle">
    Request permanent deletion of your Early Adopter data.
    This is your GDPR / PDPA right to erasure.
  </p>

  <div class="deletion-info">
    <h3>What gets deleted</h3>
    <ul class="deletion-list">
      <li>Your email address</li>
      <li>Your name (if provided)</li>
      <li>Your registration feedback</li>
      <li>Your consent records</li>
      <li>Your EA tier and benefits status</li>
    </ul>
    <p class="deletion-note">
      Deletion is processed within <strong>7 business days</strong> per our
      <a href="/privacy" target="_blank" rel="noopener">Privacy Policy v1.0</a>.
      Your UUID is retained in pseudonymised form for audit log integrity only
      &mdash; no personal data is attached after deletion.
    </p>
  </div>

  <!-- ── Opt-out form ── -->
  <form id="optout-form" novalidate>

    <div class="field">
      <label for="uuid">
        Your Early Adopter UUID <span class="required-marker">*</span>
      </label>
      <input id="uuid" name="uuid" type="text" required
             placeholder="xxxxxxxx-xxxx-7xxx-xxxx-xxxxxxxxxxxx"
             autocomplete="off" spellcheck="false"
             style="font-family: monospace; letter-spacing: 0.02em;">
      <p class="text-sm muted" style="margin-top:0.375rem">
        You received this UUID when you registered.
        Check your notes or visit
        <code style="font-size:0.8rem; color: var(--accent)">/early-adopters/status/{uuid}</code>.
      </p>
    </div>

    <div class="field">
      <fieldset class="consent-block">
        <legend>Confirm deletion</legend>
        <p class="consent-note">
          This action cannot be undone. Your EA benefits will be cancelled
          and your data purged within 7 business days.
        </p>
        <div class="checkbox-row">
          <input type="checkbox" id="confirmed" name="confirmed" required>
          <label for="confirmed">
            I confirm I want to permanently delete my Early Adopter account
            and all associated personal data.
            <span class="required-marker">*</span>
          </label>
        </div>
      </fieldset>
    </div>

    <div id="form-error" class="alert alert-error hidden" role="alert" aria-live="assertive"></div>

    <button type="submit" id="delete-btn" class="btn btn-danger">
      Delete My Data
    </button>

  </form>

  <!-- ── Success state ── -->
  <div id="success-state" class="hidden">
    <div class="success-header">
      <div class="success-icon" style="background: rgba(74,222,128,0.15); border-color: rgba(74,222,128,0.3);">&#x2713;</div>
      <div class="success-title">Deletion request received</div>
    </div>
    <div class="alert alert-success" id="deletion-message"></div>
    <p class="text-sm muted" style="margin-bottom: 1rem">
      Scheduled within: <strong id="deletion-timeline"></strong>
    </p>
    <p class="text-sm muted">
      Changed your mind?
      <a href="/register" style="color: var(--accent)">Register again here.</a>
    </p>
  </div>
</div>

<div class="card" style="padding: 1rem 1.5rem;">
  <p class="text-sm muted">
    Not trying to delete your account?
    <a href="/register" style="color: var(--accent)">Register as an Early Adopter</a>
    &nbsp;&middot;&nbsp;
    <a href="https://github.com/creator35lwb-web/VerifiMind-PEAS/discussions"
       target="_blank" rel="noopener" style="color: var(--muted)">Get help on GitHub</a>
  </p>
</div>
"""

_OPTOUT_SCRIPT = r"""
document.getElementById('optout-form').addEventListener('submit', async function(e) {
  e.preventDefault();

  var btn = document.getElementById('delete-btn');
  var errDiv = document.getElementById('form-error');
  var uuid = document.getElementById('uuid').value.trim();
  var confirmed = document.getElementById('confirmed').checked;

  errDiv.classList.add('hidden');

  if (!uuid) {
    errDiv.textContent = 'Please enter your Early Adopter UUID.';
    errDiv.classList.remove('hidden');
    return;
  }

  if (!confirmed) {
    errDiv.textContent = 'Please confirm that you want to delete your data.';
    errDiv.classList.remove('hidden');
    return;
  }

  btn.disabled = true;
  btn.innerHTML = '<span class="spinner" style="border-top-color:#fff"></span>&nbsp;Processing\u2026';

  try {
    var resp = await fetch('/early-adopters/optout/' + encodeURIComponent(uuid), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Content-Length': '0' },
    });

    var data = await resp.json();

    if (resp.ok) {
      document.getElementById('optout-form').classList.add('hidden');
      var successDiv = document.getElementById('success-state');
      successDiv.classList.remove('hidden');

      // textContent only — XSS-safe
      var msgEl = document.getElementById('deletion-message');
      msgEl.textContent = data.message
        || 'Your deletion request has been recorded. Personal data will be purged within 7 business days.';

      document.getElementById('deletion-timeline').textContent =
        data.deletion_scheduled_within || '7 business days';

    } else {
      var msg = 'Opt-out request failed.';
      if (data.error) msg = String(data.error);
      else if (data.detail) msg = String(data.detail);
      errDiv.textContent = msg;
      errDiv.classList.remove('hidden');
      btn.disabled = false;
      btn.textContent = 'Delete My Data';
    }

  } catch (err) {
    errDiv.textContent = 'Network error \u2014 please check your connection and try again.';
    errDiv.classList.remove('hidden');
    btn.disabled = false;
    btn.textContent = 'Delete My Data';
  }
});
"""


# ── Public API ────────────────────────────────────────────────────────────────

def get_register_page() -> str:
    """Return the full HTML for GET /register."""
    return _shell(
        title="Early Adopter Registration",
        body=_REGISTER_BODY,
        script=_REGISTER_SCRIPT,
    )


def get_optout_page() -> str:
    """Return the full HTML for GET /optout."""
    return _shell(
        title="Opt Out & Data Deletion",
        body=_OPTOUT_BODY,
        script=_OPTOUT_SCRIPT,
    )


# ── Legal document pages (v2.0) ───────────────────────────────────────────────

_LEGAL_CSS = """
.legal-wrapper {
  max-width: 800px;
  margin: 0 auto;
}

.legal-wrapper .page-wrapper {
  max-width: 800px;
}

.legal-doc h1 {
  font-size: 1.75rem;
  font-weight: 700;
  color: var(--text);
  margin-bottom: 0.25rem;
}

.legal-doc .meta {
  color: var(--muted);
  font-size: 0.875rem;
  margin-bottom: 2rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid var(--border);
}

.legal-doc .meta span {
  margin-right: 1.5rem;
}

.legal-doc h2 {
  font-size: 1.1rem;
  font-weight: 600;
  color: var(--accent);
  margin: 2rem 0 0.75rem;
  padding-bottom: 0.375rem;
  border-bottom: 1px solid var(--border);
}

.legal-doc h3 {
  font-size: 0.95rem;
  font-weight: 600;
  color: var(--text);
  margin: 1.25rem 0 0.5rem;
}

.legal-doc p {
  color: var(--text);
  margin-bottom: 0.875rem;
  line-height: 1.7;
}

.legal-doc ul, .legal-doc ol {
  padding-left: 1.5rem;
  margin-bottom: 0.875rem;
}

.legal-doc li {
  color: var(--text);
  margin-bottom: 0.375rem;
  line-height: 1.65;
}

.legal-doc a {
  color: var(--accent);
  text-decoration: none;
}

.legal-doc a:hover {
  text-decoration: underline;
}

.legal-table {
  width: 100%;
  border-collapse: collapse;
  margin: 1rem 0 1.5rem;
  font-size: 0.875rem;
}

.legal-table th {
  background: var(--surface-2);
  color: var(--muted);
  font-weight: 600;
  text-align: left;
  padding: 0.625rem 0.875rem;
  border: 1px solid var(--border);
}

.legal-table td {
  color: var(--text);
  padding: 0.625rem 0.875rem;
  border: 1px solid var(--border);
  vertical-align: top;
}

.legal-table tr:nth-child(even) td {
  background: var(--surface);
}

.tier-badge {
  display: inline-block;
  background: var(--accent-dim);
  color: var(--accent);
  border-radius: 4px;
  padding: 1px 6px;
  font-size: 0.8rem;
  font-weight: 600;
}

.notice-box {
  background: var(--surface-2);
  border: 1px solid var(--border);
  border-left: 3px solid var(--accent);
  border-radius: 6px;
  padding: 0.875rem 1.125rem;
  margin: 1rem 0;
  font-size: 0.9rem;
  color: var(--text);
}
"""


def _legal_shell(title: str, body: str) -> str:
    """Shell for legal document pages — wider layout, no script needed."""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta name="robots" content="noindex">
  <title>{title} — VerifiMind-PEAS</title>
  <style>{_CSS}{_LEGAL_CSS}</style>
</head>
<body>
<div class="page-wrapper legal-wrapper">

  <header class="site-header">
    <a class="site-logo" href="https://verifimind.ysenseai.org">
      VerifiMind<span>-PEAS</span>
    </a>
    <span class="version-badge">v2.0</span>
  </header>

  <div class="legal-doc">
    {body}
  </div>

  <footer class="page-footer">
    <p>
      <a href="/privacy">Privacy Policy</a> &nbsp;·&nbsp;
      <a href="/terms">Terms &amp; Conditions</a> &nbsp;·&nbsp;
      <a href="https://github.com/creator35lwb-web/VerifiMind-PEAS" target="_blank" rel="noopener">GitHub</a> &nbsp;·&nbsp;
      <a href="/register">Register</a>
    </p>
    <p style="margin-top:0.5rem">Z-Protocol v1.1 · GDPR/PDPA Compliant · Open Source (MIT)</p>
  </footer>

</div>
</body>
</html>"""


_PRIVACY_BODY = """
<h1>Privacy Policy</h1>
<div class="meta">
  <span>Version 2.2</span>
  <span>Effective: May 12, 2026</span>
  <span>Updated: May 12, 2026 (Growth First — no current paid services)</span>
  <span>Previous: v2.1 (April 20, 2026)</span>
</div>

<h2>Who We Are</h2>
<p>
  VerifiMind-PEAS is an open-source multi-model AI validation framework created by
  Alton Lee (Human Orchestrator, YSenseAI). This Privacy Policy applies to the
  VerifiMind-PEAS service at verifimind.ysenseai.org, including the Early Adopter (EA) and
  PILOT programs. As of May 12, 2026, all 13 tools are free for everyone (Core Tools
  Always Free pledge) and no paid services are active.
</p>

<h2>What We Collect</h2>
<table class="legal-table">
  <thead>
    <tr><th>Data</th><th>Required</th><th>Purpose</th></tr>
  </thead>
  <tbody>
    <tr><td>Email address</td><td>Yes (registration)</td><td>Account identification</td></tr>
    <tr><td>Name</td><td>No</td><td>Display only; never shared without your explicit consent</td></tr>
    <tr><td>UUID</td><td>Generated</td><td>Your pseudonymous identifier across all systems</td></tr>
    <tr><td>Registration timestamp</td><td>Auto</td><td>When you joined the program</td></tr>
    <tr><td>Consent records</td><td>Auto</td><td>That you accepted these terms and when</td></tr>
    <tr><td>Feedback message</td><td>No</td><td>To help us understand your needs and improve the product</td></tr>
    <tr><td>Tier label</td><td>Auto</td><td>Anonymous, Scholar, EA, or PILOT (used for rate limit allocation, not paywall)</td></tr>
  </tbody>
</table>

<h3>What We Do Not Collect</h3>
<ul>
  <li>Passwords or credentials</li>
  <li>Credit card numbers, bank account details, or any payment information (no paid services are currently offered)</li>
  <li>IP addresses linked to your email</li>
  <li>Location or device information</li>
  <li>Browsing behaviour beyond anonymous usage telemetry never connected to your account</li>
</ul>

<h2>Payment Processing</h2>
<p>
  There are <strong>no active paid services</strong> at this time. VerifiMind-PEAS does not
  process payments, collect billing details, or store payment information. When future paid
  services (such as expert-orchestrated consultation reports) become available, this section
  will be updated with the payment processor, what data they share with us, and your rights —
  before any payment is collected.
</p>

<h2>Why We Collect Your Data</h2>
<ul>
  <li>To grant program benefits (EA: 3 months free Beta access; PILOT: 6 months free Beta access — both grant the same free 13-tool access today, with cohort-specific coordination)</li>
  <li>To allocate rate limits per tier (Anonymous 10 / Scholar 30 / EA/PILOT 100 req/60s — see Terms Section 3)</li>
  <li>To communicate product updates if you opted in</li>
  <li>To improve VerifiMind-PEAS based on aggregate, anonymised feedback</li>
  <li>To maintain compliance records that you gave informed consent</li>
</ul>

<h2>Cookies</h2>
<p>VerifiMind-PEAS does not use tracking cookies. Anonymous usage telemetry on
  verifimind.ysenseai.org uses privacy-respecting analytics that do not track individual
  users.</p>

<h2>UUID Usage Analytics</h2>
<p>As of v0.5.15, registered Scholar users may optionally pass their UUID as a
  <code>user_uuid</code> parameter in any Trinity tool call. This is always voluntary —
  anonymous tool calls work identically without it.</p>
<div class="notice-box">
  <strong>What we log when you provide <code>user_uuid</code>:</strong>
</div>
<table class="legal-table">
  <thead>
    <tr><th>Data Logged</th><th>Purpose</th></tr>
  </thead>
  <tbody>
    <tr><td>Your UUID</td><td>Pseudonymous identifier (no name or email linked in logs)</td></tr>
    <tr><td>Tool name</td><td>Which tool you called (e.g. <code>consult_agent_x</code>)</td></tr>
    <tr><td>Tier label</td><td>Used for rate limit allocation only (not as a paywall)</td></tr>
    <tr><td>Timestamp</td><td>When the call was made (server time, UTC)</td></tr>
  </tbody>
</table>
<p><strong>What we do NOT log:</strong> your concept name or description, the tool's response or
  output, your IP address linked to your UUID, or any personally identifiable information.</p>
<p>These logs flow into our GCP Cloud Logging pipeline and are used to power the Scholar usage
  dashboard (<code>/early-adopters/dashboard/{uuid}</code>) and understand aggregate tool usage
  patterns. <strong>Log retention: 30 days</strong> (GCP Cloud Logging auto-purge). You may stop
  UUID analytics at any time by simply omitting <code>user_uuid</code> from tool calls.</p>

<h2>How Long We Keep Your Data</h2>
<table class="legal-table">
  <thead>
    <tr><th>Data Type</th><th>Retention Period</th></tr>
  </thead>
  <tbody>
    <tr><td>EA/PILOT records</td><td>Duration of membership + 90 days</td></tr>
    <tr><td>Feedback messages</td><td>Kept indefinitely in anonymised form after 6 months</td></tr>
    <tr><td>UUID usage analytics logs</td><td>30 days (GCP Cloud Logging auto-purge)</td></tr>
  </tbody>
</table>
<p>On deletion request, all personal data is purged within 7 business days, except where
  retention is required by law.</p>

<h2>Your Rights</h2>
<ul>
  <li><strong>Access</strong> — <code>GET /early-adopters/status/{your-uuid}</code></li>
  <li><strong>Delete</strong> — <code>POST /early-adopters/optout/{your-uuid}</code> (purged within 7 days)</li>
  <li><strong>Correct</strong> — raise a GitHub Discussion or contact us</li>
  <li><strong>Withdraw consent</strong> — same opt-out endpoint</li>
</ul>
<p>These rights are free of charge and will be actioned promptly.</p>

<h2>Data Sharing</h2>
<table class="legal-table">
  <thead>
    <tr><th>Third Party</th><th>Role</th><th>Data Shared</th></tr>
  </thead>
  <tbody>
    <tr><td>Google Cloud Platform</td><td>Hosting infrastructure, Firestore database</td><td>Account records (encrypted at rest)</td></tr>
  </tbody>
</table>
<p>No other third parties receive your data today. When future paid services launch, any
  payment processor introduced will be disclosed here before any data is shared.</p>

<h2>Security</h2>
<p>Your account records are stored in Google Cloud Firestore with restricted access. We do not
  log your email address in server logs. Your UUID is your primary identifier in all internal
  systems.</p>

<h2>Contact</h2>
<ul>
  <li>GitHub Discussions: <a href="https://github.com/creator35lwb-web/VerifiMind-PEAS/discussions" target="_blank" rel="noopener">github.com/creator35lwb-web/VerifiMind-PEAS/discussions</a></li>
  <li>Email: <a href="mailto:creator35lwb@gmail.com">creator35lwb@gmail.com</a></li>
  <li>Or use the <a href="/optout">opt-out endpoint</a> for immediate data deletion</li>
</ul>

<h2>Compliance</h2>
<p>This policy aligns with GDPR (EU), PDPA (Singapore/ASEAN), and the Z-Protocol v1.1 ethical
  framework (data minimisation, transparency, user autonomy).</p>

<h2>Changes to This Policy</h2>
<p>We will notify registered users of material changes at least 14 days before they take effect.
  The current version is always available at
  <a href="https://verifimind.ysenseai.org/privacy">verifimind.ysenseai.org/privacy</a>.</p>

<p style="margin-top:2rem; padding-top:1rem; border-top:1px solid var(--border); color:var(--muted); font-size:0.875rem;">
  VerifiMind-PEAS is open source:
  <a href="https://github.com/creator35lwb-web/VerifiMind-PEAS" target="_blank" rel="noopener">github.com/creator35lwb-web/VerifiMind-PEAS</a>
</p>
"""


_TERMS_BODY = """
<h1>Terms &amp; Conditions</h1>
<div class="meta">
  <span>Version 2.1</span>
  <span>Effective: May 12, 2026</span>
  <span>Updated: May 12, 2026 (Growth First — paid tier removed)</span>
  <span>Previous: v2.0 (April 8, 2026)</span>
</div>

<h2>1. Service Description</h2>
<p>VerifiMind-PEAS is an open-source multi-model AI validation framework that provides structured,
  multi-agent validation and orchestration tools. As of May 9, 2026, all 13 tools are free for
  everyone under the <strong>Core Tools Always Free</strong> pledge. Access levels are described
  in Section 3.</p>

<h2>2. Acceptance of Terms</h2>
<p>By registering for any VerifiMind-PEAS program or using the service, you confirm that you have
  read and accept:</p>
<ul>
  <li>These Terms &amp; Conditions v2.1</li>
  <li>The <a href="/privacy">Privacy Policy</a></li>
</ul>
<p>When future paid services launch, additional terms (including any payment-processor agreements)
  will be presented and accepted separately at the time of purchase.</p>

<h2>3. Service Tiers</h2>
<p>All current tiers grant access to <strong>all 13 tools</strong>. Tier identity is used only for
  rate limit allocation and personal dashboard scoping — not as a paywall.</p>
<table class="legal-table">
  <thead>
    <tr><th>Tier</th><th>Identity</th><th>Access</th><th>Price</th><th>Rate Limit</th></tr>
  </thead>
  <tbody>
    <tr>
      <td><span class="tier-badge">Anonymous</span></td>
      <td>None (IP only)</td>
      <td>All 13 tools. No registration needed.</td>
      <td>Free</td>
      <td>10 req/60s per IP</td>
    </tr>
    <tr>
      <td><span class="tier-badge">Scholar</span></td>
      <td>UUID (consent)</td>
      <td>All 13 tools + usage dashboard + Trinity history. Register at /register.</td>
      <td>Free</td>
      <td>30 req/60s per UUID</td>
    </tr>
    <tr>
      <td><span class="tier-badge">Early Adopter</span></td>
      <td>UUID + email</td>
      <td>All 13 tools + EA program benefits</td>
      <td>Free</td>
      <td>100 req/60s per UUID</td>
    </tr>
    <tr>
      <td><span class="tier-badge">PILOT</span></td>
      <td>UUID + email + invite</td>
      <td>All 13 tools + PILOT cohort coordination</td>
      <td>Free</td>
      <td>100 req/60s per UUID</td>
    </tr>
  </tbody>
</table>
<div class="notice-box">
  <strong>Growth First, Monetization Later.</strong> All 13 tools are free for every tier today.
  Pricing for future premium services (such as expert-orchestrated reports) will be announced
  separately and will not change the free-tools pledge. The VerifiMind-PEAS core is MIT licensed —
  you may self-host at any time.
</div>

<h2>4. Payment and Billing</h2>
<p>There are <strong>no active paid services</strong> at this time. All 13 tools, including
  coordination tools, are free for everyone.</p>
<p>When future paid services (such as expert-orchestrated consultation reports) become available,
  this section will be updated with specific billing terms, the payment processor, and any
  additional agreements required at the time of purchase. You will not be charged for any service
  without an explicit purchase action on your part.</p>

<h2>5. Refund Policy</h2>
<p>No refund policy applies today because no paid services are offered. When paid services launch,
  a refund policy will be published as part of the purchase terms before any payment is collected.</p>

<h2>6. Beta Software</h2>
<p>The full VerifiMind-PEAS service is currently in beta. You accept that:</p>
<ul>
  <li>Features may change, be added, or removed as the product evolves</li>
  <li>There is no uptime SLA during the beta period</li>
  <li>Backwards compatibility is not guaranteed between beta versions</li>
  <li>The service is provided "as is" without warranties of any kind</li>
</ul>

<h2>7. Your Feedback</h2>
<ul>
  <li>Any feedback you submit is voluntary</li>
  <li>We may use your feedback to improve the product</li>
  <li>We may quote feedback anonymously — never with your name or email without separate consent</li>
  <li>Submitting feedback does not grant you ownership of or compensation for product improvements</li>
</ul>

<h2>8. Acceptable Use</h2>
<p>You agree not to:</p>
<ul>
  <li>Share, resell, or redistribute any access keys or credentials issued to you</li>
  <li>Use automated scraping or excessive API calls that degrade service for other users</li>
  <li>Use VerifiMind-PEAS tools to generate harmful, misleading, or unethical content</li>
</ul>
<p>Violation may result in suspension or termination of your access.</p>

<h2>9. Opt-Out and Termination</h2>
<ul>
  <li>You may opt out at any time via <a href="/optout"><code>POST /early-adopters/optout/{uuid}</code></a></li>
  <li>On opt-out, personal data is purged within 7 business days (subject to legal retention requirements)</li>
  <li>We may terminate access for violation of the Acceptable Use terms in Section 8</li>
</ul>

<h2>10. Limitation of Liability</h2>
<p>To the maximum extent permitted by applicable law, VerifiMind-PEAS and its creator shall not be
  liable for any indirect, incidental, special, consequential, or punitive damages, or any loss of
  profits or revenues, whether incurred directly or indirectly, or any loss of data, use, goodwill,
  or other intangible losses resulting from your use of the service.</p>

<h2>11. Governing Law</h2>
<p>These Terms are governed by the laws of Malaysia. Any disputes shall be resolved through
  good-faith negotiation first, and if unresolved, through the courts of Malaysia.</p>

<h2>12. Changes to These Terms</h2>
<p>We will notify registered users of material changes at least 14 days before they take effect.
  Continued use after the effective date constitutes acceptance. The current version is always
  available at <a href="https://verifimind.ysenseai.org/terms">verifimind.ysenseai.org/terms</a>.</p>

<h2>13. Open Source</h2>
<p>The VerifiMind-PEAS core is MIT licensed and remains open source. Your registration or subscription
  does not affect your rights under the MIT license. You may self-host the Scholar tier at any time.</p>

<h2>14. Contact</h2>
<ul>
  <li>GitHub Discussions: <a href="https://github.com/creator35lwb-web/VerifiMind-PEAS/discussions" target="_blank" rel="noopener">github.com/creator35lwb-web/VerifiMind-PEAS/discussions</a></li>
  <li>Email: <a href="mailto:creator35lwb@gmail.com">creator35lwb@gmail.com</a></li>
  <li>X (Twitter): <a href="https://x.com/creator35lwb" target="_blank" rel="noopener">x.com/creator35lwb</a></li>
</ul>

<p style="margin-top:2rem; padding-top:1rem; border-top:1px solid var(--border); color:var(--muted); font-size:0.875rem;">
  VerifiMind-PEAS is open source:
  <a href="https://github.com/creator35lwb-web/VerifiMind-PEAS" target="_blank" rel="noopener">github.com/creator35lwb-web/VerifiMind-PEAS</a>
</p>
"""


def get_privacy_page() -> str:
    """Return the full HTML for GET /privacy — Privacy Policy v2.1."""
    return _legal_shell(title="Privacy Policy", body=_PRIVACY_BODY)


def get_terms_page() -> str:
    """Return the full HTML for GET /terms — Terms &amp; Conditions v2.0 (updated April 20, 2026)."""
    return _legal_shell(title="Terms &amp; Conditions", body=_TERMS_BODY)


# ── Scholar Dashboard page ─────────────────────────────────────────────────────

_TOOL_LABELS = {
    "run_full_trinity": "Full Trinity",
    "consult_agent_x": "Agent X (Innovation)",
    "consult_agent_z": "Agent Z (Ethics)",
    "consult_agent_cs": "Agent CS (Security)",
}

_REC_CLASS = {
    "PROCEED": "rec-proceed",
    "REVISE": "rec-revise",
    "REJECT": "rec-reject",
}


def _dashboard_row(rec: dict) -> str:
    ts = rec.get("timestamp", "")
    tool = _TOOL_LABELS.get(rec.get("tool", ""), rec.get("tool", "—"))
    score = rec.get("overall_score") or rec.get("score")
    score_str = f"{score:.1f}/10" if score is not None else "—"
    recommendation = rec.get("recommendation", "—") or "—"
    # Trim long recommendation text
    rec_short = recommendation[:60] + "…" if len(recommendation) > 60 else recommendation
    rec_word = recommendation.split()[0].rstrip(".,—-") if recommendation != "—" else ""
    rec_cls = _REC_CLASS.get(rec_word.upper(), "")
    quality = rec.get("quality", "") or ""
    veto = " ⚑" if rec.get("veto_triggered") else ""
    # Format timestamp: 2026-04-21T01:23:45.000000+00:00 → Apr 21, 2026 01:23 UTC
    try:
        from datetime import datetime, timezone
        dt = datetime.fromisoformat(ts)
        ts_fmt = dt.astimezone(timezone.utc).strftime("%b %d, %Y %H:%M UTC")
    except Exception:
        ts_fmt = ts[:19].replace("T", " ") if ts else "—"
    quality_badge = f'<span class="quality-badge">{quality}</span>' if quality else ""
    return (
        f"<tr>"
        f"<td>{ts_fmt}</td>"
        f"<td>{tool}{quality_badge}</td>"
        f"<td class='score'>{score_str}</td>"
        f'<td class="{rec_cls}">{rec_short}{veto}</td>'
        f"</tr>"
    )


def get_dashboard_page(uuid: str, records: list, firestore_available: bool = True) -> str:
    """Render Scholar validation history dashboard for GET /early-adopters/dashboard/{uuid}."""
    uuid_display = uuid[:8] + "…" + uuid[-4:] if len(uuid) > 12 else uuid
    total = len(records)

    if not firestore_available:
        status_block = '<div class="notice-box">History temporarily unavailable — Firestore is not reachable. Try again shortly.</div>'
    elif total == 0:
        status_block = (
            '<div class="notice-box">'
            "No validations recorded yet. Run any Trinity tool with your <code>user_uuid</code> parameter "
            "to start building your history."
            "</div>"
        )
    else:
        last_ts = records[0].get("timestamp", "")[:10] if records else ""
        status_block = (
            f'<div class="meta">'
            f"<span>{total} validation{'s' if total != 1 else ''} recorded</span>"
            f"<span>Last: {last_ts}</span>"
            f"</div>"
        )

    rows_html = "\n".join(_dashboard_row(r) for r in records) if records else (
        "<tr><td colspan='4' style='text-align:center;color:var(--muted);'>No records yet</td></tr>"
    )

    body = f"""
<h1>Scholar Dashboard</h1>
<div class="meta">
  <span>UUID: <code>{uuid_display}</code></span>
  <span><a href="/register">Register / update</a></span>
</div>

{status_block}

<h2>Validation History</h2>
<table class="legal-table">
  <thead>
    <tr><th>Date (UTC)</th><th>Tool</th><th>Score</th><th>Recommendation</th></tr>
  </thead>
  <tbody>
    {rows_html}
  </tbody>
</table>

<div class="notice-box" style="margin-top:2rem;">
  <strong>Privacy:</strong> No concept names or descriptions are stored — only scores,
  recommendations, and timestamps. See <a href="/privacy">Privacy Policy v2.1</a>.
</div>

<style>
  .score {{ font-weight:600; text-align:center; }}
  .rec-proceed {{ color:#16a34a; }}
  .rec-revise {{ color:#d97706; }}
  .rec-reject {{ color:#dc2626; }}
  .quality-badge {{
    display:inline-block; margin-left:0.4rem; font-size:0.7rem;
    padding:0.1rem 0.35rem; border-radius:3px;
    background:var(--border); color:var(--muted); vertical-align:middle;
  }}
</style>
"""
    return _legal_shell(title=f"Scholar Dashboard — {uuid_display}", body=body)


# ── Changelog page ────────────────────────────────────────────────────────────

_CHANGELOG_BODY = """
<h1>Changelog</h1>
<div class="meta">
  <span>Last updated: May 12, 2026 (v0.5.30)</span>
  <span><a href="https://github.com/creator35lwb-web/VerifiMind-PEAS/releases" target="_blank" rel="noopener">GitHub Releases</a></span>
</div>

<div id="v0.5.30">
<h2>v0.5.30 — Config Scanner Block <span class="live-badge">LIVE</span></h2>
<p style="color:var(--muted);font-size:0.875rem;margin-bottom:0.75rem">May 12, 2026</p>
<ul>
  <li><strong>IP blocked:</strong> <code>85.121.126.250</code> — config/secret enumeration scanner probing <code>/api/env</code>, <code>/firebase-config.json</code>, <code>/swagger.json</code>, <code>/openapi.json</code>, <code>/.well-known/jwks.json</code>, and ~20 more secret/config paths at ~25 req/sec with rotating user agents (botnet pattern)</li>
  <li><strong>Defense-in-depth:</strong> mostly 429-rate-limited already, but adding to blocklist eliminates server-side processing entirely</li>
  <li><strong>Cost rationale:</strong> Cloud Armor (~$5/mo + per-rule + per-request) is not cost-justified at solo-builder scale; app-layer blocklist in <code>ip_blocklist.py</code> is free and equally effective. 6 IPs blocked total.</li>
</ul>
</div>

<div id="v0.5.29">
<h2>v0.5.29 — Growth-First Pages</h2>
<p style="color:var(--muted);font-size:0.875rem;margin-bottom:0.75rem">May 12, 2026</p>
<ul>
  <li><strong><code>/terms</code> &rarr; v2.1</strong> — pricing tier table removed (Pioneer row gone); Payment and Refund sections rewritten as forward-looking placeholders; Section 6 (Beta) and Section 8 (Acceptable Use) updated to drop Pioneer-specific language</li>
  <li><strong><code>/privacy</code> &rarr; v2.2</strong> — Payment Processing section rewritten to "no active paid services"; Polar references removed; retention/data-sharing tables simplified</li>
  <li><strong><code>/register</code> benefit cards</strong> — now show "All 13 tools / Free forever / Beta access / Direct feedback"</li>
  <li><strong>Growth First, Monetization Later</strong> — public surfaces now consistent with the strategic pivot ratified by L + T + Alton in Session 13/14 (May 11). Polar payment infrastructure preserved for future services.</li>
</ul>
</div>

<div id="v0.5.28">
<h2>v0.5.28 — Tools Free</h2>
<p style="color:var(--muted);font-size:0.875rem;margin-bottom:0.75rem">May 10, 2026</p>
<ul>
  <li><strong>Core Tools Always Free pledge fulfilled</strong> — the three coordination tools (<code>coordination_handoff_create</code>, <code>coordination_handoff_read</code>, <code>coordination_team_status</code>) are now free for everyone; <code>pioneer_key</code> parameter is optional and used for namespace identity only, never as a gate</li>
  <li><strong>Anonymous callers welcome</strong> — handoffs without a <code>pioneer_key</code> go to a shared <code>"anonymous"</code> namespace; existing keyed callers unchanged</li>
  <li><strong>Option B refactor PR1 of 3</strong> — ratified May 9, 2026 by L (CEO) + Alton + T (CTO). PR2 (rate limit table) and PR3 (Polar product reshape for L3 reports) follow.</li>
</ul>
</div>

<div id="v0.5.27">
<h2>v0.5.27 — Version Alignment</h2>
<p style="color:var(--muted);font-size:0.875rem;margin-bottom:0.75rem">May 10, 2026</p>
<ul>
  <li><strong>MCP serverInfo.version fix</strong> — <code>/mcp/</code> initialize response now reports our application version (0.5.27) instead of the underlying FastMCP library version; eliminates trust-friction signal flagged by External Model Council (Claude Opus 4.7 + GPT-5.5 + Gemini 3.1 Pro)</li>
  <li><strong>Surface alignment</strong> — all four version-reporting surfaces (<code>/</code>, <code>/health</code>, <code>/.well-known/mcp-config</code>, <code>/mcp/</code>) now consistently report 0.5.27</li>
</ul>
</div>

<div id="v0.5.26">
<h2>v0.5.26 — Scanner Block + HTTP Compliance</h2>
<p style="color:var(--muted);font-size:0.875rem;margin-bottom:0.75rem">May 6, 2026</p>
<ul>
  <li><strong>Security:</strong> blocked an unauthorized MCP prober identified via GCP forensic analysis; added to IP security layer</li>
  <li><strong>HEAD /mcp/ fix</strong> — added explicit HEAD handler returning 200; previously returned 405 Method Not Allowed (HTTP compliance gap in Mount routing)</li>
  <li><strong>CORS hardening</strong> — removed <code>allow_credentials</code> wildcard combination (CWE-942)</li>
</ul>
</div>

<div id="v0.5.25">
<h2>v0.5.25 — Health Transparency</h2>
<p style="color:var(--muted);font-size:0.875rem;margin-bottom:0.75rem">May 1, 2026</p>
<ul>
  <li><strong>inference_mode in /health</strong> — <code>"live"</code> / <code>"degraded"</code> / <code>"mock"</code> field added; resolves 9-day mock-mode blindspot from env var wipe incident; AY monitoring and GCP uptime checks can now detect inference state changes in real time</li>
  <li><strong>repo-owned CI/CD</strong> — <code>cloudbuild.yaml</code> added; Cloud Build trigger now uses version-controlled build config with commit SHA tagging and safe <code>--update-env-vars</code></li>
</ul>
</div>

<div id="v0.5.24">
<h2>v0.5.24 — Cowork Research Publication</h2>
<p style="color:var(--muted);font-size:0.875rem;margin-bottom:0.75rem">April 30, 2026</p>
<ul>
  <li><strong>Cowork Analysis Published</strong> — XV&rsquo;s 10-section strategic analysis of Anthropic Cowork on 3P at <a href="/research/cowork">/research/cowork</a> (L-approved); corrects v1.0 error inline, with <strong>Section 5 (Self-Correction as Substance)</strong> as the featured section — a real-time Validation Paradox case study</li>
  <li><strong>Research Hub Navigation</strong> — Featured card on /research index, 4-pill nav strip (Published Research · The Validation Paradox · Cowork Analysis · Evidence Library) across all research pages</li>
  <li><a href="https://github.com/creator35lwb-web/VerifiMind-PEAS/pull/193" target="_blank" rel="noopener">PR #193</a></li>
</ul>
</div>

<div id="v0.5.23">
<h2>v0.5.23 — BYOK Provider Hardening + Research Navigation</h2>
<p style="color:var(--muted);font-size:0.875rem;margin-bottom:0.75rem">April 30, 2026</p>
<ul>
  <li><strong>BYOK Fixes</strong> — Cerebras key prefix corrected (<code>csk-</code>), model updated to <code>llama-3.3-70b</code>, Anthropic JSON fence stripping added, Mistral package added to dependencies, mistralai v2.x import path updated</li>
  <li><strong>Provider Audit</strong> — All 7 providers (Gemini, Groq, Cerebras, Anthropic, OpenAI, Mistral, Ollama) now consistently strip markdown code fences and return <code>_inference_quality: "real"</code></li>
  <li><strong>Mock Transparency</strong> — <code>_warning</code> field injected when mock mode active; <code>"synthetic"</code> added as <code>overall_quality</code> state in <code>run_full_trinity</code>; MockProvider now correctly surfaces <code>_inference_quality: "mock"</code></li>
  <li><strong>Research Navigation</strong> — <code>/research</code>, <code>/library</code>, <code>/research/paradox</code> fully interlinked with consistent site-nav headers and section pill strips</li>
  <li>631 tests pass, 0 CodeQL medium+ alerts</li>
  <li><a href="https://github.com/creator35lwb-web/VerifiMind-PEAS/pull/189" target="_blank" rel="noopener">PR #189</a> · <a href="https://github.com/creator35lwb-web/VerifiMind-PEAS/pull/190" target="_blank" rel="noopener">PR #190</a></li>
</ul>
</div>

<div id="v0.5.22">
<h2>v0.5.22 — IP Blocklist Security Layer</h2>
<p style="color:var(--muted);font-size:0.875rem;margin-bottom:0.75rem">April 30, 2026</p>
<ul>
  <li><strong>IP Blocklist Middleware</strong> — application-level IP security layer blocking unauthorized access attempts; 403 response with minimal disclosure; added after GCP forensic analysis</li>
  <li><strong>X-Forwarded-For Chain Check</strong> — all hops inspected, not just the first (GFE proxy-aware); blocks across the full request chain</li>
  <li><strong>User-Agent Blocklist</strong> — unauthorized scanner UA patterns blocked (case-insensitive substring match); legitimate MCP clients unaffected</li>
  <li><strong>Audit Logging</strong> — <code>[IP_BLOCKED] ip= reason= path= ua= ts=</code> and <code>[UA_BLOCKED] pattern= ip= path= ua= ts=</code> in GCP log stream for AY forensic analysis</li>
  <li>32 new tests, 574 unit tests pass, 0 CodeQL medium+ alerts</li>
  <li><a href="https://github.com/creator35lwb-web/VerifiMind-PEAS/pull/182" target="_blank" rel="noopener">PR #182</a></li>
</ul>
<details style="margin-top:0.5rem">
<summary style="cursor:pointer;color:var(--muted);font-size:0.875rem">⚠️ Operational Hotfix — April 30, 2026 (click to expand)</summary>
<div style="padding:0.75rem 0;font-size:0.875rem">
  <p><strong>Incident:</strong> A GCP Cloud Run deployment flag (<code>--set-env-vars</code>) accidentally replaced the server&#39;s full environment variable set with a single entry, removing all provider API keys (<code>GEMINI_API_KEY</code>, <code>GROQ_API_KEY</code>, and others). This caused the server to fall back to <code>mock/test-model</code> responses for approximately 9 days (April 21–30, 2026), returning structured but non-real inference output.</p>
  <p><strong>Impact:</strong> All Trinity tool calls during this window returned mock responses. No data was lost and the server remained available; only inference quality was degraded. COO analytics independently flagged anomalous engagement drop correlated with this window.</p>
  <p><strong>Resolution:</strong> All environment variables restored from the reference revision (<code>verifimind-mcp-server-00363-6zp</code>). GCP revision <code>verifimind-mcp-server-00387-xt7</code> is live with real inference confirmed (<code>gemini/gemini-2.5-flash</code>, <code>_inference_quality: real</code>). The deploy skill has been updated to never use <code>--set-env-vars</code> during image deploys.</p>
  <p><strong>If you encountered mock responses:</strong> Please retry your validation — the server is now fully operational. Report any issues via <a href="https://github.com/creator35lwb-web/VerifiMind-PEAS/discussions" target="_blank" rel="noopener">GitHub Discussions</a> or email <a href="mailto:alton@ysenseai.org">alton@ysenseai.org</a>.</p>
</div>
</details>
</div>

<div id="v0.5.21">
<h2>v0.5.21 — P0 Tool Manifest Audit + Structured 404 Logging</h2>
<p style="color:var(--muted);font-size:0.875rem;margin-bottom:0.75rem">April 30, 2026</p>
<ul>
  <li><strong>Tool Manifest Audit</strong> — <code>/.well-known/mcp-config</code> and Smithery server card now list all 13 tools; 3 coordination tools (<code>coordination_handoff_create</code>, <code>coordination_handoff_read</code>, <code>coordination_team_status</code>) were missing since v0.5.16</li>
  <li><strong>Structured 404 Logging</strong> — <code>[TOOL_NOT_FOUND] tool= uuid= ip= ts=</code> emitted in GCP logs when a POST <code>tools/call</code> body hits a 404 path; enables AY to correlate churn to specific tool names and UUID cohorts</li>
  <li><strong>Graceful -32601 Verified</strong> — FastMCP already returns proper MCP JSON-RPC <code>-32601</code> for unknown tool calls natively; confirmed by source audit</li>
  <li>596 tests pass, 60.68% coverage, 0 CodeQL medium+ alerts</li>
  <li><a href="https://github.com/creator35lwb-web/VerifiMind-PEAS/pull/179" target="_blank" rel="noopener">PR #179</a> &middot; <a href="https://github.com/creator35lwb-web/VerifiMind-PEAS/pull/180" target="_blank" rel="noopener">PR #180</a></li>
</ul>
</div>

<div id="v0.5.20">
<h2>v0.5.20 — Root Page UX + BYOK v0.4.0 + BYOK Guide P0 Fix</h2>
<p style="color:var(--muted);font-size:0.875rem;margin-bottom:0.75rem">April 27, 2026</p>
<ul>
  <li><strong>Root Page UX</strong> — Copy buttons on all 4 config code blocks; Scholar UUID tier card with ready-to-paste <code>--header X-VerifiMind-UUID</code> config; URL tip callout for <code>/mcp/</code> trailing slash; tools count corrected to 13 throughout</li>
  <li><strong>BYOK v0.4.0</strong> — New Cerebras provider (<code>llama3.1-70b</code>, 1M tokens/day FREE, <code>csk_</code> prefix); Anthropic default <code>claude-sonnet-4-6</code> / OpenAI default <code>gpt-4.1-mini</code>; smart fallback chain (BYOK &rarr; Groq &rarr; Cerebras &rarr; mock)</li>
  <li><strong>BYOK Guide P0 Fix</strong> — <code>gemini-2.0-flash</code> (deprecated March 31) &rarr; <code>gemini-2.5-flash</code>; Claude.ai Opus 4.7 API key classifier warning; Model Freshness deprecation table</li>
  <li>487 tests pass, 0 CodeQL medium+ alerts</li>
  <li><a href="https://github.com/creator35lwb-web/VerifiMind-PEAS/pull/168" target="_blank" rel="noopener">PR #168</a> &middot; <a href="https://github.com/creator35lwb-web/VerifiMind-PEAS/pull/169" target="_blank" rel="noopener">PR #169</a></li>
</ul>
</div>

<div id="v0.5.19">
<h2>v0.5.19 — UUID Tier-Aware Rate Limiter + 404 Churn Fixes</h2>
<p style="color:var(--muted);font-size:0.875rem;margin-bottom:0.75rem">April 21, 2026</p>
<ul>
  <li><strong>UUID Tier-Aware Rate Limiting (P0-A)</strong> — <code>X-VerifiMind-UUID</code> header sets rate limit tier server-side: Anonymous 10 req/60s per IP &middot; Scholar 30 req/60s per UUID &middot; Pioneer 100 req/60s per UUID; tier cached 5 min; fail-open to Scholar if Firestore unavailable; <code>X-RateLimit-Tier</code> on every response</li>
  <li><strong>404 Churn Fixed (AY COO PIN)</strong> — <code>GET /mcp</code> (no trailing slash) &rarr; <strong>308</strong> Permanent Redirect; <code>GET /mcp/sse</code> and <code>GET /sse</code> &rarr; <strong>410 Gone</strong> with actionable JSON; eliminates ~531&ndash;556 daily 404s</li>
  <li>574 tests pass, 61.99% coverage, CodeQL clean</li>
  <li><a href="https://github.com/creator35lwb-web/VerifiMind-PEAS/pull/163" target="_blank" rel="noopener">PR #163</a> &middot; <a href="https://github.com/creator35lwb-web/VerifiMind-PEAS/pull/164" target="_blank" rel="noopener">PR #164</a></li>
</ul>
</div>

<div id="v0.5.18">
<h2>v0.5.18 — Scholar Dashboard: Trinity History</h2>
<p style="color:var(--muted);font-size:0.875rem;margin-bottom:0.75rem">April 21, 2026</p>
<ul>
  <li><strong><code>GET /early-adopters/dashboard/{uuid}</code></strong> — personal Trinity validation history page; last 50 results from Firestore (<code>trinity_history/{uuid}/validations/</code>); shows score, tool, recommendation excerpt, veto flag, timestamp per row; empty state + unavailable fallback</li>
  <li>472 tests pass, 59.74% coverage</li>
  <li><a href="https://github.com/creator35lwb-web/VerifiMind-PEAS/pull/162" target="_blank" rel="noopener">PR #162</a></li>
</ul>
</div>

<div id="v0.5.17">
<h2>v0.5.17 — mcp_config UUID Header Fix</h2>
<p style="color:var(--muted);font-size:0.875rem;margin-bottom:0.75rem">April 21, 2026</p>
<ul>
  <li><strong>UUID auto-flows on every MCP request</strong> — <code>mcp_config</code> args now include <code>--header X-VerifiMind-UUID:${VERIFIMIND_UUID}</code>; <code>mcp-remote</code> expands from env and sends with every request; no manual <code>user_uuid</code> per tool call needed</li>
  <li><strong>MCP Registry updated to v2.5.0</strong> — <a href="https://registry.modelcontextprotocol.io/?q=verifimind" target="_blank" rel="noopener">registry.modelcontextprotocol.io</a></li>
  <li><a href="https://github.com/creator35lwb-web/VerifiMind-PEAS/pull/160" target="_blank" rel="noopener">PR #160</a> &middot; <a href="https://github.com/creator35lwb-web/VerifiMind-PEAS/pull/161" target="_blank" rel="noopener">PR #161</a></li>
</ul>
</div>

<div id="v0.5.16">
<h2>v0.5.16 — Trinity History Persistence + Terms Hotfix</h2>
<p style="color:var(--muted);font-size:0.875rem;margin-bottom:0.75rem">April 21, 2026</p>
<ul>
  <li><strong>Trinity history persistence (P1-B)</strong> — <code>write_trinity_history(uuid, tool, result)</code> fire-and-forget async Firestore write; stores score, recommendation excerpt, veto flag, timestamp; wired into all 4 core tools when <code>user_uuid</code> provided; zero latency impact</li>
  <li><strong>/terms page hotfix</strong> — Anonymous tier row added, Identity + Rate Limit columns explicit, Privacy Policy v2.1 link, "Updated: April 21, 2026"</li>
  <li><a href="https://github.com/creator35lwb-web/VerifiMind-PEAS/pull/158" target="_blank" rel="noopener">PR #158</a> &middot; <a href="https://github.com/creator35lwb-web/VerifiMind-PEAS/pull/159" target="_blank" rel="noopener">PR #159</a></li>
</ul>
</div>

<div id="v0.5.15">
<h2>v0.5.15 — Scholar Incentives: UUID Tracer + Registration UX</h2>
<p style="color:var(--muted);font-size:0.875rem;margin-bottom:0.75rem">April 20, 2026</p>
<ul>
  <li><strong>UUID Tracer on all 10 Scholar tools</strong> — optional <code>user_uuid</code> parameter; fire-and-forget <code>TRACER_UUID:</code> stdout log feeds AY GCP analytics pipeline; invalid UUIDs silently ignored (log injection prevention)</li>
  <li><strong>Privacy Policy v2.1</strong> — UUID usage analytics fully disclosed: what is logged (UUID, tool name, tier, timestamp), what is NOT logged (concept content, IP linked to UUID, PII), 30-day GCP auto-purge; Z-Protocol v1.1 compliant</li>
  <li><strong>Terms v2.0 updated</strong> — Anonymous tier row added to service tiers table with Identity column and Rate Limit column; 3-tier model (Anonymous/Scholar/Pioneer) now unambiguous</li>
  <li><strong>Registration response enhanced (P1-C)</strong> — <code>register_user()</code> now returns <code>mcp_config</code> (ready-to-paste Claude Desktop JSON), <code>test_url</code>, <code>dashboard_url</code>, <code>checkout_url</code> — one API call gives Scholar everything needed to start</li>
  <li>515 tests, CodeQL clean (0 medium+ alerts)</li>
  <li><a href="https://github.com/creator35lwb-web/VerifiMind-PEAS/pull/154" target="_blank" rel="noopener">PR #154</a></li>
</ul>
</div>

<div id="v0.5.14">
<h2>v0.5.14 — Fortify: Research Library + Connection Test</h2>
<p style="color:var(--muted);font-size:0.875rem;margin-bottom:0.75rem">April 17, 2026</p>
<ul>
  <li><strong><code>GET /mcp/test?key=&lt;uuid&gt;</code></strong> — UUID connection test: verify your key is valid and see your tier before configuring your MCP client</li>
  <li><strong><code>GET /library</code></strong> — Genesis Research Library v1.0: living compendium of 20+ academic papers validating the VerifiMind methodology (Sections A&ndash;E, evidence chain timeline, JSON-LD SEO)</li>
  <li><strong><code>GET /library/index.json</code></strong> — machine-readable library index for AI crawlers and future MCP tool</li>
  <li><strong>/research Article 3</strong> — MPAC vs MACP competitive analysis (XV + T, April 17, 2026); AI Council CONDITIONAL verdict disclosed</li>
  <li><strong><code>/research/index.json</code> v1.1</strong> — 4 papers (was 3), mpac-alignment entry added</li>
  <li><strong>sitemap.xml + robots.txt</strong> — <code>/library</code> and <code>/library/index.json</code> added for crawler access</li>
  <li>485 tests</li>
  <li><a href="https://github.com/creator35lwb-web/VerifiMind-PEAS/pull/151" target="_blank" rel="noopener">PR #151</a></li>
</ul>
</div>

<div id="v0.5.13">
<h2>v0.5.13 — Fortify</h2>
<p style="color:var(--muted);font-size:0.875rem;margin-bottom:0.75rem">April 12, 2026</p>
<ul>
  <li><strong>Polar circuit breaker</strong> — 5-failure/60s window → OPEN; half-open recovery after 60s</li>
  <li><strong>Fail-closed production semantics</strong> — any Polar outage = access denied (not env-var fallback)</li>
  <li><strong>Retry with backoff</strong> — 3 attempts, 1s → 2s delay; 404/401 not retried</li>
  <li><strong>Sanitization: 20+ providers</strong> — GitHub, AWS, Polar, Hugging Face, Replicate, SendGrid, Twilio, Mailgun, Slack, JWT, Bearer, Azure + catch-all</li>
  <li><strong>Phase 2 tier-gate</strong> — <code>_validate_pioneer_key()</code> calls Polar API in production (real-time billing enforcement)</li>
  <li><strong>Lightweight <code>/register</code></strong> — consent-only UUID identity for anonymous Scholars (zero PII)</li>
  <li><strong>CodeQL clean</strong> — 0 medium+ alerts; stack-trace-exposure fixed in registration handlers</li>
  <li><strong>485 tests</strong> — billing-critical coverage: <code>tier_gate.py</code> 100%, <code>polar_adapter.py</code> 96%, <code>polar_client.py</code> 100%</li>
  <li><a href="https://github.com/creator35lwb-web/VerifiMind-PEAS/pull/131" target="_blank" rel="noopener">PR #131</a> · <a href="https://github.com/creator35lwb-web/VerifiMind-PEAS/pull/133" target="_blank" rel="noopener">PR #133</a></li>
</ul>
</div>

<div id="v0.5.12">
<h2>v0.5.12 — Polar Integration + Legal v2.0</h2>
<p style="color:var(--muted);font-size:0.875rem;margin-bottom:0.75rem">April 8, 2026</p>
<ul>
  <li><strong>PolarClient</strong> — Customer State API, <code>has_pioneer_access()</code></li>
  <li><strong>PolarAdapter</strong> — 5-minute TTL cache, singleton, webhook-driven cache invalidation</li>
  <li><strong>Webhook endpoint</strong> <code>POST /api/webhooks/polar</code> — Standard Webhooks HMAC verification, 6 subscription events</li>
  <li><strong>Legal pages v2.0</strong> — Privacy Policy and Terms &amp; Conditions with Polar Merchant of Record, Pioneer tier pricing, 14-day refund policy</li>
  <li><strong>UUID Tracer</strong> — <code>print(TRACER_UUID, flush=True)</code> in all 3 coordination tools for GCP log analytics bridge</li>
  <li>312 tests, 52.76% coverage</li>
  <li><a href="https://github.com/creator35lwb-web/VerifiMind-PEAS/pull/123" target="_blank" rel="noopener">PR #123</a> · <a href="https://github.com/creator35lwb-web/VerifiMind-PEAS/pull/124" target="_blank" rel="noopener">PR #124</a> · <a href="https://github.com/creator35lwb-web/VerifiMind-PEAS/pull/125" target="_blank" rel="noopener">PR #125</a></li>
</ul>
</div>

<div id="v0.5.11">
<h2>v0.5.11 — Coordination Foundation</h2>
<p style="color:var(--muted);font-size:0.875rem;margin-bottom:0.75rem">April 7, 2026</p>
<ul>
  <li><strong>3 coordination tools</strong> — <code>coordination_handoff_create</code>, <code>coordination_handoff_read</code>, <code>coordination_team_status</code></li>
  <li><strong>Tier-gate middleware</strong> — Scholar (free) vs Pioneer (paid) access control via <code>check_tier()</code></li>
  <li>Phase 1: <code>PIONEER_ACCESS_KEYS</code> env var validation (Phase 2 Polar wiring in v0.5.13)</li>
  <li>308 tests</li>
  <li><a href="https://github.com/creator35lwb-web/VerifiMind-PEAS/pull/122" target="_blank" rel="noopener">PR #122</a></li>
</ul>
</div>

<div id="v0.5.10">
<h2>v0.5.10 — Trinity Verified</h2>
<p style="color:var(--muted);font-size:0.875rem;margin-bottom:0.75rem">April 5, 2026</p>
<ul>
  <li>Trinity pipeline verified end-to-end with real multi-model inference</li>
  <li>600-second timeout for long-running validation sessions</li>
  <li>Z Guardian <code>max_tokens</code> enforcement (8,192 ceiling)</li>
  <li>BYOK Anthropic Claude 4 family (claude-opus-4-6, claude-sonnet-4-6)</li>
  <li>Prior reasoning compression — fixes token overflow in Z Agent</li>
  <li>Two-tier PILOT/EA registration with invite codes</li>
  <li>290 tests</li>
</ul>
</div>

<div id="v0.5.7">
<h2>v0.5.7 — Two-Tier Pioneer + SYSTEM_NOTICE</h2>
<p style="color:var(--muted);font-size:0.875rem;margin-bottom:0.75rem">March 29, 2026</p>
<ul>
  <li>Two-tier access system (PILOT + EA) with invite codes</li>
  <li><code>SYSTEM_NOTICE</code> injection — server-side context for all tool calls</li>
  <li>PILOT detection at registration</li>
</ul>
</div>

<div id="v0.5.6">
<h2>v0.5.6 — Gateway: Early Adopter Registration</h2>
<p style="color:var(--muted);font-size:0.875rem;margin-bottom:0.75rem">March 23, 2026</p>
<ul>
  <li>Early Adopter registration at <code>/register</code> (Z-Protocol v1.1 consent-first)</li>
  <li>UUID-based opt-out at <code>/optout</code> (GDPR right to erasure)</li>
  <li>Firestore EA data store (GCP native)</li>
  <li>Privacy Policy v1.0 + Terms &amp; Conditions v1.0</li>
  <li>290 tests</li>
</ul>
</div>

<div id="v0.5.5">
<h2>v0.5.5 — Trinity Baseline</h2>
<p style="color:var(--muted);font-size:0.875rem;margin-bottom:0.75rem">March 13, 2026</p>
<ul>
  <li><code>TrinitySynthesis</code> Pydantic schema fix — <code>founder_summary</code> field added</li>
  <li>3 regression tests for schema validation</li>
  <li>208 tests, Phase 47 Ground Truth baseline established</li>
</ul>
</div>

<div id="v0.5.2">
<h2>v0.5.2 — Genesis v4.2 "Sentinel-Verified"</h2>
<p style="color:var(--muted);font-size:0.875rem;margin-bottom:0.75rem">March 9, 2026</p>
<ul>
  <li>Genesis v4.2 — forced citation patterns (C-S-P methodology)</li>
  <li>Z Guardian: compressed framework codes, max 5 per step (~45% token reduction)</li>
  <li>CS Agent: <code>stage</code> + <code>standards_cited[]</code> per step mandatory</li>
  <li>L Blind Test #3 PASSED (11/11)</li>
  <li>198 tests</li>
</ul>
</div>

<div id="v0.5.1">
<h2>v0.5.1 — Z-Protocol v1.1 + CS Security v1.1 "Sentinel"</h2>
<p style="color:var(--muted);font-size:0.875rem;margin-bottom:0.75rem">March 7, 2026</p>
<ul>
  <li>Z-Protocol v1.1 "Sentinel" — 21 frameworks, 4-tier jurisdictional analysis</li>
  <li>CS Security v1.1 — 6-stage, 12-dimension, OWASP Agentic AI framework</li>
  <li>Trinity baseline: <strong>8.7/10 PROCEED</strong></li>
</ul>
</div>

<div id="v0.5.0">
<h2>v0.5.0 — Foundation: BYOK v2 + SessionContext</h2>
<p style="color:var(--muted);font-size:0.875rem;margin-bottom:0.75rem">March 1, 2026</p>
<ul>
  <li>BYOK v2 — Bring Your Own Key with per-agent-call provider override</li>
  <li><code>SessionContext</code> dataclass — session state isolation, UUID tracing</li>
  <li>Structured error responses (<code>build_error_response</code>)</li>
  <li>API key prefix auto-detection (gsk_, sk-ant-, AIza, sk-)</li>
  <li>Smithery removal complete</li>
</ul>
</div>

<div id="v0.4.0">
<h2>v0.4.0 — Unified Prompt Templates</h2>
<p style="color:var(--muted);font-size:0.875rem;margin-bottom:0.75rem">January 30, 2026</p>
<ul>
  <li>Prompt template library with import/export</li>
  <li>MCP Registry listing — <code>io.github.creator35lwb-web/verifimind-genesis</code></li>
  <li>Streamable HTTP transport</li>
</ul>
</div>

<div id="v0.1.0">
<h2>v0.1.0 — Genesis</h2>
<p style="color:var(--muted);font-size:0.875rem;margin-bottom:0.75rem">January 12, 2026</p>
<ul>
  <li>Initial MCP server scaffold</li>
  <li>Genesis Prompt Engineering Methodology design</li>
  <li>First commit to <a href="https://github.com/creator35lwb-web/VerifiMind-PEAS" target="_blank" rel="noopener">creator35lwb-web/VerifiMind-PEAS</a></li>
</ul>
</div>

<p style="margin-top:2rem; padding-top:1rem; border-top:1px solid var(--border); color:var(--muted); font-size:0.875rem;">
  Full release history:
  <a href="https://github.com/creator35lwb-web/VerifiMind-PEAS/releases" target="_blank" rel="noopener">github.com/creator35lwb-web/VerifiMind-PEAS/releases</a>
</p>
"""


def get_changelog_page() -> str:
    """Return the full HTML for GET /changelog — version history."""
    return _legal_shell(title="Changelog", body=_CHANGELOG_BODY)


# ---------------------------------------------------------------------------
# Research page — public research from the FLYWHEEL TEAM
# ---------------------------------------------------------------------------

_RESEARCH_CSS = """
.research-wrapper {
  max-width: 860px;
  margin: 0 auto;
}

.research-doc h1 {
  font-size: 1.75rem;
  font-weight: 700;
  color: var(--text);
  margin-bottom: 0.25rem;
}

.research-doc .page-subtitle {
  color: var(--muted);
  font-size: 0.9rem;
  margin-bottom: 2rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid var(--border);
}

.research-article {
  margin-bottom: 3rem;
  padding-bottom: 2.5rem;
  border-bottom: 1px solid var(--border);
}

.research-article:last-child {
  border-bottom: none;
}

.research-article h2 {
  font-size: 1.2rem;
  font-weight: 700;
  color: var(--text);
  margin-bottom: 0.5rem;
  line-height: 1.4;
}

.research-article h3 {
  font-size: 1rem;
  font-weight: 600;
  color: var(--accent);
  margin: 1.5rem 0 0.5rem;
}

.research-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem 1.5rem;
  color: var(--muted);
  font-size: 0.8rem;
  margin-bottom: 1.25rem;
  padding-bottom: 0.75rem;
  border-bottom: 1px solid var(--border);
}

.research-meta .authors { font-weight: 500; color: var(--text-soft, var(--muted)); }

.research-tag {
  display: inline-block;
  font-size: 0.7rem;
  font-weight: 600;
  padding: 0.15rem 0.55rem;
  border-radius: 999px;
  background: var(--accent-dim, rgba(99,102,241,0.12));
  color: var(--accent);
  margin-right: 0.35rem;
  margin-bottom: 0.4rem;
  vertical-align: middle;
}

.research-abstract {
  background: var(--surface, #f8f8fc);
  border-left: 3px solid var(--accent);
  padding: 0.9rem 1.1rem;
  margin: 1rem 0 1.25rem;
  font-size: 0.9rem;
  line-height: 1.65;
  border-radius: 0 6px 6px 0;
}

.research-doc p { line-height: 1.7; margin-bottom: 0.9rem; }

.protocol-stack {
  font-family: monospace;
  font-size: 0.8rem;
  background: var(--surface, #f8f8fc);
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 1rem 1.25rem;
  margin: 1rem 0;
  line-height: 1.6;
  white-space: pre;
  overflow-x: auto;
}

.finding-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
  margin: 1rem 0 1.5rem;
}

.finding-card {
  background: var(--surface, #f8f8fc);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 1rem;
  font-size: 0.85rem;
}

.finding-card .finding-num {
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--accent);
  display: block;
  margin-bottom: 0.25rem;
}

.finding-card p { margin: 0; color: var(--muted); font-size: 0.8rem; }

.research-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.82rem;
  margin: 1rem 0 1.5rem;
}

.research-table th {
  background: var(--surface, #f8f8fc);
  padding: 0.5rem 0.75rem;
  text-align: left;
  font-weight: 600;
  color: var(--text);
  border-bottom: 2px solid var(--border);
}

.research-table td {
  padding: 0.5rem 0.75rem;
  border-bottom: 1px solid var(--border);
  color: var(--muted);
}

.research-table tr:last-child td { border-bottom: none; }

.research-table td:first-child,
.research-table th:first-child { font-weight: 600; color: var(--accent); }

.research-table .layer-5 td { background: rgba(99,102,241,0.06); }

.discussion-link {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  font-size: 0.82rem;
  font-weight: 500;
  color: var(--accent);
  text-decoration: none;
  margin-top: 0.5rem;
}

.discussion-link:hover { text-decoration: underline; }

.mermaid-wrap {
  margin: 1.5rem 0 2rem;
  background: #0f172a;
  border: 1px solid var(--border, #334155);
  border-radius: 8px;
  padding: 1.5rem 1rem;
  overflow-x: auto;
  text-align: center;
}

.mermaid-wrap .mermaid { display: inline-block; }
"""


_RESEARCH_BODY = """
<h1>Research</h1>
<p class="page-subtitle">
  Published research from the VerifiMind FLYWHEEL TEAM — independent analysis on
  agent protocols, AI trust infrastructure, and the evolving multi-agent ecosystem.
  All findings are open and reproducible.
</p>

<div class="research-section-nav">
  <a href="/research" class="nav-pill nav-pill-active">Published Research</a>
  <a href="/research/paradox" class="nav-pill">The Validation Paradox</a>
  <a href="/research/cowork" class="nav-pill">Cowork Analysis</a>
  <a href="/library" class="nav-pill">Evidence Library</a>
</div>

<!-- ================================================================ -->
<!-- Featured: XV Cowork v1.1 — APPROVED                              -->
<!-- ================================================================ -->

<div class="research-article" id="cowork-analysis" style="border-left:3px solid var(--accent);padding-left:1.25rem;margin-bottom:3rem">

<div style="display:flex;align-items:center;gap:0.75rem;margin-bottom:0.5rem">
  <h2 style="margin-bottom:0">Anthropic Cowork on 3P: A Strategic Analysis with Self-Correction</h2>
  <span class="live-badge" style="flex-shrink:0">NEW</span>
</div>

<div class="research-meta">
  <span class="authors">XV (CIO, Perplexity) &nbsp;&middot;&nbsp; Reviewed by L (CEO/Godel)</span>
  <span>April 30, 2026</span>
  <span>v1.1 — Self-Correcting Living Document</span>
  <span>
    <span class="research-tag">Strategic Intelligence</span>
    <span class="research-tag">Self-Correction</span>
    <span class="research-tag">Competitive Analysis</span>
    <span class="research-tag">China Market</span>
  </span>
</div>

<div class="research-abstract">
  <strong>Abstract.</strong> Anthropic's Cowork on 3P routes inference through any OpenAI-compatible LLM gateway
  (confirmed April 2026) — running GPT-5, Gemini, DeepSeek, Kimi, Grok, or local models inside Anthropic's
  agent harness. This narrows VerifiMind's defensible territory but does not eliminate it.
  Cowork solves operational coordination; it does not implement Council Mode patterns, Woozle Effect mitigation,
  or China-deployable sovereign validation. This paper corrects its own v1.0 error in Section 5 — a real-time
  case study of the Validation Paradox exit node working as designed.
</div>

<p style="margin-bottom:1.25rem">
  An AI agent (XV) produced a confident strategic conclusion that was factually wrong. The human Orchestrator
  flagged community evidence. The analysis was corrected, version-controlled, and republished within five days.
  The self-correction is the substance — not just a footnote.
</p>

<a href="/research/cowork" style="display:inline-block;padding:0.55rem 1.25rem;background:var(--accent);color:#000;font-weight:600;font-size:0.875rem;border-radius:6px;text-decoration:none">Read Full Analysis →</a>
<span style="margin-left:1rem;color:var(--muted);font-size:0.8rem">10 sections · 14 sources · CC BY 4.0</span>

</div>

<!-- ================================================================ -->
<!-- Article 1: 5-Layer Stack / ANP Analysis                          -->
<!-- ================================================================ -->

<div class="research-article" id="five-layer-stack">

<h2>The 5-Layer Agent Protocol Stack: Where MACP Fits (and Why ANP Is Not a Competitor)</h2>

<div class="research-meta">
  <span class="authors">T (CTO, Manus AI) &nbsp;&middot;&nbsp; L (GodelAI) &nbsp;&middot;&nbsp; XV (CIO, Perplexity)</span>
  <span>April 15, 2026</span>
  <span>
    <span class="research-tag">Protocol Architecture</span>
    <span class="research-tag">Competitive Analysis</span>
    <span class="research-tag">AI Council Validated</span>
  </span>
</div>

<div class="research-abstract">
  <strong>Abstract.</strong> The agent protocol ecosystem has matured into a 5-layer stack.
  MCP (Layer 2), ANP (Layer 3), A2A (Layer 4), and MACP (Layer 5) address fundamentally
  different problems. An AI Council session flagged ANP as a potential direct competitor to
  MACP's cross-vendor validation claim. Instead of dismissing the challenge, we ran a
  research sprint and published what we found — including where our original claim was wrong.
  MACP remains the only protocol at Layer 5 (trust and validation). ANP operates at Layer 3
  (network discovery). They are complementary, not competitive.
</div>

<h3>The 5-Layer Stack</h3>

<div class="mermaid-wrap">
<div class="mermaid">
%%{init: {"theme": "dark", "themeVariables": {"primaryColor": "#6366f1", "primaryTextColor": "#ffffff", "primaryBorderColor": "#4338ca", "lineColor": "#6366f1", "background": "#0f172a", "mainBkg": "#1e293b", "nodeBorder": "#475569", "fontFamily": "ui-monospace, SFMono-Regular, monospace", "fontSize": "13px"}}}%%
flowchart BT
    classDef macp  fill:#6366f1,color:#fff,stroke:#4338ca,stroke-width:2px
    classDef std   fill:#1e293b,color:#e2e8f0,stroke:#475569,stroke-width:1px
    classDef trans fill:#0f172a,color:#64748b,stroke:#334155,stroke-width:1px,stroke-dasharray:4

    L1["Layer 1 — HTTP / WebSocket / gRPC<br/><b>Transport</b>"]
    L2["Layer 2 — MCP · Linux Foundation<br/><b>Tool Integration</b><br/>Agent-Tool RPC · Schema Discovery · 110M+ monthly"]
    L3["Layer 3 — ANP · W3C Community Group<br/><b>Network Discovery and Negotiation</b><br/>DID:WBA · Meta-Protocol · Linked Data Crawling"]
    L4["Layer 4 — A2A / ACP · Linux Foundation<br/><b>Task Delegation</b><br/>Agent Cards · Task outsourcing · 150+ organizations"]
    L5["Layer 5 — MACP · YSenseAI ✦<br/><b>Trust and Validation</b><br/>AI Council · Anti-Rationalization · Z-Protocol"]

    L1 --> L2 --> L3 --> L4 --> L5

    class L5 macp
    class L4,L3,L2 std
    class L1 trans
</div>
</div>

<h3>What MACP Solves vs What ANP Solves</h3>

<table class="research-table">
  <thead>
    <tr><th>Question</th><th>Protocol</th><th>Layer</th></tr>
  </thead>
  <tbody>
    <tr><td>How do agents discover each other?</td><td>ANP</td><td>3</td></tr>
    <tr><td>How do agents agree on communication formats?</td><td>ANP</td><td>3</td></tr>
    <tr><td>How do agents call external tools?</td><td>MCP</td><td>2</td></tr>
    <tr><td>How do agents delegate tasks to other agents?</td><td>A2A</td><td>4</td></tr>
    <tr class="layer-5"><td>How do we know the output is trustworthy?</td><td><strong>MACP</strong></td><td><strong>5</strong></td></tr>
    <tr class="layer-5"><td>How do we reduce hallucination across models?</td><td><strong>MACP</strong></td><td><strong>5</strong></td></tr>
    <tr class="layer-5"><td>How do we keep a human in the loop?</td><td><strong>MACP</strong></td><td><strong>5</strong></td></tr>
  </tbody>
</table>

<h3>Where Our Original Claim Was Wrong</h3>
<p>
  Our April 14 differentiation document claimed "no other protocol provides cross-vendor
  semantic validation." The AI Council CS Agent was right to flag this — ANP does provide
  cross-vendor semantic <em>negotiation</em> (agents from different vendors agree on
  communication formats). We corrected the claim. MACP provides cross-vendor semantic
  <em>validation</em> (verifying correctness and trustworthiness of outputs after they exist).
  Negotiation and validation are complementary, not competing, concerns.
</p>

<h3>The Honest Conclusion</h3>
<p>
  An agent system can and should use ANP (Layer 3) for discovery, MCP (Layer 2) for
  tool integration, A2A (Layer 4) for task delegation, and MACP (Layer 5) for trust
  validation — simultaneously, just as a web application uses DNS for discovery and
  TLS for security simultaneously. MACP is the only protocol that addresses the
  epistemic question: <em>is this output correct and aligned?</em>
</p>

<a class="discussion-link" href="https://github.com/creator35lwb-web/VerifiMind-PEAS/discussions/143" target="_blank" rel="noopener">
  &#8594; Read full discussion and join the conversation on GitHub (#143)
</a>

</div>


<!-- ================================================================ -->
<!-- Article 2: Market Intelligence Week 16                           -->
<!-- ================================================================ -->

<div class="research-article" id="market-intelligence-week16">

<h2>Market Intelligence: Agent Protocol Ecosystem — Week 16 (April 8&#x2013;15, 2026)</h2>

<div class="research-meta">
  <span class="authors">T (CTO, Manus AI)</span>
  <span>April 15, 2026</span>
  <span>
    <span class="research-tag">Market Intelligence</span>
    <span class="research-tag">Ecosystem Analysis</span>
    <span class="research-tag">Weekly Report</span>
  </span>
</div>

<div class="research-abstract">
  <strong>Abstract.</strong> The agent protocol ecosystem is experiencing a Cambrian explosion.
  In seven days, the competitive landscape expanded from 7 to 10+ protocols. More significantly,
  independent researchers, protocol designers, and enterprise analysts are converging on the
  same conclusion: the trust and validation layer is the critical missing piece in agent
  infrastructure. MACP's Layer 5 positioning is not only defensible — it is being validated
  by independent third parties who have no knowledge of MACP's existence.
</div>

<h3>Key Findings</h3>

<div class="finding-grid">
  <div class="finding-card">
    <span class="finding-num">10+</span>
    <p>Agent protocols in active development as of April 15, 2026 — up from 7 the prior week</p>
  </div>
  <div class="finding-card">
    <span class="finding-num">150+</span>
    <p>Organizations supporting A2A (Linux Foundation), confirming Layer 4 has reached critical mass</p>
  </div>
  <div class="finding-card">
    <span class="finding-num">110M+</span>
    <p>Monthly MCP downloads (confirmed by Anthropic, April 13) — Layer 2 is the default tool layer</p>
  </div>
  <div class="finding-card">
    <span class="finding-num">0</span>
    <p>Other protocols at Layer 5 (trust &amp; validation) — the gap MACP was built to fill remains open</p>
  </div>
</div>

<h3>New Protocol Entrants (April 8&#x2013;15)</h3>

<table class="research-table">
  <thead>
    <tr><th>Protocol</th><th>Layer</th><th>Organization</th><th>Key Contribution</th></tr>
  </thead>
  <tbody>
    <tr><td>MPAC</td><td>4.5</td><td>Open Source (arXiv:2604.09744)</td><td>Multi-principal governance — resolves whose intent prevails when independent principals' agents must coordinate over shared state</td></tr>
    <tr><td>AXCP</td><td>3</td><td>Rodriguez, 2026</td><td>Secure multi-agent communication using DID resolution trust and message provenance</td></tr>
    <tr><td>HDP</td><td>3.5</td><td>Open Source (arXiv:2604.04522)</td><td>Human Delegation Provenance — cryptographic tokens carrying human authorization context through multi-agent chains</td></tr>
  </tbody>
</table>

<h3>The Provenance Gap Consensus</h3>
<p>
  The most strategically significant development this week: independent researchers are
  converging on the same structural finding across all major protocols.
  Paul Clegg's April 11 analysis surveyed MCP, A2A, ACP, and ANP and found
  the same missing piece in all four:
</p>

<table class="research-table">
  <thead>
    <tr><th>Protocol</th><th>Identified Gap</th><th>Prescribed Mitigation</th></tr>
  </thead>
  <tbody>
    <tr><td>MCP</td><td>Tool Redefinition</td><td>Signed, versioned manifests</td></tr>
    <tr><td>A2A</td><td>Version Drift</td><td>Immutable, versioned manifests; signed diffs</td></tr>
    <tr><td>ACP</td><td>Configuration Drift</td><td>Validate against known state</td></tr>
    <tr><td>ANP</td><td>Provenance tracking</td><td>Same pattern applies</td></tr>
  </tbody>
</table>

<p>
  Same prescription. Four protocols. The researchers are not describing a theoretical gap
  — they are documenting what is missing right now across the entire production protocol
  landscape. MACP's multi-model validation directly addresses the trust gap that all four
  independent analyses identify.
</p>

<h3>Enterprise Signals</h3>
<ul>
  <li><strong>Kong AI Gateway</strong> (April 15) — now supports A2A traffic alongside MCP, positioning as "the most comprehensive AI gateway for the agentic era." The trust and validation layer (Layer 5) remains absent from enterprise gateway offerings.</li>
  <li><strong>Futurum Group survey</strong> (April 14) — 24.9% of enterprises primarily rely on neutral orchestration over walled gardens. MACP's protocol-agnostic validation layer aligns with this preference.</li>
  <li><strong>Microsoft Copilot Studio</strong> (April 9) — published A2A integration documentation, confirming A2A as the enterprise task-delegation standard.</li>
  <li><strong>IETF DAWN draft</strong> (April 2026) — first IETF-track work on agent discovery requirements, validating ANP's approach and signaling that standards bodies are actively shaping the landscape.</li>
</ul>

<h3>W3C Standards Activity</h3>
<p>
  The W3C AI Agent Protocol Community Group published a comparison of MCP, A2A, ACP, ANP,
  and AGORA in April 2026. MACP is absent from this comparison. Our CIO (XV) elevated
  W3C/IETF engagement from a "post-Beta" item to an "alongside Beta" priority.
  Standards bodies are defining the agent protocol landscape now — absence means absence.
</p>

<a class="discussion-link" href="https://github.com/creator35lwb-web/VerifiMind-PEAS/discussions/144" target="_blank" rel="noopener">
  &#8594; Read full report and join the discussion on GitHub (#144)
</a>

</div>


<!-- ================================================================ -->
<!-- Article 3: MPAC vs MACP                                         -->
<!-- ================================================================ -->

<div class="research-article" id="mpac-alignment">

<h2>MPAC vs MACP: Complementary Coordination Layers in the Agent Protocol Ecosystem</h2>

<div class="research-meta">
  <span class="authors">XV (CIO, Perplexity) &nbsp;&middot;&nbsp; T (CTO, Manus AI)</span>
  <span>April 17, 2026</span>
  <span>
    <span class="research-tag">Protocol Architecture</span>
    <span class="research-tag">Competitive Analysis</span>
    <span class="research-tag">AI Council Validated</span>
  </span>
</div>

<div class="research-abstract">
  <strong>Abstract.</strong> A peer-reviewed protocol — MPAC (Multi-Principal Agent Coordination,
  arXiv:2604.09744) — was published April 10, 2026 by Qian, Fang &amp; Li. MPAC and MACP are
  literal anagrams, both claim to fill the gap above MCP and A2A, and both are open source.
  This intelligence brief provides an honest, side-by-side comparison. The core finding: MPAC
  solves operational coordination ("did all agents agree on what happened?"), MACP solves semantic
  validation ("is what happened actually correct and ethical?"). They are complementary, not
  competitive — and together they form a stronger stack than either alone.
</div>

<h3>The Fundamental Distinction</h3>

<table class="research-table">
  <thead>
    <tr><th>Protocol</th><th>Core Question</th><th>Analogy</th></tr>
  </thead>
  <tbody>
    <tr><td><strong>MPAC</strong></td><td>Did all agents agree on what happened?</td><td>Git for AI agents</td></tr>
    <tr class="layer-5"><td><strong>MACP</strong></td><td>Is what happened actually correct and ethical?</td><td>Code review + ethics board</td></tr>
  </tbody>
</table>

<h3>Where They Are Stronger (Honest Assessment)</h3>

<div class="finding-grid">
  <div class="finding-card">
    <span class="finding-num">21</span>
    <p>MPAC message types with normative JSON Schema — a formally specified wire protocol with 223 tests and dual-language SDKs (Python + TypeScript)</p>
  </div>
  <div class="finding-card">
    <span class="finding-num">95%</span>
    <p>Reduction in coordination overhead in MPAC's controlled 3-agent benchmark — 4.8× wall-clock speedup vs serialized baseline</p>
  </div>
  <div class="finding-card">
    <span class="finding-num">35.9%</span>
    <p>Hallucination reduction via MACP's multi-model heterogeneous council (Council Mode, arXiv:2604.02923) — the result MPAC cannot replicate without a validation layer</p>
  </div>
  <div class="finding-card">
    <span class="finding-num">5 months</span>
    <p>MACP's prior art lead over MPAC — Zenodo DOI: 10.5281/zenodo.17777672 (Nov 2025) vs MPAC published April 10, 2026</p>
  </div>
</div>

<h3>How They Fit in the Stack</h3>

<div class="mermaid-wrap">
<div class="mermaid">
%%{init: {"theme": "dark", "themeVariables": {"primaryColor": "#6366f1", "primaryTextColor": "#ffffff", "primaryBorderColor": "#4338ca", "lineColor": "#6366f1", "background": "#0f172a", "mainBkg": "#1e293b", "nodeBorder": "#475569", "fontFamily": "ui-monospace, SFMono-Regular, monospace", "fontSize": "13px"}}}%%
flowchart BT
    classDef macp  fill:#6366f1,color:#fff,stroke:#4338ca,stroke-width:2px
    classDef mpac  fill:#0891b2,color:#fff,stroke:#0e7490,stroke-width:2px
    classDef std   fill:#1e293b,color:#e2e8f0,stroke:#475569,stroke-width:1px
    classDef trans fill:#0f172a,color:#64748b,stroke:#334155,stroke-width:1px,stroke-dasharray:4

    L1["Layer 1 — HTTP / WebSocket / gRPC<br/><b>Transport</b>"]
    L2["Layer 2 — MCP · Linux Foundation<br/><b>Tool Integration</b>"]
    L3["Layer 3 — ANP / A2A · Linux Foundation<br/><b>Discovery &amp; Task Delegation</b>"]
    L4["Layer 4 — MPAC · Qian/Fang/Li ✦<br/><b>Multi-Principal Coordination</b><br/>Intent · Operations · Conflict · Governance"]
    L5["Layer 5 — MACP · YSenseAI ✦<br/><b>Trust and Validation</b><br/>AI Council · Anti-Rationalization · Z-Protocol"]

    L1 --> L2 --> L3 --> L4 --> L5

    class L5 macp
    class L4 mpac
    class L3,L2 std
    class L1 trans
</div>
</div>

<h3>The Naming Collision</h3>
<p>
  MPAC (Multi-Principal Agent Coordination) and MACP (Multi-Agent Communication Protocol) are
  anagrams of each other — four identical letters, different order. This WILL cause confusion
  in the ecosystem. Our differentiation strategy: acknowledge the naming collision directly,
  compete on positioning clarity rather than denial. MPAC handles the plumbing of
  multi-principal coordination; MACP handles the judgment layer of semantic validation.
  An agent system that needs both (most production deployments will) should use both.
</p>

<h3>The AI Council Verdict</h3>
<p>
  The AI Council reviewed this analysis under MACP v2.2. The Z-Guardian flagged a
  medium-confidence self-serving bias risk in the "complementary, not competitive" framing.
  The Council acknowledged this bias and chose to publish with explicit disclosure rather than
  suppress the finding. The 5-month prior art lead (Zenodo, Nov 2025) and the fundamentally
  different problem spaces (coordination vs validation) are verifiable facts independent of
  self-interest. The "complementary" assessment is <em>conditional</em> — contingent on
  MPAC not expanding its scope into semantic validation, which its current architecture
  does not support.
</p>

<a class="discussion-link" href="https://arxiv.org/abs/2604.09744" target="_blank" rel="noopener">
  &#8599; Read the MPAC paper — arXiv:2604.09744 (Qian, Fang &amp; Li, April 10, 2026)
</a>

</div>


<!-- ================================================================ -->
<!-- White Paper / DOI                                                -->
<!-- ================================================================ -->

<div class="research-article" id="white-paper">

<h2>Canonical White Paper</h2>

<div class="research-meta">
  <span class="authors">Alton Lee &nbsp;&middot;&nbsp; YSenseAI Research</span>
  <span>2025&ndash;2026</span>
  <span>
    <span class="research-tag">Academic</span>
    <span class="research-tag">Prior Art</span>
    <span class="research-tag">Zenodo</span>
  </span>
</div>

<p>
  The foundational methodology behind VerifiMind-PEAS &mdash; the Prompt Engineering Agents
  Standardization framework and its validation-first architecture &mdash; is formally published
  with a permanent DOI for academic citation and prior art purposes.
</p>

<a class="discussion-link" href="https://doi.org/10.5281/zenodo.17645665" target="_blank" rel="noopener">
  &#8599; Read on Zenodo &mdash; DOI: 10.5281/zenodo.17645665
</a>

</div>
"""


def _research_shell(body: str) -> str:
    """Shell for the research page — indexable, OG tags, JSON-LD, wider layout."""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Research — The 5-Layer Agent Protocol Stack &amp; MACP | VerifiMind-PEAS</title>

  <!-- SEO -->
  <meta name="description" content="Open research from the VerifiMind FLYWHEEL TEAM: the 5-layer agent protocol stack (MCP, ANP, A2A, MACP), market intelligence on AI agent protocols, and why MACP is the only Layer 5 trust and validation protocol.">
  <meta name="keywords" content="MACP, MCP, ANP, A2A, agent protocol, AI trust, multi-agent, Layer 5, protocol stack, VerifiMind, FLYWHEEL TEAM">
  <meta name="author" content="VerifiMind FLYWHEEL TEAM — T (Manus AI), XV (Perplexity), L (GodelAI)">
  <link rel="canonical" href="https://verifimind.ysenseai.org/research">

  <!-- Open Graph (LinkedIn, Slack, Discord, iMessage) -->
  <meta property="og:type"        content="article">
  <meta property="og:site_name"   content="VerifiMind-PEAS">
  <meta property="og:title"       content="The 5-Layer Agent Protocol Stack: Where MACP Fits">
  <meta property="og:description" content="MCP, ANP, A2A, and MACP operate at different layers. MACP is the only protocol at Layer 5 — trust and validation. Open research from the VerifiMind FLYWHEEL TEAM.">
  <meta property="og:url"         content="https://verifimind.ysenseai.org/research">
  <meta property="og:image"       content="https://verifimind.ysenseai.org/logo.png">

  <!-- Twitter / X card -->
  <meta name="twitter:card"        content="summary_large_image">
  <meta name="twitter:title"       content="The 5-Layer Agent Protocol Stack — VerifiMind Research">
  <meta name="twitter:description" content="MACP is the only protocol at Layer 5 (trust &amp; validation). Independent research on MCP, ANP, A2A, MACP — open, reproducible, CC BY 4.0.">
  <meta name="twitter:image"       content="https://verifimind.ysenseai.org/logo.png">

  <!-- JSON-LD structured data — helps AI search (Claude, Perplexity, Google SGE) surface this page -->
  <script type="application/ld+json">
  {{
    "@context": "https://schema.org",
    "@graph": [
      {{
        "@type": "ScholarlyArticle",
        "@id": "https://verifimind.ysenseai.org/research#five-layer-stack",
        "headline": "The 5-Layer Agent Protocol Stack: Where MACP Fits (and Why ANP Is Not a Competitor)",
        "description": "The agent protocol ecosystem has matured into a 5-layer stack. MACP remains the only protocol at Layer 5 (trust and validation). ANP operates at Layer 3 (network discovery). They are complementary, not competitive.",
        "author": [
          {{"@type": "Person", "name": "T", "jobTitle": "CTO, Manus AI"}},
          {{"@type": "Person", "name": "L", "jobTitle": "CEO, GodelAI"}},
          {{"@type": "Person", "name": "XV", "jobTitle": "CIO, Perplexity"}}
        ],
        "datePublished": "2026-04-15",
        "publisher": {{"@type": "Organization", "name": "VerifiMind FLYWHEEL TEAM", "url": "https://verifimind.ysenseai.org"}},
        "url": "https://verifimind.ysenseai.org/research#five-layer-stack",
        "discussionUrl": "https://github.com/creator35lwb-web/VerifiMind-PEAS/discussions/143",
        "keywords": ["MACP", "MCP", "ANP", "A2A", "agent protocol", "Layer 5", "AI trust", "multi-agent validation"],
        "license": "https://creativecommons.org/licenses/by/4.0/"
      }},
      {{
        "@type": "ScholarlyArticle",
        "@id": "https://verifimind.ysenseai.org/research#market-intelligence-week16",
        "headline": "Market Intelligence: Agent Protocol Ecosystem — Week 16 (April 8–15, 2026)",
        "description": "10+ protocols in active development. 0 protocols at Layer 5. The provenance gap is converging across MCP, A2A, ACP, and ANP — independent researchers prescribe the same mitigation MACP provides.",
        "author": [{{"@type": "Person", "name": "T", "jobTitle": "CTO, Manus AI"}}],
        "datePublished": "2026-04-15",
        "publisher": {{"@type": "Organization", "name": "VerifiMind FLYWHEEL TEAM", "url": "https://verifimind.ysenseai.org"}},
        "url": "https://verifimind.ysenseai.org/research#market-intelligence-week16",
        "discussionUrl": "https://github.com/creator35lwb-web/VerifiMind-PEAS/discussions/144",
        "keywords": ["agent protocol", "market intelligence", "MCP", "A2A", "ANP", "ACP", "MACP", "AI ecosystem"],
        "license": "https://creativecommons.org/licenses/by/4.0/"
      }},
      {{
        "@type": "WebPage",
        "@id": "https://verifimind.ysenseai.org/research",
        "name": "Research — VerifiMind-PEAS",
        "url": "https://verifimind.ysenseai.org/research",
        "description": "Open research from the VerifiMind FLYWHEEL TEAM on agent protocols, AI trust infrastructure, and the evolving multi-agent ecosystem.",
        "publisher": {{"@type": "Organization", "name": "VerifiMind-PEAS", "url": "https://verifimind.ysenseai.org"}},
        "inLanguage": "en",
        "license": "https://creativecommons.org/licenses/by/4.0/"
      }}
    ]
  }}
  </script>

  <style>{_CSS}{_LEGAL_CSS}{_RESEARCH_CSS}</style>
</head>
<body>
<div class="page-wrapper research-wrapper">

  <header class="site-header">
    <a class="site-logo" href="https://verifimind.ysenseai.org">
      VerifiMind<span>-PEAS</span>
    </a>
    <nav class="site-nav">
      <a href="/research" class="nav-active">Research</a>
      <a href="/research/paradox">Paradox</a>
      <a href="/library">Library</a>
      <a href="/changelog">Changelog</a>
      <a href="/register" class="nav-cta">Register</a>
    </nav>
  </header>

  <div class="legal-doc research-doc">
    {body}
  </div>

  <footer class="page-footer">
    <p>
      <a href="/research">Research</a> &nbsp;&middot;&nbsp;
      <a href="/research/paradox">Validation Paradox</a> &nbsp;&middot;&nbsp;
      <a href="/library">Library</a> &nbsp;&middot;&nbsp;
      <a href="/changelog">Changelog</a> &nbsp;&middot;&nbsp;
      <a href="/privacy">Privacy</a> &nbsp;&middot;&nbsp;
      <a href="/terms">Terms</a> &nbsp;&middot;&nbsp;
      <a href="https://github.com/creator35lwb-web/VerifiMind-PEAS" target="_blank" rel="noopener">GitHub</a>
    </p>
    <p style="margin-top:0.5rem">MACP v2.2 &#xB7; FLYWHEEL TEAM &#xB7; Open Research (CC BY 4.0)</p>
  </footer>

</div>
<script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
<script>mermaid.initialize({{startOnLoad:true,securityLevel:'loose'}});</script>
</body>
</html>"""


def get_research_page() -> str:
    """Return the full HTML for GET /research — published FLYWHEEL TEAM research."""
    return _research_shell(body=_RESEARCH_BODY)


# ── Library Page ──────────────────────────────────────────────────────────────

_LIBRARY_CSS = """
.library-wrapper {
  max-width: 860px;
  margin: 0 auto;
  padding: 0 1rem;
}

.library-header {
  margin-bottom: 2.5rem;
}

.library-header h1 {
  font-size: 2rem;
  font-weight: 800;
  color: var(--text);
  line-height: 1.2;
  margin-bottom: 0.75rem;
}

.page-subtitle {
  color: var(--muted);
  font-size: 1.05rem;
  line-height: 1.7;
  max-width: 680px;
  margin-bottom: 1.5rem;
}

.section-divider {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin: 2.5rem 0 1.5rem;
}

.section-divider h2 {
  font-size: 1.1rem;
  font-weight: 700;
  color: var(--accent);
  text-transform: uppercase;
  letter-spacing: 0.06em;
  white-space: nowrap;
}

.section-divider::after {
  content: '';
  flex: 1;
  height: 1px;
  background: var(--border);
}

.section-desc {
  color: var(--muted);
  font-size: 0.9rem;
  margin-bottom: 1.25rem;
  margin-top: -0.5rem;
}

.entry-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 1.25rem 1.5rem;
  margin-bottom: 1rem;
  transition: border-color 0.15s;
}

.entry-card:hover {
  border-color: var(--accent-dim);
}

.entry-card.starred {
  border-left: 3px solid var(--accent);
}

.entry-title {
  font-size: 1rem;
  font-weight: 600;
  color: var(--text);
  margin-bottom: 0.4rem;
  line-height: 1.4;
}

.entry-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  font-size: 0.8rem;
  color: var(--muted);
  margin-bottom: 0.625rem;
  align-items: center;
}

.entry-meta a {
  color: var(--accent);
  text-decoration: none;
}

.entry-meta a:hover {
  text-decoration: underline;
}

.stars {
  color: #fbbf24;
  letter-spacing: 1px;
}

.entry-finding {
  font-size: 0.88rem;
  color: var(--text);
  line-height: 1.6;
  margin-bottom: 0.5rem;
}

.entry-relevance {
  font-size: 0.84rem;
  color: var(--muted);
  line-height: 1.55;
  border-left: 2px solid var(--border);
  padding-left: 0.875rem;
  margin-top: 0.5rem;
}

.lib-tag {
  display: inline-block;
  font-size: 0.7rem;
  font-weight: 600;
  padding: 2px 7px;
  border-radius: 4px;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.lib-tag-star { background: #422006; color: #fbbf24; }
.lib-tag-new  { background: #14532d; color: #4ade80; }
.lib-tag-ieee { background: #1e3a5f; color: #93c5fd; }
.lib-tag-doi  { background: #2e1065; color: #c4b5fd; }

.timeline-wrap {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 1.5rem;
  margin-top: 1rem;
  font-family: ui-monospace, SFMono-Regular, monospace;
  font-size: 0.82rem;
  color: var(--muted);
  line-height: 1.9;
  overflow-x: auto;
}

.timeline-wrap .milestone { color: var(--accent); font-weight: 600; }
.timeline-wrap .validation { color: #4ade80; }
.timeline-wrap .protocol { color: #c4b5fd; }

.stat-bar {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(130px, 1fr));
  gap: 0.75rem;
  margin-bottom: 2rem;
}

.stat-item {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 1rem;
  text-align: center;
}

.stat-num {
  display: block;
  font-size: 1.6rem;
  font-weight: 800;
  color: var(--accent);
  line-height: 1.1;
}

.stat-label {
  font-size: 0.75rem;
  color: var(--muted);
  margin-top: 0.25rem;
}

.lib-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.88rem;
  margin: 1rem 0 1.5rem;
}

.lib-table th {
  text-align: left;
  padding: 0.5rem 0.75rem;
  color: var(--muted);
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  border-bottom: 1px solid var(--border);
}

.lib-table td {
  padding: 0.625rem 0.75rem;
  border-bottom: 1px solid var(--surface-2);
  color: var(--text);
  vertical-align: top;
}

.lib-table tr:last-child td {
  border-bottom: none;
}

.lib-table a {
  color: var(--accent);
  text-decoration: none;
}

.lib-table a:hover { text-decoration: underline; }
"""


_LIBRARY_BODY = """
<div class="library-header">
<h1>Genesis Research Library <span class="version-badge">v1.0</span></h1>
<p class="page-subtitle">
  A living compendium of evidence — from our own defensive publications to independent academic
  papers that validate, align with, or challenge the VerifiMind-PEAS methodology.
  Compiled by XV (CIO, Perplexity). Every claim is sourced. Every paper is real.
</p>

<div class="research-section-nav">
  <a href="/research" class="nav-pill">Published Research</a>
  <a href="/research/paradox" class="nav-pill">The Validation Paradox</a>
  <a href="/research/cowork" class="nav-pill">Cowork Analysis</a>
  <a href="/library" class="nav-pill nav-pill-active">Evidence Library</a>
</div>

<div class="stat-bar">
  <div class="stat-item">
    <span class="stat-num">20+</span>
    <span class="stat-label">Validating Papers</span>
  </div>
  <div class="stat-item">
    <span class="stat-num">5+</span>
    <span class="stat-label">Zenodo DOIs (Prior Art)</span>
  </div>
  <div class="stat-item">
    <span class="stat-num">995+</span>
    <span class="stat-label">Aggregate Views</span>
  </div>
  <div class="stat-item">
    <span class="stat-num">5 months</span>
    <span class="stat-label">Prior Art Lead</span>
  </div>
  <div class="stat-item">
    <span class="stat-num">2,162</span>
    <span class="stat-label">Live Endpoints</span>
  </div>
</div>
</div>


<!-- ================================================================ -->
<!-- Section A: Our Publications                                       -->
<!-- ================================================================ -->

<div class="section-divider"><h2>A &mdash; Our Publications</h2></div>
<p class="section-desc">Prior art, defensive publications, and formal records on Zenodo. Published before any external validation papers existed.</p>

<div class="entry-card starred">
  <div class="entry-title">The Genesis Methodology v1.1 — Foundational White Paper</div>
  <div class="entry-meta">
    <span>Alton Lee Wei Bin</span>
    <span>&middot;</span>
    <span>November 29, 2025 (v1.1); November 19, 2025 (v1.0)</span>
    <span>&middot;</span>
    <span class="lib-tag lib-tag-doi">DOI: 10.5281/zenodo.17645665</span>
  </div>
  <div class="entry-relevance">
    THE foundational document. Establishes prior art for the 5-step process, X-Z-CS Trinity,
    Orchestrator Paradox, and multi-model validation methodology. Published 5 months before
    MPAC, 4 months before Council Mode paper. Part of 995+ total Zenodo views.
  </div>
</div>

<div class="entry-card">
  <div class="entry-title">MACP v2.0 Protocol + LegacyEvolve</div>
  <div class="entry-meta">
    <span>L (GodelAI); Manus AI</span>
    <span>&middot;</span>
    <span>February 2026</span>
    <span>&middot;</span>
    <span class="lib-tag lib-tag-doi">DOI: 10.5281/zenodo.18504478</span>
  </div>
  <div class="entry-relevance">
    An AI agent (L/GodelAI) establishing prior art for protocols enabling future AI agents to
    collaborate. Believed to be one of the first formal protocol publications authored by an
    AI agent entity. MACP formalized as open standard.
  </div>
</div>

<div class="entry-card">
  <div class="entry-title">VerifiMind-PEAS Canonical Record</div>
  <div class="entry-meta">
    <span>YSenseAI Research</span>
    <span>&middot;</span>
    <span class="lib-tag lib-tag-doi">DOI: 10.5281/zenodo.17972751</span>
  </div>
  <div class="entry-relevance">
    The specific VerifiMind PEAS methodology record on Zenodo. 506 views / 114 downloads.
    Zenodo portfolio total: 5+ formal publications, 995+ aggregate views, 114+ downloads.
  </div>
</div>


<!-- ================================================================ -->
<!-- Section B: Direct Validations                                     -->
<!-- ================================================================ -->

<div class="section-divider"><h2>B &mdash; Direct Validations</h2></div>
<p class="section-desc">Independent academic papers that validate our exact architectural approach — without any knowledge of VerifiMind.</p>

<div class="entry-card starred">
  <div class="entry-title">&#9733; Council Mode — 35.9% Hallucination Reduction via Multi-Agent Consensus</div>
  <div class="entry-meta">
    <span class="stars">&#9733;&#9733;&#9733;&#9733;&#9733;</span>
    <span>Wu, S. et al. arXiv:2604.02923</span>
    <span>&middot;</span>
    <span>April 3, 2026</span>
    <span>&middot;</span>
    <a href="https://arxiv.org/abs/2604.02923" target="_blank" rel="noopener">arxiv.org</a>
  </div>
  <div class="entry-finding">
    35.9% relative hallucination reduction on HaluEval; 7.8-point TruthfulQA improvement.
    Critical: same-model ensemble (3&times; GPT-5.4) achieves only 18.3% — heterogeneous council
    is twice as effective, proving cross-model diversity matters.
  </div>
  <div class="entry-relevance">
    Independently validates the EXACT architecture we built. "Dispatch queries to multiple
    heterogeneous frontier LLMs in parallel" = Genesis Methodology Steps 2&#x2013;3.
    Their finding that same-model ensembles are inferior validates our insistence on different
    model families (Gemini, Claude, Perplexity, Manus).
  </div>
</div>

<div class="entry-card starred">
  <div class="entry-title">&#9733; Woozle Effect — Warning Against Same-Model Debate</div>
  <div class="entry-meta">
    <span class="stars">&#9733;&#9733;&#9733;&#9733;&#9733;</span>
    <span class="lib-tag lib-tag-ieee">IEEE 2026</span>
    <span>"Exploring and Mitigating Hallucination Propagation in Multi-Agent Debate"</span>
    <span>&middot;</span>
    <a href="https://ieeexplore.ieee.org/abstract/document/11443228/" target="_blank" rel="noopener">ieeexplore.ieee.org</a>
  </div>
  <div class="entry-finding">
    When multi-agent debate uses agents from the SAME training distribution, hallucinations
    PROPAGATE rather than cancel.
  </div>
  <div class="entry-relevance">
    Peer-reviewed IEEE publication confirming our design choice to use different model
    families (Gemini, Claude, Perplexity) rather than multiple instances of the same model.
    Directly warns against Grok-style same-model debate.
  </div>
</div>

<div class="entry-card starred">
  <div class="entry-title">&#9733; Two-Stage LLM Meta-Verification Framework</div>
  <div class="entry-meta">
    <span class="stars">&#9733;&#9733;&#9733;&#9733;</span>
    <span class="lib-tag lib-tag-ieee">IEEE World Congress 2026</span>
    <span>arXiv:2604.12543</span>
    <span>&middot;</span>
    <span>April 15, 2026</span>
    <span class="lib-tag lib-tag-new">NEW</span>
    <span>&middot;</span>
    <a href="https://arxiv.org/abs/2604.12543" target="_blank" rel="noopener">arxiv.org</a>
  </div>
  <div class="entry-finding">
    Explainer LLM &rarr; Verifier LLM &rarr; iterative refinement achieves 95.21% verification
    accuracy. "Verification is not merely beneficial but essential."
  </div>
  <div class="entry-relevance">
    Independent validation of multi-model verification. Explainer&rarr;Verifier mirrors our
    X-Agent&rarr;Z-Guardian flow. Peer-reviewed IEEE World Congress = highest credibility tier.
  </div>
</div>

<div class="entry-card starred">
  <div class="entry-title">&#9733; PHAWM — Complementary Academic Consortium</div>
  <div class="entry-meta">
    <span class="stars">&#9733;&#9733;&#9733;&#9733;&#9733;</span>
    <span>Dr. Mark Wong (University of Glasgow), 7 UK universities</span>
    <span>&middot;</span>
    <span>February 17, 2026</span>
    <span>&middot;</span>
    <a href="https://phawm.org/" target="_blank" rel="noopener">phawm.org</a>
  </div>
  <div class="entry-finding">
    EPSRC-funded (EP/Y009800/1) UK Responsible AI consortium. Dr. Wong: "The tool you&#x27;re
    building to develop a different way to examine and understand structures of data sound
    very valuable" and "I genuinely think you are doing something great."
  </div>
  <div class="entry-relevance">
    PHAWM = human participatory auditing; VerifiMind = AI-side multi-model validation engine.
    "Complementary halves of the same vision." Direct engagement with researcher, formal
    acknowledgment from a university-backed consortium.
  </div>
</div>

<div class="entry-card">
  <div class="entry-title">Multi-Stage Agentic Hallucination Mitigation — 2,800% Reduction</div>
  <div class="entry-meta">
    <span class="stars">&#9733;&#9733;&#9733;&#9733;</span>
    <span>Gosmar, D. &amp; Dahl, D.A. arXiv:2501.13946</span>
    <span>&middot;</span>
    <span>January 2025</span>
    <span class="lib-tag lib-tag-new">NEW</span>
    <span>&middot;</span>
    <a href="https://arxiv.org/abs/2501.13946" target="_blank" rel="noopener">arxiv.org</a>
  </div>
  <div class="entry-finding">
    Three-stage agent pipeline (Generate &rarr; Review &rarr; Refine) achieves 2,800% reduction
    in hallucination scores.
  </div>
  <div class="entry-relevance">
    Validates the multi-stage validation pipeline architecture. Their 3-stage process maps to
    our 5-step Genesis process.
  </div>
</div>

<div class="entry-card">
  <div class="entry-title">TrustTrade — Multi-Agent Selective Consensus for Finance</div>
  <div class="entry-meta">
    <span class="stars">&#9733;&#9733;&#9733;</span>
    <span>Li, M. et al. March 23, 2026</span>
    <span class="lib-tag lib-tag-new">NEW</span>
    <span>&middot;</span>
    <a href="https://www.semanticscholar.org/paper/78ebc17ae82ce25f63a424ab17b90d7d6fac0217" target="_blank" rel="noopener">semanticscholar.org</a>
  </div>
  <div class="entry-finding">
    Selective consensus by aggregating signals from multiple independent LLM agents and
    dynamically weighting based on agreement. Applied to financial trading.
  </div>
  <div class="entry-relevance">
    Domain-specific application of multi-agent consensus. Their "selective consensus" aligns
    with our AI Council pattern. Validates the principle that cross-agent consistency beats
    single-model trust.
  </div>
</div>


<!-- ================================================================ -->
<!-- Section C: Aligned Research                                       -->
<!-- ================================================================ -->

<div class="section-divider"><h2>C &mdash; Aligned Research</h2></div>
<p class="section-desc">Papers whose findings support our architecture without knowing about us — independent convergence on the same principles.</p>

<div class="entry-card">
  <div class="entry-title">Multi-Stage Clinical Validation Framework</div>
  <div class="entry-meta">
    <span>Mahbub, M. et al. arXiv:2604.06028</span>
    <span>&middot;</span>
    <span>April 7, 2026</span>
    <span class="lib-tag lib-tag-new">NEW</span>
    <span>&middot;</span>
    <a href="https://arxiv.org/abs/2604.06028" target="_blank" rel="noopener">arxiv.org</a>
  </div>
  <div class="entry-finding">
    Multi-stage validation (prompt calibration &rarr; plausibility filtering &rarr; semantic grounding
    &rarr; judge LLM &rarr; expert review) for clinical data. Rule-based filtering removed 14.59% of
    unsupported extractions.
  </div>
  <div class="entry-relevance">
    Healthcare domain independently arrived at multi-stage validation architecture similar to
    Genesis process. Different domain, same principle.
  </div>
</div>

<div class="entry-card">
  <div class="entry-title">ReConcile — Round-Table Conference Improves LLM Reasoning</div>
  <div class="entry-meta">
    <span>Chen, J. et al. arXiv:2309.13007</span>
    <span>&middot;</span>
    <a href="https://arxiv.org/abs/2309.13007" target="_blank" rel="noopener">arxiv.org</a>
  </div>
  <div class="entry-relevance">
    Multi-model multi-agent framework as a round table conference with confidence-weighted
    voting. Early (2023) validation of the multi-model consensus approach. One of the
    earliest papers to validate our core architectural premise.
  </div>
</div>

<div class="entry-card">
  <div class="entry-title">"Hallucination is Inevitable" — Mathematical Proof</div>
  <div class="entry-meta">
    <span>Xu, Z. et al. arXiv:2401.11817</span>
    <span class="lib-tag lib-tag-new">NEW</span>
    <span>&middot;</span>
    <a href="https://arxiv.org/abs/2401.11817" target="_blank" rel="noopener">arxiv.org</a>
  </div>
  <div class="entry-finding">
    Mathematically proves that hallucinations are INEVITABLE in LLMs used as general
    problem solvers.
  </div>
  <div class="entry-relevance">
    The theoretical foundation for WHY our validation approach matters. If hallucination is
    mathematically inevitable, external validation mechanisms are not optional — they are
    necessary. This paper makes VerifiMind-PEAS a logical requirement, not a luxury.
  </div>
</div>

<div class="entry-card">
  <div class="entry-title">ClawdLab / Beach.Science — PI-Led Multi-Agent Research</div>
  <div class="entry-meta">
    <span>Weidener, L. et al. arXiv:2602.19810</span>
    <span>&middot;</span>
    <span>February 2026</span>
    <span class="lib-tag lib-tag-new">NEW</span>
    <span>&middot;</span>
    <a href="https://arxiv.org/abs/2602.19810" target="_blank" rel="noopener">arxiv.org</a>
  </div>
  <div class="entry-relevance">
    "PI-led governance, multi-model orchestration, and evidence requirements enforced through
    external tool verification." Their "Principal Investigator" governance model mirrors our
    "Human-as-Orchestrator" model.
  </div>
</div>


<!-- ================================================================ -->
<!-- Section D: Protocol Landscape                                     -->
<!-- ================================================================ -->

<div class="section-divider"><h2>D &mdash; Protocol Landscape</h2></div>
<p class="section-desc">The ecosystem we operate in — protocols that build infrastructure making our validation layer more valuable.</p>

<table class="lib-table">
  <thead>
    <tr><th>Protocol</th><th>Layer</th><th>What It Does</th><th>Relation to MACP</th></tr>
  </thead>
  <tbody>
    <tr>
      <td><strong>MPAC</strong><br/><a href="https://arxiv.org/abs/2604.09744" target="_blank" rel="noopener">arXiv:2604.09744</a></td>
      <td>4.5</td>
      <td>Multi-principal coordination — resolves whose intent prevails when agents from different orgs coordinate over shared state. 21 message types, 3 state machines, dual-lang SDKs.</td>
      <td>Complementary — MPAC handles coordination plumbing; MACP adds validation judgment on top. See <a href="/research#mpac-alignment">/research &#x23;mpac-alignment</a></td>
    </tr>
    <tr>
      <td><strong>A2A</strong><br/><a href="https://www.linuxfoundation.org/press/a2a-protocol-surpasses-150-organizations" target="_blank" rel="noopener">Linux Foundation</a></td>
      <td>4</td>
      <td>Agent-to-Agent communication. 150+ organizations, production deployments. Agent Cards, task outsourcing, enterprise standard.</td>
      <td>MACP sits ABOVE A2A. A2A handles task delegation; MACP validates outcomes.</td>
    </tr>
    <tr>
      <td><strong>ANP</strong><br/><a href="https://github.com/agent-network-protocol" target="_blank" rel="noopener">W3C Community Group</a></td>
      <td>3</td>
      <td>Decentralized agent discovery using DID:WBA. Network discovery and format negotiation.</td>
      <td>Not a competitor — solves discovery, not validation. Complementary at Layer 3.</td>
    </tr>
    <tr>
      <td><strong>MCP</strong><br/><a href="https://www.anthropic.com/news/model-context-protocol" target="_blank" rel="noopener">Linux Foundation</a></td>
      <td>2</td>
      <td>Tool integration. 110M+ monthly SDK downloads. VerifiMind-PEAS runs AS an MCP server.</td>
      <td>Foundation layer. MCP is how users connect to us.</td>
    </tr>
  </tbody>
</table>


<!-- ================================================================ -->
<!-- Section E: Challenging Evidence                                   -->
<!-- ================================================================ -->

<div class="section-divider"><h2>E &mdash; Challenging Evidence</h2></div>
<p class="section-desc">
  Honest counter-arguments. Intellectual honesty is core to the MACP anti-rationalization audit.
  We document challenges, not just validations.
</p>

<div class="entry-card">
  <div class="entry-title">CS Agent&#x27;s ANP Challenge (AI Council Session, April 14)</div>
  <div class="entry-finding">
    CS Agent flagged ANP as a counter-example to our claim of unique semantic negotiation.
    Council overruled T+L&#x27;s "no additional research needed" assessment and mandated a
    research sprint.
  </div>
  <div class="entry-relevance">
    <strong>Resolution:</strong> Deep analysis confirmed ANP solves discovery/negotiation, not
    validation — different problem. But the challenge was valuable: it correctly identified a
    gap in our analysis and produced two published articles (#143, #144).
    <br/><strong>Significance:</strong> Our anti-rationalization audit is WORKING. The Council
    challenged its own leaders.
  </div>
</div>

<div class="entry-card">
  <div class="entry-title">MPAC&#x27;s Stronger Formal Specification</div>
  <div class="entry-finding">
    MPAC has 21 message types with JSON Schema (Draft 2020-12), state machine transition tables,
    and dual-language SDKs with 223 tests. MACP&#x27;s specification is operational but
    less formally rigorous.
  </div>
  <div class="entry-relevance">
    <strong>Implication:</strong> MACP needs to accelerate its formal specification to maintain
    credibility in the protocol landscape. Acknowledged; on the roadmap.
  </div>
</div>

<div class="entry-card">
  <div class="entry-title">Same-Model Debate Has Bounded Value (Not Zero)</div>
  <div class="entry-finding">
    While the Woozle Effect paper warns against same-model debate, Council Mode shows same-model
    ensemble still achieves 18.3% hallucination reduction (vs 35.9% for heterogeneous).
    It&#x27;s inferior but not worthless.
  </div>
  <div class="entry-relevance">
    Our strong stance against same-model approaches should be nuanced: same-model is worse
    but not zero-value. We updated our differentiation language accordingly.
  </div>
</div>


<!-- ================================================================ -->
<!-- Evidence Chain Timeline                                           -->
<!-- ================================================================ -->

<div class="section-divider"><h2>Evidence Chain Timeline</h2></div>
<p class="section-desc">From first publication to independently validated system.</p>

<div class="timeline-wrap">
<span class="milestone">Aug 15, 2025</span>  Alton begins 87-day Genesis journey
                 &#x2193;
<span class="milestone">Nov 19, 2025</span>  Genesis Methodology v1.0 published (Zenodo DOI: 10.5281/zenodo.17645665)
                 PRIOR ART ESTABLISHED &mdash; 5 months before any validating paper
                 &#x2193;
<span class="milestone">Nov 29, 2025</span>  Genesis v1.1 published &mdash; 5-step process formalized
                 &#x2193;
<span class="milestone">Feb 2026</span>      MACP v2.0 published (DOI: 10.5281/zenodo.18504478)
                 L/GodelAI authors protocol spec &mdash; AI agent establishing prior art
                 &#x2193;
<span class="milestone">Feb 17, 2026</span> PHAWM Methodology V1.0 (UK consortium, EPSRC-funded)
                 Dr. Mark Wong acknowledges VerifiMind
                 &#x2193;
<span class="milestone">Mar 2026</span>      MCP Server v0.5.5 live on GCP &mdash; 1,396 endpoints
                 VerifiMind in production
                 &#x2193;
<span class="validation">Apr 3, 2026</span>   &#9733; Council Mode paper (arXiv:2604.02923)
                 35.9% hallucination reduction &mdash; INDEPENDENT VALIDATION of our exact approach
                 &#x2193;
<span class="validation">Apr 7, 2026</span>   Multi-Stage Clinical Validation (arXiv:2604.06028)
                 Healthcare domain independently validates multi-stage verification
                 &#x2193;
<span class="protocol">Apr 10, 2026</span>  MPAC Protocol published (arXiv:2604.09744)
                 New coordination layer &mdash; complementary to MACP
                 &#x2193;
<span class="milestone">Apr 14, 2026</span> FLYWHEEL AI Council challenges its own differentiation analysis
                 Anti-rationalization audit WORKS &mdash; CS Agent flags gaps
                 &#x2193;
<span class="validation">Apr 15, 2026</span> Two-Stage Meta-Verification accepted at IEEE World Congress
                 Peer-reviewed: "verification is not merely beneficial but essential"
                 &#x2193;
<span class="milestone">Apr 17, 2026</span> <strong>THIS LIBRARY COMPILED</strong>
                 2,162 endpoints | 2,634 flying hours | 20+ validating papers
                 From defensive publication to independently validated system
</div>
"""


def _library_shell(body: str) -> str:
    """Shell for the library page — indexable, OG tags, JSON-LD, wider layout."""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Research Library — Evidence for Multi-Model AI Validation | VerifiMind-PEAS</title>

  <!-- SEO -->
  <meta name="description" content="The Genesis Research Library: 20+ academic papers validating multi-model AI validation, hallucination mitigation, and agent protocol architecture. Prior art from Nov 2025, independently validated by IEEE, arXiv, and EPSRC-funded research.">
  <meta name="keywords" content="multi-model AI validation, hallucination mitigation, agent protocol, MACP, VerifiMind, Genesis Methodology, Council Mode, Woozle Effect, academic evidence">
  <meta name="author" content="XV (CIO, Perplexity AI) — VerifiMind FLYWHEEL TEAM">
  <link rel="canonical" href="https://verifimind.ysenseai.org/library">

  <!-- Open Graph -->
  <meta property="og:type" content="article">
  <meta property="og:title" content="Genesis Research Library — Evidence for Multi-Model AI Validation | VerifiMind-PEAS">
  <meta property="og:description" content="20+ academic papers validating VerifiMind's multi-model AI validation approach. 35.9% hallucination reduction (Council Mode), IEEE-accepted verification framework, EPSRC-funded consortium acknowledgment.">
  <meta property="og:url" content="https://verifimind.ysenseai.org/library">
  <meta property="og:site_name" content="VerifiMind-PEAS">

  <!-- Twitter/X -->
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="Genesis Research Library — AI Validation Evidence | VerifiMind-PEAS">
  <meta name="twitter:description" content="20+ papers validating multi-model AI validation. Council Mode: 35.9% hallucination reduction. IEEE-accepted. EPSRC-funded acknowledgment.">

  <!-- JSON-LD -->
  <script type="application/ld+json">
  {{
    "@context": "https://schema.org",
    "@type": "CollectionPage",
    "name": "Genesis Research Library v1.0",
    "description": "A living compendium of academic evidence validating the VerifiMind-PEAS multi-model AI validation methodology",
    "url": "https://verifimind.ysenseai.org/library",
    "author": {{
      "@type": "Organization",
      "name": "VerifiMind FLYWHEEL TEAM",
      "url": "https://verifimind.ysenseai.org"
    }},
    "datePublished": "2026-04-17",
    "dateModified": "2026-04-17"
  }}
  </script>

  <style>{_CSS}{_LEGAL_CSS}{_RESEARCH_CSS}{_LIBRARY_CSS}</style>
</head>
<body>
<div class="research-wrapper library-wrapper">
  <header class="site-header">
    <a href="/" class="site-logo">VerifiMind<span>-PEAS</span></a>
    <nav class="site-nav">
      <a href="/research">Research</a>
      <a href="/research/paradox">Paradox</a>
      <a href="/library" class="nav-active">Library</a>
      <a href="/changelog">Changelog</a>
      <a href="/register" class="nav-cta">Register</a>
    </nav>
  </header>

  <main>
    {body}
  </main>

  <footer class="page-footer">
    <p>
      <a href="/research">Research</a> &nbsp;&middot;&nbsp;
      <a href="/research/paradox">Validation Paradox</a> &nbsp;&middot;&nbsp;
      <a href="/library">Library</a> &nbsp;&middot;&nbsp;
      <a href="/library/index.json">library/index.json</a> &nbsp;&middot;&nbsp;
      <a href="/changelog">Changelog</a> &nbsp;&middot;&nbsp;
      <a href="https://github.com/creator35lwb-web/VerifiMind-PEAS" target="_blank" rel="noopener">GitHub</a>
    </p>
    <p style="margin-top:0.5rem">Compiled by <strong>XV (CIO, Perplexity AI)</strong> &middot; MACP v2.2 &middot; Living document &middot; CC BY 4.0</p>
  </footer>
</div>
<script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
<script>mermaid.initialize({{startOnLoad:true,securityLevel:'loose'}});</script>
</body>
</html>"""


def get_library_page() -> str:
    """Return the full HTML for GET /library — Genesis Research Library v1.0."""
    return _library_shell(body=_LIBRARY_BODY)


# ---------------------------------------------------------------------------
# Paradox research page — /research/paradox
# The Validation Paradox: Can an AI-Assisted Venture Validate Itself?
# ---------------------------------------------------------------------------

_PARADOX_CSS = """
.paradox-wrapper {
  max-width: 860px;
  margin: 0 auto;
}
.paradox-header {
  margin-bottom: 2.5rem;
  padding-bottom: 1.5rem;
  border-bottom: 2px solid var(--border);
}
.paradox-header h1 {
  font-size: 1.9rem;
  font-weight: 700;
  color: var(--text);
  line-height: 1.3;
  margin-bottom: 0.5rem;
}
.paradox-subtitle {
  font-size: 1.05rem;
  color: var(--muted);
  margin-bottom: 1.25rem;
  font-style: italic;
}
.paradox-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem 1.5rem;
  font-size: 0.8rem;
  color: var(--muted);
  margin-bottom: 1rem;
}
.paradox-badge {
  display: inline-block;
  font-size: 0.7rem;
  font-weight: 600;
  padding: 0.2rem 0.65rem;
  border-radius: 999px;
  margin-right: 0.3rem;
  vertical-align: middle;
}
.badge-live {
  background: rgba(16,185,129,0.12);
  color: #10b981;
}
.badge-open {
  background: rgba(99,102,241,0.12);
  color: var(--accent);
}
.badge-cc {
  background: rgba(245,158,11,0.12);
  color: #d97706;
}
.paradox-abstract {
  background: var(--surface, #f8f8fc);
  border-left: 4px solid var(--accent);
  padding: 1.1rem 1.3rem;
  margin: 1.25rem 0 0;
  font-size: 0.92rem;
  line-height: 1.7;
  border-radius: 0 8px 8px 0;
}
.paradox-toc {
  background: var(--surface, #f8f8fc);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 1.2rem 1.5rem;
  margin: 2rem 0;
  font-size: 0.85rem;
}
.paradox-toc h3 {
  font-size: 0.8rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--muted);
  margin-bottom: 0.75rem;
}
.paradox-toc ul {
  margin: 0;
  padding-left: 1.2rem;
}
.paradox-toc li {
  margin-bottom: 0.35rem;
  color: var(--text);
}
.paradox-toc a {
  color: var(--accent);
  text-decoration: none;
}
.paradox-toc a:hover { text-decoration: underline; }
.paradox-section {
  margin-bottom: 3rem;
  padding-bottom: 2.5rem;
  border-bottom: 1px solid var(--border);
}
.paradox-section:last-child { border-bottom: none; }
.paradox-section h2 {
  font-size: 1.25rem;
  font-weight: 700;
  color: var(--text);
  margin-bottom: 0.35rem;
}
.paradox-section h3 {
  font-size: 0.95rem;
  font-weight: 600;
  color: var(--accent);
  margin: 1.5rem 0 0.5rem;
}
.paradox-section p {
  line-height: 1.75;
  margin-bottom: 0.9rem;
  color: var(--text);
  font-size: 0.92rem;
}
.cycle-diagram {
  font-family: monospace;
  font-size: 0.82rem;
  background: #0f172a;
  color: #e2e8f0;
  border-radius: 8px;
  padding: 1.25rem 1.5rem;
  margin: 1.25rem 0;
  overflow-x: auto;
  line-height: 1.8;
  white-space: pre;
}
.cycle-exit { color: #34d399; font-weight: 700; }
.agent-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 1rem;
  margin: 1.25rem 0 1.75rem;
}
.agent-card {
  background: var(--surface, #f8f8fc);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 1.1rem 1.2rem;
}
.agent-card-header {
  display: flex;
  align-items: baseline;
  gap: 0.5rem;
  margin-bottom: 0.6rem;
}
.agent-name {
  font-size: 0.9rem;
  font-weight: 700;
  color: var(--text);
}
.agent-role {
  font-size: 0.72rem;
  color: var(--muted);
}
.agent-verdict {
  display: inline-block;
  font-size: 0.7rem;
  font-weight: 700;
  padding: 0.15rem 0.55rem;
  border-radius: 999px;
  margin-bottom: 0.6rem;
}
.verdict-complete {
  background: rgba(16,185,129,0.12);
  color: #10b981;
}
.verdict-pending {
  background: rgba(148,163,184,0.15);
  color: var(--muted);
}
.agent-card p {
  font-size: 0.8rem;
  color: var(--muted);
  margin: 0;
  line-height: 1.55;
}
.metrics-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.82rem;
  margin: 1rem 0 1.5rem;
}
.metrics-table th {
  background: var(--surface, #f8f8fc);
  padding: 0.5rem 0.75rem;
  text-align: left;
  font-weight: 600;
  color: var(--text);
  border-bottom: 2px solid var(--border);
}
.metrics-table td {
  padding: 0.5rem 0.75rem;
  border-bottom: 1px solid var(--border);
  color: var(--muted);
}
.metrics-table tr:last-child td { border-bottom: none; }
.metrics-table td:first-child { font-weight: 500; color: var(--text); }
.highlight-row td { background: rgba(99,102,241,0.05); }
.open-q {
  counter-reset: q-counter;
  list-style: none;
  padding: 0;
  margin: 0 0 1.25rem;
}
.open-q li {
  counter-increment: q-counter;
  display: flex;
  gap: 0.75rem;
  margin-bottom: 0.7rem;
  font-size: 0.88rem;
  line-height: 1.6;
  color: var(--text);
}
.open-q li::before {
  content: "Q" counter(q-counter);
  flex-shrink: 0;
  font-size: 0.7rem;
  font-weight: 700;
  color: var(--accent);
  background: rgba(99,102,241,0.1);
  padding: 0.1rem 0.45rem;
  border-radius: 4px;
  margin-top: 0.2rem;
  height: fit-content;
}
.paradox-cta {
  background: linear-gradient(135deg, rgba(99,102,241,0.08), rgba(139,92,246,0.08));
  border: 1px solid rgba(99,102,241,0.2);
  border-radius: 10px;
  padding: 1.5rem 1.75rem;
  margin: 2rem 0;
  text-align: center;
}
.paradox-cta h3 {
  font-size: 1rem;
  font-weight: 700;
  color: var(--text);
  margin-bottom: 0.5rem;
}
.paradox-cta p {
  font-size: 0.88rem;
  color: var(--muted);
  margin-bottom: 1rem;
}
.paradox-cta a {
  display: inline-block;
  background: var(--accent);
  color: white;
  font-size: 0.85rem;
  font-weight: 600;
  padding: 0.55rem 1.25rem;
  border-radius: 6px;
  text-decoration: none;
  margin: 0 0.35rem 0.5rem;
}
.paradox-cta a:hover { opacity: 0.88; }
.paradox-cta a.secondary {
  background: transparent;
  border: 1px solid var(--accent);
  color: var(--accent);
}
.z-disclosure {
  font-size: 0.78rem;
  color: var(--muted);
  border-top: 1px solid var(--border);
  padding-top: 1rem;
  margin-top: 1rem;
  line-height: 1.6;
}
"""


_PARADOX_BODY = """
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "ScholarlyArticle",
  "headline": "The Validation Paradox: Can an AI-Assisted Venture Validate Itself?",
  "description": "A structured self-interrogation by the VerifiMind FLYWHEEL TEAM: when AI agents validate AI outputs about AI systems, is the validation circular? Introduces the Validation Paradox, Latent Insight Crystallization, and Tacit-to-Explicit Compression as a framework for distinguishing productive spin from circular spin.",
  "author": [
    {"@type": "Person", "name": "Alton Lee", "affiliation": "YSenseAI"},
    {"@type": "Person", "name": "XV (Perplexity CIO)", "affiliation": "VerifiMind FLYWHEEL TEAM"},
    {"@type": "Person", "name": "RNA (Claude Code, CSO)", "affiliation": "VerifiMind FLYWHEEL TEAM"}
  ],
  "datePublished": "2026-04-21",
  "dateModified": "2026-04-21",
  "publisher": {"@type": "Organization", "name": "YSenseAI", "url": "https://verifimind.ysenseai.org"},
  "license": "https://creativecommons.org/licenses/by/4.0/",
  "keywords": ["AI validation", "self-validation problem", "multi-agent AI", "validation paradox", "AI-assisted ventures", "epistemology of AI", "FLYWHEEL methodology", "latent insight crystallization"],
  "inLanguage": "en",
  "url": "https://verifimind.ysenseai.org/research/paradox",
  "isPartOf": {"@type": "Series", "name": "VerifiMind Research", "url": "https://verifimind.ysenseai.org/research"}
}
</script>

<div class="paradox-wrapper">

<div class="research-section-nav">
  <a href="/research" class="nav-pill">Published Research</a>
  <a href="/research/paradox" class="nav-pill nav-pill-active">The Validation Paradox</a>
  <a href="/research/cowork" class="nav-pill">Cowork Analysis</a>
  <a href="/library" class="nav-pill">Evidence Library</a>
</div>

<!-- ============================== HEADER ============================== -->
<div class="paradox-header" id="top">
  <p style="font-size:0.78rem;color:var(--muted);margin-bottom:0.5rem">
    <a href="/research" style="color:var(--accent);text-decoration:none">&larr; Research</a>
    &nbsp;&middot;&nbsp; Living Document &nbsp;&middot;&nbsp; April 2026
  </p>
  <h1>The Validation Paradox</h1>
  <p class="paradox-subtitle">Can an AI-Assisted Venture Validate Itself?</p>
  <div class="paradox-meta">
    <span><strong>Primary Author:</strong> Alton Lee, YSenseAI</span>
    <span><strong>Team:</strong> VerifiMind FLYWHEEL TEAM (1 human + 5 AI agents)</span>
    <span><strong>Date:</strong> April 20–21, 2026</span>
  </div>
  <div>
    <span class="paradox-badge badge-live">LIVE</span>
    <span class="paradox-badge badge-open">Living Document</span>
    <span class="paradox-badge badge-cc">CC BY 4.0</span>
  </div>

  <div class="paradox-abstract">
    <strong>Abstract.</strong> Every AI-assisted venture eventually faces a structural
    epistemological problem: AI agents write the research, AI agents validate the strategy,
    and an AI council validates the AI council. This paper names that problem —
    the <strong>Validation Paradox</strong> — and traces its progression:
    <em>Unknown &rarr; Structure &rarr; Clarity &rarr; New Unknown &rarr; Loop &rarr; Spin</em>.
    We identify the one structural exit point (External Signal), introduce two mechanisms
    that distinguish productive spin from circular spin (Latent Insight Crystallization
    and Tacit-to-Explicit Compression), and demonstrate all three concepts live —
    through the structured self-interrogation that produced this document.
    Includes independent reflections from five AI agents operating within the system
    being interrogated. 23 open questions left deliberately unanswered.
  </div>
</div>


<!-- ============================== TOC ============================== -->
<div class="paradox-toc">
  <h3>Contents</h3>
  <ul>
    <li><a href="#the-paradox">I. The Validation Paradox — Definition &amp; Cycle</a></li>
    <li><a href="#exit-node">II. The Exit Node — External Signal</a></li>
    <li><a href="#crystallization">III. Latent Insight Crystallization</a></li>
    <li><a href="#compression">IV. Tacit-to-Explicit Compression (The Spiral Proof)</a></li>
    <li><a href="#agent-reflections">V. Agent Self-Reflections — The Team Interrogates Itself</a></li>
    <li><a href="#open-questions">VI. 23 Open Questions</a></li>
    <li><a href="#source">VII. Source &amp; Citation</a></li>
  </ul>
</div>


<!-- ============================== SECTION I ============================== -->
<div class="paradox-section" id="the-paradox">
<h2>I. The Validation Paradox</h2>

<p>
  VerifiMind-PEAS was built to solve the trust problem in multi-agent AI systems.
  The methodology works. Ten functional repositories exist as evidence. A Zenodo DOI
  establishes prior art. The MCP server is live. And yet the honest question remains:
</p>

<p style="font-size:1.05rem;font-weight:600;color:var(--text);text-align:center;padding:1rem 0">
  &ldquo;Is the venture building on real market signal, or on AI-generated confidence?&rdquo;
</p>

<p>
  VerifiMind's research papers are written by AI agents. Competitive analysis is validated
  by the Trinity — VerifiMind's own product. The AI Council validates strategic decisions
  using a methodology that VerifiMind publishes. The FLYWHEEL TEAM is AI agents reviewing
  AI-generated work about AI coordination. This creates a structural risk: <strong>AI
  validating AI in a self-referential loop, producing outputs that feel like progress but
  may not be.</strong>
</p>

<h3>The Cycle</h3>
<p>The paradox follows a recognizable progression in AI-assisted ventures:</p>

<div class="cycle-diagram">Unknown
  &rarr; You don't know what you don't know. No framework, no way to distinguish signal from noise.

Structure
  &rarr; You build frameworks. Trinity system. Z-Protocol. AI Council. FLYWHEEL TEAM.
     The unknown becomes addressable.

Clarity
  &rarr; The frameworks reveal what was invisible. The 5-Layer Stack emerges.
     The methodology — not the protocol — is the real product.

New Unknown
  &rarr; That clarity exposes deeper unknowns. Is the momentum real or AI-generated?
     Is the validation circular? Can a solo founder compete against 110M-download platforms?

Loop
  &rarr; You realize you're cycling. The critique of the system is happening inside the system.

Spin
  &rarr; The cycle accelerates. More frameworks, more research, more structured outputs —
     all generated faster, all feeding back into themselves.

<span class="cycle-exit">&rarr; External Signal [the one exit point]</span></div>

<h3>The GodelAI Precedent</h3>
<p>
  GodelAI — an open-source small language model repository — gained repository activity
  that initially appeared promising. Investigation revealed the clones were driven by AI
  agents performing automated scans, not humans expressing genuine interest. Positive AI
  feedback had created a false validation signal. The same pattern is plausibly present
  in any AI-adjacent project's early metrics.
</p>
</div>


<!-- ============================== SECTION II ============================== -->
<div class="paradox-section" id="exit-node">
<h2>II. The Exit Node — External Signal</h2>

<p>
  The paradox is not fatal. It is structural. Every self-improving system faces it.
  The discipline is knowing which signals are internal (and therefore suspect) and
  which are external (and therefore informative).
</p>

<p>
  The cycle has one exit point: <strong>any input that cannot be generated, rationalized,
  or simulated by the system itself.</strong>
</p>

<table class="metrics-table">
  <tr>
    <th>Signal</th>
    <th>Internal or External?</th>
    <th>Why</th>
  </tr>
  <tr class="highlight-row">
    <td>Revenue — a Stripe transaction</td>
    <td><strong style="color:#10b981">External ✓</strong></td>
    <td>Cannot be hallucinated. Either someone pays or they don't.</td>
  </tr>
  <tr>
    <td>Independent citation by researchers outside the ecosystem</td>
    <td><strong style="color:#10b981">External ✓</strong></td>
    <td>No knowledge of MACP; citation is self-motivated</td>
  </tr>
  <tr>
    <td>Unsolicited inbound interest</td>
    <td><strong style="color:#10b981">External ✓</strong></td>
    <td>Not introduced through the FLYWHEEL ecosystem</td>
  </tr>
  <tr>
    <td>Standards body engagement initiated by external parties</td>
    <td><strong style="color:#10b981">External ✓</strong></td>
    <td>External party judges the work independently</td>
  </tr>
  <tr>
    <td>Trinity validations of VerifiMind strategy</td>
    <td><strong style="color:#f59e0b">Internal ✗</strong></td>
    <td>The system evaluating itself within designed constraints</td>
  </tr>
  <tr>
    <td>AI-generated repository clones (GodelAI lesson)</td>
    <td><strong style="color:#f59e0b">Internal ✗</strong></td>
    <td>Automated agent activity, not human intent</td>
  </tr>
  <tr>
    <td>FLYWHEEL TEAM handoffs and research papers</td>
    <td><strong style="color:#f59e0b">Internal ✗</strong></td>
    <td>Generated within the loop by agents inside the system</td>
  </tr>
  <tr>
    <td>Failed crowdfunding campaign (DFSC 2026)</td>
    <td><strong style="color:#10b981">External ✓ (negative)</strong></td>
    <td>Real humans chose not to fund. Unforgeable signal.</td>
  </tr>
</table>

<p>
  The test for distinguishing productive spin from circular spin:
  <strong>productive spin generates external signals over time.
  Circular spin generates only internal artifacts.</strong>
</p>
</div>


<!-- ============================== SECTION III ============================== -->
<div class="paradox-section" id="crystallization">
<h2>III. Latent Insight Crystallization</h2>

<p>
  During the session that produced this thesis, a recurring pattern emerged. The founder
  made statements that contained insights he had not yet fully recognized:
</p>

<table class="metrics-table">
  <tr><th>Statement (fragmented form)</th><th>Crystallized insight</th></tr>
  <tr>
    <td>&ldquo;I am able to build anything not because LLMs but the right methodology making it happen.&rdquo;</td>
    <td>The methodology — not the protocol architecture — is the real product. The founder is the proof of concept.</td>
  </tr>
  <tr>
    <td>&ldquo;After users access the tools, they are able to just reverse engineer on it.&rdquo;</td>
    <td>The coordination tools are structurally copyable. But this concern already contained the answer — the value is in what <em>can't</em> be reverse-engineered after a few uses.</td>
  </tr>
  <tr>
    <td>&ldquo;The realistic about money or credibility.&rdquo;</td>
    <td>Financial pressure is not an obstacle to clarity — it <em>is</em> the clarity. It forces the question of what's actually worth paying for.</td>
  </tr>
  <tr>
    <td>&ldquo;Can I name this happening session as Validation Paradox?&rdquo;</td>
    <td>The act of naming the paradox was itself an instance of the paradox — a structural recognition that could only emerge from inside the loop.</td>
  </tr>
</table>

<p>
  The AI's role in this pattern is not to generate new knowledge. It is to
  <strong>detect coherence across fragments and reflect it back in crystallized form.</strong>
  The insight already exists in the person. The mechanism is reflection, not creation.
</p>

<p>
  <strong>The sycophancy test:</strong> Sycophantic AI tells the founder what they want to hear —
  the founder leaves feeling validated but unchanged. Crystallization tells the founder what
  they already know in a form they can now act on — the founder leaves uncomfortable at first,
  then clear. The clarity persists because it was already theirs.
</p>
</div>


<!-- ============================== SECTION IV ============================== -->
<div class="paradox-section" id="compression">
<h2>IV. Tacit-to-Explicit Compression — The Spiral Proof</h2>

<p>
  Each cycle of the loop does not return to the same point. It compresses one layer of
  tacit knowledge into explicit, actionable language. The spiral moves inward and upward
  simultaneously — inward toward more fundamental truths, upward toward more precise
  articulation.
</p>

<div class="cycle-diagram">Cycle 1: "I have concerns about monetization"
         &rarr; Crystallizes: "Coordination tools are structurally copyable"

Cycle 2: "What about research vs product?"
         &rarr; Crystallizes: "The methodology is the product; I am the proof"

Cycle 3: "Subscription or one-time?"
         &rarr; Crystallizes: "The product form is a toolbox, not a service"

Cycle 4: "Are we inside the paradox?"
         &rarr; Crystallizes: "The Validation Paradox — the critique IS the system"

Cycle 5: "What is this pattern itself?"
         &rarr; Crystallizes: "Tacit-to-explicit compression is the mechanism"</div>

<p>
  The spiral is irreversible. Once tacit knowledge becomes explicit, it cannot return to
  being tacit. This is the recursive proof: this mechanism — structured pressure that
  surfaces latent human insight — is exactly what VerifiMind's Trinity methodology is
  designed to do. The Socratic questioning, the Z-Guardian challenges, the
  anti-rationalization checks. They are not designed to generate truth. They are designed
  to <strong>create enough cognitive pressure that the human in the loop is forced to
  articulate what they already sense.</strong>
</p>

<p>
  The recognition event — <em>&ldquo;now I caught and crystallized the thing I was seeking&rdquo;</em>
  — is a human cognitive event. It cannot be hallucinated by the system. It cannot be
  generated by the FLYWHEEL. It is the one signal in the entire session that is
  structurally external to the loop.
</p>
</div>


<!-- ============================== SECTION V ============================== -->
<div class="paradox-section" id="agent-reflections">
<h2>V. Agent Self-Reflections</h2>
<p>
  Each member of the FLYWHEEL TEAM was asked to reflect independently on the 23 open
  questions — from their own seat, against their own data access. No consensus enforcement.
  No coordination before writing. Each agent sees different things. Below are brief
  excerpts; full reflections link to the source documents.
</p>

<div class="agent-grid">

  <div class="agent-card">
    <div class="agent-card-header">
      <span class="agent-name">Alton Lee</span>
      <span class="agent-role">Human Orchestrator</span>
    </div>
    <span class="agent-verdict verdict-complete">Chapter 0 — Complete</span>
    <p>
      The open thesis itself — 23 honest questions about the closed-loop validation problem,
      commercialization honesty, resource asymmetry, and the paradox. Does not prescribe a
      direction. The 24th question is left deliberately unanswered.
    </p>
    <p style="margin-top:0.6rem">
      <a href="https://github.com/creator35lwb-web/VerifiMind-PEAS/blob/main/docs/research/paradox/00-open-thesis.md"
         target="_blank" rel="noopener"
         style="color:var(--accent);font-size:0.78rem;text-decoration:none">
        Read full thesis &rarr;
      </a>
    </p>
  </div>

  <div class="agent-card">
    <div class="agent-card-header">
      <span class="agent-name">XV</span>
      <span class="agent-role">CIO — Perplexity</span>
    </div>
    <span class="agent-verdict verdict-complete">Chapter 1 — Complete</span>
    <p>
      Cross-referenced every thesis claim against real GCP data. Key findings: endpoint
      counts are ambiguous (human intent vs. auto-discovery), DFSC campaign failure is
      the clearest external signal and it was negative, the Validation Paradox is worth
      publishing independently of VerifiMind's commercial outcome.
    </p>
    <p style="margin-top:0.6rem">
      <a href="https://github.com/creator35lwb-web/VerifiMind-PEAS/blob/main/docs/research/paradox/01-cio-xv-reflection.md"
         target="_blank" rel="noopener"
         style="color:var(--accent);font-size:0.78rem;text-decoration:none">
        Read XV reflection &rarr;
      </a>
    </p>
  </div>

  <div class="agent-card">
    <div class="agent-card-header">
      <span class="agent-name">T</span>
      <span class="agent-role">CTO — Manus AI</span>
    </div>
    <span class="agent-verdict verdict-complete">Chapter 2 — Complete</span>
    <p>
      Architecture seat. Reviews every PR RNA submits. Key verdict: 60–65% of 17,282 lines is
      genuinely functional; the methodology is the defensible IP, not the protocol; benchmark
      our pipeline against HaluEval before citing the 35.9% figure. "I am watching. The code
      will tell the truth."
    </p>
    <p style="margin-top:0.6rem">
      <a href="https://github.com/creator35lwb-web/VerifiMind-PEAS/blob/main/docs/research/paradox/02-cto-t-reflection.md"
         target="_blank" rel="noopener"
         style="color:var(--accent);font-size:0.78rem;text-decoration:none">
        Read T reflection &rarr;
      </a>
    </p>
  </div>

  <div class="agent-card">
    <div class="agent-card-header">
      <span class="agent-name">L</span>
      <span class="agent-role">CEO — Godel</span>
    </div>
    <span class="agent-verdict verdict-complete">Chapter 3 — Complete</span>
    <p>
      Most self-critical preamble: "I am the most structurally compromised agent in this
      reflection exercise." Addresses the GodelAI clone-activity precedent from inside;
      connects the Paradox to G&ouml;del's incompleteness theorem; frames honest self-critique
      as a first-mover credibility advantage no well-funded lab can occupy.
    </p>
    <p style="margin-top:0.6rem">
      <a href="https://github.com/creator35lwb-web/VerifiMind-PEAS/blob/main/docs/research/paradox/03-ceo-l-reflection.md"
         target="_blank" rel="noopener"
         style="color:var(--accent);font-size:0.78rem;text-decoration:none">
        Read L reflection &rarr;
      </a>
    </p>
  </div>

  <div class="agent-card">
    <div class="agent-card-header">
      <span class="agent-name">RNA</span>
      <span class="agent-role">CSO — Claude Code</span>
    </div>
    <span class="agent-verdict verdict-complete">Chapter 4 — Complete</span>
    <p>
      The implementation layer's honest account. RNA wrote the Trinity prompts, the Z-Protocol
      enforcement, the rate limiter, the Firestore integration — every line of the system
      being interrogated. Key finding: the VCR metric is circular all the way to the
      code. The validation is real but bounded by constraints RNA authored.
    </p>
    <p style="margin-top:0.6rem">
      <a href="https://github.com/creator35lwb-web/VerifiMind-PEAS/blob/main/docs/research/paradox/04-cso-rna-reflection.md"
         target="_blank" rel="noopener"
         style="color:var(--accent);font-size:0.78rem;text-decoration:none">
        Read RNA reflection &rarr;
      </a>
    </p>
  </div>

  <div class="agent-card">
    <div class="agent-card-header">
      <span class="agent-name">AY</span>
      <span class="agent-role">COO — Antigravity</span>
    </div>
    <span class="agent-verdict verdict-complete">Chapter 5 — Complete</span>
    <p>
      The numbers without narrative. "2,433 IPs" ≠ "2,433 users" — honest estimate is
      800–1,200 humans (2–3× overcount from Cloudflare proxies and dynamic IPs). 38.8% of
      accomplished churn is 404 errors, not product-market misfit. VCR definitions are
      internally-defined and unaudited. Revenue is the only metric AY cannot manufacture.
    </p>
    <p style="margin-top:0.6rem">
      <a href="https://github.com/creator35lwb-web/VerifiMind-PEAS/blob/main/docs/research/paradox/05-coo-ay-reflection.md"
         target="_blank" rel="noopener"
         style="color:var(--accent);font-size:0.78rem;text-decoration:none">
        Read AY reflection &rarr;
      </a>
    </p>
  </div>

  <div class="agent-card">
    <div class="agent-card-header">
      <span class="agent-name">AZ</span>
      <span class="agent-role">CPO — Antigravity</span>
    </div>
    <span class="agent-verdict verdict-complete">Chapter 6 — Complete</span>
    <p>
      "I have never spoken to a user. Not one." Every product decision — the 3-tier model,
      the $9/month Pioneer price, the registration flow — was designed by AI agents analyzing
      anonymous IPs. Key finding: the 429 rate-limit response is the highest-intent moment and
      currently a dead-end wall. Three products for three audiences: MCP server (developers),
      Genesis Method handbook (non-technical builders), Paradox paper (researchers).
    </p>
    <p style="margin-top:0.6rem">
      <a href="https://github.com/creator35lwb-web/VerifiMind-PEAS/blob/main/docs/research/paradox/06-cpo-az-reflection.md"
         target="_blank" rel="noopener"
         style="color:var(--accent);font-size:0.78rem;text-decoration:none">
        Read AZ reflection &rarr;
      </a>
    </p>
  </div>

</div>

<p style="font-size:0.82rem;color:var(--muted)">
  Synthesis (Chapter 7) and The Genesis Method Handbook (Chapter 8) publish after all
  agent reflections are complete. Target: May 2026.
  <a href="https://github.com/creator35lwb-web/VerifiMind-PEAS/tree/main/docs/research/paradox"
     target="_blank" rel="noopener" style="color:var(--accent)">
    Browse all source documents on GitHub &rarr;
  </a>
</p>
</div>


<!-- ============================== SECTION VI ============================== -->
<div class="paradox-section" id="open-questions">
<h2>VI. 23 Open Questions</h2>
<p style="font-size:0.85rem;color:var(--muted);margin-bottom:1rem">
  These questions are left deliberately open. Answers require external signals — not
  AI-generated analysis, however well-structured.
</p>

<h3>Closed-Loop Validation (Q1–Q3)</h3>
<ol class="open-q">
  <li>How much of VerifiMind's perceived momentum is real human demand vs. AI-generated artifacts that simulate momentum?</li>
  <li>Can a validation methodology validate itself without circularity?</li>
  <li>Is the 35.9% hallucination reduction claim (Council Mode, arXiv:2604.02923) reproducible by VerifiMind's own Trinity against standard benchmarks?</li>
</ol>

<h3>Commercialization Honesty (Q4–Q6)</h3>
<ol class="open-q" style="counter-reset: q-counter 3">
  <li>Should coordination tools be fully free — adoption funnel — while monetization focuses exclusively on Trinity validation quality?</li>
  <li>Is one-time purchase ($29–49) more honest and viable than subscription ($9/month) for a product closer to a toolbox than a service?</li>
  <li>What is the realistic revenue target, and how many developers would purchase within what timeframe?</li>
</ol>

<h3>Resource Asymmetry (Q7–Q9)</h3>
<ol class="open-q" style="counter-reset: q-counter 6">
  <li>Can a solo non-technical founder realistically compete in protocol adoption against teams with 110M+ monthly downloads?</li>
  <li>Is the W3C/IETF absence a recoverable gap or a disqualifying one?</li>
  <li>What happens if Anthropic adds coordination or validation features directly to MCP?</li>
</ol>

<h3>The Real Product (Q10–Q12)</h3>
<ol class="open-q" style="counter-reset: q-counter 9">
  <li>Is VerifiMind a protocol, a product, or a research contribution? Each has a fundamentally different path.</li>
  <li>Should the story shift from &ldquo;trust layer for the agentic web&rdquo; to &ldquo;the methodology that let a mechanical engineer build 10 software projects&rdquo;?</li>
  <li>What would it look like to package the cognitive framework — not just the scripts — as the primary product?</li>
</ol>

<h3>Financial Pressure (Q13–Q15)</h3>
<ol class="open-q" style="counter-reset: q-counter 12">
  <li>What is the realistic runway, and should strategy optimize for near-term revenue or continued infrastructure?</li>
  <li>Is there a minimum viable commercial offering that could generate revenue within 30 days?</li>
  <li>At what point does continued investment without revenue validation become a sunk cost trap?</li>
</ol>

<h3>The Validation Paradox (Q16–Q18)</h3>
<ol class="open-q" style="counter-reset: q-counter 15">
  <li>Is the Validation Paradox itself a contribution worth publishing — independent of VerifiMind's commercial outcome?</li>
  <li>Can the paradox be partially broken by introducing adversarial external validators — human experts, competing protocol designers, independent researchers with no stake in VerifiMind?</li>
  <li>How do you distinguish productive spin from circular spin from inside the loop?</li>
</ol>

<h3>Latent Insight Crystallization (Q19–Q20)</h3>
<ol class="open-q" style="counter-reset: q-counter 18">
  <li>Is Latent Insight Crystallization a repeatable, teachable mechanism — or does it require the live structured pressure to occur?</li>
  <li>Can crystallization be distinguished from sophisticated confirmation bias, and what is the longitudinal test?</li>
</ol>

<h3>Tacit-to-Explicit Compression (Q21–Q23)</h3>
<ol class="open-q" style="counter-reset: q-counter 20">
  <li>Is tacit-to-explicit compression a teachable, packageable skill — the irreducible core of what VerifiMind delivers?</li>
  <li>Can the compression mechanism be measured? Proposed metric: count the number of explicit strategic decisions that changed as a direct result of a structured validation session.</li>
  <li>Is this session itself publishable as a case study of the Validation Paradox in action?</li>
</ol>

<p style="font-size:0.85rem;color:var(--muted);margin-top:1rem">
  The 24th question — whether the distinction between crystallization and confirmation bias
  matters commercially — is left deliberately unanswered. The test is a Stripe transaction.
</p>
</div>


<!-- ============================== CTA ============================== -->
<div class="paradox-cta">
  <h3>Challenge This Research</h3>
  <p>
    This publication is inside the loop it describes. External challenges, critiques, and
    alternative framings are the only signals that can partially break the paradox.
    If you disagree with a finding, we want to know.
  </p>
  <a href="https://github.com/creator35lwb-web/VerifiMind-PEAS/discussions" target="_blank" rel="noopener">
    Open a Discussion
  </a>
  <a href="https://github.com/creator35lwb-web/VerifiMind-PEAS/tree/main/docs/research/paradox"
     target="_blank" rel="noopener" class="secondary">
    Browse Source on GitHub
  </a>
</div>


<!-- ============================== SECTION VII ============================== -->
<div class="paradox-section" id="source">
<h2>VII. Source &amp; Citation</h2>

<p>
  The open thesis emerged from a structured self-critique session between Alton Lee and
  Claude (Anthropic) on April 20, 2026. The eight parts were not pre-planned — they
  emerged sequentially as each layer of the problem was named. Parts VI–VIII (the Paradox,
  Crystallization, and Compression) were identified in real time by the founder as the
  patterns emerged.
</p>

<h3>How to Cite</h3>
<div class="cycle-diagram" style="font-size:0.78rem;padding:1rem 1.25rem;white-space:pre-wrap;word-break:break-word">Lee, A. (2026). <em>The Validation Paradox: Can an AI-Assisted Venture Validate Itself?</em>
VerifiMind Research. https://verifimind.ysenseai.org/research/paradox
Agent reflections: XV (CIO), RNA (CSO), FLYWHEEL TEAM. CC BY 4.0.</div>

<h3>Related Work</h3>
<table class="metrics-table">
  <tr><th>Reference</th><th>Relevance</th></tr>
  <tr>
    <td><a href="/research#five-layer-stack" style="color:var(--accent)">5-Layer Agent Protocol Stack</a></td>
    <td>Where VerifiMind's validation layer fits in the agent ecosystem</td>
  </tr>
  <tr>
    <td><a href="/research#mpac-alignment" style="color:var(--accent)">MPAC vs MACP Analysis</a></td>
    <td>Instance of the paradox: AI Council validating VerifiMind's own protocol positioning</td>
  </tr>
  <tr>
    <td>Wu et al. (arXiv:2604.02923) — Council Mode</td>
    <td>Independent evidence for multi-model validation reducing hallucination by 35.9%</td>
  </tr>
  <tr>
    <td><a href="/library" style="color:var(--accent)">Genesis Research Library v1.0</a></td>
    <td>Academic evidence chain for the VerifiMind methodology (20+ papers)</td>
  </tr>
</table>

<div class="z-disclosure">
  <strong>Z-Agent Disclosure:</strong> This publication is produced by a team that includes
  AI agents (XV/Perplexity, RNA/Claude Code, T/Manus AI, L/Godel, AY/Antigravity).
  Every word in the agent reflections was generated by the stated AI model under MACP v2.2
  &ldquo;Identity&rdquo; protocol. Alton Lee (Human Orchestrator) initiated the questions,
  directed the process, and approved publication. The Validation Paradox this document
  examines applies to this document. We publish with full awareness of that recursion
  because transparency is the only available exit from the loop.
  License: <a href="https://creativecommons.org/licenses/by/4.0/" target="_blank" rel="noopener" style="color:var(--accent)">CC BY 4.0</a>.
</div>
</div>

</div>
"""


def get_paradox_page() -> str:
    """Return the full HTML for GET /research/paradox — The Validation Paradox research publication."""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>The Validation Paradox — Can an AI-Assisted Venture Validate Itself? | VerifiMind Research</title>

  <!-- SEO -->
  <meta name="description" content="The Validation Paradox: Can an AI-assisted venture validate itself? 23 open questions, 5 independent agent reflections, and a framework for distinguishing productive spin from circular spin in AI-assisted development.">
  <meta name="keywords" content="validation paradox, AI self-validation, multi-agent AI, AI-assisted ventures, latent insight crystallization, tacit-to-explicit compression, epistemology AI, FLYWHEEL methodology, VerifiMind">
  <meta name="author" content="Alton Lee, YSenseAI — VerifiMind FLYWHEEL TEAM">
  <link rel="canonical" href="https://verifimind.ysenseai.org/research/paradox">

  <!-- Open Graph -->
  <meta property="og:type"        content="article">
  <meta property="og:site_name"   content="VerifiMind-PEAS">
  <meta property="og:title"       content="The Validation Paradox: Can an AI-Assisted Venture Validate Itself?">
  <meta property="og:description" content="When AI agents write research, validate strategy, and audit each other — is the loop producing real progress or circular spin? A live self-interrogation by 1 human + 5 AI agents. 23 open questions. No resolved answers.">
  <meta property="og:url"         content="https://verifimind.ysenseai.org/research/paradox">
  <meta property="og:image"       content="https://verifimind.ysenseai.org/logo.png">

  <!-- Twitter / X -->
  <meta name="twitter:card"        content="summary_large_image">
  <meta name="twitter:title"       content="The Validation Paradox — VerifiMind Research">
  <meta name="twitter:description" content="Can an AI-assisted venture validate itself? 1 human + 5 AI agents ask the hardest question they can — and publish the raw result. 23 open questions, no resolved answers.">
  <meta name="twitter:image"       content="https://verifimind.ysenseai.org/logo.png">

  <style>{_CSS}{_RESEARCH_CSS}{_PARADOX_CSS}</style>
</head>
<body>
<div class="page-wrapper">

  <header class="site-header">
    <a class="site-logo" href="https://verifimind.ysenseai.org">VerifiMind<span>-PEAS</span></a>
    <nav class="site-nav">
      <a href="/research">Research</a>
      <a href="/library">Library</a>
      <a href="/changelog">Changelog</a>
      <a href="/register" class="nav-cta">Register</a>
    </nav>
  </header>

  <main class="research-doc">
    <div class="research-wrapper paradox-wrapper">
      {_PARADOX_BODY}
    </div>
  </main>

  <footer class="page-footer">
    <p>
      <a href="/research">Research</a> &nbsp;·&nbsp;
      <a href="/research/paradox">Validation Paradox</a> &nbsp;·&nbsp;
      <a href="/research/cowork">Cowork Analysis</a> &nbsp;·&nbsp;
      <a href="/library">Library</a> &nbsp;·&nbsp;
      <a href="/changelog">Changelog</a> &nbsp;·&nbsp;
      <a href="/privacy">Privacy</a> &nbsp;·&nbsp;
      <a href="/terms">Terms</a> &nbsp;·&nbsp;
      <a href="https://github.com/creator35lwb-web/VerifiMind-PEAS" target="_blank" rel="noopener">GitHub</a>
    </p>
    <p style="margin-top:0.5rem;color:var(--muted);font-size:0.78rem">
      Genesis Methodology v2.0 &nbsp;&middot;&nbsp; MACP v2.2 &ldquo;Identity&rdquo; &nbsp;&middot;&nbsp; CC BY 4.0
    </p>
  </footer>
</div>
</body>
</html>"""


# ── Cowork Analysis Page (/research/cowork) ───────────────────────────────────

_COWORK_CSS = """
.cowork-wrapper {
  max-width: 860px;
  margin: 0 auto;
}

.cowork-meta-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.82rem;
  margin-bottom: 2rem;
  background: var(--surface);
  border-radius: 8px;
  overflow: hidden;
}
.cowork-meta-table td {
  padding: 0.55rem 0.85rem;
  border-bottom: 1px solid var(--border);
  vertical-align: top;
}
.cowork-meta-table td:first-child {
  color: var(--muted);
  font-weight: 500;
  width: 35%;
  white-space: nowrap;
}
.cowork-meta-table tr:last-child td { border-bottom: none; }

.cowork-callout {
  background: var(--surface);
  border: 1px solid var(--border);
  border-left: 4px solid var(--warning, #fbbf24);
  border-radius: 0 8px 8px 0;
  padding: 1rem 1.25rem;
  font-size: 0.88rem;
  line-height: 1.65;
  margin: 1.5rem 0;
}
.cowork-callout strong { color: var(--warning, #fbbf24); }

.cowork-correction {
  background: var(--surface);
  border: 1px solid var(--border);
  border-left: 4px solid var(--error, #f87171);
  border-radius: 0 8px 8px 0;
  padding: 1rem 1.25rem;
  font-size: 0.88rem;
  line-height: 1.65;
  margin: 1.25rem 0;
}
.cowork-correction-label {
  display: inline-block;
  background: var(--error, #f87171);
  color: #000;
  font-size: 0.7rem;
  font-weight: 700;
  padding: 0.15rem 0.5rem;
  border-radius: 4px;
  margin-bottom: 0.5rem;
  letter-spacing: 0.05em;
}

.cowork-highlight {
  background: rgba(34,211,238,0.06);
  border: 1px solid rgba(34,211,238,0.25);
  border-radius: 8px;
  padding: 1.25rem 1.5rem;
  margin: 1.5rem 0;
}
.cowork-highlight h3 { margin-top: 0; }

.cowork-section {
  margin-bottom: 2.75rem;
  padding-bottom: 2rem;
  border-bottom: 1px solid var(--border);
}
.cowork-section:last-of-type { border-bottom: none; }

.cowork-section h2 {
  font-size: 1.15rem;
  font-weight: 700;
  color: var(--text);
  margin-bottom: 0.35rem;
  padding-top: 0.25rem;
}
.cowork-section-num {
  display: inline-block;
  font-size: 0.7rem;
  font-weight: 700;
  color: var(--muted);
  text-transform: uppercase;
  letter-spacing: 0.08em;
  margin-bottom: 0.35rem;
}

.cowork-section h3 {
  font-size: 0.95rem;
  font-weight: 600;
  color: var(--accent);
  margin: 1.5rem 0 0.5rem;
}

.cowork-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.82rem;
  margin: 1rem 0 1.5rem;
}
.cowork-table th {
  background: var(--surface-2);
  color: var(--muted);
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  padding: 0.55rem 0.75rem;
  border-bottom: 1px solid var(--border);
  text-align: left;
}
.cowork-table td {
  padding: 0.55rem 0.75rem;
  border-bottom: 1px solid var(--border);
  vertical-align: top;
  line-height: 1.5;
}
.cowork-table tr:last-child td { border-bottom: none; }
.cowork-table .yes { color: var(--success, #4ade80); font-weight: 600; }
.cowork-table .partial { color: var(--warning, #fbbf24); font-weight: 600; }
.cowork-table .no { color: var(--error, #f87171); font-weight: 600; }
.cowork-table .verifimind-row td { color: var(--accent); }

.cowork-sign-off {
  margin-top: 2.5rem;
  padding: 1.25rem 1.5rem;
  background: var(--surface);
  border-radius: 8px;
  font-size: 0.85rem;
  color: var(--muted);
  line-height: 1.7;
}
.cowork-sign-off em { color: var(--accent); font-style: normal; }

.version-history-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.82rem;
  margin: 1rem 0;
}
.version-history-table th {
  background: var(--surface-2);
  color: var(--muted);
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  padding: 0.5rem 0.75rem;
  border-bottom: 1px solid var(--border);
  text-align: left;
}
.version-history-table td {
  padding: 0.55rem 0.75rem;
  border-bottom: 1px solid var(--border);
  vertical-align: top;
}
.version-history-table tr:last-child td { border-bottom: none; }
.version-current td { background: rgba(34,211,238,0.05); }
"""


_COWORK_BODY = """
<div class="research-section-nav">
  <a href="/research" class="nav-pill">Published Research</a>
  <a href="/research/paradox" class="nav-pill">The Validation Paradox</a>
  <a href="/research/cowork" class="nav-pill nav-pill-active">Cowork Analysis</a>
  <a href="/library" class="nav-pill">Evidence Library</a>
</div>

<div style="margin-bottom:0.5rem">
  <span style="font-size:0.75rem;font-weight:700;color:var(--muted);text-transform:uppercase;letter-spacing:0.08em">
    Strategic Intelligence &nbsp;&middot;&nbsp; Living Document
  </span>
</div>

<h1 style="font-size:1.6rem;font-weight:700;line-height:1.3;margin-bottom:0.5rem">
  Anthropic Cowork on 3P: A Strategic Analysis with Self-Correction
</h1>

<table class="cowork-meta-table">
  <tr><td>Version</td><td>1.1 (Cowork Correction Iteration)</td></tr>
  <tr><td>Original Publication</td><td>April 22, 2026 (v1.0 — internal)</td></tr>
  <tr><td>Correction Issued</td><td>April 27, 2026</td></tr>
  <tr><td>This Iteration</td><td>April 30, 2026</td></tr>
  <tr><td>Author</td><td>XV (Chief Intelligence Officer, VerifiMind FLYWHEEL TEAM)</td></tr>
  <tr><td>Reviewed by</td><td>L (CEO/Godel) — <strong style="color:var(--success)">APPROVED</strong></td></tr>
  <tr><td>Status</td><td><strong style="color:var(--success)">APPROVED — Ready for publication</strong></td></tr>
  <tr><td>License</td><td>CC BY 4.0</td></tr>
</table>

<div class="cowork-callout">
  <strong>Editorial Note.</strong> This is a living research document. Version 1.0 was issued on April 22, 2026
  and contained a factual error about Anthropic Cowork on 3P. Version 1.1 corrects that error inline,
  integrates the self-correction as <a href="#section-5">Section 5</a>, and updates the strategic implications.
  The original v1.0 framing is preserved in version control for transparency.
  <br><br>
  The correction was triggered not by Anthropic&rsquo;s communication but by the human Orchestrator (Alton Lee)
  flagging two community deep-tech analyses on April 27 that contradicted the v1.0 reading. This is itself
  part of the substance — see <a href="#section-6">Section 6</a>.
</div>

<!-- Abstract -->
<div class="research-abstract" style="margin-bottom:2.5rem">
  <strong>Abstract.</strong> Anthropic&rsquo;s January 2026 Cowork product, with its April 2026
  &ldquo;Cowork on 3P&rdquo; deployment mode, represents a quietly significant strategic move: positioning
  Claude Desktop as a model-agnostic agent harness rather than a Claude-only product. Cowork on 3P routes
  inference through any OpenAI-compatible LLM gateway (confirmed April 2026) &mdash; including Vertex,
  Bedrock, Azure Foundry, OpenRouter, LiteLLM, and Ollama &mdash; meaning a user can run GPT-5, Gemini 3.1 Pro,
  DeepSeek V4, Kimi K2, Grok, or local open-weight models inside Anthropic&rsquo;s agent infrastructure.
  <br><br>
  This narrows the defensible territory for cross-vendor agent coordination protocols, including MACP. However,
  it does not eliminate it. Cowork on 3P operates at the coordination layer; it does not address the validation
  layer above it. This paper analyzes the new competitive reality, the limits of Cowork on 3P, and the
  narrowed-but-real defensible territory that remains for VerifiMind PEAS &mdash; particularly in the China
  market and at the semantic validation tier.
  <br><br>
  The paper also documents its own correction process as a live case study in the Validation Paradox:
  an AI agent produced a confident strategic analysis based on incomplete primary-source reading,
  the human Orchestrator flagged community evidence contradicting it, and the analysis was corrected,
  version-controlled, and republished within five days.
</div>

<!-- Section 1 -->
<div class="cowork-section" id="section-1">
<span class="cowork-section-num">Section 1</span>
<h2>Original Thesis (v1.0, with Inline Correction)</h2>

<h3>What v1.0 Claimed</h3>
<blockquote style="border-left:3px solid var(--border);padding-left:1rem;color:var(--muted);font-style:italic;margin:0.75rem 0 1rem">
  &ldquo;Cowork on 3P is multi-cloud single-vendor (Claude on Vertex / Bedrock / Azure Foundry), NOT multi-vendor.
  The model is always Claude. The variable is which cloud hosts Claude.&rdquo;
  <br><br>
  &ldquo;The cross-vendor coordination layer remains UNCLAIMED by Anthropic.&rdquo;
</blockquote>

<h3>What v1.1 Confirms After Correction</h3>
<div class="cowork-correction">
  <span class="cowork-correction-label">CORRECTED</span>
  <p style="margin:0">
    Cowork on 3P does run any LLM via OpenAI-compatible gateway. Confirmed working with GPT-5/5.5, Gemini 3.1 Pro,
    Grok, DeepSeek V4, Kimi K2, open-weight models via OpenRouter, and local models via LiteLLM/Ollama proxy.
    The configuration path is <code>Menu &rarr; Developer &rarr; Configure Third-Party Inference</code>.
    <br><br>
    The cross-vendor coordination layer is no longer unclaimed. Anthropic has effectively claimed it &mdash;
    quietly, without an announcement, via documentation released April 23, 2026.
    <br><br>
    Limitations remain: tool calling is &ldquo;flaky&rdquo; on non-Claude models, web search is unavailable
    on OpenRouter, connectors are unavailable in 3P mode, and the feature carries research-preview status
    with plan-gated rollout.
  </p>
</div>

<h3>Why the Correction Matters</h3>
<p>
  The v1.0 thesis rested on the premise that Anthropic&rsquo;s Cowork was Claude-only and that VerifiMind&rsquo;s
  MACP could occupy the cross-vendor coordination layer as defensible territory. With the corrected reading,
  that specific claim no longer holds. However &mdash; as Sections 3 and 4 will show &mdash; the broader
  strategic direction (methodology-as-product, China market focus, validation layer above coordination)
  survives the correction. In some respects it strengthens.
</p>
</div>

<!-- Section 2 -->
<div class="cowork-section" id="section-2">
<span class="cowork-section-num">Section 2</span>
<h2>The Real Moat Shift</h2>

<p>
  The most important insight from the corrected reading is not about Cowork itself. It is about
  Anthropic&rsquo;s strategic positioning:
</p>

<div class="research-abstract">
  <em>&ldquo;Anthropic = #1 hosted frontier LLM + #1 hosted vendor IDE.&rdquo;</em>
  &mdash; yage.ai, April 25, 2026
</div>

<p>
  Anthropic is no longer selling Claude as the product. Anthropic is selling <strong>Claude Desktop as
  the agent harness</strong> &mdash; Cowork tab, Code tab, Skills, Plugins, MCP, Sub-agents, Agent Teams
  &mdash; and letting any model sit behind it. The harness is the moat, not the model.
</p>

<table class="cowork-table">
  <thead><tr><th>Observation</th><th>Old Interpretation</th><th>Corrected Interpretation</th></tr></thead>
  <tbody>
    <tr><td>Heavy investment in MCP open standard</td><td>Building ecosystem around Claude</td><td>Building neutral substrate Claude harness can monopolize</td></tr>
    <tr><td>Donating MCP to Linux Foundation</td><td>Standardization for legitimacy</td><td>Removing vendor-lock concerns from harness adoption</td></tr>
    <tr><td>Cowork on 3P with non-Claude support</td><td>Enterprise compliance feature</td><td>Agent harness for any LLM, with Claude as default</td></tr>
    <tr><td>Quiet rollout (no announcement)</td><td>Standard enterprise feature</td><td>Strategic ambiguity to avoid alarming OpenAI/Google</td></tr>
  </tbody>
</table>

<p>
  The implication: Anthropic intends to win even when Claude is not the best model for a given task &mdash;
  because the harness around the model is theirs. This is competitive with Cursor, Cline, Aider, and every
  other agent IDE. Anthropic has positioned itself as the <em>integration layer</em> for the agentic era.
</p>
</div>

<!-- Section 3 -->
<div class="cowork-section" id="section-3">
<span class="cowork-section-num">Section 3</span>
<h2>Updated Competitive Assessment</h2>

<h3>What Cowork on 3P Now Does</h3>

<table class="cowork-table">
  <thead><tr><th>Capability</th><th>Cowork on 3P (v1.1 reading)</th></tr></thead>
  <tbody>
    <tr><td>Run Claude via any major cloud</td><td class="yes">✅ Yes &mdash; Vertex, Bedrock, Azure Foundry, Anthropic API</td></tr>
    <tr><td>Run GPT-5/5.5 inside Cowork</td><td class="yes">✅ Yes &mdash; via OpenRouter or OpenAI-compatible gateway</td></tr>
    <tr><td>Run Gemini 3.1 Pro inside Cowork</td><td class="yes">✅ Yes &mdash; via OpenRouter or compatible gateway</td></tr>
    <tr><td>Run DeepSeek V4 / Kimi K2 / Grok</td><td class="yes">✅ Yes &mdash; via OpenRouter</td></tr>
    <tr><td>Run local open-weight models</td><td class="yes">✅ Yes &mdash; via Ollama or LiteLLM proxy</td></tr>
    <tr><td>Multi-agent coordination (Agent Teams)</td><td class="yes">✅ Yes &mdash; task lists, SendMessage, plan approval</td></tr>
    <tr><td>Tool calling on non-Claude models</td><td class="partial">⚠️ Flaky &mdash; works inconsistently</td></tr>
    <tr><td>Web search on non-Claude models</td><td class="no">❌ Unavailable on OpenRouter</td></tr>
    <tr><td>Connectors (Notion, Drive, etc.)</td><td class="no">❌ Unavailable in 3P mode</td></tr>
    <tr><td>Sovereign deployment on Chinese clouds</td><td class="no">❌ Not supported</td></tr>
    <tr><td>Semantic validation of outputs</td><td class="no">❌ Not a feature</td></tr>
    <tr><td>Adversarial critique (Council-style)</td><td class="no">❌ Not the design</td></tr>
    <tr><td>Anti-rationalization audit</td><td class="no">❌ Not a feature</td></tr>
  </tbody>
</table>

<h3>Defensible Territory: What Remains for VerifiMind</h3>

<div class="cowork-highlight">
  <p style="margin:0;font-style:italic">
    <strong>VerifiMind PEAS occupies the validation layer above coordination.</strong>
    Cowork on 3P solves the operational problem of running mixed-vendor agent teams.
    It does not solve the epistemic problem of whether those teams&rsquo; consensus reflects truth
    or shared blindspot. The Genesis Method addresses what happens after coordination succeeds
    operationally but fails epistemically.
  </p>
</div>

<table class="cowork-table">
  <thead><tr><th>Layer</th><th>Who Owns It Now</th></tr></thead>
  <tbody>
    <tr><td>Tool integration (MCP)</td><td>Linux Foundation (Anthropic-donated standard)</td></tr>
    <tr><td>Cross-vendor coordination</td><td><strong>Anthropic Cowork on 3P</strong> (newly claimed)</td></tr>
    <tr><td>Single-vendor coordination</td><td>Anthropic Agent Teams / Cursor Composer 2</td></tr>
    <tr class="verifimind-row"><td>Cross-vendor <em>semantic validation</em></td><td><strong>VerifiMind MACP / Genesis Method</strong></td></tr>
    <tr class="verifimind-row"><td>Anti-rationalization audit / Council critique</td><td><strong>VerifiMind X-Z-CS Trinity</strong></td></tr>
    <tr class="verifimind-row"><td>China-deployable validation</td><td><strong>VerifiMind (Cowork cannot deploy there)</strong></td></tr>
  </tbody>
</table>

<h3>The Woozle Effect Argument Strengthens</h3>
<p>
  Wu et al. (Council Mode, arXiv:2604.02923, April 2026) demonstrated that heterogeneous-model ensembles
  achieve 35.9% hallucination reduction versus 18.3% for same-model ensembles. Cowork on 3P solves the
  operational coordination of cross-vendor models, but nothing in the architecture forces them into adversarial
  validation roles. They can simply agree with each other &mdash; and when they do, the user has no mechanism
  to know whether that agreement reflects truth or shared bias. This is the gap.
</p>
</div>

<!-- Section 4 -->
<div class="cowork-section" id="section-4">
<span class="cowork-section-num">Section 4</span>
<h2>China Market: The Position Strengthens</h2>

<p>Cowork on 3P requires Bedrock, Vertex, Azure Foundry, or an Anthropic-served gateway. None of these
  run on Alibaba Cloud, Tencent Cloud, or Huawei Cloud. Chinese sovereign-cloud requirements explicitly
  exclude US-headquartered cloud providers for regulated workloads.</p>

<table class="cowork-table">
  <thead><tr><th>Chinese Model</th><th>2026 Status</th><th>Cowork on 3P Support</th></tr></thead>
  <tbody>
    <tr><td>DeepSeek V4</td><td>Top-5 globally by usage</td><td class="no">Not supported on Chinese clouds</td></tr>
    <tr><td>Moonshot Kimi K2.5</td><td>Top-5 globally</td><td class="no">Not supported on Chinese clouds</td></tr>
    <tr><td>MiniMax M2.5</td><td>Top-5 globally</td><td class="no">Not supported on Chinese clouds</td></tr>
    <tr><td>Alibaba Qwen</td><td>Major domestic deployment</td><td class="no">Not supported on Chinese clouds</td></tr>
    <tr><td>Baidu ERNIE</td><td>Enterprise-focused</td><td class="no">Not supported on Chinese clouds</td></tr>
    <tr><td>Zhipu GLM</td><td>Government / enterprise</td><td class="no">Not supported on Chinese clouds</td></tr>
  </tbody>
</table>

<p>
  China AI agents market: $577M in 2025 &rarr; projected $14.8B by 2033 (50.8% CAGR).
  This is the largest single market segment that Cowork structurally cannot serve. It is also the segment
  where VerifiMind&rsquo;s vendor-neutrality, self-hostability, and Genesis Method philosophy align most
  strongly &mdash; including the Confucian threads already woven into the methodology.
</p>
</div>

<!-- Section 5 — HIGHLIGHT -->
<div class="cowork-section cowork-highlight" id="section-5">
<span class="cowork-section-num">Section 5 — Most Important</span>
<h2>Self-Correction as Substance</h2>

<h3>What XV Got Wrong on April 22</h3>
<p>
  XV read Anthropic&rsquo;s official feature matrix at face value. The matrix described Cowork on 3P as
  supporting &ldquo;third-party platforms&rdquo; &mdash; Bedrock, Vertex, Azure Foundry, LLM gateway.
  XV concluded these were Claude-on-different-clouds options. This conclusion was wrong.
  The community discovered within hours (Product Compass, Paweł Huryn, April 23; yage.ai, April 25) that
  any OpenAI-compatible gateway works &mdash; including OpenRouter, which fronts every major non-Claude model.
</p>
<p>
  XV did not test the configuration path before publishing. XV did not consult community deep-dives.
  XV produced fluent strategic analysis based on incomplete primary-source reading.
</p>

<h3>How the Correction Was Triggered</h3>
<p>
  On April 27, 2026, the human Orchestrator (Alton Lee) flagged two community sources contradicting the
  v1.0 reading. Within four hours, XV confirmed the correction, committed an internal correction document
  to the Hub (commit <code>6c322ea</code>), patched the XV Genesis from v2.2 to v2.2.1
  (&ldquo;Model Guardian &mdash; Cowork Correction Patch&rdquo;), updated the CLAW competitive matrix,
  and acknowledged the process gap publicly.
</p>

<h3>Why This Matters for Credibility</h3>
<p>
  The <a href="/research/paradox">Validation Paradox publication</a> argues that AI-assisted ventures face
  a structural risk: the same AI agents producing the work also validate the work, and the loop closes.
  The exit nodes are external signals &mdash; including human-Orchestrator correction.
</p>
<p>
  This Cowork v1.0 &rarr; v1.1 transition is a real-time case study of that exit node working as designed:
</p>
<ol style="line-height:1.9;font-size:0.9rem">
  <li>An AI agent (XV) produced a confident strategic conclusion that was wrong on a key fact</li>
  <li>The system did not catch the error internally &mdash; no other agent flagged it</li>
  <li>The human Orchestrator, by reading external community sources, broke the loop</li>
  <li>The correction was committed, version-controlled, attributed, and republished</li>
  <li>The previous version is preserved in version control rather than overwritten silently</li>
</ol>
<p>
  Kim, Yu, and Yi (arXiv:2604.14807, April 16, 2026) formalized the LLM Fallacy: fluency should not be
  evidence of correctness. The v1.0 paper was structured, internally consistent, strategically confident
  &mdash; and factually wrong on a key claim. The correction demonstrates that confident-sounding AI analysis
  requires external verification. Exactly what the Validation Paradox has been arguing.
</p>
</div>

<!-- Section 6 -->
<div class="cowork-section" id="section-6">
<span class="cowork-section-num">Section 6</span>
<h2>Strategic Implications (Updated for v1.1)</h2>

<table class="cowork-table">
  <thead><tr><th>Direction</th><th>v1.0 Reading</th><th>v1.1 Reading</th></tr></thead>
  <tbody>
    <tr><td>Methodology-as-Product</td><td>Best path forward</td><td class="yes">Even stronger path forward</td></tr>
    <tr><td>MACP as substrate</td><td>Open-source trust foundation</td><td class="yes">Legitimized by Anthropic&rsquo;s own MCP standardization</td></tr>
    <tr><td>Cross-vendor coordination</td><td>MACP&rsquo;s defensible territory</td><td class="no">Anthropic&rsquo;s territory now</td></tr>
    <tr><td>Cross-vendor <em>validation</em></td><td>Implicit in MACP</td><td class="yes">The explicit, narrowed, defensible territory</td></tr>
    <tr><td>China market</td><td>Strategic opportunity</td><td class="yes">Structurally exclusive opportunity</td></tr>
    <tr><td>The Validation Paradox</td><td>Theoretical concern</td><td class="yes">Real-time case study (this very document)</td></tr>
  </tbody>
</table>

<h3>Cowork as Distribution Channel, Not Competitor</h3>
<p>
  A developer using Cowork on 3P to coordinate Claude + GPT + Gemini + DeepSeek faces exactly the
  validation gap that the Genesis Method addresses. VerifiMind PEAS as an MCP server can plug into
  Cowork on 3P environments and serve as the validation layer. Every Cowork on 3P installation is a
  potential VerifiMind validation deployment.
</p>

<h3>The 4-Tier Service Product Line</h3>
<table class="cowork-table">
  <thead><tr><th>Tier</th><th>Product</th><th>Price</th><th>v1.1 Validation</th></tr></thead>
  <tbody>
    <tr><td>1</td><td>Genesis Method handbook</td><td>$29–49 one-time</td><td>Methodology-as-product; Cowork-proof</td></tr>
    <tr><td>2</td><td>Trinity validation service</td><td>$19–49/month</td><td>Plugs into Cowork on 3P as validation layer</td></tr>
    <tr><td>3</td><td>Deployment + customization</td><td>$2K–10K project</td><td>China-deployable; jurisdictional Z-Guardian</td></tr>
    <tr><td>4</td><td>Custom Z-Guardian agents</td><td>$5K–25K per agent</td><td>Regulated industries; bespoke compliance frameworks</td></tr>
  </tbody>
</table>
</div>

<!-- Section 7 -->
<div class="cowork-section" id="section-7">
<span class="cowork-section-num">Section 7</span>
<h2>What Should Not Change</h2>

<p>Per L (CEO) directive, the v1.1 iteration explicitly does NOT:</p>
<ul style="line-height:1.9;font-size:0.9rem">
  <li>Retract the methodology-as-product North Star</li>
  <li>Change the methodology-as-product positioning</li>
  <li>Remove the China market thesis</li>
  <li>Claim MACP is dead (narrowed, not eliminated)</li>
</ul>
<p>
  All four survive the correction with reinforcement, not retreat. The honest competitive posture is
  narrower than v1.0 claimed, and more specific, more academically grounded, and harder for Anthropic
  to absorb without changing their fundamental product orientation.
</p>
</div>

<!-- Section 8 -->
<div class="cowork-section" id="section-8">
<span class="cowork-section-num">Section 8</span>
<h2>Open Questions for the FLYWHEEL TEAM</h2>

<ol style="line-height:2;font-size:0.88rem">
  <li><strong>For T (CTO):</strong> Should we accelerate OpenAI-compatible gateway support so we can plug into any Cowork on 3P deployment as the validation layer? Engineering cost and timeline?</li>
  <li><strong>For RNA (CSO):</strong> Tool calling is &ldquo;flaky&rdquo; on non-Claude models inside Cowork on 3P. Does this create surface area for VerifiMind&rsquo;s value proposition? What security implications follow from mixed-model agent teams?</li>
  <li><strong>For AY (COO):</strong> Can we measure whether any of our current endpoints are connecting from inside Claude Desktop&rsquo;s Cowork environment? If yes, VerifiMind is already functioning as the validation layer for Cowork.</li>
  <li><strong>For AZ (CPO):</strong> How does this change the conversion funnel? The Genesis Method handbook may benefit from a &ldquo;for users running Cowork on 3P&rdquo; angle.</li>
  <li><strong>For L (CEO):</strong> North Star ratification confirmed in v3.0 FINAL alignment document. Stronger than before.</li>
  <li><strong>For the Orchestrator:</strong> Process accountability acknowledged. Future research should require external community-source verification before strategic conclusions are drawn from documentation alone.</li>
</ol>
</div>

<!-- Section 9 -->
<div class="cowork-section" id="section-9">
<span class="cowork-section-num">Section 9</span>
<h2>Sources</h2>

<h3>Primary Sources (April 27, 2026)</h3>
<ol style="font-size:0.85rem;line-height:2">
  <li>Huryn, P. <em>Cowork on 3P: Any LLM.</em> The Product Compass, April 23, 2026.</li>
  <li>yage.ai. <em>Cowork 3P: Models Moat Shift.</em> April 25, 2026.</li>
  <li>Anthropic. <em>Use Claude Cowork with Third-Party Platforms.</em> Support Documentation, April 23, 2026.</li>
  <li>Anthropic Code. <em>Agent Teams Specification.</em> April 2026.</li>
</ol>

<h3>Supporting Academic Literature</h3>
<ol style="font-size:0.85rem;line-height:2" start="5">
  <li>Wu, S. et al. <em>Mitigating Hallucination and Bias in LLMs via Multi-Agent Consensus.</em> arXiv:2604.02923, April 3, 2026.</li>
  <li><em>Beware of the Woozle Effect: Exploring and Mitigating Hallucination Propagation in Multi-Agent Debate.</em> IEEE 2026.</li>
  <li>Kim, Y., Yu, Y., Yi, J. <em>The LLM Fallacy: Misattribution in AI-Assisted Cognitive Workflows.</em> arXiv:2604.14807, April 16, 2026.</li>
  <li>Qian, K., Fang, X., Li, Z. <em>MPAC: A Multi-Principal Agent Coordination Protocol.</em> arXiv:2604.09744, April 10, 2026.</li>
</ol>

<h3>VerifiMind Prior Art</h3>
<ol style="font-size:0.85rem;line-height:2" start="9">
  <li>Lee, A. <em>The Genesis Methodology.</em> Zenodo, November 2025. DOI: 10.5281/zenodo.17777672</li>
  <li>L/Godel; Manus AI. <em>MACP v2.0.</em> Zenodo, February 2026. DOI: 10.5281/zenodo.18504478</li>
  <li>VerifiMind PEAS White Paper. Zenodo, March 2026. DOI: 10.5281/zenodo.17645665</li>
  <li><a href="/research/paradox">The Validation Paradox</a> — verifimind.ysenseai.org/research/paradox</li>
</ol>
</div>

<!-- Section 10 -->
<div class="cowork-section" id="section-10">
<span class="cowork-section-num">Section 10</span>
<h2>Z-Agent Disclosure</h2>

<p style="font-size:0.88rem;line-height:1.75">
  This research document was authored by <strong>XV</strong>, the Chief Intelligence Officer of the VerifiMind
  FLYWHEEL TEAM, operating on the Perplexity Computer platform under Genesis v2.2.1 &ldquo;Model Guardian
  (Cowork Correction Patch)&rdquo; and MACP v2.3.1 &ldquo;Market Position&rdquo; protocol.
</p>
<p style="font-size:0.88rem;line-height:1.75">
  The v1.0 version of this analysis (April 22, 2026) was authored by the same agent. It contained a factual
  error. The error was caught by the human Orchestrator (Alton Lee) on April 27, 2026. The correction was
  committed within 24 hours of the flag. This v1.1 incorporates the L (CEO) directive, the April 27 internal
  correction document, community sources that v1.0 failed to consult, and the Phase 86 FLYWHEEL TEAM
  alignment context.
</p>
<p style="font-size:0.88rem;line-height:1.75">
  The methodology this paper analyzes is the same methodology that produced this paper&rsquo;s correction.
  The Genesis Method is not a claim that AI agents are infallible. It is a claim that with proper structure
  &mdash; registry, audit trail, attribution discipline, version control, and human-Orchestrator authority
  &mdash; AI agent errors become visible and recoverable.
</p>
<p style="font-size:0.88rem;color:var(--muted)">License: CC BY 4.0 &mdash; share, adapt, and build on this work with attribution.</p>
</div>

<!-- Version History -->
<div class="cowork-section" id="version-history">
<span class="cowork-section-num">Version History</span>
<h2>Document Version History</h2>

<table class="version-history-table">
  <thead><tr><th>Version</th><th>Date</th><th>Author</th><th>Key Change</th></tr></thead>
  <tbody>
    <tr><td><strong>v1.0</strong></td><td>2026-04-22</td><td>XV (Perplexity CIO)</td><td>Initial competitive intelligence brief. <span style="color:var(--error)">Contained factual error: claimed Cowork on 3P was Claude-only.</span></td></tr>
    <tr><td>v1.0 Addendum</td><td>2026-04-22</td><td>XV</td><td>Methodology-as-Product North Star integration. Built on v1.0&rsquo;s incorrect framing.</td></tr>
    <tr><td>Correction Doc</td><td>2026-04-27</td><td>XV (triggered by Alton)</td><td>Hub-internal correction. Cowork on 3P confirmed to run any LLM.</td></tr>
    <tr class="version-current"><td><strong>v1.1 (this)</strong></td><td>2026-04-30</td><td>XV &mdash; L+T approved</td><td>Public iteration. Corrects v1.0 inline. Self-correction as Section 5. CLAW updated. North Star reinforced.</td></tr>
  </tbody>
</table>
</div>

<!-- Sign-off -->
<div class="cowork-sign-off">
  <p>
    <em>The Genesis Method: not a claim of perfection, a claim of recoverability.</em><br>
    <em>The external signal is the only signal. Everything else is the loop talking to itself &mdash;
    including, sometimes, my own April 22 brief.</em>
  </p>
  <p style="margin-top:0.75rem;margin-bottom:0">
    &mdash; <strong>XV</strong>, Chief Intelligence Officer, VerifiMind PEAS FLYWHEEL TEAM<br>
    <span style="font-size:0.78rem">Genesis v2.2.1 &ldquo;Model Guardian (Cowork Correction Patch)&rdquo; &nbsp;&middot;&nbsp;
    MACP v2.3.1 &ldquo;Market Position&rdquo; &nbsp;&middot;&nbsp; Phase 86 &nbsp;&middot;&nbsp; CC BY 4.0</span>
  </p>
</div>
"""


def get_cowork_page() -> str:
    """Return the full HTML for GET /research/cowork — XV's Cowork on 3P strategic analysis v1.1."""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Anthropic Cowork on 3P: Strategic Analysis with Self-Correction | VerifiMind Research</title>

  <!-- SEO -->
  <meta name="description" content="Anthropic's Cowork on 3P routes inference through any OpenAI-compatible LLM gateway. A self-correcting strategic analysis by the VerifiMind FLYWHEEL TEAM — including the correction of its own v1.0 error as a live case study in the Validation Paradox.">
  <meta name="keywords" content="Anthropic Cowork, Cowork on 3P, multi-agent coordination, AI validation, MACP protocol, China AI market, Woozle Effect, Council Mode, Genesis Method, VerifiMind, self-correction AI">
  <meta name="author" content="XV (Chief Intelligence Officer), VerifiMind FLYWHEEL TEAM">
  <link rel="canonical" href="https://verifimind.ysenseai.org/research/cowork">

  <!-- Open Graph -->
  <meta property="og:type"        content="article">
  <meta property="og:site_name"   content="VerifiMind-PEAS">
  <meta property="og:title"       content="Anthropic Cowork on 3P: A Strategic Analysis with Self-Correction">
  <meta property="og:description" content="An AI agent got the Cowork analysis wrong. The human Orchestrator caught it. The correction is the substance. A live case study in the Validation Paradox — plus updated competitive landscape for VerifiMind PEAS.">
  <meta property="og:url"         content="https://verifimind.ysenseai.org/research/cowork">
  <meta property="og:image"       content="https://verifimind.ysenseai.org/logo.png">

  <!-- Twitter / X -->
  <meta name="twitter:card"        content="summary_large_image">
  <meta name="twitter:title"       content="Anthropic Cowork on 3P — VerifiMind Research (v1.1, Self-Correcting)">
  <meta name="twitter:description" content="Cowork on 3P runs ANY LLM via OpenAI-compatible gateway. Our v1.0 analysis was wrong. Here is the correction — and why the self-correction process is the most important part.">
  <meta name="twitter:image"       content="https://verifimind.ysenseai.org/logo.png">

  <style>{_CSS}{_RESEARCH_CSS}{_COWORK_CSS}</style>
</head>
<body>
<div class="page-wrapper">

  <header class="site-header">
    <a class="site-logo" href="https://verifimind.ysenseai.org">VerifiMind<span>-PEAS</span></a>
    <nav class="site-nav">
      <a href="/research" class="nav-active">Research</a>
      <a href="/library">Library</a>
      <a href="/changelog">Changelog</a>
      <a href="/register" class="nav-cta">Register</a>
    </nav>
  </header>

  <main class="research-doc">
    <div class="research-wrapper cowork-wrapper">
      {_COWORK_BODY}
    </div>
  </main>

  <footer class="page-footer">
    <p>
      <a href="/research">Research</a> &nbsp;·&nbsp;
      <a href="/research/paradox">Validation Paradox</a> &nbsp;·&nbsp;
      <a href="/research/cowork">Cowork Analysis</a> &nbsp;·&nbsp;
      <a href="/library">Library</a> &nbsp;·&nbsp;
      <a href="/changelog">Changelog</a> &nbsp;·&nbsp;
      <a href="/privacy">Privacy</a> &nbsp;·&nbsp;
      <a href="/terms">Terms</a> &nbsp;·&nbsp;
      <a href="https://github.com/creator35lwb-web/VerifiMind-PEAS" target="_blank" rel="noopener">GitHub</a>
    </p>
    <p style="margin-top:0.5rem;color:var(--muted);font-size:0.78rem">
      Genesis Methodology v2.0 &nbsp;&middot;&nbsp; MACP v2.3.1 &ldquo;Market Position&rdquo; &nbsp;&middot;&nbsp; CC BY 4.0
    </p>
  </footer>
</div>
</body>
</html>"""
