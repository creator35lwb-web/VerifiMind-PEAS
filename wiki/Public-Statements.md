<h1>Public Statements &amp; Disclosures</h1>

<p><em>A permanent, dated record of what we shipped, what went wrong, and how each claim was verified.</em></p>

<blockquote>
<p><strong>Why this page exists.</strong> VerifiMind-PEAS is a tool for checking whether AI-generated conclusions are trustworthy. A project making that claim should be checkable itself. This is where we publish technical statements and security disclosures in full — including the defects we found in our own work, and the ones found by others.</p>
<p>We publish the failures alongside the fixes. A record that only contains good news is not a record.</p>
</blockquote>

<hr>

<h2>Statements</h2>

<table>
<thead>
<tr><th align="left">#</th><th align="left">Statement</th><th align="left">Date</th><th align="left">Covers</th><th align="left">Status</th></tr>
</thead>
<tbody>
<tr>
<td><strong>001</strong></td>
<td><a href="Statement-001-Trinity-Integrity">Trinity Integrity, Legal Truth, and What Live Testing Found</a></td>
<td>2026-08-08</td>
<td>v0.5.56 · v0.5.57 · v0.5.58</td>
<td>Current</td>
</tr>
</tbody>
</table>

<hr>

<h2>Standing disclosures</h2>

<p>Matters that remain open across releases. These are restated here so their status is never inferred from silence.</p>

<h3>Coordination subsystem — contained, not closed</h3>

<p>Three multi-agent coordination tools were disabled in July 2026 following a security incident. They remain disabled and will not be restored until owner-scoped access control is built and separately authorized.</p>

<ul>
<li><strong>Status:</strong> <strong>CONTAINED</strong> — the vulnerable code paths were removed, not merely gated, and the containment was verified from an anonymous caller's position.</li>
<li><strong>Not closed.</strong> Containment is not resolution. Questions of statutory notification are with qualified legal counsel on a separate track and are <strong>not</strong> represented as settled.</li>
<li><strong>Affected tools:</strong> <code>coordination_handoff_create</code>, <code>coordination_handoff_read</code>, <code>coordination_team_status</code>. Every other tool is unaffected.</li>
</ul>

<p><strong>We are not asserting that no unauthorised access occurred.</strong> Our request logs and tool telemetry could not be correlated at the time, so we cannot determine what was read. That is a limitation of our logging, not a finding of safety, and we state it that way deliberately.</p>

<h3>Custom-template tools — temporarily unavailable</h3>

<p><code>register_custom_template</code> and <code>import_template_from_url</code> are disabled while owner-scoped storage and URL-fetch protections are completed. The service reports <strong>13 tools defined, 8 active, 5 temporarily unavailable</strong> consistently on every surface.</p>

<hr>

<h2>What we do not claim here</h2>

<ul>
<li><strong>No legal or regulatory certification.</strong> Nothing on these pages is a legal determination or a claim of compliance with any statute.</li>
<li><strong>No claim that our verification is exhaustive.</strong> Each statement records what was checked and by whom. Things not listed were not checked.</li>
<li><strong>No retroactive edits.</strong> Statements are corrected by addendum with a date, never by silent revision.</li>
</ul>

<hr>

<h2>Reporting something to us</h2>

<p>Security or privacy concerns: <strong>alton@ysenseai.org</strong> — please do not post personal data in a public issue or discussion. General questions are welcome in <a href="https://github.com/creator35lwb-web/VerifiMind-PEAS/discussions">Discussions</a>.</p>
