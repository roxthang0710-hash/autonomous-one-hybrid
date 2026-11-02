"""Unit tests for safe, real-API-compatible Threads publishing; fully mocked."""
import os
import unittest
from unittest.mock import Mock, patch

from threads.brand import BRAND_KEY
from threads.publisher import enabled, access, authenticate, do_publish, publish_due


class PublisherTests(unittest.TestCase):
    def test_unconfigured_is_never_live(self):
        with patch.dict(os.environ, {"THREADS_PUBLISH_ENABLED": "",
                                     "THREADS_ACCESS_TOKEN": "",
                                     "THREADS_EXPECTED_USERNAME": ""}):
            self.assertFalse(enabled())
            self.assertIsNone(access())
            db = Mock()
            with patch("threads.credentials.load_credentials", return_value=None):
                self.assertEqual(
                    publish_due(db),
                    "waiting_for_owner_oauth_and_enable_switch")
            db.request.assert_not_called()

    def test_token_alone_does_not_enable_live_posting(self):
        with patch.dict(os.environ, {"THREADS_PUBLISH_ENABLED": "false",
                                     "THREADS_ACCESS_TOKEN": "secret",
                                     "THREADS_EXPECTED_USERNAME": "my_brand"}):
            self.assertIsNone(access())

    def test_requires_expected_username(self):
        with patch.dict(os.environ, {"THREADS_PUBLISH_ENABLED": "true",
                                     "THREADS_ACCESS_TOKEN": "secret",
                                     "THREADS_EXPECTED_USERNAME": ""}):
            self.assertIsNone(access())

    def test_wrong_oauth_account_rejected(self):
        db = Mock()
        with patch("threads.publisher.thread_request",
                   return_value={"id": "111", "username": "other_brand"}):
            with self.assertRaises(ValueError):
                authenticate(db, "token", "my_brand")
        db.patch.assert_not_called()

    def test_account_verified_before_any_db_activation(self):
        db = Mock()
        channel = {"id": "channel", "username": None, "platform_user_id": None,
                   "status": "awaiting_account", "auto_publish_enabled": False}
        with patch("threads.publisher.thread_request",
                   return_value={"id": "444", "username": "my_brand"}), \
             patch("threads.publisher.get_channel", return_value=channel):
            authenticate(db, "token", "my_brand")
        args = db.request.call_args
        self.assertEqual(args.args[1], "/rpc/activate_threads_channel")
        self.assertEqual(args.kwargs["payload"]["p_platform_user_id"], "444")
        db.patch.assert_not_called()

    def test_meta_two_step_flow_not_autopublish_container(self):
        calls = []
        def fake(method, path, token, **kwargs):
            calls.append((method, path, kwargs))
            if path.endswith("/threads"):
                return {"id": "container"}
            if path.endswith("/threads_publish"):
                return {"id": "postid"}
            return {"id": "postid", "permalink": "https://www.threads.net/@x/post/abc"}
        with patch("threads.publisher.thread_request", side_effect=fake):
            result = do_publish(
                "token", "Một cách đơn giản là phân loại đồ làm việc theo tần suất sử dụng, "
                         "rồi dành phần mặt bàn dễ với tới cho những món dùng mỗi ngày."
            )
        self.assertEqual(result[1], "postid")
        self.assertEqual(calls[0][1], "/me/threads")
        self.assertEqual(calls[1][1], "/me/threads_publish")
        self.assertNotIn("auto_publish_text", calls[0][2]["data"])

    def test_native_topic_tag_only_for_allowlisted_direct_posts(self):
        calls = []
        def fake(method,path,token,**kwargs):
            calls.append((method,path,kwargs))
            if path == "/me/threads":
                return {"id":"container"}
            if path == "/me/threads_publish":
                return {"id":"post"}
            return {"id":"post","permalink":"https://www.threads.com/@dohay_dilam/post/abc"}
        with patch("threads.publisher.thread_request",side_effect=fake):
            do_publish("token","Một góc bàn làm việc nhỏ vẫn có thể rất gọn. "
                       "Hãy thử giữ đồ hay dùng trong tầm với.",topic_tag="Góc làm việc")
            self.assertEqual(calls[0][2]["data"]["topic_tag"],"Góc làm việc")
            with self.assertRaises(ValueError):
                do_publish("token","Một góc bàn làm việc nhỏ vẫn có thể rất gọn. "
                           "Hãy thử giữ đồ hay dùng trong tầm với.",topic_tag="Tin nóng")
        self.assertEqual(sum(call[1]=="/me/threads" for call in calls),1)

    def test_one_claim_max_per_worker_cycle(self):
        db = Mock()
        item = {"id": "post", "content_type": "editorial",
                "text_content": ("Bạn có mẹo nào để sắp xếp hành lý nhẹ hơn mà "
                                 "vẫn mang đủ đồ cần thiết cho chuyến công tác ngắn?")}
        db.request.side_effect = [0, [item]]
        db.insert.return_value = {"id": "attempt"}
        with patch.dict(os.environ, {"THREADS_PUBLISH_ENABLED": "true",
                                     "THREADS_ACCESS_TOKEN": "secret",
                                     "THREADS_EXPECTED_USERNAME": "my_brand"}), \
             patch("threads.credentials.load_credentials",
                   return_value=("token", "my_brand")), \
             patch("threads.publisher.authenticate"), \
             patch("threads.publisher.do_publish",
                   return_value=("container", "post123", "https://example.com/post")):
            self.assertEqual(publish_due(db), "published")
        claim = [x for x in db.request.call_args_list
                 if "/rpc/claim_threads_post" in str(x)]
        self.assertEqual(len(claim), 1)
        self.assertTrue(any(
            call.args[0] == "threads_posts"
            and call.args[2].get("topic_tag_requested") in ("Công sở",None)
            for call in db.patch.call_args_list
        ))
        db.insert.assert_called_once()

    def test_network_timeout_marks_uncertain_never_requeued(self):
        db = Mock()
        item = {"id": "post", "content_type": "editorial",
                "text_content": ("Có ai thấy góc làm việc gọn gàng giúp tìm đồ dễ hơn không? "
                                 "Bạn dùng mẹo sắp xếp nào thấy hợp với mình?")}
        db.request.side_effect = [0, [item]]
        db.insert.return_value = {"id": "attempt"}
        with patch.dict(os.environ, {"THREADS_PUBLISH_ENABLED": "true",
                                     "THREADS_ACCESS_TOKEN": "secret",
                                     "THREADS_EXPECTED_USERNAME": "my_brand"}), \
             patch("threads.credentials.load_credentials",
                   return_value=("token", "my_brand")), \
             patch("threads.publisher.authenticate"), \
             patch("threads.publisher.do_publish", side_effect=TimeoutError()):
            with self.assertRaises(RuntimeError):
                publish_due(db)
        self.assertTrue(any(
            call.args[0] == "threads_posts" and call.args[2]["status"] == "uncertain"
            for call in db.patch.call_args_list
        ))


if __name__ == "__main__":
    unittest.main()
