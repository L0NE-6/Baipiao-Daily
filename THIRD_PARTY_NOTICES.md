# Third-Party Notices

This repository contains an independently written Python implementation of
the Baipiao daily check-in flow. Credentials are supplied at runtime and are
not included in the repository.

## Protocol Evidence

### magpie-bit-api

- Source: `081ben/magpie-bit-api`
- Fixed commit reviewed: `761e93c2dfdaeb591b3d22936a017fd94afc56b2`
- License: MIT
- Copyright: 2026 magpie-community/plugins contributors
- Use: the fixed source was reviewed for the Bearer session model,
  `POST /api/checkin`, the no-body request shape, and the
  `claimed` / `checked_in` / `reward` response semantics.
- Local implementation: Python, requests-based, independently structured, with
  `/api/overview` status reads before and after a claim.

The reviewed source sends `POST /api/checkin` with an `Authorization: Bearer`
header and no request body. `claimed=true` means this request granted the
reward. `claimed=false` with `checked_in=true` means the day was already
recorded. `claimed=false` with `checked_in=false` means no active check-in was
reported. The fixed source does not define `checked_in` as a substitute for a
post-request status read.

## Third-Party MIT License

MIT License

Copyright (c) 2026 magpie-community/plugins contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

## Runtime Dependencies

- `requests` is installed from PyPI under its own license.

## Project License

The local implementation is released under the MIT License reproduced in
[`LICENSE`](LICENSE).
