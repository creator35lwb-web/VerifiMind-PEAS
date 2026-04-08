"""
VerifiMind-PEAS Privacy Policy — v2.0
Z-Protocol v1.1 compliant: data minimisation, explicit consent, right to erasure.
GDPR / PDPA / Polar MOR (Stripe Connect) aligned.
Effective: April 8, 2026
"""

PRIVACY_POLICY_VERSION = "2.0"
PRIVACY_POLICY_EFFECTIVE_DATE = "2026-04-08"

PRIVACY_POLICY = """
VerifiMind-PEAS — Privacy Policy v2.0
Effective: April 8, 2026 (previous: v1.0, March 18, 2026)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

WHO WE ARE
VerifiMind-PEAS is an open-source multi-model AI validation framework created
by Alton Lee (Human Orchestrator, YSenseAI). This Privacy Policy applies to
the VerifiMind-PEAS service at verifimind.ysenseai.org, including the Early
Adopter (EA) program, PILOT program, and Pioneer subscription tier.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

WHAT WE COLLECT
When you register or subscribe to any VerifiMind-PEAS program:

  Data               Required  Purpose
  ─────────────────────────────────────────────────────────────────
  Email address      Yes       Account identification, subscription management
  Name               No        Display only; never shared without consent
  UUID               Generated Pseudonymous identifier across all systems
  Registration date  Auto      When you joined the program
  Consent records    Auto      That you accepted these terms and when
  Feedback message   No        To understand your needs and improve the product
  Tier status        Auto      Scholar, EA, PILOT, or Pioneer
  Subscription status Auto     Active, cancelled, or expired

WHAT WE DO NOT COLLECT
  ✗ Passwords or credentials
  ✗ Credit card numbers or bank details (handled entirely by Polar — see below)
  ✗ IP addresses linked to your email
  ✗ Location or device information
  ✗ Browsing behaviour beyond anonymous usage telemetry (never linked to your account)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

PAYMENT PROCESSING AND POLAR
Pioneer tier subscriptions are processed by Polar Software Inc ("Polar"),
which acts as our merchant of record. Polar is the legal seller of the Pioneer
subscription and handles all payment processing, tax compliance, invoicing, and
billing on behalf of VerifiMind-PEAS.

What Polar collects directly:
  When you subscribe, Polar collects your payment information (credit card,
  PayPal, or other method) through their secure checkout powered by Stripe
  Connect. VerifiMind-PEAS never sees, stores, or has access to your payment
  credentials.

What Polar shares with us:
  Subscription status (active, cancelled, expired), tier level (Pioneer),
  Polar transaction ID, subscription dates, granted benefit flags (feature
  access indicators), and the email address you used for payment.

Polar's privacy practices:
  Polar processes payment data under their own Privacy Policy:
  polar.sh/legal/privacy-policy
  Polar is GDPR-compliant and PCI-DSS compliant (via Stripe Connect).

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

WHY WE COLLECT YOUR DATA
  • To grant program benefits (EA: 3 months free, PILOT: 6 months free,
    Pioneer: full coordination tools access)
  • To manage your subscription and tier access via Polar's Customer State API
  • To communicate product updates, if you opted in
  • To improve VerifiMind-PEAS based on aggregate, anonymised feedback
  • To maintain compliance records that you gave informed consent

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

COOKIES
VerifiMind-PEAS does not use tracking cookies. When you use the Polar checkout,
Polar may set cookies for payment processing and fraud prevention (governed by
Polar's privacy practices). Anonymous usage telemetry on verifimind.ysenseai.org
uses privacy-respecting analytics that do not track individual users.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

HOW LONG WE KEEP YOUR DATA

  Data Type                    Retention Period
  ─────────────────────────────────────────────────────────────────────────────
  EA/PILOT records             Duration of membership + 90 days
  Pioneer subscription records Duration of subscription + 7 years (tax/legal)
  Feedback messages            Indefinitely in anonymised form after 6 months
  Transaction metadata         7 years from transaction date (tax compliance)

On deletion request, all personal data is purged within 7 business days,
except where retention is required by law (e.g., tax records from Polar).

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

YOUR RIGHTS
You have the right to:
  • Access your data — GET /early-adopters/status/{your-uuid}
  • Delete your data — POST /early-adopters/optout/{your-uuid}
    (marks your record for deletion; purged within 7 days)
  • Correct your data — raise a GitHub Discussion or contact us
  • Withdraw consent at any time — same opt-out endpoint

For payment data held by Polar, exercise rights directly at:
  polar.sh/legal/privacy-policy

These rights are free of charge and will be actioned promptly.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

DATA SHARING
We do NOT sell, rent, or share your personal data with any third party, except:

  Third Party              Role                      Data Shared
  ─────────────────────────────────────────────────────────────────
  Google Cloud Platform    Hosting, Firestore DB     Account records (encrypted)
  Polar Software Inc       MOR, payment processing   Email (invoice matching),
                                                     UUID (tier-gating)

No other third parties receive your data.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

SECURITY
Your account records are stored in Google Cloud Firestore with restricted access.
We do not log your email address in server logs. Your UUID is your primary
identifier in all internal systems. Payment data is secured by Polar's Stripe
Connect infrastructure (PCI-DSS compliant) and never stored on our servers.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

CONTACT
  GitHub Discussions: github.com/creator35lwb-web/VerifiMind-PEAS/discussions
  Email: creator35lwb@gmail.com
  Or use the opt-out endpoint for immediate data deletion.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

COMPLIANCE
This policy aligns with GDPR (EU), PDPA (Singapore/ASEAN), and the
Z-Protocol v1.1 ethical framework (data minimisation, transparency, user
autonomy). Polar's merchant-of-record model ensures tax compliance across
all supported jurisdictions via Stripe Connect Express.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

CHANGES TO THIS POLICY
We will notify registered users of material changes at least 14 days before
they take effect. The current version is always available at:
  verifimind.ysenseai.org/privacy

VerifiMind-PEAS is open source: github.com/creator35lwb-web/VerifiMind-PEAS
"""
