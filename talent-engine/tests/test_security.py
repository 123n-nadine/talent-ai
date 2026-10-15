import json

from app.core.security import hash_api_key, sign_callback, verify_callback


def test_hmac_sign_and_verify():
    body = json.dumps({"screening_id": "scr_1", "score": 81.5}).encode()
    sig = sign_callback("secret", "1700000000", body)
    assert sig.startswith("sha256=")
    assert verify_callback("secret", "1700000000", body, sig, now=1700000100)
    assert not verify_callback("other", "1700000000", body, sig, now=1700000100)
    assert not verify_callback("secret", "1700000000", body + b" ", sig, now=1700000100)
    assert not verify_callback(
        "secret", "1700000001", body, sig, now=1700000100
    )  # timestamp is signed


def test_old_timestamp_rejected():
    body = b"{}"
    sig = sign_callback("secret", "1700000000", body)
    assert not verify_callback("secret", "1700000000", body, sig, now=1700000000 + 301)
    assert verify_callback("secret", "1700000000", body, sig, now=1700000000 + 299)


def test_api_key_hash_is_stable():
    assert hash_api_key("abc") == hash_api_key("abc") and len(hash_api_key("abc")) == 64
