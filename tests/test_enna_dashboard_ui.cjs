"use strict";
const test=require("node:test");
const assert=require("node:assert/strict");
const fs=require("node:fs");
const vm=require("node:vm");

test("public Enna dashboard journal script is valid JavaScript",()=>{
  const html=fs.readFileSync("docs/enna/index.html","utf8");
  const scripts=[...html.matchAll(/<script(?:\s[^>]*)?>([\s\S]*?)<\/script>/g)];
  assert.ok(scripts.length>0,"Inline dashboard script must exist");
  for(const m of scripts)assert.doesNotThrow(()=>new vm.Script(m[1]));
});
test("only real backend events are labeled activity, and refresh is periodic",()=>{
  const html=fs.readFileSync("docs/enna/index.html","utf8");
  const edge=fs.readFileSync("supabase/functions/enna-public-status/index.ts","utf8");
  assert.match(html,/setInterval\(loadEvents,15000\)/);
  assert.match(html,/mode=events/);
  assert.match(html,/codeLabels=/);
  assert.match(html,/Tự chạy theo lịch gần nhất/);
  assert.match(html,/kiểm thử thủ công/);
  assert.match(edge,/trigger_kind/);
  assert.match(html,/sys-followers/);
  assert.match(html,/sys-autonomous/);
  assert.match(edge,/followerKpi/);
  assert.match(edge,/metaPosted.size/);
  assert.match(edge,/enna_activity_events\?select=occurred_at,kind,status,code/);
  assert.match(edge,/Cache-Control':'no-store/);
  assert.doesNotMatch(edge,/select=\*/);
});
