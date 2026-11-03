"use strict";
const test=require("node:test");
const assert=require("node:assert/strict");
const fs=require("node:fs");
const vm=require("node:vm");

test("Link bio is a real searchable and navigable page with a working free resource",()=>{
 const html=fs.readFileSync("docs/enna/links/index.html","utf8");
 const kit=fs.readFileSync("docs/enna/kit/index.html","utf8");
 assert.match(html,/id="filter"/);
 assert.match(html,/data-category="desk"/);
 assert.match(html,/data-category="bag"/);
 assert.match(html,/data-category="work"/);
 assert.match(html,/href="\.\.\/kit\//);
 assert.match(kit,/Enna Mini/);
 const scripts=[...html.matchAll(/<script(?:\s[^>]*)?>([\s\S]*?)<\/script>/g)];
 assert.equal(scripts.length,1);
 assert.doesNotThrow(()=>new vm.Script(scripts[0][1]));
});
test("No unapproved affiliate URLs, tracking, silent redirect or shopping link in initial bio",()=>{
 const html=fs.readFileSync("docs/enna/links/index.html","utf8");
 const data=JSON.parse(fs.readFileSync("docs/enna/links/approved.json","utf8"));
 assert.equal(data.stage,"pre_revenue");
 assert.deepEqual(data.items,[]);
 assert.match(html,/Liên kết tiếp thị/);
 assert.doesNotMatch(html,/window\.location\s*=|location\.replace\(|location\.assign\(/);
 assert.doesNotMatch(html,/localStorage|sendBeacon|dataLayer|gtag\(/);
 assert.doesNotMatch(html,/<script[^>]+src=/i);
 assert.match(html,/rel="noopener noreferrer sponsored"/);
});
