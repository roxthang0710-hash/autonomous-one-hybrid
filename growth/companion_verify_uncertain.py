"""Read-only verification of ambiguous official Threads reply attempts.

Uses only Meta's own-user replies endpoint. NEVER sends a Threads POST.
A confirmed reply must belong to the OAuth account, match the exact parent
Threads media ID, and fall within the one-shot attempt's time window.
"""
from datetime import datetime, timedelta, timezone
import requests

from agent import Database
from growth.engage import get_credentials, verify_meta_account
from threads.publisher import thread_request

FIELDS="id,text,timestamp,replied_to,root_post,permalink"
BACKUP_FIELDS="id,text,timestamp,replied_to"


def timestamp(value):
    try:
        if not isinstance(value,str):
            return None
        t=datetime.fromisoformat(value.replace("Z","+00:00"))
        return t.astimezone(timezone.utc) if t.tzinfo else None
    except ValueError:
        return None


def parent_id(item):
    ref=item.get("replied_to")
    if isinstance(ref,dict):
        return str(ref.get("id") or "")
    return str(ref or "") if isinstance(ref,(str,int)) else ""


def matching_reply(item, attempt):
    if not isinstance(item,dict):
        return False
    if not str(item.get("id") or "").isdecimal():
        return False
    if not item.get("text") or not parent_id(item):
        return False
    if parent_id(item)!=str(attempt.get("target_post_id") or ""):
        return False
    created=timestamp(item.get("timestamp"))
    started=timestamp(attempt.get("attempted_at"))
    # A single attempted write can have server acknowledgement failure; look
    # for actual user-owned replies shortly after that attempt, not unrelated
    # historical comments on the same source post.
    if not created or not started:
        return False
    return started-timedelta(seconds=90)<=created<=started+timedelta(hours=2)


def read_own_replies(token, *, read=thread_request):
    for fields in (FIELDS,BACKUP_FIELDS):
        try:
            data=read("GET","/me/replies",token,
                      params={"fields":fields,"limit":50})
            items=data.get("data") if isinstance(data,dict) else None
            return items if isinstance(items,list) else []
        except requests.HTTPError as exc:
            code=getattr(getattr(exc,"response",None),"status_code",0)
            if code==400 and fields==FIELDS:
                continue
            raise
    return []


def verify_ambiguous(db, *, token=None, expected=None, read=thread_request,
                     now=None):
    now=now or datetime.now(timezone.utc)
    pending=db.request("GET","/enna_companion_attempts",params={
        "select":"id,github_issue_id,target_post_id,status,attempted_at",
        "status":"eq.uncertain",
        "attempted_at":"gte."+(now-timedelta(hours=48)).isoformat(),
        "order":"attempted_at.desc",
        "limit":"12",
    })
    if not isinstance(pending,list) or not pending:
        return {"state":"no_uncertain_attempts","verified":0}
    if token is None or expected is None:
        credential=get_credentials(db)
        if credential is None:
            return {"state":"oauth_not_available","verified":0}
        token,expected=credential
    if expected!="dohay_dilam":
        return {"state":"account_mismatch","verified":0}
    try:
        verify_meta_account(token,expected)
        replies=read_own_replies(token,read=read)
    except requests.HTTPError as exc:
        status=getattr(getattr(exc,"response",None),"status_code",0)
        return {"state":"meta_read_http_"+str(status or "error"),"verified":0}
    except (requests.RequestException,ValueError,KeyError,TypeError):
        return {"state":"meta_read_unavailable","verified":0}

    seen=set()
    confirmed=0
    for attempt in pending:
        reply=next((item for item in replies
                    if matching_reply(item,attempt)
                    and str(item["id"]) not in seen),None)
        if reply is None:
            continue
        rid=str(reply["id"])
        seen.add(rid)
        # This corrects only a previously ambiguous attempt; never submits a
        # new comment or changes any definitively rejected attempt.
        db.patch("enna_companion_attempts",str(attempt["id"]),{
            "status":"posted",
            "meta_reply_id":rid,
            "finished_at":now.isoformat(),
            "error_kind":None,
        })
        confirmed+=1
        print("Enna Meta self-reply verified for one prior uncertain attempt")
    return {"state":"verified" if confirmed else "no_matching_reply",
            "verified":confirmed,"checked":len(pending)}


def main():
    db=Database()
    result=verify_ambiguous(db)
    print("Enna read-only reply verification:",
          result["state"],"verified",result["verified"])


if __name__=="__main__":
    main()
