from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

AGE_EXTRACTION = [
    "mother is 5 times daughters present age and after 6 years mother is 3 times daughters age",
    "how old is the daughter",
]


def _start(problem_id):
    resp = client.post("/api/v1/sessions/start", json={"problem_id": problem_id})
    assert resp.status_code == 200
    return resp.json()


def _step(session_id, text):
    resp = client.post(f"/api/v1/sessions/{session_id}/step", json={"student_input": text})
    assert resp.status_code == 200
    return resp.json()


def _classify(problem_id, lines):
    resp = client.post("/api/v1/jev/classify", json={"problem_id": problem_id, "lines": lines})
    assert resp.status_code == 200
    return resp.json()


def test_use_jev_on_start_and_reset():
    for pid in ("g08-lin-ex003", "g08-hegp206-age-q7", "g10-quad-ex001"):
        data = _start(pid)
        assert data["use_jev"] is True
        reset = client.post(f"/api/v1/sessions/{data['session_id']}/reset").json()
        assert reset["use_jev"] is True
    plain = _start("g08-hegp201-ex010")
    assert plain["use_jev"] is False
    assert client.post(f"/api/v1/sessions/{plain['session_id']}/reset").json()["use_jev"] is False


def test_classify_shared_step_is_correct_but_uncertain():
    data = _classify("g08-lin-ex003", ["3x - 6 + 5 = 2x + 4"])
    assert data["status"] == "uncertain"
    assert data["method"]["status"] == "uncertain"
    assert data["validation"]["is_valid"] is True
    assert any(l["status"] == "valid" for l in data["validation"]["lines"])
    assert data["method_labels"] == {"m1_transpose": "Transposition", "m2_balance": "Balancing", "m3_trial": "Trial and Error"}
    assert data["declared_methods"] == [None]


def test_classify_maths_mistake_wins():
    data = _classify("g08-lin-ex003", ["3x - 6 + 5 = 2x + 4", "3x - 6 + 5 = 2x + 5"])
    assert data["status"] == "fix_mistake"
    assert "mistake" in data["feedback"]


def test_classify_selects_method_from_all_lines():
    data = _classify("g08-lin-ex003", ["3x - 6 + 5 = 2x + 4", "3x - 2x = 4 + 1"])
    assert data["status"] == "on_track"
    assert data["method"]["methodId"] == "m1_transpose"
    # a line that is also a graph step is not a bare method declaration
    assert data["declared_methods"] == [None, None]


def test_classify_reports_method_declaration():
    data = _classify("g08-hegp206-age-q7", ["mother = x"])
    assert data["method"]["methodId"] == "method2"
    assert data["declared_methods"] == ["method2"]


def test_classify_unknown_problem_and_empty_lines():
    assert client.post("/api/v1/jev/classify", json={"problem_id": "nope", "lines": ["x"]}).status_code == 404
    assert client.post("/api/v1/jev/classify", json={"problem_id": "g08-lin-ex003", "lines": ["  "]}).status_code == 400


def test_lock_method_then_replay_pending_lines():
    sid = _start("g08-lin-ex003")["session_id"]
    lock = client.post(f"/api/v1/sessions/{sid}/method", json={"method_id": "m2_balance"})
    assert lock.status_code == 200
    assert lock.json()["method_id"] == "m2"
    assert lock.json()["active_node_id"] == "m2_s1"

    step = _step(sid, "3x - 6 + 5 = 2x + 4")
    assert step["verdict"] == "ACCEPT"
    assert step["active_node_id"] == "m2_s2"


def test_lock_method_with_unprefixed_method_id():
    # "method2" has no m2_ prefix; the session must still use the m2_step* chain
    sid = _start("g08-hegp206-age-q7")["session_id"]
    for line in AGE_EXTRACTION:
        assert _step(sid, line)["verdict"] == "ACCEPT"
    lock = client.post(f"/api/v1/sessions/{sid}/method", json={"method_id": "method2"}).json()
    assert lock["method_id"] == "m2"
    assert lock["method_label"] == "Method 2: Linear Equation (Mother = x)"
    for line in ["daughter = x/5", "x + 6 = 3(x/5 + 6)", "x = 30", "30/5 = 6"]:
        assert _step(sid, line)["verdict"] == "ACCEPT"
    assert _step(sid, "daughter is 6 and mother is 30")["completed"] is True


def test_lock_method_rejected_before_extraction_or_twice():
    sid = _start("g08-hegp206-age-q7")["session_id"]
    assert client.post(f"/api/v1/sessions/{sid}/method", json={"method_id": "method1"}).status_code == 409

    sid = _start("g08-lin-ex003")["session_id"]
    assert client.post(f"/api/v1/sessions/{sid}/method", json={"method_id": "m1_transpose"}).status_code == 200
    assert client.post(f"/api/v1/sessions/{sid}/method", json={"method_id": "m2_balance"}).status_code == 409
    assert client.post("/api/v1/sessions/missing/method", json={"method_id": "m1_transpose"}).status_code == 404


def test_legacy_jev_method_endpoint_unchanged():
    data = client.post("/api/jev/method", json={"problemId": "g10-quad-ex001", "studentWork": "factor it"}).json()
    assert data["status"] == "selected"
    assert data["methodId"] == "m1_factor"
