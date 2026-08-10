# Early Adopter and Registration Guide

Registration is an optional way to receive a UUID, participate in feedback, and
use registered-tier service controls. It is not required to use the eight
active hosted tools.

## No paid-access or free-period promise

The Early Adopter program does **not** promise a future paid Beta, a three- or
six-month free-access period, or an entitlement to tools that are unavailable
for security maintenance.

The active tools remain free under the Core Tools Always Free pledge.
Registration may affect health-protection rate limits or feedback-cohort
participation, but it does not turn the five unavailable tools on.

Check current terms and availability at:

- [`/register`](https://verifimind.ysenseai.org/register)
- [`/setup`](https://verifimind.ysenseai.org/setup)
- [`/health`](https://verifimind.ysenseai.org/health)
- [Current Production Status](Current-Production-Status)

## Choose the minimum identity you need

### Anonymous use

Use the active tools without a UUID. Normal service-security and rate-limit
logs still apply, but no UUID-linked usage metadata is requested.

### Lightweight registration

Use the current [registration page](https://verifimind.ysenseai.org/register)
to create a pseudonymous UUID after accepting the live policies. Optional
profile fields should be left blank unless they are useful to you.

Save the UUID securely. It is an identifier, not a password, and should not be
posted in an issue, discussion, screenshot, or public transcript.

### Feedback-cohort participation

The service may offer an Early Adopter or Pilot feedback cohort. Cohort capacity,
fields, and benefits are operational facts owned by the live registration
surface and Terms. Do not rely on a historical launch announcement for current
eligibility.

## What a UUID changes

Supplying `user_uuid` on a tool call is optional and separate from
`save_to_history`.

Depending on the live policy and selected tier, a UUID can be used for:

- pseudonymous rate-limit classification;
- a personal usage/status surface;
- bounded UUID-linked validation metadata;
- feedback and consent records.

Omitting a UUID avoids UUID-linked metadata but does not disable ordinary
security, request, or provider processing.

## Aggregate history is a separate choice

`run_full_trinity` defaults `save_to_history` to `false`.

If explicitly enabled, aggregate history is shared within the service instance,
bounded to the newest 20 opt-in results, and has no guaranteed fixed time-based
retention period. It is cleared when the instance is replaced. Exception-
incomplete Trinity runs are not written to it.

Leave `save_to_history=false` for sensitive or confidential concepts. A UUID
does not make aggregate history private or owner-scoped.

## Consent and policy versions

Do not copy policy version numbers from this Wiki into a client. Registration
must bind to the versions and effective dates returned by the live service:

- [Terms](https://verifimind.ysenseai.org/terms)
- [Privacy Policy](https://verifimind.ysenseai.org/privacy)

The policies explain:

- required and optional registration data;
- hosted and BYOK provider processing;
- cross-border processing;
- UUID-linked metadata and aggregate-history behavior;
- retention and security logging;
- access, correction, deletion, withdrawal, and contact channels.

“Z-Protocol” is an internal design framework. It is not a claim that the service
is certified compliant with GDPR, PDPA, or any other law. Legal sufficiency and
statutory questions require qualified counsel.

## Feedback

Use the live registration/feedback surface or
[GitHub Discussions](https://github.com/creator35lwb-web/VerifiMind-PEAS/discussions)
for general product feedback.

Do not include personal data, credentials, UUIDs, confidential concepts, or
security-sensitive details in a public discussion. Security or privacy concerns
should use the private contact channel listed in
[Public Statements](Public-Statements).

## Opt out and request deletion

Use the current [opt-out page](https://verifimind.ysenseai.org/optout) or the
documented API route with your UUID.

The current policy targets remaining personal data for purge within seven
business days, subject to stated legal/security holds. If account storage is
unavailable, the service must not manufacture success: it returns an explicit
unprocessed response and asks the user to retry or use the private policy
contact.

Always verify the live policy before making a retention or deletion
representation.

## Current service availability

Registration does not alter the global tool-containment contract:

- **13 tools defined**
- **8 active**
- **5 temporarily unavailable**

The unavailable set consists of custom-template mutation (2) and public
coordination (3). There is no registered, Early Adopter, Pilot, or anonymous
path around that containment.

## Historical context

The original program launched in an earlier release and its announcement
remains useful as history:

[Discussion #100 — Early Adopter launch](https://github.com/creator35lwb-web/VerifiMind-PEAS/discussions/100)

It is not the source of current benefits, policy versions, availability, or
API behavior.

---

[← Home](Home) · [Installation](Installation) · [Public Statements](Public-Statements)
