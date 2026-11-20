# Enna · Printify API (without TinyFish)

This integration reads Printify shop products and audits manufacturer-supported color variants. It does not mutate products, order samples, change prices, or publish listings.

## Connect securely

1. Open https://printify.com/app/connections and create a dedicated Printify API token named `enna-piepo-audit`, using only available read scopes for shops, products and catalog. Never share it in ChatGPT.
2. In the GitHub repository `roxthang0710-hash/autonomous-one-hybrid`, open **Settings → Secrets and variables → Actions → New repository secret**.
3. Set secret name: `PRINTIFY_API_TOKEN`; value: the Printify token. Keep it private.
4. After this branch is merged, open **Actions → Enna - Printify API color audit (read-only) → Run workflow**. If the Printify account has multiple stores and the correct store title isn't unique, enter the exact Printify shop ID.
5. Review the workflow **Summary**. It shows only aggregate results to avoid leaking product-level private data via public GitHub Actions logs.

Run locally:
```bash
PRINTIFY_API_TOKEN='...' python integrations/printify/audit.py --shop-id 1234567 --include-unpublished --output local-report.json
```
Do not commit `local-report.json`.

## Production rules

- Printify is the system of record for fulfillment SKUs. Shopify should not be edited to invent non-manufacturable color variants.
- A phone case can have a printed background color but no separate manufacturer color option. Treat the `no-color-option` flag as a design task, not proof that more physical blanks exist.
- Follow up with API catalog/print-area QA and design variants. A separate write-authorized workflow is needed for product edits/publication after live read-only audit.
- Read-only API credential is not a secret we can create or discover from Shopify's own API. The store owner must generate it once.

Docs: https://developers.printify.com/
