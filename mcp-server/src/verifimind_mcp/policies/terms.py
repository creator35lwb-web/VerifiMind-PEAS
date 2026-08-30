"""Canonical plain-text Terms & Conditions served to JSON clients."""

from verifimind_mcp.policies.activation_notice import (
    REGISTRATION_GATE_EFFECTIVE_HUMAN_EN as _GATE_DATE_EN,
)

TERMS_VERSION = "2.5"
TERMS_EFFECTIVE_DATE = "2026-09-02"

TERMS_AND_CONDITIONS = f"""
VerifiMind-PEAS — Terms & Conditions v2.5
Published and effective: September 2, 2026 (previous: v2.4, August 6, 2026)

1. SERVICE DESCRIPTION
VerifiMind-PEAS is an open-source multi-model AI validation framework. Eight
validation and built-in-template tools are currently available. Three coordination
tools and two custom-template mutation tools are discoverable but temporarily
unavailable while owner-scoped controls and URL-fetch protections are rebuilt.

2. ACCEPTANCE
By registering or using the hosted service, you accept these Terms v2.5 and the
Privacy Policy v2.6 at verifimind.ysenseai.org/privacy.

3. ACCESS, TIERS, AND THE ANNOUNCED REGISTRATION REQUIREMENT
Anonymous, Scholar, Early Adopter, and PILOT users may currently use the same 8
active tools. Tier identity is used for rate-limit allocation, cohort management,
and personal dashboard scoping. Three coordination and two custom-template
mutation tools are unavailable to every tier during maintenance.

ADVANCE NOTICE — effective {_GATE_DATE_EN}: the four execution tools
(consult_agent_x, consult_agent_z, consult_agent_cs, run_full_trinity) will
require a free registered UUID, presented as the X-VerifiMind-UUID header.
This applies to hosted-key and BYOK execution alike. The MCP handshake, tool
discovery, template-read tools, and every web page remain available without
registration. Registration is free, takes under a minute at
verifimind.ysenseai.org/register, and does not change what the tools cost:
they remain free. Until that date, anonymous execution remains available.

From that date your UUID also functions as your access credential for the
execution tools: keep it private like a key. A lost UUID can be replaced by
registering again; a compromised UUID can be closed through the private
request channel in Section 14.

Current rate-limit targets are:
  • Anonymous: 10 requests per 60 seconds per IP
  • Scholar: 30 requests per 60 seconds per UUID
  • Early Adopter/PILOT: 100 requests per 60 seconds per UUID

Registration does not create a time-limited access entitlement. No current
service is sold through a paid checkout.

Growth First, Monetization Later: the 8 active tools are free for every tier.
The registration requirement announced above is an identity and abuse-control
measure, not a price change, and does not alter the free-tools pledge. Pricing
for future premium services (such as expert-orchestrated reports) will be
announced separately and will not change the free-tools pledge. The
VerifiMind-PEAS core is MIT licensed — you may self-host at any time, without
registration.

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
  • Impersonate another user or agent, or use another user's UUID
  • Register identities through automated scripts or in bulk
  • Abuse rate limits, scrape excessively, or degrade the service
  • Use outputs as a substitute for qualified legal, medical, security, or
    financial advice

8. SUSPENSION
Access may be limited or suspended to protect users, investigate abuse, comply
with law, or maintain the service. This includes closing registrations created
in violation of Section 7.

9. OPT-OUT AND DELETION
You may request deletion at POST /early-adopters/optout/{{uuid}}. The principal
account PII is de-identified when the request is accepted. Remaining personal
data is targeted for purge within 7 business days. A legal obligation or a
documented security/legal hold may delay or limit deletion as described in the
Privacy Policy. After the registration requirement takes effect, a deleted
registration also ends that UUID's access to the execution tools; you may
register again at any time.

10. OUTPUTS, PROCESSORS, AND HUMAN REVIEW
Model outputs may be incomplete or incorrect. You are responsible for human
review and for decisions made using those outputs. Validation prompts and chained
agent context are sent to the hosted or BYOK AI provider selected for the call;
see Privacy Policy v2.6 for the current providers and processing details.

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
Private account or privacy requests: alton@ysenseai.org (fallback:
creator35lwb@gmail.com). Do not post personal data in a public GitHub Discussion.
General questions may use:
github.com/creator35lwb-web/VerifiMind-PEAS/discussions

This v2.5 revision serves as the advance notice promised by Terms v2.4: it
announces the registration requirement in Section 3 more than 14 days before
that requirement takes effect on {_GATE_DATE_EN}. Every other change in this
revision is effective on publication because it does not introduce a fee,
remove a user right, or shorten an entitlement. Registered users will be
notified of future material adverse changes at least 14 days before they take
effect. The current terms are at
verifimind.ysenseai.org/terms.
"""
