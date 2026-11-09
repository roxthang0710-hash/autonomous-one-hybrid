/**
 * Free read-only browser smoke check. Manual cart/checkout option stops
 * before entering contact information or completing any purchase.
 */
const { chromium } = require(process.env.PLAYWRIGHT_MODULE_PATH || 'playwright');
const ROOT = 'https://dohaydilam-shop.fourthwall.com';
const COLLECTION = ROOT + '/collections/start-here-workday-gift-picks';
const PRODUCT = ROOT + '/products/master-of-the-tiny-gaps-11oz-office-coffee-mug-2';
const CHECKOUT_DRY_RUN = process.env.CHECKOUT_DRY_RUN === 'true';

function ensure(ok, message) { if (!ok) throw new Error(message); }
async function verify(page, url, text) {
  const response = await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 35000 });
  ensure(response && response.status() >= 200 && response.status() < 400,
    'HTTP error at ' + url + ': ' + (response ? response.status() : 'no response'));
  await page.getByText(text, { exact: false }).first().waitFor({ timeout: 20000 });
  console.log('PASS ' + url + ' (' + text + ')');
}
async function main() {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ locale: 'en-US', viewport: {width:1365,height:768} });
  try {
    await verify(page, ROOT, 'dohaydilam');
    await verify(page, COLLECTION, 'Start Here');
    const count = await page.locator('a[href*="/products/"]').count();
    ensure(count >= 5, 'Expected >=5 product links; found ' + count);
    // Tracking instrumentation: verify the tag and the product-view event are
    // present. A GA4 ID in HTML does not prove that GA4 receives events.
    const homeTracking = await page.evaluate(() => ({
      measurementId: window.creatorGa4Id || null,
      hasDataLayer: Array.isArray(window.dataLayer),
    }));
    ensure(/^G-[A-Z0-9]{7,14}$/.test(homeTracking.measurementId || ''),
      'GA4 measurement ID missing or malformed on storefront');
    ensure(homeTracking.hasDataLayer, 'dataLayer missing from storefront');
    console.log('PASS: GA4 Measurement ID and dataLayer present (delivery unverified)');
    await verify(page, PRODUCT, 'Master of the Tiny Gaps');
    await page.waitForFunction(() => Array.isArray(window.dataLayer) &&
      window.dataLayer.some(entry => entry && entry.event === 'view_item'),
      { timeout: 20000 }).catch(() => {});
    const ga4Product = await page.evaluate(() => ({
      measurementId: window.creatorGa4Id || null,
      viewEvent: Array.isArray(window.dataLayer) ?
        window.dataLayer.find(e => e && e.event === 'view_item') : null,
    }));
    ensure(ga4Product.measurementId === homeTracking.measurementId,
      'GA4 ID differs between homepage and product page');
    ensure(ga4Product.viewEvent && ga4Product.viewEvent.ecommerce &&
      Array.isArray(ga4Product.viewEvent.ecommerce.items),
      'GA4 view_item event missing product ecommerce payload');
    console.log('PASS: product view_item ecommerce payload present (GA4 reception unverified)');
    const body = await page.locator('body').innerText();
    ensure(body.includes('$19.95'), 'Mug price $19.95 not visible');
    console.log('PASS: storefront, featured collection, five links and product price');
    if (!CHECKOUT_DRY_RUN) return;
    const add = page.getByRole('button', { name: /add to cart|add to bag/i }).first();
    ensure(await add.count(), 'No Add to cart button found');
    await add.click({ timeout: 15000 });
    await page.goto(ROOT + '/cart', { waitUntil: 'domcontentloaded', timeout: 35000 });
    ensure((await page.locator('body').innerText()).includes('Master of the Tiny Gaps'),
      'Cart did not contain mug');
    const button = page.getByRole('button', { name: /checkout|check out|proceed to checkout/i }).first();
    if (await button.count()) await button.click({ timeout: 15000 });
    else {
      const link = page.getByRole('link', { name: /checkout|check out/i }).first();
      ensure(await link.count(), 'No checkout entry link or button');
      await link.click({ timeout: 15000 });
    }
    await page.waitForLoadState('domcontentloaded', { timeout: 25000 }).catch(() => {});
    const checkoutBody = await page.locator('body').innerText();
    ensure(/checkout|email|contact|delivery|shipping|payment/i.test(checkoutBody) ||
      /checkout/i.test(page.url()), 'Could not confirm checkout entry');
    console.log('PASS: checkout entry reached; stopped before personal info/payment');
  } finally {
    await browser.close();
  }
}
main().catch(err => { console.error(err.stack || err); process.exitCode = 1; });
