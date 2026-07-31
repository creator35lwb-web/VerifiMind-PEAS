"""Canonical plain-text Privacy Policy served to JSON clients."""

PRIVACY_POLICY_VERSION = "2.4"
PRIVACY_POLICY_EFFECTIVE_DATE = "2026-08-01"

PRIVACY_POLICY = """
VerifiMind-PEAS — Privacy Policy v2.4
Effective: August 1, 2026 (previous: v2.3, July 30, 2026)

1. WHO WE ARE
VerifiMind-PEAS is an open-source multi-model AI validation framework created
by Alton Lee (Human Orchestrator, YSenseAI). This policy applies to the hosted
service at verifimind.ysenseai.org and its Early Adopter and PILOT programs.

2. CURRENT SERVICE AVAILABILITY
Eight validation and built-in template tools are currently available. Three
coordination and two custom-template mutation tools are temporarily unavailable
while owner-scoped controls and URL-fetch protections are rebuilt.
No paid services are active. Registration does not create a time-limited
access entitlement.

3. DATA WE COLLECT
For registration we may collect:
  • Email address (required on the Early Adopter form)
  • Name (optional)
  • A generated pseudonymous UUID
  • Registration timestamp and consent records
  • Feedback and feedback category (optional)
  • Tier or cohort label

We do not collect passwords, payment details, location, or device information
through registration. No paid checkout is currently offered.

4. WHY WE COLLECT IT
We use registration data to identify accounts, allocate rate limits, manage EA
and PILOT feedback cohorts, communicate updates when separately consented to,
process feedback, and retain evidence of consent.

5. UUID USAGE ANALYTICS
When a caller voluntarily supplies a UUID, the service may log the UUID, tool
name, tier label, and UTC timestamp. It does not intentionally log the submitted
concept or tool output as UUID-linked analytics. Operational infrastructure may
process network metadata needed to secure and run the service.

Runtime custom-template registration and URL import are disabled. The hosted
service exposes built-in templates only and does not accept, list, export, or
retain custom prompt content while owner-scoped storage is being built.

6. STORAGE AND RETENTION
Account records are stored in Google Cloud Firestore with restricted access.
UUID usage analytics in Google Cloud Logging are retained for 30 days under the
configured retention policy. EA/PILOT records are retained for the duration of
membership plus 90 days. Feedback may be retained in anonymised form. Deletion
requests are targeted for completion within 7 business days unless retention is
required by law or a documented security/legal hold applies.

7. DATA SHARING
Google Cloud Platform processes account records as the hosting and database
provider. We do not sell personal data. No payment processor receives
registration data because no paid service is currently active.

8. YOUR CHOICES AND RIGHTS
You may:
  • Check status at GET /early-adopters/status/{your-uuid}
  • Request deletion at POST /early-adopters/optout/{your-uuid}
  • Ask for correction through GitHub Discussions or the contact below
  • Stop optional UUID analytics by omitting the UUID from tool calls
  • Withdraw optional email-update consent

9. SECURITY
Do not submit passwords, API keys, or other secrets through registration,
feedback, or validation prompts. Security controls reduce risk but no hosted
service can guarantee absolute security.

10. CONTACT
GitHub Discussions:
github.com/creator35lwb-web/VerifiMind-PEAS/discussions
Email: creator35lwb@gmail.com

11. CHANGES
Material changes will be communicated according to the applicable terms. The
current policy is always available at verifimind.ysenseai.org/privacy.

This v2.4 revision clarifies custom-template isolation and current availability.
It does not introduce a fee or shorten an existing entitlement.
"""
