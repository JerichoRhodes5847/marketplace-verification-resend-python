from marketplace_verification import VerificationRequest, resend_verification, summarize_delivery


def test_latest_delivery_event_is_surface_for_handoff():
    events = [{"status": "queued"}, {"status": "delivered"}]
    assert summarize_delivery(events) == "delivered"
    assert summarize_delivery([]) == "pending"


def test_resend_sends_message_id_in_body():
    class Client:
        def __init__(self):
            self.calls = []

        def request(self, method, path, body=None):
            self.calls.append((method, path, body))
            return []

    client = Client()
    item = VerificationRequest("seller", "", "message-123", "order")
    resend_verification(item, client)
    assert client.calls[0] == ("POST", "/v1/sms/resend/message-123", {"message_id": "message-123"})
