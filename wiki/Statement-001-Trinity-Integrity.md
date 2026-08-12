<h1>Statement 001 — Trinity Integrity, Legal Truth, and What Live Testing Found</h1>

<p>
<img src="https://img.shields.io/badge/statement-001-informational" alt="Statement 001">
<img src="https://img.shields.io/badge/releases-v0.5.56%20%C2%B7%20v0.5.57%20%C2%B7%20v0.5.58-success" alt="Releases">
<img src="https://img.shields.io/badge/published-2026--08--08-lightgrey" alt="Published">
</p>

<p><strong>Published:</strong> 2026-08-08 · <strong>Covers:</strong> v0.5.56, v0.5.57, v0.5.58 · <strong>Status:</strong> Current</p>

<blockquote>
<p>Three releases in three days. This statement covers all of them — including two defects that live testing found <em>after</em> the first one shipped, and one that our own catalogue check found in production.</p>
</blockquote>

<hr>

<h2>The idea behind all three</h2>

<p><strong>A validation result should never look more complete than it actually is.</strong></p>

<p>VerifiMind runs three independent AI seats over a concept — X for opportunity, Z for ethics, CS for security — and synthesises a verdict. The failure mode that matters is not a crash. It is a result that <em>looks</em> finished when one of the three seats did not really work. That produces a confident number nobody should trust, and it is worse than an error, because an error is visible.</p>

<p>These three releases exist to make that impossible.</p>

<hr>

<h2>v0.5.56 — degradation fails closed</h2>

<p>If any Trinity stage returns anything other than real inference, that stage can no longer contribute a score, a confidence value, a verdict, or a derived count. You get an explicitly incomplete result marked for human review, with the failing stage named and its generated fields withheld. A trusted ethics veto still takes precedence.</p>

<p><strong>Security.</strong> A time-of-check/time-of-use DNS-rebinding weakness in the template URL-fetch paths was closed: addresses are resolved once and only validated public addresses are dialled, while the original hostname is preserved for TLS certificate verification.</p>

<p><strong>Terms v2.3 and Privacy Policy v2.4</strong>, rendered from a single canonical source so the browser page and the API response cannot drift apart. They state where data is actually stored, name the AI providers that process validation prompts, describe cross-border processing, and give a <strong>private email channel</strong> for access, correction and deletion requests. There is a <strong>Bahasa Malaysia</strong> section.</p>

<hr>

<h2>Then we tested it live — and found two things</h2>

<p>The day v0.5.56 shipped, testing against production surfaced two real defects. We report them here rather than quietly fixing them, because a release about not overstating completeness cannot open by overstating its own.</p>

<h3>1. The plain-language summary could contradict its own analysis</h3>

<p>It could state <em>"no major ethical or legal concerns"</em> while simultaneously listing an ethical concern it had received. The underlying analysis was correct; the summary line was not.</p>

<p>Investigating it found something the original report could not have seen: <strong>the same fault existed on the security side too</strong>, where a high security score produced <em>"no significant security risks identified"</em> while a vulnerability was listed directly beneath it. The cause in both cases was the same — a numeric score threshold rendered as an absolute claim of absence.</p>

<h3>2. A provider rate-limit destroyed the entire validation</h3>

<p>When a hosted AI provider rate-limited us or returned a truncated response, the whole run failed with a generic error and an unhelpful hint — discarding two stages that had completed successfully alongside the one that failed.</p>

<p>Production logs identified both causes precisely: one token-rate rejection, and one truncation that <strong>our own v0.5.56 guard correctly refused to parse</strong> as a complete stage. The refusal was right. The way we reported it was not.</p>

<p><strong>Neither defect caused an incorrect validation to be presented as correct.</strong></p>

<hr>

<h2>v0.5.57 — post-release repair</h2>

<ul>
<li><strong>Deletion requests no longer fail silently.</strong> Storage failures now return a structured, non-enumerating, retryable <strong>HTTP 503</strong>. A failed operation is never reported as successful.</li>
<li><strong>Opt-in validation history is bounded</strong> — at most the 20 newest results, oldest evicted on every read and write, written atomically, with persistence reported truthfully.</li>
<li><strong>One source for legal text</strong> — duplicate policy copies removed.</li>
<li><strong>Terms v2.4 and Privacy Policy v2.5</strong>, English and Bahasa Malaysia, describing the retention contract in the same words the code enforces.</li>
</ul>

<hr>

<h2>v0.5.58 — the repair for what live testing found</h2>

<ul>
<li><strong>A provider failure no longer destroys the whole validation.</strong> The affected stage degrades and is named — with its provider and model — while the stages that succeeded are preserved. The result is explicitly incomplete; it can never present as complete.</li>
<li><strong>Typed failure reporting</strong> — rate limit, truncation, timeout and authentication failures each carry an accurate retryable flag and a recovery hint specific to the <em>actual</em> failure, replacing a generic message that suggested changing a setting the caller had never used.</li>
<li><strong>The summary can no longer contradict its own analysis</strong> — fixed on the ethics surface and the security surface.</li>
<li><strong>Incomplete runs are never written to shared history.</strong></li>
<li><strong>Provider logs are sanitized</strong> — failure events carry an exception type, never a response body, key, or provider account metadata.</li>
<li><strong>Model catalogue currency</strong> across all six BYOK providers: a retired-model gate and a 90-day verification ceiling. <strong>This fixed a live defect</strong> where our Cerebras default pointed at a decommissioned model and failed for anyone who selected it.</li>
</ul>

<hr>

<h2>How these were verified</h2>

<table>
<thead>
<tr><th align="left">Release</th><th align="left">Internal review</th><th align="left">Independent security review</th><th align="left">Post-deploy smoke</th></tr>
</thead>
<tbody>
<tr><td><strong>v0.5.56</strong></td><td>2 seats, multiple rounds</td><td><strong>2 runs</strong> — different model family and platform</td><td>24 passed / 0 failed</td></tr>
<tr><td><strong>v0.5.57</strong></td><td>2 seats</td><td><strong>1 run</strong> — with a parent-commit differential</td><td>25 passed / 0 failed</td></tr>
<tr><td><strong>v0.5.58</strong></td><td>2 seats</td><td><strong>1 run</strong> — fault injection incl. simultaneous all-stage failure</td><td><strong>31 passed / 0 failed</strong></td></tr>
</tbody>
</table>

<p>Independent reviews were run on a different model family, on a different platform, from a clean checkout of the exact commit, with the reviewer required to prove its own checkout before its verdict was accepted.</p>

<details>
<summary><strong>The verification detail we think matters most</strong> (click to expand)</summary>

<p>For v0.5.57, the independent reviewer ran the new regression tests <strong>against the previous commit</strong> and confirmed <strong>16 of them fail there</strong>. That is the difference between a test suite that passes and a test suite that would have <em>noticed</em>. We reproduced that result independently, test by test.</p>

<p>Read the other way, those 16 failures are an itemised list of what was actually wrong before: history that was never capped, a crash on a malformed history file, storage exceptions escaping as generic errors, and a duplicate policy copy that could drift.</p>

<p>For v0.5.58, the independent reviewer injected typed failures — rate limit, truncation, authentication, and <strong>all three stages failing at once</strong> — and confirmed that even a total failure produces a withheld, explicitly incomplete result rather than a confident empty verdict. That all-stage case was the one our internal review had <em>not</em> tested.</p>
</details>

<hr>

<h2>Then production proved it, by accident</h2>

<blockquote>
<p>During the post-deploy smoke for v0.5.58 — minutes after it went live — <strong>a real, unplanned provider failure occurred.</strong></p>
<p>One stage failed. The other two returned genuine analysis. The run degraded the failed stage, named it, withheld its fields, and marked the result incomplete.</p>
<p>Under the previous release, that same event would have returned a bare error and discarded two stages of successful work.</p>
</blockquote>

<p>We did not plan this test. It is the strongest evidence in this statement precisely because we did not.</p>

<hr>

<h2>What is still open</h2>

<ul>
<li><strong>The coordination tools remain disabled.</strong> That incident is <strong>contained, not closed</strong> — see <a href="Public-Statements">Standing disclosures</a>. Statutory notification questions are with qualified counsel on a separate track.</li>
<li><strong>Model diversity.</strong> Our three-seat design assumes three independent perspectives. We found that two of the three seats were running the <em>same</em> model, which weakens that premise. We have measured a configuration of three seats across three providers and three model families, and are validating it before it ships. The rate-limit failure above is what exposed this.</li>
<li><strong>No legal certification.</strong> Nothing in these releases or this statement is a legal determination or a claim of regulatory compliance.</li>
</ul>

<hr>

<h2>Unchanged</h2>

<p>All <strong>8 active tools remain free for every tier</strong>. The core is <strong>MIT licensed</strong> and you can self-host at any time.</p>

<hr>

<h2>Provenance</h2>

<p>Each release is bound to an exact commit and build, and each GitHub Release tag resolves to the deployed commit:</p>

<table>
<thead>
<tr><th align="left">Release</th><th align="left">Merge commit</th><th align="left">Deployed</th></tr>
</thead>
<tbody>
<tr><td><a href="https://github.com/creator35lwb-web/VerifiMind-PEAS/releases/tag/v0.5.56">v0.5.56</a></td><td><code>40a48924</code></td><td>2026-08-05</td></tr>
<tr><td><a href="https://github.com/creator35lwb-web/VerifiMind-PEAS/releases/tag/v0.5.57">v0.5.57</a></td><td><code>6faadef5</code></td><td>2026-08-06</td></tr>
<tr><td><a href="https://github.com/creator35lwb-web/VerifiMind-PEAS/releases/tag/v0.5.58">v0.5.58</a></td><td><code>3019f5c4</code></td><td>2026-08-07</td></tr>
</tbody>
</table>

<p>Full technical detail: <a href="https://github.com/creator35lwb-web/VerifiMind-PEAS/blob/main/CHANGELOG.md">CHANGELOG.md</a> · Live status: <a href="https://verifimind.ysenseai.org/health">/health</a> · <a href="https://verifimind.ysenseai.org/terms">Terms</a> · <a href="https://verifimind.ysenseai.org/privacy">Privacy</a></p>

<hr>

<p><em>Corrections to this statement will be published as dated addenda below, never as silent edits.</em></p>
