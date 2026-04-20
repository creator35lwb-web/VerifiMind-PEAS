"""
VerifiMind-PEAS Terms & Conditions — v2.0
Pioneer subscription tier + Polar merchant of record.
Effective: April 8, 2026
"""

TERMS_VERSION = "2.0"
TERMS_EFFECTIVE_DATE = "2026-04-08"

TERMS_AND_CONDITIONS = """
VerifiMind-PEAS — Terms & Conditions v2.0
Effective: April 8, 2026 (previous: v1.0, March 18, 2026)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. SERVICE DESCRIPTION
VerifiMind-PEAS is an open-source multi-model AI validation framework that
provides structured, multi-agent validation and orchestration tools. The service
is offered in tiered access levels as described in Section 3.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

2. ACCEPTANCE OF TERMS
By registering for any VerifiMind-PEAS program or using the service, you confirm
that you have read and accept:
  • These Terms & Conditions v2.0
  • The Privacy Policy v2.0 at verifimind.ysenseai.org/privacy
  • Polar's Master Services Terms at polar.sh/legal/master-services-terms
    (applicable to Pioneer tier subscribers)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

3. SERVICE TIERS

  Tier          Identity   Access                              Price          Rate Limit
  ────────────────────────────────────────────────────────────────────────────────────────
  Anonymous     None       All 10 Trinity validation tools +   Free forever   10 req/60s
                (IP only)  templates. No registration needed.                 (per IP)
  Scholar       UUID       Same tools + usage dashboard +       Free forever   30 req/60s
                (consent)  Trinity history. Register at /register.            (per UUID)
  Early Adopter UUID +     All Scholar tools + Pioneer          Free 3 months  100 req/60s
  (EA)          email      coordination tools                   then Pioneer   (per UUID)
  PILOT         UUID +     All Scholar tools + Pioneer          Free 6 months  100 req/60s
                email      coordination tools                   then Pioneer   (per UUID)
  Pioneer       UUID +     All Scholar + 6 coordination         $9/month (USD) 100 req/60s
                payment    tools (handoff mgmt, team status,    Monthly        (per UUID)
                           session coordination)

The Anonymous tier provides full Trinity access with zero friction and no
registration. The Scholar tier is free forever and adds UUID-based identity,
usage analytics (opt-in via user_uuid parameter), and a personal dashboard.
You never lose Scholar access by registering for any program.
The core is MIT licensed — self-host anytime.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

4. PAYMENT AND BILLING

4.1 Merchant of Record
All paid subscriptions are processed by Polar Software Inc ("Polar"), which
acts as the merchant of record. Polar handles all payment processing, tax
calculation, invoicing, and billing via Stripe Connect. By subscribing to the
Pioneer tier, you also agree to:
  • Polar's Master Services Terms: polar.sh/legal/master-services-terms
  • Polar's Acceptable Use Policy: polar.sh/legal/acceptable-use-policy

4.2 Subscription Terms
  • Pioneer subscriptions are billed monthly in USD
  • Subscriptions auto-renew unless cancelled
  • You may cancel anytime through the Polar customer portal or by contacting us
  • Cancellation takes effect at end of current billing period — full access retained
  • Local taxes may apply and are calculated by Polar based on your location

4.3 Free Period Transition
  • You will receive at least 14 days' advance notice before any billing begins
  • You will never be charged without explicit action on your part
  • If you do not subscribe after your free period ends, access reverts to Scholar
    with no penalty
  • You may subscribe to Pioneer at any time after your free period ends

4.4 Alternative Payment
Multiple payment methods available through Polar checkout: credit card, US bank
account, Cash App Pay, Apple Pay and Google Pay (device dependent). A
BuyMeACoffee page (PayPal) is also available as a backup support channel.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

5. REFUND POLICY

5.1 14-Day Money-Back Guarantee
If you are not satisfied with the Pioneer tier, you may request a full refund
within 14 days of your first subscription payment. No questions asked.

5.2 After 14 Days
No prorated refunds after the initial 14-day period. You may cancel anytime;
cancellation takes effect at end of the current billing period.

5.3 How to Request a Refund
  • Polar customer portal (link in your subscription confirmation email)
  • Email: creator35lwb@gmail.com
  • GitHub Discussions: github.com/creator35lwb-web/VerifiMind-PEAS/discussions
  Refunds are processed by Polar and typically appear within 5-10 business days.

5.4 Dispute Resolution
Payment disputes are handled through Polar's buyer protection process. Please
contact us directly before initiating a payment dispute.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

6. BETA SOFTWARE
The Pioneer coordination tools are currently in beta. You accept that:
  • Features may change, be added, or removed as the product evolves
  • There is no uptime SLA during the beta period
  • Backwards compatibility is not guaranteed between beta versions
  • The service is provided "as is" without warranties of any kind

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

7. YOUR FEEDBACK
  • Any feedback you submit is voluntary
  • We may use your feedback to improve the product
  • We may quote feedback anonymously, but never with your name or email
    unless you give separate explicit consent
  • Submitting feedback does not grant you ownership of or compensation for
    product improvements derived from it

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

8. ACCEPTABLE USE
You agree not to:
  • Share, resell, or redistribute your Pioneer access key or credentials
  • Use automated scraping or excessive API calls that degrade service for others
  • Use VerifiMind-PEAS tools to generate harmful, misleading, or unethical content

Violation may result in suspension or termination of your access. This section
supplements Polar's Acceptable Use Policy: polar.sh/legal/acceptable-use-policy

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

9. OPT-OUT AND TERMINATION
  • You may opt out at any time: POST /early-adopters/optout/{uuid}
  • On opt-out, personal data is purged within 7 business days (subject to legal
    retention requirements for completed transactions)
  • We may terminate access for violation of the Acceptable Use terms in Section 8
  • If we terminate your paid subscription due to a violation, no refund is issued

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

10. LIMITATION OF LIABILITY
To the maximum extent permitted by applicable law, VerifiMind-PEAS and its
creator shall not be liable for any indirect, incidental, special, consequential,
or punitive damages, or any loss of profits or revenues, whether incurred directly
or indirectly, or any loss of data, use, goodwill, or other intangible losses
resulting from your use of the service.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

11. GOVERNING LAW
These Terms are governed by the laws of Malaysia. Any disputes shall be resolved
through good-faith negotiation first, and if unresolved, through the courts of
Malaysia.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

12. CHANGES TO THESE TERMS
We will notify registered users of material changes at least 14 days before they
take effect. Continued use after the effective date constitutes acceptance. The
current version is always available at:
  verifimind.ysenseai.org/terms

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

13. OPEN SOURCE
The VerifiMind-PEAS core is MIT licensed and remains open source. Your
registration or subscription does not affect your rights under the MIT license.
You may self-host the Scholar tier at any time.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

14. CONTACT
  GitHub Discussions: github.com/creator35lwb-web/VerifiMind-PEAS/discussions
  Email: creator35lwb@gmail.com
  X (Twitter): x.com/creator35lwb

VerifiMind-PEAS is open source: github.com/creator35lwb-web/VerifiMind-PEAS
"""
