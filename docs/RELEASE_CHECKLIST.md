# Owner approval and real-world validation checklist

This is an initial source release, not evidence of OSS community impact.

Before any public release:
- [x] GitHub confirmed site-preflight available under mizuho-Te; no package registry name is claimed.
- [ ] Review all source, documentation, generated artifacts and potential third-party rights.
- [x] MIT license approved, attributed to the public GitHub handle mizuho-Te.
- [x] Public release authorized; authenticated connector account is mizuho-Te. No customer repositories/data.
- [ ] Establish a private security-reporting channel and update SECURITY.md.
- [ ] Review GitHub Actions permissions and run CI on the intended supported platforms.
- [ ] Test on actual exports with permission, document limitations, and remove sensitive fixtures.
- [ ] Have a human check Japanese/English instructions and first-run usability.
- [ ] Tag and publish only after those decisions. No registry publishing or credentials are required for the source-only first release.

After release:
1. Ask a small number of relevant site creators to try a concrete workflow; do not misrepresent endorsement.
2. Log real issues, review false positives, and ship tested fixes with a changelog.
3. Maintain public documentation and respond honestly to feedback. Do not promise a response-time SLA you cannot keep.
4. Keep evidence of genuine useful maintenance and impact. Never buy/fabricate stars, users, activity or testimonials.
5. Review the current requirements of any open-source support program at application time. Creating this project alone does not establish eligibility or guarantee acceptance.
