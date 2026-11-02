"""Safe official Meta Threads search diagnostic; never posts, stores tokens, or prints content.

Separates: API empty / scoped-to-own / results present but filtered out / eligible.
No scraping, no third-party data brokerage, no public content in GitHub logs.
"""
import json
import requests
from datetime import datetime, timedelta, timezone
from agent import Database
from growth.scoring import classify

API = "https://graph.threads.net/v1.0/keyword_search"
CASES = (
    ("self_control", "Sống gọn hơn", "KEYWORD", "RECENT"),
    ("office_recent", "bàn làm việc", "KEYWORD", "RECENT"),
    ("office_top", "công sở", "KEYWORD", "TOP"),
    ("work_topic", "văn phòng", "TAG", "TOP"),
)


def inspect(token, *, fetch=requests.get, now=None, cases=CASES):
    now = now or datetime.now(timezone.utc)
    output = []
    for name, query, mode, ranking in cases:
        try:
            resp = fetch(API,
                headers={"Authorization": "Bearer " + token},
                params={"q":query,"search_mode":mode,"search_type":ranking,
                        "fields":"id,text,username,permalink,timestamp","limit":30},
                timeout=15)
            resp.raise_for_status()
            payload = resp.json()
            rows = payload.get("data", [])
            if not isinstance(rows,list):
                raise ValueError("MalformedData")
            own = other = recent = qualifying = 0
            for item in rows[:30]:
                if not isinstance(item,dict):
                    continue
                is_own = str(item.get("username","")).casefold().lstrip("@") == "dohay_dilam"
                own += int(is_own)
                other += int(not is_own)
                raw_t = str(item.get("timestamp") or "").replace("Z","+00:00")
                try:
                    timestamp = datetime.fromisoformat(raw_t)
                    is_fresh = timestamp.tzinfo and timedelta(0) <= now-timestamp <= timedelta(hours=48)
                except (ValueError,TypeError):
                    is_fresh = False
                if not is_own and is_fresh:
                    recent += 1
                    if classify(item.get("text",""),timestamp,now=now)["state"]=="candidate":
                        qualifying += 1
            output.append({"test":name,"status":"ok","raw":len(rows),
                           "own":own,"foreign":other,"fresh_48h":recent,"eligible":qualifying})
        except requests.HTTPError as e:
            # No response body or URL: API error could contain private details.
            status = e.response.status_code if e.response is not None else None
            output.append({"test":name,"status":"http_error","http_code":status})
        except (requests.RequestException, ValueError, TypeError, OverflowError):
            output.append({"test":name,"status":"unavailable"})
    own_probe = next((x for x in output if x["test"]=="self_control"),{})
    foreign = sum(x.get("foreign",0) for x in output)
    raw = sum(x.get("raw",0) for x in output)
    eligible = sum(x.get("eligible",0) for x in output)
    if any(x["status"]=="http_error" for x in output):
        conclusion="api_error_review_permissions"
    elif foreign:
        conclusion="external_posts_present" if eligible else "external_posts_filtered"
    elif own_probe.get("own",0)>0:
        conclusion="own_only_possible_app_review"
    elif raw==0:
        conclusion="empty_raw_results_cause_unconfirmed"
    else:
        conclusion="only_own_posts_outside_control"
    return {"diagnostic_version":1,"result":conclusion,"tests":output}


def main():
    db=Database()
    rows=db.request("POST","/rpc/threads_read_vault_token",
                    payload={"p_brand_key":"do_hay_di_lam"})
    if not rows or rows[0].get("enable_replies") is not True:
        return {"result":"owner_oauth_switch_off"}
    from threads.credentials import load_credentials
    auth=load_credentials(db,refresh=False)
    if not auth:
        return {"result":"owner_oauth_unavailable"}
    result=inspect(auth[0])
    return result


if __name__=="__main__":
    try:
        print("Enna search diagnostic:",json.dumps(main(),ensure_ascii=False))
    except Exception as exc:
        print("Enna search diagnostic:", json.dumps({"result":"internal_failure","error_class":type(exc).__name__}))
