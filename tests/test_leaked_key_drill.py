from src.leaked_key_drill import decide_drill, verify_webhook


def test_only_temporary_key_is_rotated_after_blast_radius_search():
    decision = decide_drill("temporary-1", 3, True)
    assert decision.log_hits == 3
    assert decision.rotate_temporary_key is True
    assert decide_drill("active-checkout", 3, False).rotate_temporary_key is False


def test_registered_webhook_signature_is_verified():
    body = b'{"event":"order.updated"}'
    assert verify_webhook(body, "8e2c8c9c", "secret") is False
