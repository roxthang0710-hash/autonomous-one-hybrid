"use strict";
const test=require("node:test");
const assert=require("node:assert/strict");
const fs=require("node:fs");
const vm=require("node:vm");

test("office-kit prototype is self-contained valid JavaScript",()=>{
 const html=fs.readFileSync("products/office-kit/index.html","utf8");
 const scripts=[...html.matchAll(/<script(?:\s[^>]*)?>([\s\S]*?)<\/script>/g)];
 assert.ok(scripts.length===1,"One local script expected");
 assert.doesNotThrow(()=>new vm.Script(scripts[0][1]));
 assert.match(html,/Miễn phí|miễn phí/);
 assert.match(html,/Không cần tài khoản/);
 assert.match(html,/type="button"/);
});
test("office-kit has no external trackers, payments or credential capture",()=>{
 const html=fs.readFileSync("products/office-kit/index.html","utf8");
 assert.doesNotMatch(html,/<script[^>]+src=/i);
 assert.doesNotMatch(html,/<form[^>]+action=/i);
 assert.doesNotMatch(html,/https?:\/\//i);
 assert.doesNotMatch(html,/fetch\(|sendBeacon|XMLHttpRequest|localStorage|sessionStorage/);
 assert.doesNotMatch(html,/(?:stripe|paypal|banking|thanh toán qua)/i);
 assert.match(html,/URL\.createObjectURL/);
});
