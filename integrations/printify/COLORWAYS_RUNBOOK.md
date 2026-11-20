# Pie & Po — Printify Pastel Phone Cases Operations

Snapshot: 20 Nov 2026 UTC. Source: Printify shop 29780383, Shopify `pienpocase.myshopify.com`.

## Changes actually made
- Created 36 genuine Printify products derived from 9 phone-case designs (four base backgrounds: Blush Pink, Cream, Sage Green, Sky Blue).
- Verified each product's manufacturer blueprint, original transparent image ID, design placement, background hex, enabled device variants and visual color presence in generated mockups.
- QA batch output: **36/36** pass at Printify API level. This does not replace physical sample QA.
- Published 26/36 to Shopify and confirmed all 26 ACTIVE, price-aligned, stocked-for-sale, with SKU and media. US retail targets: iPhone Tough $29.95; Samsung Galaxy Tough $31.95; iPhone 18 Pro Max Magnetic Tough $34.95.
- Added 26 products to the existing `phone-cases-pie-and-po` collection (35 products total, including nine originals).
- Added direct links to available printed colorways in eight of nine original phone-case descriptions, without claiming different shell material.
- **Ten outstanding** products: Printify POST publish returned HTTP 200, but `is_locked=true`, `external=null` after status checks. No matching Shopify listing seen. Requests sent to Merchant Support with product IDs. DO NOT blindly retry or recreate them.
- Production cost and US first-item shipping have been assessed. Gross margin after shipping is not net profit; payment processing, taxes, refunds and sample quality remain to be verified.

## Status monitoring
- `Enna - Printify write token safe preflight` runs read-only via GitHub Actions every six hours (also manual workflow dispatch).
- A locked product with no external ID means publishing remains unresolved; check both Shopify Admin (including DRAFT) and Printify before resubmission.
- Avoid `/publishing_failed.json` and forced unlock operations until Printify confirms they are safe for its Shopify-connected channel.

## Security and next steps
- All GitHub Actions automatic mutation steps in `enna-printify-audit.yml` are disabled (`if: false`). Audit can be run manually. The scripts to create and publish have explicit environment variable guards and must never be scheduled unattended.
- Credentials are stored only in GitHub Secrets: `PRINTIFY_API_TOKEN`, `PRINTIFY_API_TOKEN_WRITE`.
- Be cautious: Printify source listing prices for newly cloned products were originally inherited from their base Printify listings, which can differ from the public Shopify prices. Do not republish existing colorways before reconciling source-side pricing; source-of-truth reconciliation for Printify remains pending.
- If Merchant Support clears the queue, verify all 36 Printify external mappings first, then reconcile Shopify SKU, prices, availability and add newly synced items to collection.
- Standalone colorway products currently link to each other via Shopify product descriptions on originals. They are NOT a single-product `Color` option. In theme UX, sibling swatch links are a possible future improvement.
- No customer order, sample order, refund, or fee-generating purchase has been made by this workflow.
