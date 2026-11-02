"""Read-only community listening on Enna's own Threads posts.

Official Meta endpoints only. Aggregates counts; stores no comment text,
usernames or identifiers. No follow, like, reply or external keyword search.
"""
import json
from datetime import datetime, timezone
from agent import Database
from threads.credentials import load_credentials
from threads.publisher import thread_request

def observe(db=None, *, request=thread_request):
    db = db or Database()
    credentials = load_credentials(db, refresh=False)
    if credentials is None:
        return {"state": "oauth_unavailable"}
    token, expected = credentials
    profile = request("GET", "/me", token, params={"fields":"id,username"})
    if str(profile.get("username","")).casefold() != "dohay_dilam" or not profile.get("id"):
        return {"state": "account_mismatch"}
    recent = request("GET", "/me/threads", token, params={
        "fields":"id,timestamp,permalink", "limit":30,
    })
    own = recent.get("data")
    if not isinstance(own,list):
        return {"state":"own_feed_unavailable"}
    total = visible = unknown = 0
    for post in own[:15]:
        if not isinstance(post,dict) or not str(post.get("id","")).isdigit():
            continue
        total += 1
        try:
            response=request("GET","/"+str(post["id"])+"/replies",token,params={
                "fields":"id,timestamp","limit":25
            })
            replies=response.get("data")
            if isinstance(replies,list):
                visible += len(replies)
            else:
                unknown += 1
        except Exception:
            # A missing scope does not mean a post has zero replies.
            unknown += 1
    return {"state":"partial" if unknown else "ok",
            "own_posts_checked":total,
            "visible_direct_replies_sample":visible,
            "unavailable_post_reply_reads":unknown,
            "sample_is_paginated":True,
            "automated_reply_posted":False}

if __name__ == "__main__":
    try:
        print("Enna own-thread listening:",json.dumps(observe(),ensure_ascii=False))
    except Exception as exc:
        # Never log raw Meta response, tokens or private content.
        print("Enna own-thread listening:",json.dumps({
            "state":"source_unavailable","error_class":type(exc).__name__}))
