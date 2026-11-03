"""Single-use official Meta reply probe for an owner-selected public Threads post.

No HTML automation, cookie access, internal endpoints or hidden API calls.
A public post permalink supplies a numeric candidate post ID. Meta remains
the ultimate authority to accept or reject reply_to_id.

Never retry an ambiguous Meta publish response.
"""
import requests

from threads.publisher import thread_request


class ConfirmedMetaRejection(Exception):
    """The FIRST create-container request was definitively rejected by Meta."""

    def __init__(self, http_status):
        self.http_status = int(http_status)
        super().__init__("meta_create_rejected_" + str(self.http_status))


def status_code(exc):
    response = getattr(exc, "response", None)
    return getattr(response, "status_code", None)


def target_read_limited(exc):
    """Try a direct publish only when Meta actively refused a READ operation.

    Network errors, malformed results and HTTP 5xx are not permission evidence.
    Even then the caller must independently verify owner intent and post age.
    """
    return isinstance(exc, requests.HTTPError) and status_code(exc) in (400, 403)


def direct_reply(token, target_id, text, *, request=thread_request):
    """Call the regular official two-step reply API, at most once.

    Failure on the *create* call is distinguishable from a failure after a
    container was created, which is conservatively treated as uncertain.
    """
    if not (isinstance(target_id, str) and target_id.isdecimal()
            and 10 <= len(target_id) <= 28):
        raise ValueError("invalid_target_id")
    if not isinstance(text, str) or not 60 <= len(text) <= 380:
        raise ValueError("unsafe_reply_length")
    try:
        created = request("POST", "/me/threads", token,
                          data={"media_type": "TEXT", "text": text,
                                "reply_to_id": target_id})
    except requests.HTTPError as exc:
        status = status_code(exc)
        if status in (400, 401, 403, 404, 429):
            raise ConfirmedMetaRejection(status) from None
        raise
    container_id = str(created.get("id") or "")
    if not container_id:
        raise RuntimeError("meta_container_missing")
    # A create container may have succeeded. Never retry after this point.
    published = request("POST", "/me/threads_publish", token,
                        data={"creation_id": container_id})
    reply_id = str(published.get("id") or "")
    if not reply_id:
        raise RuntimeError("meta_publish_unconfirmed")
    return container_id, reply_id
