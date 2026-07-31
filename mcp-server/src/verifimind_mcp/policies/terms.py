"""Canonical plain-text Terms & Conditions served to JSON clients."""

TERMS_VERSION = "2.3"
TERMS_EFFECTIVE_DATE = "2026-08-01"

TERMS_AND_CONDITIONS = """
VerifiMind-PEAS — Terms & Conditions v2.3
Effective: August 1, 2026 (previous: v2.2, July 30, 2026)

1. SERVICE DESCRIPTION
VerifiMind-PEAS is an open-source multi-model AI validation framework. Eight
validation and built-in template tools are currently available. Three coordination
tools and two custom-template mutation tools are discoverable but temporarily
unavailable while owner-scoped controls and URL-fetch protections are rebuilt.

2. ACCEPTANCE
By registering or using the hosted service, you accept these Terms v2.3 and the
Privacy Policy v2.4 at verifimind.ysenseai.org/privacy.

3. ACCESS AND TIERS
Anonymous, Scholar, Early Adopter, and PILOT users may use the same 8 active
tools. Tier identity is used for rate-limit allocation, cohort management, and
personal dashboard scoping. Three coordination and two custom-template mutation
tools are unavailable to every tier during maintenance.

Current rate-limit targets are:
  • Anonymous: 10 requests per 60 seconds per IP
  • Scholar: 30 requests per 60 seconds per UUID
  • Early Adopter/PILOT: 100 requests per 60 seconds per UUID

Registration does not create a time-limited access entitlement. No current
service is sold through a paid checkout.

4. PAYMENT
There are no active paid services. You will not be charged without a separate,
explicit purchase action under terms presented before purchase.

5. BETA SERVICE
The hosted service is beta software. Features may change, be added, be removed,
or be temporarily unavailable. No uptime service-level agreement is offered.
The service is provided "as is" to the extent permitted by applicable law.

6. FEEDBACK
Feedback is voluntary. We may use it to improve the product and may quote it
only anonymously unless you provide separate permission for attribution.

7. ACCEPTABLE USE
You agree not to:
  • Probe for or attempt unauthorised access to other users' data
  • Submit secrets, credentials, or unlawful content
  • Impersonate another user or agent
  • Abuse rate limits, scrape excessively, or degrade the service
  • Use outputs as a substitute for qualified legal, medical, security, or
    financial advice

8. SUSPENSION
Access may be limited or suspended to protect users, investigate abuse, comply
with law, or maintain the service.

9. OPT-OUT AND DELETION
You may request deletion at POST /early-adopters/optout/{uuid}. Requests are
targeted for completion within 7 business days, subject to legal or documented
security-retention obligations described in the Privacy Policy.

10. OUTPUTS AND HUMAN REVIEW
Model outputs may be incomplete or incorrect. You are responsible for human
review and for decisions made using those outputs.

11. LIMITATION OF LIABILITY
To the maximum extent permitted by applicable law, VerifiMind-PEAS and its
creator are not liable for indirect, incidental, special, consequential, or
punitive damages arising from use of the hosted service.

12. GOVERNING LAW
These Terms are governed by the laws of Malaysia. Disputes should first be
addressed through good-faith negotiation and, if unresolved, through the courts
of Malaysia.

13. OPEN SOURCE
The VerifiMind-PEAS source code is MIT licensed. Hosted-service terms do not
reduce rights granted by that license.

14. CONTACT AND CHANGES
GitHub Discussions:
github.com/creator35lwb-web/VerifiMind-PEAS/discussions
Email: creator35lwb@gmail.com

The current terms are at verifimind.ysenseai.org/terms. This v2.3 revision
clarifies template containment and current availability. It does not introduce
a fee or shorten an existing entitlement.
"""
