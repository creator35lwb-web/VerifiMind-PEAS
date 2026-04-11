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
      <span class="benefit-icon">&#x23F0;</span>
      <strong>3 months free</strong>
      <div class="benefit-label">Pioneer tier</div>
    </div>
    <div class="benefit-item">
      <span class="benefit-icon">&#x1F9EA;</span>
      <strong>Beta access</strong>
      <div class="benefit-label">v0.6.0 Pioneer</div>
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
  <span>Version 2.0</span>
  <span>Effective: April 8, 2026</span>
  <span>Previous: v1.0 (March 18, 2026)</span>
</div>

<h2>Who We Are</h2>
<p>
  VerifiMind-PEAS is an open-source multi-model AI validation framework created by
  Alton Lee (Human Orchestrator, YSenseAI). This Privacy Policy applies to the
  VerifiMind-PEAS service at verifimind.ysenseai.org, including the Early Adopter (EA)
  program, PILOT program, and Pioneer subscription tier.
</p>

<h2>What We Collect</h2>
<table class="legal-table">
  <thead>
    <tr><th>Data</th><th>Required</th><th>Purpose</th></tr>
  </thead>
  <tbody>
    <tr><td>Email address</td><td>Yes</td><td>Account identification, subscription management</td></tr>
    <tr><td>Name</td><td>No</td><td>Display only; never shared without your explicit consent</td></tr>
    <tr><td>UUID</td><td>Generated</td><td>Your pseudonymous identifier across all systems</td></tr>
    <tr><td>Registration timestamp</td><td>Auto</td><td>When you joined the program</td></tr>
    <tr><td>Consent records</td><td>Auto</td><td>That you accepted these terms and when</td></tr>
    <tr><td>Feedback message</td><td>No</td><td>To help us understand your needs and improve the product</td></tr>
    <tr><td>Tier status</td><td>Auto</td><td>Scholar, EA, PILOT, or Pioneer</td></tr>
    <tr><td>Subscription status</td><td>Auto</td><td>Active, cancelled, or expired</td></tr>
  </tbody>
</table>

<h3>What We Do Not Collect</h3>
<ul>
  <li>Passwords or credentials</li>
  <li>Credit card numbers or bank account details — payment is handled entirely by Polar (see below)</li>
  <li>IP addresses linked to your email</li>
  <li>Location or device information</li>
  <li>Browsing behaviour beyond anonymous usage telemetry never connected to your account</li>
</ul>

<h2>Payment Processing and Polar</h2>
<p>
  Pioneer tier subscriptions are processed by <strong>Polar Software Inc</strong> ("Polar"),
  which acts as our <strong>merchant of record</strong>. Polar is the legal seller of the Pioneer
  subscription and handles all payment processing, tax compliance, invoicing, and billing on
  behalf of VerifiMind-PEAS.
</p>
<div class="notice-box">
  <strong>VerifiMind-PEAS never sees, stores, or has access to your payment credentials.</strong>
  Payment information is collected directly by Polar through their Stripe Connect checkout.
</div>
<p><strong>What Polar shares with us:</strong> Subscription status (active, cancelled, expired),
  tier level (Pioneer), Polar transaction ID, subscription dates, granted benefit flags, and the
  email address you used for payment (to match your VerifiMind-PEAS account).</p>
<p><strong>Polar's privacy practices:</strong> Polar processes your payment data under their own
  Privacy Policy at <a href="https://polar.sh/legal/privacy-policy" target="_blank" rel="noopener">polar.sh/legal/privacy-policy</a>.
  Polar is GDPR-compliant and PCI-DSS compliant via Stripe Connect.</p>

<h2>Why We Collect Your Data</h2>
<ul>
  <li>To grant program benefits (EA: 3 months free, PILOT: 6 months free, Pioneer: full coordination tools access)</li>
  <li>To manage your subscription and tier access via Polar's Customer State API</li>
  <li>To communicate product updates if you opted in</li>
  <li>To improve VerifiMind-PEAS based on aggregate, anonymised feedback</li>
  <li>To maintain compliance records that you gave informed consent</li>
</ul>

<h2>Cookies</h2>
<p>VerifiMind-PEAS does not use tracking cookies. When you use the Polar checkout, Polar may set
  cookies for payment processing and fraud prevention (governed by Polar's privacy practices).
  Anonymous usage telemetry on verifimind.ysenseai.org uses privacy-respecting analytics that
  do not track individual users.</p>

<h2>How Long We Keep Your Data</h2>
<table class="legal-table">
  <thead>
    <tr><th>Data Type</th><th>Retention Period</th></tr>
  </thead>
  <tbody>
    <tr><td>EA/PILOT records</td><td>Duration of membership + 90 days</td></tr>
    <tr><td>Pioneer subscription records</td><td>Duration of subscription + 7 years (tax and legal compliance)</td></tr>
    <tr><td>Feedback messages</td><td>Kept indefinitely in anonymised form after 6 months</td></tr>
    <tr><td>Transaction metadata (Polar IDs, dates)</td><td>7 years from transaction date (tax compliance)</td></tr>
  </tbody>
</table>
<p>On deletion request, all personal data is purged within 7 business days, except where
  retention is required by law (e.g., tax records associated with completed transactions).</p>

<h2>Your Rights</h2>
<ul>
  <li><strong>Access</strong> — <code>GET /early-adopters/status/{your-uuid}</code></li>
  <li><strong>Delete</strong> — <code>POST /early-adopters/optout/{your-uuid}</code> (purged within 7 days)</li>
  <li><strong>Correct</strong> — raise a GitHub Discussion or contact us</li>
  <li><strong>Withdraw consent</strong> — same opt-out endpoint</li>
</ul>
<p>For payment-related data held by Polar, exercise your rights directly at
  <a href="https://polar.sh/legal/privacy-policy" target="_blank" rel="noopener">polar.sh/legal/privacy-policy</a>.</p>
<p>These rights are free of charge and will be actioned promptly.</p>

<h2>Data Sharing</h2>
<table class="legal-table">
  <thead>
    <tr><th>Third Party</th><th>Role</th><th>Data Shared</th></tr>
  </thead>
  <tbody>
    <tr><td>Google Cloud Platform</td><td>Hosting infrastructure, Firestore database</td><td>Account records (encrypted at rest)</td></tr>
    <tr><td>Polar Software Inc</td><td>Merchant of record, payment processing</td><td>Email address (invoice matching), UUID (tier-gating)</td></tr>
  </tbody>
</table>
<p>No other third parties receive your data.</p>

<h2>Security</h2>
<p>Your account records are stored in Google Cloud Firestore with restricted access. We do not
  log your email address in server logs. Your UUID is your primary identifier in all internal
  systems. Payment data is secured by Polar's Stripe Connect infrastructure (PCI-DSS compliant)
  and is never stored on VerifiMind-PEAS servers.</p>

<h2>Contact</h2>
<ul>
  <li>GitHub Discussions: <a href="https://github.com/creator35lwb-web/VerifiMind-PEAS/discussions" target="_blank" rel="noopener">github.com/creator35lwb-web/VerifiMind-PEAS/discussions</a></li>
  <li>Email: <a href="mailto:creator35lwb@gmail.com">creator35lwb@gmail.com</a></li>
  <li>Or use the <a href="/optout">opt-out endpoint</a> for immediate data deletion</li>
</ul>

<h2>Compliance</h2>
<p>This policy aligns with GDPR (EU), PDPA (Singapore/ASEAN), and the Z-Protocol v1.1 ethical
  framework (data minimisation, transparency, user autonomy). Polar's merchant-of-record model
  ensures tax compliance across all supported jurisdictions via Stripe Connect Express.</p>

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
  <span>Version 2.0</span>
  <span>Effective: April 8, 2026</span>
  <span>Previous: v1.0 (March 18, 2026)</span>
</div>

<h2>1. Service Description</h2>
<p>VerifiMind-PEAS is an open-source multi-model AI validation framework that provides structured,
  multi-agent validation and orchestration tools. The service is offered in tiered access levels
  as described in Section 3.</p>

<h2>2. Acceptance of Terms</h2>
<p>By registering for any VerifiMind-PEAS program or using the service, you confirm that you have
  read and accept:</p>
<ul>
  <li>These Terms &amp; Conditions v2.0</li>
  <li>The <a href="/privacy">Privacy Policy v2.0</a></li>
  <li><a href="https://polar.sh/legal/master-services-terms" target="_blank" rel="noopener">Polar's Master Services Terms</a>
    (applicable to Pioneer tier subscribers)</li>
</ul>

<h2>3. Service Tiers</h2>
<table class="legal-table">
  <thead>
    <tr><th>Tier</th><th>Access</th><th>Price</th><th>Duration</th></tr>
  </thead>
  <tbody>
    <tr>
      <td><span class="tier-badge">Scholar</span></td>
      <td>All 10 Trinity validation tools + templates. Open-source core (MIT).</td>
      <td>Free forever</td>
      <td>Permanent</td>
    </tr>
    <tr>
      <td><span class="tier-badge">Early Adopter</span></td>
      <td>All Scholar tools + Pioneer coordination tools</td>
      <td>Free 3 months, then Pioneer pricing</td>
      <td>3 months free</td>
    </tr>
    <tr>
      <td><span class="tier-badge">PILOT</span></td>
      <td>All Scholar tools + Pioneer coordination tools</td>
      <td>Free 6 months, then Pioneer pricing</td>
      <td>6 months free</td>
    </tr>
    <tr>
      <td><span class="tier-badge">Pioneer</span></td>
      <td>All Scholar tools + 6 coordination tools (handoff management, team status, session coordination)</td>
      <td><strong>$9/month (USD)</strong></td>
      <td>Monthly subscription</td>
    </tr>
  </tbody>
</table>
<div class="notice-box">
  The Scholar tier remains free forever. You never lose access to the Scholar tier by registering
  for any program. The VerifiMind-PEAS core is MIT licensed — you may self-host at any time.
</div>

<h2>4. Payment and Billing</h2>

<h3>4.1 Merchant of Record</h3>
<p>All paid subscriptions are processed by <strong>Polar Software Inc</strong> ("Polar"), which acts as
  the merchant of record. Polar handles all payment processing, tax calculation, invoicing, and billing
  via Stripe Connect. By subscribing to the Pioneer tier, you also agree to
  <a href="https://polar.sh/legal/master-services-terms" target="_blank" rel="noopener">Polar's Master Services Terms</a>
  and
  <a href="https://polar.sh/legal/acceptable-use-policy" target="_blank" rel="noopener">Polar's Acceptable Use Policy</a>.</p>

<h3>4.2 Subscription Terms</h3>
<ul>
  <li>Pioneer subscriptions are billed monthly in USD</li>
  <li>Subscriptions auto-renew at the end of each billing period unless cancelled</li>
  <li>You may cancel anytime through the Polar customer portal or by contacting us</li>
  <li>Cancellation takes effect at end of current billing period — full access retained until then</li>
  <li>Local taxes may apply, calculated and collected by Polar based on your location</li>
</ul>

<h3>4.3 Free Period Transition</h3>
<ul>
  <li>You will receive at least 14 days' advance notice before any billing begins</li>
  <li>You will never be charged without explicit action on your part</li>
  <li>If you do not subscribe after your free period ends, access reverts to Scholar — no penalty</li>
  <li>You may subscribe to Pioneer at any time after your free period ends</li>
</ul>

<h3>4.4 Alternative Payment</h3>
<p>Multiple payment methods are available through the Polar checkout: credit card, US bank account,
  Cash App Pay, Apple Pay and Google Pay (device dependent). A BuyMeACoffee page (PayPal) is also
  available as a backup support channel.</p>

<h2>5. Refund Policy</h2>

<h3>5.1 14-Day Money-Back Guarantee</h3>
<p>If you are not satisfied with the Pioneer tier, you may request a full refund within 14 days of
  your first subscription payment. No questions asked.</p>

<h3>5.2 After 14 Days</h3>
<p>After the initial 14-day period, no prorated refunds are issued. You may cancel anytime;
  cancellation takes effect at the end of the current billing period.</p>

<h3>5.3 How to Request a Refund</h3>
<ul>
  <li>Polar customer portal (link in your subscription confirmation email)</li>
  <li>Email: <a href="mailto:creator35lwb@gmail.com">creator35lwb@gmail.com</a></li>
  <li><a href="https://github.com/creator35lwb-web/VerifiMind-PEAS/discussions" target="_blank" rel="noopener">GitHub Discussions</a></li>
</ul>
<p>Refunds are processed by Polar and typically appear within 5–10 business days.</p>

<h3>5.4 Dispute Resolution</h3>
<p>Payment disputes are handled through Polar's buyer protection process. Please contact us directly
  before initiating a payment dispute.</p>

<h2>6. Beta Software</h2>
<p>The Pioneer coordination tools are currently in beta. You accept that:</p>
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
  <li>Share, resell, or redistribute your Pioneer access key or subscription credentials</li>
  <li>Use automated scraping or excessive API calls that degrade service for other users</li>
  <li>Use VerifiMind-PEAS tools to generate harmful, misleading, or unethical content</li>
</ul>
<p>Violation may result in suspension or termination of your access. This section supplements
  <a href="https://polar.sh/legal/acceptable-use-policy" target="_blank" rel="noopener">Polar's Acceptable Use Policy</a>.</p>

<h2>9. Opt-Out and Termination</h2>
<ul>
  <li>You may opt out at any time via <a href="/optout"><code>POST /early-adopters/optout/{uuid}</code></a></li>
  <li>On opt-out, personal data is purged within 7 business days (subject to legal retention requirements)</li>
  <li>We may terminate access for violation of the Acceptable Use terms in Section 8</li>
  <li>If we terminate your paid subscription due to a violation, no refund is issued</li>
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
    """Return the full HTML for GET /privacy — Privacy Policy v2.0."""
    return _legal_shell(title="Privacy Policy", body=_PRIVACY_BODY)


def get_terms_page() -> str:
    """Return the full HTML for GET /terms — Terms &amp; Conditions v2.0."""
    return _legal_shell(title="Terms &amp; Conditions", body=_TERMS_BODY)


# ── Changelog page ────────────────────────────────────────────────────────────

_CHANGELOG_BODY = """
<h1>Changelog</h1>
<div class="meta">
  <span>Last updated: April 12, 2026</span>
  <span><a href="https://github.com/creator35lwb-web/VerifiMind-PEAS/releases" target="_blank" rel="noopener">GitHub Releases</a></span>
</div>

<div id="v0.5.13">
<h2>v0.5.13 — Fortify <span class="live-badge">LIVE</span></h2>
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
