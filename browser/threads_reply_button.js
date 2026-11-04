/* Enna reply locator v0.7: fail-closed DOM candidate selection.
 * Read-only locator; a separate authorized workflow controls any click.
 */
(function (root, factory) {
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  else root.EnnaReplyLocator = api;
})(typeof globalThis !== 'undefined' ? globalThis : this, function () {
  'use strict';
  const EXACT = new Set(['post','reply','send','đăng','trả lời','gửi','đăng trả lời','post reply']);
  const BAD = /^(?:repost|quote|share|like|thích|chia sẻ|đăng lại|trích dẫn|hủy|cancel|discard|xóa)$/i;
  function words(s) { return String(s || '').replace(/\s+/g, ' ').trim().toLocaleLowerCase(); }
  function labels(el) { return [el.textContent,el.getAttribute('aria-label'),el.getAttribute('title'),el.getAttribute('data-testid')].map(words).filter(Boolean); }
  function visible(el) {
    if (!el || !el.isConnected || el.hidden || el.getAttribute('aria-hidden') === 'true') return false;
    const style = el.ownerDocument.defaultView?.getComputedStyle(el);
    if (style && (style.display === 'none' || style.visibility === 'hidden' || style.opacity === '0')) return false;
    return !!el.getClientRects().length;
  }
  function locate(composer, opts = {}) {
    if (!composer || !visible(composer) || !composer.matches('[contenteditable="true"],textarea,[role="textbox"]') ||
       composer.matches('[aria-disabled="true"],[disabled],[readonly]')) return {status:'invalid_composer'};
    const dialog = composer.closest('[role="dialog"],dialog,[aria-modal="true"]');
    const boundary = dialog || composer.closest('form,[data-reply-composer],[data-pressable-container="true"]');
    if (!boundary) return {status:'missing_reply_boundary'};
    const candidates=[];
    for(const el of boundary.querySelectorAll('button,[role="button"],input[type="submit"]')){
      if (!visible(el) || el.disabled || el.getAttribute('aria-disabled')==='true') continue;
      const ls=labels(el);
      if (ls.some(x=>BAD.test(x)) || !ls.some(x=>EXACT.has(x))) continue;
      const nested=el.closest('[role="dialog"],dialog,[aria-modal="true"]');
      if(dialog && nested!==dialog) continue;
      const score=(dialog?10:0)+(el.tagName==='BUTTON'?3:0)+
        (ls.some(x=>x==='trả lời'||x==='reply'||x==='đăng trả lời'||x==='post reply')?2:0);
      candidates.push({element:el,score});
    }
    candidates.sort((a,b)=>b.score-a.score);
    if(!candidates.length)return {status:'submit_button_not_found'};
    if(candidates.length>1 && candidates[0].score===candidates[1].score)
      return {status:'ambiguous_submit_buttons',count:candidates.length};
    if(!opts.allowClick)return {status:'located_preview_only',element:candidates[0].element};
    return {status:'ready_for_one_owner_approved_click',element:candidates[0].element};
  }
  return {locate};
});
