# DOHAYDILAM POD — v4.7 release state
Date: 2026-11-10 (Asia/Ho_Chi_Minh)

## Verified shop state
- Fourthwall: https://dohaydilam-shop.fourthwall.com/
- Live account: dohaydilam; shop LIVE; 43 offers and 9 collections at audit time.
- Existing homepage is **not yet the v4.7 design**. Its hero still uses a previous asset and the editorial section uses Pexels stock.

## v4.7 source
- Custom code: [DOHAYDILAM_V4_7_FOURTHWALL_CUSTOM_CODE.html](DOHAYDILAM_V4_7_FOURTHWALL_CUSTOM_CODE.html)
- Image manifest: [mockups/web/manifest.json](mockups/web/manifest.json)
- Design archive: https://drive.google.com/drive/folders/1lGBcCSFCVqs4ujCEOofBeDbnq8jyLMiG

## Implemented in source code
- New responsive hero, 4 product-in-context cards, coffee-break feature, gift category shortcuts, and disclosure of illustrative mockups.
- Four verified public WebP image paths (no Drive hotlinks); optimized files total ~375 KB.
- Four confirmed live Fourthwall product links and matched live USD prices.
- CSS namespaced to #enna-pod-v47; **no JavaScript, inline base64, or blank spacer blocks**.
- Source is 11,615 characters, suitable as a single Fourthwall Custom code section.
- Reusing native Fourthwall checkout/product pages; no custom shopping cart or fake inventory.

## QA done
- All four product URLs responded with real product content and matching prices.
- GitHub source was read back after commit, confirming 6 image tags, 4 unique WebP assets, no Drive URLs, no JS, and no repeated blank lines.

## Publication status: pending
Fourthwall1's connected shop tools support products and collections but do not provide a storefront **Site design / Custom code** editor action.
The TinyFish saved browser profile named 'Enna POD - Fourthwall' has a verified Google sign-in only, not a verified Fourthwall admin sign-in; do not attempt an authenticated admin edit without authorization or a connected logged-in browser session.
To publish when an authenticated browser session is available, open Fourthwall dashboard > Site design > Layout > Home > existing Custom code section, replace that section's code with the HTML file contents, save and publish. Do not paste this code into sitewide header/footer HTML. Keep a backup of the existing live section before overwriting.
Re-check desktop/mobile and live image loads after publishing. No live site update is claimed in this release record.

## Risk notes
- Mockups are conceptual marketing images, not photos of shipped items.
- Actual physical product samples still need inspection before spending on paid ads.
- Previously disclosed API credentials should be rotated without reposting them in chat.
