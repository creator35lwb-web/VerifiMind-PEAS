# Third-Party Notices

VerifiMind-PEAS (MIT) redistributes and depends on the third-party components
below — the OAuth dependency closure (Authlib, joserfc, cryptography). The
other exact pins in `pyproject.toml` are outside the scope of this notice.
Each component remains governed by its own license. For each component listed
below this notice reproduces the complete license text — copyright notice,
conditions, and disclaimer — **verbatim** from the exact pinned release
artifact, together with SHA-256 receipts that bind the reproduced bytes to that
artifact. No license text is paraphrased; the short explanatory prose in each
section is not a substitute for the reproduced text. This is a technical
redistribution and attribution record; it is not legal advice and makes no
legal-certification claim.

## Provenance method (2026-09-02)

| Step | Evidence |
|---|---|
| Pins | `Authlib==1.8.0`, `joserfc==1.7.5`, `cryptography==46.0.1` in `pyproject.toml` (the deployment dependency authority) and `requirements.txt`; parity is enforced locally by `tests/unit/test_dependency_manifest_parity.py` and inside the built production image by the `Production Image Dependency Parity` CI job. |
| Artifacts | Every wheel and sdist listed below was downloaded from PyPI and its SHA-256 verified equal to the digest PyPI publishes for that file. |
| License files | Every license file inside every listed artifact was extracted and verified byte-identical to the copy pip installs at `<dist>.dist-info/licenses/`. The blocks below are those exact bytes. `tests/unit/test_third_party_notices.py` re-verifies each block byte-for-byte against the installed pinned distribution in CI. |
| Publisher provenance | PyPI attestation bundles (PEP 740) were retrieved from `https://pypi.org/integrity/<name>/<version>/<file>/provenance` for the artifacts named in each section; each bundle names the GitHub Trusted Publisher repository and workflow recorded there. |
| Runtime target | Production image base `ghcr.io/astral-sh/uv:python3.12-bookworm-slim`. Authlib and joserfc install from pure-Python wheels (`py2.py3-none-any`, `py3-none-any`). For the x86_64 Cloud Run target, cryptography is expected to resolve to a `cp311-abi3-manylinux*_x86_64` wheel (pip's resolution for cp3.12 / x86_64 / glibc 2.36 selects `manylinux_2_34`; the image build does not print the chosen wheel tag, so uv's exact selection is not receipted here). The license files are byte-identical across every artifact listed, including each sdist. The image carries these upstream license files at `<dist>.dist-info/licenses/` (installed by `uv pip install`); this notice file itself is not copied into the image because `.dockerignore` excludes `*.md` — recorded as a follow-up for the release lane, not changed here. |

Each reproduced file is fenced by `LICENSE-FILE` markers carrying its installed
path and the SHA-256 of the reproduced bytes.

## Authlib 1.8.0 — BSD-3-Clause

OAuth 2.1 authorization-server protocol core (D-ALTON-2026-09-01-AUTHLIB).

- Homepage: https://authlib.org/ · Documentation: https://docs.authlib.org/
- Source: https://github.com/authlib/authlib (tag `v1.8.0`,
  commit `1a86748b31a2b1940b09cf627d1b70e03d85c077`)
- PyPI: https://pypi.org/project/Authlib/1.8.0/ — both artifacts below carry a
  PyPI attestation bundle (Trusted Publisher: GitHub `authlib/authlib`,
  workflow `pypi.yml`)
- Package METADATA: `License: BSD-3-Clause` · `License-File: LICENSE` ·
  `Author-email` name: Hsiaoming Yang
- Release artifacts (PyPI, uploaded 2026-08-30):
  - `authlib-1.8.0-py2.py3-none-any.whl` — SHA-256
    `88aebbd9af6757e14e912d5dc007ae1dc1f3e27e3b2152ce7c552ee2c3b3c121`
  - `authlib-1.8.0.tar.gz` — SHA-256
    `f3ecd5f1da737262fb53bf1a4d95c4ea1ad9dd509316587a255c99ab1838a4f0`
- License file `LICENSE` — 1514 bytes — SHA-256 `8e1b48518de9c6cd00cb48c7fe5b8023fd90d5552ca12ebe7362a0df30ddbe45`
  (identical in the wheel, the sdist, and the installed distribution)

The full license text is reproduced below and governs this redistribution.
VerifiMind makes no claim of endorsement by the copyright holder or the
Authlib maintainers.

### `LICENSE` — verbatim

<!-- LICENSE-FILE: authlib-1.8.0.dist-info/licenses/LICENSE sha256=8e1b48518de9c6cd00cb48c7fe5b8023fd90d5552ca12ebe7362a0df30ddbe45 -->
```text
BSD 3-Clause License

Copyright (c) 2017, Hsiaoming Yang
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

* Redistributions of source code must retain the above copyright notice, this
  list of conditions and the following disclaimer.

* Redistributions in binary form must reproduce the above copyright notice,
  this list of conditions and the following disclaimer in the documentation
  and/or other materials provided with the distribution.

* Neither the name of the copyright holder nor the names of its
  contributors may be used to endorse or promote products derived from
  this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
```
<!-- END-LICENSE-FILE -->

## joserfc 1.7.5 — BSD-3-Clause

JOSE / issuer-validation support in Authlib's dependency closure. Pinned at
1.7.5 (>=1.7.3 carries the issuer-validation fix, advisory
GHSA-r74j-q665-7rpj).

- Source: https://github.com/authlib/joserfc ·
  Documentation: https://jose.authlib.org/
- PyPI: https://pypi.org/project/joserfc/1.7.5/ — both artifacts below carry a
  PyPI attestation bundle (Trusted Publisher: GitHub `authlib/joserfc`,
  workflow `pypi.yml`)
- Package METADATA: `License: BSD-3-Clause` · `License-File: LICENSE` ·
  `Author-email` name: Hsiaoming Yang
- Release artifacts (PyPI, uploaded 2026-08-29):
  - `joserfc-1.7.5-py3-none-any.whl` — SHA-256
    `add2c2c84e8373b084d526a8b53daba5d7a513a118cd2dcd9fc9f979d0922159`
  - `joserfc-1.7.5.tar.gz` — SHA-256
    `d5ff536e658e17664f8c1b1ab60dc4aa62aa973fcef1edd33cc44bda45d6f5ea`
- License file `LICENSE` — 1501 bytes — SHA-256 `19ee1fafcc9ec4217fc32b8a651d820538c789cf4041cb4e46b4b176a5f2a9c8`
  (identical in the wheel, the sdist, and the installed distribution)

### `LICENSE` — verbatim

<!-- LICENSE-FILE: joserfc-1.7.5.dist-info/licenses/LICENSE sha256=19ee1fafcc9ec4217fc32b8a651d820538c789cf4041cb4e46b4b176a5f2a9c8 -->
```text
BSD 3-Clause License

Copyright (c) 2023, Hsiaoming Yang

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this
   list of conditions and the following disclaimer.

2. Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution.

3. Neither the name of the copyright holder nor the names of its
   contributors may be used to endorse or promote products derived from
   this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
```
<!-- END-LICENSE-FILE -->

## cryptography 46.0.1 — Apache-2.0 OR BSD-3-Clause

Cryptographic backend used by Authlib and joserfc.

- Source: https://github.com/pyca/cryptography ·
  Documentation: https://cryptography.io/
- PyPI: https://pypi.org/project/cryptography/46.0.1/ — the sdist and both
  wheels below carry a PyPI attestation bundle (Trusted Publisher: GitHub
  `pyca/cryptography`, workflow `pypi-publish.yml`)
- Package METADATA: `License-Expression: Apache-2.0 OR BSD-3-Clause` ·
  `License-File: LICENSE`, `LICENSE.APACHE`, `LICENSE.BSD` ·
  `Author-email` name: The Python Cryptographic Authority and individual
  contributors
- Release artifacts (PyPI, uploaded 2025-09-17):
  - `cryptography-46.0.1.tar.gz` — SHA-256
    `ed570874e88f213437f5cf758f9ef26cbfc3f336d889b1e592ee11283bb8d1c7`
  - `cryptography-46.0.1-cp311-abi3-manylinux_2_28_x86_64.whl` — SHA-256
    `f7a24ea78de345cfa7f6a8d3bde8b242c7fac27f2bd78fa23474ca38dfaeeab9`
  - `cryptography-46.0.1-cp311-abi3-manylinux_2_34_x86_64.whl` — SHA-256
    `449ef2b321bec7d97ef2c944173275ebdab78f3abdd005400cc409e27cd159ab`
- License files (each identical across the sdist, both wheels, and the
  installed distribution):
  - `LICENSE` — 197 bytes — SHA-256 `3e0c7c091a948b82533ba98fd7cbb40432d6f1a9acbf85f5922d2f99a93ae6bb`
  - `LICENSE.BSD` — 1532 bytes — SHA-256 `602c4c7482de6479dd2e9793cda275e5e63d773dacd1eca689232ab7008fb4fb`
  - `LICENSE.APACHE` — 11360 bytes — SHA-256 `aac73b3148f6d1d7111dbca32099f68d26c644c6813ae1e4f05f6579aa2663fe`

The package is offered under *either* license (see `LICENSE`). Both texts
are reproduced so the redistribution record is complete under whichever
terms apply.

### `LICENSE` — verbatim

<!-- LICENSE-FILE: cryptography-46.0.1.dist-info/licenses/LICENSE sha256=3e0c7c091a948b82533ba98fd7cbb40432d6f1a9acbf85f5922d2f99a93ae6bb -->
```text
This software is made available under the terms of *either* of the licenses
found in LICENSE.APACHE or LICENSE.BSD. Contributions to cryptography are made
under the terms of *both* these licenses.
```
<!-- END-LICENSE-FILE -->

### `LICENSE.BSD` — verbatim

<!-- LICENSE-FILE: cryptography-46.0.1.dist-info/licenses/LICENSE.BSD sha256=602c4c7482de6479dd2e9793cda275e5e63d773dacd1eca689232ab7008fb4fb -->
```text
Copyright (c) Individual contributors.
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

    1. Redistributions of source code must retain the above copyright notice,
       this list of conditions and the following disclaimer.

    2. Redistributions in binary form must reproduce the above copyright
       notice, this list of conditions and the following disclaimer in the
       documentation and/or other materials provided with the distribution.

    3. Neither the name of PyCA Cryptography nor the names of its contributors
       may be used to endorse or promote products derived from this software
       without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
```
<!-- END-LICENSE-FILE -->

### `LICENSE.APACHE` — verbatim

<!-- LICENSE-FILE: cryptography-46.0.1.dist-info/licenses/LICENSE.APACHE sha256=aac73b3148f6d1d7111dbca32099f68d26c644c6813ae1e4f05f6579aa2663fe -->
```text

                                 Apache License
                           Version 2.0, January 2004
                        https://www.apache.org/licenses/

   TERMS AND CONDITIONS FOR USE, REPRODUCTION, AND DISTRIBUTION

   1. Definitions.

      "License" shall mean the terms and conditions for use, reproduction,
      and distribution as defined by Sections 1 through 9 of this document.

      "Licensor" shall mean the copyright owner or entity authorized by
      the copyright owner that is granting the License.

      "Legal Entity" shall mean the union of the acting entity and all
      other entities that control, are controlled by, or are under common
      control with that entity. For the purposes of this definition,
      "control" means (i) the power, direct or indirect, to cause the
      direction or management of such entity, whether by contract or
      otherwise, or (ii) ownership of fifty percent (50%) or more of the
      outstanding shares, or (iii) beneficial ownership of such entity.

      "You" (or "Your") shall mean an individual or Legal Entity
      exercising permissions granted by this License.

      "Source" form shall mean the preferred form for making modifications,
      including but not limited to software source code, documentation
      source, and configuration files.

      "Object" form shall mean any form resulting from mechanical
      transformation or translation of a Source form, including but
      not limited to compiled object code, generated documentation,
      and conversions to other media types.

      "Work" shall mean the work of authorship, whether in Source or
      Object form, made available under the License, as indicated by a
      copyright notice that is included in or attached to the work
      (an example is provided in the Appendix below).

      "Derivative Works" shall mean any work, whether in Source or Object
      form, that is based on (or derived from) the Work and for which the
      editorial revisions, annotations, elaborations, or other modifications
      represent, as a whole, an original work of authorship. For the purposes
      of this License, Derivative Works shall not include works that remain
      separable from, or merely link (or bind by name) to the interfaces of,
      the Work and Derivative Works thereof.

      "Contribution" shall mean any work of authorship, including
      the original version of the Work and any modifications or additions
      to that Work or Derivative Works thereof, that is intentionally
      submitted to Licensor for inclusion in the Work by the copyright owner
      or by an individual or Legal Entity authorized to submit on behalf of
      the copyright owner. For the purposes of this definition, "submitted"
      means any form of electronic, verbal, or written communication sent
      to the Licensor or its representatives, including but not limited to
      communication on electronic mailing lists, source code control systems,
      and issue tracking systems that are managed by, or on behalf of, the
      Licensor for the purpose of discussing and improving the Work, but
      excluding communication that is conspicuously marked or otherwise
      designated in writing by the copyright owner as "Not a Contribution."

      "Contributor" shall mean Licensor and any individual or Legal Entity
      on behalf of whom a Contribution has been received by Licensor and
      subsequently incorporated within the Work.

   2. Grant of Copyright License. Subject to the terms and conditions of
      this License, each Contributor hereby grants to You a perpetual,
      worldwide, non-exclusive, no-charge, royalty-free, irrevocable
      copyright license to reproduce, prepare Derivative Works of,
      publicly display, publicly perform, sublicense, and distribute the
      Work and such Derivative Works in Source or Object form.

   3. Grant of Patent License. Subject to the terms and conditions of
      this License, each Contributor hereby grants to You a perpetual,
      worldwide, non-exclusive, no-charge, royalty-free, irrevocable
      (except as stated in this section) patent license to make, have made,
      use, offer to sell, sell, import, and otherwise transfer the Work,
      where such license applies only to those patent claims licensable
      by such Contributor that are necessarily infringed by their
      Contribution(s) alone or by combination of their Contribution(s)
      with the Work to which such Contribution(s) was submitted. If You
      institute patent litigation against any entity (including a
      cross-claim or counterclaim in a lawsuit) alleging that the Work
      or a Contribution incorporated within the Work constitutes direct
      or contributory patent infringement, then any patent licenses
      granted to You under this License for that Work shall terminate
      as of the date such litigation is filed.

   4. Redistribution. You may reproduce and distribute copies of the
      Work or Derivative Works thereof in any medium, with or without
      modifications, and in Source or Object form, provided that You
      meet the following conditions:

      (a) You must give any other recipients of the Work or
          Derivative Works a copy of this License; and

      (b) You must cause any modified files to carry prominent notices
          stating that You changed the files; and

      (c) You must retain, in the Source form of any Derivative Works
          that You distribute, all copyright, patent, trademark, and
          attribution notices from the Source form of the Work,
          excluding those notices that do not pertain to any part of
          the Derivative Works; and

      (d) If the Work includes a "NOTICE" text file as part of its
          distribution, then any Derivative Works that You distribute must
          include a readable copy of the attribution notices contained
          within such NOTICE file, excluding those notices that do not
          pertain to any part of the Derivative Works, in at least one
          of the following places: within a NOTICE text file distributed
          as part of the Derivative Works; within the Source form or
          documentation, if provided along with the Derivative Works; or,
          within a display generated by the Derivative Works, if and
          wherever such third-party notices normally appear. The contents
          of the NOTICE file are for informational purposes only and
          do not modify the License. You may add Your own attribution
          notices within Derivative Works that You distribute, alongside
          or as an addendum to the NOTICE text from the Work, provided
          that such additional attribution notices cannot be construed
          as modifying the License.

      You may add Your own copyright statement to Your modifications and
      may provide additional or different license terms and conditions
      for use, reproduction, or distribution of Your modifications, or
      for any such Derivative Works as a whole, provided Your use,
      reproduction, and distribution of the Work otherwise complies with
      the conditions stated in this License.

   5. Submission of Contributions. Unless You explicitly state otherwise,
      any Contribution intentionally submitted for inclusion in the Work
      by You to the Licensor shall be under the terms and conditions of
      this License, without any additional terms or conditions.
      Notwithstanding the above, nothing herein shall supersede or modify
      the terms of any separate license agreement you may have executed
      with Licensor regarding such Contributions.

   6. Trademarks. This License does not grant permission to use the trade
      names, trademarks, service marks, or product names of the Licensor,
      except as required for reasonable and customary use in describing the
      origin of the Work and reproducing the content of the NOTICE file.

   7. Disclaimer of Warranty. Unless required by applicable law or
      agreed to in writing, Licensor provides the Work (and each
      Contributor provides its Contributions) on an "AS IS" BASIS,
      WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
      implied, including, without limitation, any warranties or conditions
      of TITLE, NON-INFRINGEMENT, MERCHANTABILITY, or FITNESS FOR A
      PARTICULAR PURPOSE. You are solely responsible for determining the
      appropriateness of using or redistributing the Work and assume any
      risks associated with Your exercise of permissions under this License.

   8. Limitation of Liability. In no event and under no legal theory,
      whether in tort (including negligence), contract, or otherwise,
      unless required by applicable law (such as deliberate and grossly
      negligent acts) or agreed to in writing, shall any Contributor be
      liable to You for damages, including any direct, indirect, special,
      incidental, or consequential damages of any character arising as a
      result of this License or out of the use or inability to use the
      Work (including but not limited to damages for loss of goodwill,
      work stoppage, computer failure or malfunction, or any and all
      other commercial damages or losses), even if such Contributor
      has been advised of the possibility of such damages.

   9. Accepting Warranty or Additional Liability. While redistributing
      the Work or Derivative Works thereof, You may choose to offer,
      and charge a fee for, acceptance of support, warranty, indemnity,
      or other liability obligations and/or rights consistent with this
      License. However, in accepting such obligations, You may act only
      on Your own behalf and on Your sole responsibility, not on behalf
      of any other Contributor, and only if You agree to indemnify,
      defend, and hold each Contributor harmless for any liability
      incurred by, or claims asserted against, such Contributor by reason
      of your accepting any such warranty or additional liability.

   END OF TERMS AND CONDITIONS

   APPENDIX: How to apply the Apache License to your work.

      To apply the Apache License to your work, attach the following
      boilerplate notice, with the fields enclosed by brackets "[]"
      replaced with your own identifying information. (Don't include
      the brackets!)  The text should be enclosed in the appropriate
      comment syntax for the file format. We also recommend that a
      file or class name and description of purpose be included on the
      same "printed page" as the copyright notice for easier
      identification within third-party archives.

   Copyright [yyyy] [name of copyright owner]

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       https://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
```
<!-- END-LICENSE-FILE -->

---

These OAuth dependencies participate in the deployment dependency authority
(`pyproject.toml`) and are enforced by
`tests/unit/test_dependency_manifest_parity.py`; the license blocks above are
enforced by `tests/unit/test_third_party_notices.py`. This is a technical
compatibility and attribution record, not legal advice.
