# ENNA POD — Pricing and unit economics risk register (2026-11-10)

**Important:** The numeric catalog `priceFrom` / `priceTo` ranges below are reference pricing from Fourthwall source products, **not verified SKU-specific manufacturing costs**. The rough difference vs current listing price is NOT realized profit and must not be published as a margin, ROI, or business result. It does not include payment processing fees, discounts, refunds, shipping, taxes or any variant/printing adjustments. `ecommerce_get_customization_pricing` was queried for mug/tote but currently omits the numeric amount in its serialized cost objects.

| Live product type | Current retail price | Catalog price range (not a verified SKU cost) | Retail less catalog range, illustrative only | Caveat |
|---|---:|---:|---:|---|
| Die-cut sticker | $7.95 | $3.78–$5.96 | $1.99–$4.17 | Multiple sticker sizes in catalog; live shop offer is 3 x 3 in |
| 11 oz ceramic mug | $19.95 | $5.95–$10.50 | $9.45–$14.00 | Catalog covers 11, 15 and 20 oz sizes; live listing only 11 oz |
| Spiral notebook | $21.95 | $10.95 | $11.00 | Single size in catalog |
| 12 x 16 in matte poster | $24.95 | $5.50–$18.00 | $6.95–$19.45 | Catalog covers 14 sizes; live listing is 12 x 16 in |
| Organic cotton tote | $29.95 | $15.56–$21.51 | $8.44–$14.39 | Catalog source may include variant/print configurations |

## Current promotion and guardrails

- `WORKDAY10`: 10% off US orders of at least $30 USD, maximum 40 redemptions, one per customer, shipping excluded. Usage count: 0 at last check.
- A single $29.95 tote **does not qualify** for the code, nor does a $19.95 mug, $21.95 notebook or $7.95 sticker. A $29.95 tote plus a $7.95 sticker reaches $37.90 but shipping/taxes are extra. Do not promise final savings until cart validation.
- Do not lower prices or broaden discount coverage until an exact per-variant production cost plus payment fees can be obtained in Fourthwall.
- Shop is in USD. Existing audience of Vietnamese Threads is not the primary market for $20–30 English-language physical items; do not push sales posts there.

## How to close the margin gap

1. In Fourthwall admin product editing, inspect **price/cost/profit** for the live 11 oz mug, 3 x 3 sticker, 12 x 16 poster, one-size notebook, Oyster tote. Record exact SKU cost, retail price, fees and expected shipping region.
2. If possible, use Fourthwall connector's customization pricing only after numeric amount is returned; the current tool returns `currency`, `currencyScale`, and sign flags, but not the value.
3. Compute `product contribution = retail - manufacturer cost - creator-paid discounts - processing charges - any creator-paid shipping costs`. Exclude taxes paid by customers from profit. Confirm after a real order using Fourthwall Sales Over Time `net_profit`.
4. Compare 10% discount against SKU-specific contribution before changing `WORKDAY10`. Do not increase marketing spend before traffic and checkout are measurable.
