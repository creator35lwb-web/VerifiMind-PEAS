"""Canonical plain-text Privacy Policy served to JSON clients."""

from verifimind_mcp.policies.activation_notice import (
    REGISTRATION_GATE_EFFECTIVE_HUMAN_EN as _GATE_DATE_EN,
    REGISTRATION_GATE_EFFECTIVE_HUMAN_MS as _GATE_DATE_MS,
)

PRIVACY_POLICY_VERSION = "2.6"
PRIVACY_POLICY_EFFECTIVE_DATE = "2026-09-02"

PRIVACY_POLICY = f"""
VerifiMind-PEAS — Privacy Policy and Personal Data Protection Notice v2.6
Published and effective: September 2, 2026 (previous: v2.5, August 6, 2026)

1. WHO WE ARE
The hosted service at verifimind.ysenseai.org is operated by Alton Lee Wei Bin
(YSenseAI, an independent project in Malaysia), who is the data controller for
that service. VerifiMind-PEAS is an open-source multi-model AI validation
framework. This notice also covers its Early Adopter (EA) and PILOT programs.

2. CURRENT SERVICE AVAILABILITY
Eight validation and built-in-template tools are currently available. Three
coordination and two custom-template mutation tools are temporarily unavailable
while owner-scoped controls and URL-fetch protections are rebuilt. No paid
services are active. Registration does not create a time-limited entitlement.
As announced in Section 3, the four execution tools will require a free
registered UUID from {_GATE_DATE_EN}.

3. DATA, SOURCES, AND YOUR CHOICES
We receive data directly from registration, feedback, and validation-tool calls,
and generate limited timestamps, identifiers, and operational records.

Registration through the /register page requires an email address and
acceptance/acknowledgement of the current Terms and Privacy Policy. A name,
feedback, feedback category, and email-update consent are optional. The
lightweight API registration (POST /register) requires only consent; an email
there is optional and used for account recovery and duplicate prevention. We
generate a pseudonymous UUID, registration timestamp, tier/cohort label, and
consent record.

ADVANCE NOTICE — effective {_GATE_DATE_EN}: the four execution tools
(consult_agent_x, consult_agent_z, consult_agent_cs, run_full_trinity) will
require presenting a free registered UUID as the X-VerifiMind-UUID header,
for hosted-key and BYOK execution alike. Until that date, the eight active
tools remain available anonymously. From that date, the MCP handshake, tool
discovery, the template-read tools, and every web page remain available
without registration, and registration remains free. From that date your UUID
also functions as your access credential for the execution tools: keep it
private like a key.

Using a validation tool requires concept or prompt content. Additional context,
BYOK credentials, and save_to_history are optional. Without the required
prompt the requested validation cannot run. IP addresses and request metadata are
automatically processed for rate limiting, service operation, and abuse/security
investigation. Security logs may be correlated with account or UUID activity only
when reasonably needed for those purposes or legal compliance.

We do not intentionally request or store account passwords, API keys, payment
details, precise-location profiles, or browsing profiles as registration fields.
No paid checkout is active and we never sell personal data. Do not submit
passwords, API keys, credentials, or other secrets in registration, feedback, or
validation prompts. Prompt content you submit is processed as described below.

4. PURPOSES
We process data to provide AI validation, identify registered cohorts, allocate
rate limits, operate dashboards, respond to private requests, process feedback,
send updates when separately consented to, prevent abuse, secure and maintain the
service, verify that execution-tool callers hold a registered identity once the
Section 3 requirement takes effect, and retain evidence of consent and
release/security decisions.

5. UUID METADATA AND VALIDATION HISTORY
If you voluntarily supply the user_uuid tool argument, Cloud Logging records the
UUID, tool, tier, and UTC timestamp for 30 days. A pseudonymous Firestore
validation record may also retain the UUID, validation/tool identifiers, scores,
recommendations, quality indicators, and timestamps. It does not include the
submitted concept name or description. Omitting user_uuid prevents that
UUID-linked metadata, but ordinary IP/request security logs may still be
retained.

From {_GATE_DATE_EN}, executing one of the four gated execution tools requires
presenting your registered UUID, and the service then records structured
authorization and run-lifecycle events — your UUID, the tool name, run outcome
and quality/failure metadata, and UTC timestamps — in Cloud Logging for 30
days. These records never include your concept or prompt content. This
recording is a condition of using the gated execution tools; the alternatives
are using the ungated tools and pages anonymously, or self-hosting the MIT-
licensed code. Denied or unverified execution attempts are recorded without
any caller-supplied identifier.

Separately, save_to_history=true on run_full_trinity (off by default) stores the
full result, including submitted concept text, in a shared, instance-local JSON
history. Raw records are not exposed through the public history resources, but
this store is not owner-scoped. It retains at most the 20 newest opt-in results;
the oldest entries are evicted whenever the store is read or written, and an
instance replacement clears the store. Because eviction also depends on instance
activity and lifetime, no fixed time-based retention period is guaranteed. Leave
save_to_history false for private or sensitive concepts.

Runtime custom-template registration and URL import are disabled. The hosted
service exposes built-in templates only and does not currently accept or retain
custom prompt templates.

6. STORAGE, RETENTION, AND CROSS-BORDER PROCESSING
Account, feedback, and UUID-validation records are stored in Google Cloud
Firestore in the United States (us-central1). Operational logs are held in Google
Cloud Logging for 30 days. EA/PILOT account records are retained for the duration
of membership plus 90 days unless deletion is requested earlier. Identifiable
feedback is reviewed for deletion or anonymisation when no longer needed and no
later than six months after the relevant follow-up closes, subject to a lawful or
documented security/legal hold. Pseudonymous UUID-validation records are included
in the scope of an account deletion request, subject to the same holds.

An accepted deletion request immediately de-identifies the principal account PII.
Remaining personal data is targeted for purge within 7 business days. A legal
obligation or documented security/legal hold may delay or limit deletion; where
permitted, we will explain that limitation to the requester. After the Section 3
requirement takes effect, an accepted deletion request also ends that UUID's
access to the execution tools; you may register again at any time.

Validation prompts and chained agent context are processed outside Malaysia when
hosted inference uses the providers in Section 7. Do not submit personal data or
confidential material unless you have authority to send it to those providers.

7. PROCESSORS AND DISCLOSURE
Google Cloud Platform hosts the service, Firestore, and operational logs and may
process account, feedback, validation-metadata, prompt, and request data needed to
provide that infrastructure.

Google Gemini and Groq are the active hosted AI-inference providers. The selected
provider receives the concept/prompt, optional context, and any prior agent output
needed to generate the requested analysis. Z and CS may use Gemini as a
construction-time fallback when Groq cannot be configured; in-flight provider
failover is currently disabled.

If you choose BYOK, your prompt and ephemeral API key are sent to the provider you
select (Google Gemini, Groq, OpenAI, Anthropic, Cerebras, or Mistral; Ollama may run
locally). Provider processing, location, and retention are also governed by the
selected provider's terms and your provider-account settings. BYOK keys are used
for the call and are not intentionally written to application storage.

We may disclose data when required by law or to investigate and contain abuse or
security incidents. We do not sell personal data and no payment processor receives
registration data while paid checkout is inactive.

8. YOUR RIGHTS AND PRIVATE REQUEST CHANNEL
GET /early-adopters/status/{{your-uuid}} returns only a limited account-status
summary; it is not a complete personal-data access response. For a private access,
correction, deletion, consent-withdrawal, inquiry, or complaint request, email
alton@ysenseai.org (fallback: creator35lwb@gmail.com) and include your UUID plus
enough information to verify the request. Do not post personal data in a public
GitHub Discussion. General, non-personal questions may use GitHub Discussions.
A postal address for formal private correspondence is available through the same
verified email channel.

You may stop the optional user_uuid argument's analytics by omitting it, leave
save_to_history=false to avoid the shared full-result history, and withdraw
optional email-update consent. These requests are free of charge. From
{_GATE_DATE_EN}, the Section 5 authorization and lifecycle records are a
condition of gated-tool execution and cannot be disabled while using those
tools; the ungated tools, all pages, and self-hosting remain available without
them.

9. SECURITY AND COOKIES
We use restricted infrastructure access and data minimisation, but no hosted
service can guarantee absolute security. VerifiMind-PEAS does not use tracking
cookies.

10. CONTACT
Private privacy/data requests: alton@ysenseai.org
Fallback email: creator35lwb@gmail.com
General public discussion:
github.com/creator35lwb-web/VerifiMind-PEAS/discussions

11. CHANGES
This v2.6 notice serves as the advance notice promised by v2.5: it announces
the registration requirement and its associated processing in Sections 3 and 5
more than 14 days before they take effect on {_GATE_DATE_EN}. Its other
clarifications (the lightweight registration path, denial records without
caller identifiers) are effective on publication because they do not introduce
a fee, remove a user right, or shorten an entitlement. We will notify
registered users of future material adverse changes at least 14 days before
they take effect. The current notice is always available at
verifimind.ysenseai.org/privacy.

12. NOTIS PERLINDUNGAN DATA PERIBADI — BAHASA MALAYSIA
Versi 2.6 — Diterbitkan dan berkuat kuasa pada 2 September 2026

SIAPA KAMI
Perkhidmatan di verifimind.ysenseai.org dikendalikan oleh Alton Lee Wei Bin
(YSenseAI, projek bebas di Malaysia), selaku pengawal data bagi perkhidmatan ini.
Notis ini turut meliputi program Early Adopter (EA) dan PILOT.

DATA, SUMBER DAN PILIHAN ANDA
Kami menerima data terus daripada borang pendaftaran, maklum balas dan panggilan
alat validasi, serta menjana cap masa, UUID samaran dan rekod operasi yang terhad.
Pendaftaran melalui halaman /register memerlukan alamat e-mel serta
penerimaan/pengakuan Terma dan Dasar Privasi. Nama, maklum balas dan persetujuan
menerima e-mel kemas kini adalah pilihan. Pendaftaran ringan melalui API
(POST /register) hanya memerlukan persetujuan; e-mel adalah pilihan.

NOTIS AWAL — berkuat kuasa {_GATE_DATE_MS}: empat alat pelaksanaan
(consult_agent_x, consult_agent_z, consult_agent_cs, run_full_trinity) akan
memerlukan UUID berdaftar percuma yang dihantar sebagai pengepala
X-VerifiMind-UUID, bagi pelaksanaan kunci hos dan BYOK. Sehingga tarikh itu,
lapan alat aktif masih boleh digunakan secara tanpa nama. Selepas tarikh itu,
penemuan alat, alat bacaan templat dan semua halaman web kekal boleh diakses
tanpa pendaftaran, dan pendaftaran kekal percuma. UUID anda juga berfungsi
sebagai kelayakan akses bagi alat pelaksanaan: rahsiakannya seperti kunci.

Penggunaan alat memerlukan kandungan konsep atau arahan. Konteks tambahan,
kelayakan BYOK dan save_to_history adalah pilihan. Alamat IP dan metadata
permintaan diproses secara automatik untuk had kadar, operasi, keselamatan dan
pencegahan penyalahgunaan. Kami tidak meminta kata laluan akaun, kunci API,
butiran pembayaran atau rahsia sebagai medan pendaftaran. Jangan masukkan rahsia
dalam arahan, pendaftaran atau maklum balas.

TUJUAN PEMPROSESAN
Data digunakan untuk menyediakan validasi AI, mengurus kohort dan had kadar,
mengendalikan papan pemuka, menjawab permintaan peribadi, memproses maklum balas,
menghantar kemas kini dengan persetujuan berasingan, mencegah penyalahgunaan,
menjaga keselamatan perkhidmatan, mengesahkan bahawa pemanggil alat pelaksanaan
mempunyai identiti berdaftar selepas keperluan itu berkuat kuasa, dan menyimpan
bukti persetujuan.

UUID DAN SEJARAH VALIDASI
Jika argumen user_uuid diberikan secara sukarela, Cloud Logging menyimpan UUID,
alat, tahap dan cap masa UTC selama 30 hari. Firestore juga boleh menyimpan
metadata validasi samaran seperti skor, cadangan, ID validasi, petunjuk kualiti
dan cap masa, tetapi bukan nama atau penerangan konsep. Tanpa UUID, metadata
berkaitan UUID tidak disimpan; log keselamatan IP/permintaan biasa masih boleh
disimpan.

Mulai {_GATE_DATE_MS}, pelaksanaan empat alat berpagar memerlukan UUID
berdaftar anda, dan perkhidmatan kemudian merekodkan peristiwa kebenaran dan
kitaran larian berstruktur — UUID anda, nama alat, hasil larian serta metadata
kualiti/kegagalan, dan cap masa UTC — dalam Cloud Logging selama 30 hari.
Rekod ini tidak pernah mengandungi kandungan konsep atau arahan anda.
Perekodan ini adalah syarat penggunaan alat pelaksanaan berpagar; alternatifnya
ialah menggunakan alat dan halaman tanpa pagar secara tanpa nama, atau
mengehos sendiri kod berlesen MIT. Percubaan pelaksanaan yang ditolak atau
tidak disahkan direkodkan tanpa sebarang pengecam yang dibekalkan pemanggil.

save_to_history=true (lalai: false) menyimpan keputusan penuh termasuk teks
konsep dalam sejarah JSON setempat kepada instans yang dikongsi dan belum
diasingkan mengikut pemilik. Rekod mentah tidak dipaparkan melalui sumber sejarah
awam. Hanya 20 keputusan pilihan masuk yang terbaharu dikekalkan; rekod tertua
dikeluarkan apabila stor dibaca atau ditulis, dan penggantian instans mengosongkan
stor. Tiada tempoh simpanan berasaskan masa yang tetap kerana pengeluaran juga
bergantung pada aktiviti dan jangka hayat instans. Kekalkan false untuk konsep
peribadi atau sensitif.

STORAN, TEMPOH SIMPANAN DAN PEMINDAHAN RENTAS SEMPADAN
Rekod akaun, maklum balas dan metadata validasi disimpan dalam Google Cloud
Firestore di Amerika Syarikat (us-central1). Log operasi disimpan 30 hari. Rekod
EA/PILOT disimpan sepanjang keahlian tambah 90 hari kecuali pemadaman diminta
lebih awal. Maklum balas yang boleh dikenal pasti disemak untuk pemadaman atau
penyahpengenalan selewat-lewatnya enam bulan selepas tindakan susulan tamat,
tertakluk kepada undang-undang atau penahanan keselamatan/undang-undang yang
didokumenkan.

Apabila permintaan pemadaman diterima, maklumat peribadi utama akaun dinyahkenal
pasti dengan segera dan baki data peribadi disasarkan untuk dipadam dalam 7 hari
bekerja. Kewajipan undang-undang atau penahanan yang didokumenkan boleh mengehadkan
atau melambatkan pemadaman. Selepas keperluan pendaftaran berkuat kuasa,
permintaan pemadaman yang diterima turut menamatkan akses UUID itu kepada alat
pelaksanaan; anda boleh mendaftar semula pada bila-bila masa.

PEMPROSES DAN PENZAHIRAN
Google Cloud Platform menyediakan hos, Firestore dan log. Google Gemini dan Groq
ialah penyedia inferens AI hos yang aktif; penyedia terpilih menerima arahan,
konsep, konteks pilihan dan output ejen terdahulu yang diperlukan. Z dan CS boleh
menggunakan Gemini sebagai sandaran semasa pembinaan jika Groq tidak dapat
dikonfigurasi; pertukaran penyedia semasa permintaan sedang berjalan tidak aktif.

Jika anda memilih BYOK, arahan dan kunci API sementara dihantar kepada penyedia
pilihan anda (Google Gemini, Groq, OpenAI, Anthropic, Cerebras atau Mistral;
Ollama boleh berjalan secara tempatan). Pemprosesan, lokasi dan tempoh simpanan
penyedia turut tertakluk kepada terma penyedia dan tetapan akaun anda. Data juga
boleh dizahirkan apabila diwajibkan undang-undang atau untuk menyiasat insiden
keselamatan. Data peribadi tidak dijual.

HAK DAN SALURAN PERMINTAAN PERIBADI
GET /early-adopters/status/{{uuid}} hanya memberikan ringkasan status dan bukan
jawapan akses data yang lengkap. Untuk akses, pembetulan, pemadaman, penarikan
persetujuan, pertanyaan atau aduan secara peribadi, e-mel alton@ysenseai.org
(sandaran: creator35lwb@gmail.com) dengan UUID dan maklumat yang mencukupi untuk
pengesahan. Jangan siarkan data peribadi dalam GitHub Discussion awam. Alamat pos
untuk surat-menyurat rasmi boleh diperoleh melalui saluran e-mel yang disahkan.
Anda boleh menghentikan analitik argumen user_uuid dengan tidak memberikannya,
mengekalkan save_to_history=false, dan menarik persetujuan e-mel pilihan. Mulai
{_GATE_DATE_MS}, rekod kebenaran dan kitaran larian adalah syarat pelaksanaan
alat berpagar dan tidak boleh dimatikan semasa menggunakan alat tersebut; alat
tanpa pagar, semua halaman dan pengehosan sendiri kekal tersedia tanpanya.

KESELAMATAN, KUKI DAN PERUBAHAN
Kami menggunakan akses infrastruktur terhad dan peminimuman data, tetapi tiada
perkhidmatan hos dapat menjamin keselamatan mutlak. Kami tidak menggunakan kuki
penjejakan. Versi 2.6 ialah notis awal yang dijanjikan oleh v2.5: ia mengumumkan
keperluan pendaftaran dan pemprosesan berkaitannya lebih daripada 14 hari sebelum
ia berkuat kuasa pada {_GATE_DATE_MS}. Pengguna berdaftar akan dimaklumkan
sekurang-kurangnya 14 hari sebelum perubahan material yang memudaratkan pada masa
hadapan berkuat kuasa.
"""
