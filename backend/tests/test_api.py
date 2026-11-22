from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_get_all_problems():
    response = client.get("/api/v1/problems")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 34
    assert any(p["problem_uuid"] == "g08-hegp201-ex010" for p in data)
    assert any(p["problem_uuid"] == "g10-prob-bag-balls" for p in data)
    assert any(p["problem_uuid"] == "g10-prob-die-throw" for p in data)


def test_get_problem_details():
    response = client.get("/api/v1/problems/g08-hegp201-ex010")
    assert response.status_code == 200
    data = response.json()
    assert data["problem_id"] == "g08-hegp201-ex010"
    assert "₹21,000" in data["problem_text"]
    assert data["extraction_optional"] is False

    # Test graph endpoint
    graph_resp = client.get("/api/v1/problems/g08-hegp201-ex010/graph")
    assert graph_resp.status_code == 200
    g_data = graph_resp.json()
    assert "nodes" in g_data
    assert "edges" in g_data
    assert g_data["start_node"] == "start"
    assert g_data["conclusion_node"] == "conclusion"



def test_session_lifecycle_and_step_verification():
    # 1. Start Session
    start_resp = client.post("/api/v1/sessions/start", json={"problem_id": "g08-hegp201-ex010"})
    assert start_resp.status_code == 200
    session_data = start_resp.json()
    session_id = session_data["session_id"]
    assert session_data["active_node_id"] == "given_extraction"
    assert session_data["active_label"] == "Extract Given Information"
    assert session_data["completed"] is False

    # 2. Submit Given Extraction
    step1 = client.post(
        f"/api/v1/sessions/{session_id}/step",
        json={"student_input": "Original value = ₹21000, Rate = 5%, Time = 1 year"}
    )
    assert step1.status_code == 200
    s1_data = step1.json()
    assert s1_data["verdict"] == "ACCEPT"
    assert s1_data["active_node_id"] == "goal_extraction"

    # 3. Submit Goal Extraction
    step2 = client.post(
        f"/api/v1/sessions/{session_id}/step",
        json={"student_input": "Value after 1 year"}
    )
    assert step2.status_code == 200
    s2_data = step2.json()
    assert s2_data["verdict"] == "ACCEPT"

    # 4. Method 1 Step 1
    step3 = client.post(
        f"/api/v1/sessions/{session_id}/step",
        json={"student_input": "1050"}
    )
    assert step3.status_code == 200
    s3_data = step3.json()
    assert s3_data["verdict"] == "ACCEPT"
    assert s3_data["active_node_id"] == "m1_step2"

    # 5. Method 1 Step 2 (The calculation from user screenshots!)
    step4 = client.post(
        f"/api/v1/sessions/{session_id}/step",
        json={"student_input": "₹21,000 - ₹1050 = ₹19,950"}
    )
    assert step4.status_code == 200
    s4_data = step4.json()
    assert s4_data["verdict"] == "ACCEPT"
    assert s4_data["active_node_id"] == "conclusion"

    # 6. Conclusion
    step5 = client.post(
        f"/api/v1/sessions/{session_id}/step",
        json={"student_input": "19950"}
    )
    assert step5.status_code == 200
    s5_data = step5.json()
    assert s5_data["verdict"] == "CONCLUSION_RIGHT"
    assert s5_data["completed"] is True

    # 7. Reset session
    reset_resp = client.post(f"/api/v1/sessions/{session_id}/reset")
    assert reset_resp.status_code == 200
    r_data = reset_resp.json()
    assert r_data["completed"] is False
    assert r_data["active_node_id"] == "given_extraction"


def test_api_404_handling():
    # Unknown problem
    resp1 = client.post("/api/v1/sessions/start", json={"problem_id": "non-existent-problem"})
    assert resp1.status_code == 404

    # Unknown session
    resp2 = client.post("/api/v1/sessions/sess_fake123/step", json={"student_input": "1050"})
    assert resp2.status_code == 404


def test_jev_method_endpoint():
    # Test factoring
    res1 = client.post(
        "/api/jev/method",
        json={"problemId": "g10-quad-ex001", "studentWork": "(x - 2)(x - 3) = 0"}
    )
    assert res1.status_code == 200
    d1 = res1.json()
    assert d1["status"] in ("selected", "off_graph", "uncertain")
    if d1["status"] == "selected":
        assert d1["methodKey"] == "factoring"

    # Test gibberish
    res2 = client.post(
        "/api/jev/method",
        json={"problemId": "g10-quad-ex001", "studentWork": "gdjgdj"}
    )
    assert res2.status_code == 200
    d2 = res2.json()
    assert d2["status"] in ("off_graph", "uncertain")


def test_full_conversation_history_recording():
    # 1. Start session
    start_resp = client.post("/api/v1/sessions/start", json={"problem_id": "g08-hegp201-ex010"})
    assert start_resp.status_code == 200
    sess = start_resp.json()
    session_id = sess["session_id"]
    assert sess["history"] == []

    # 2. Submit wrong step
    wrong_resp = client.post(
        f"/api/v1/sessions/{session_id}/step",
        json={"student_input": "1050 + 500 = 2000"}
    )
    assert wrong_resp.status_code == 200
    w_data = wrong_resp.json()
    assert len(w_data["history"]) == 1
    turn1 = w_data["history"][0]
    assert turn1["turn"] == 1
    assert turn1["input"] == "1050 + 500 = 2000"
    assert turn1["is_correct"] is False
    assert turn1["verdict"] == "WRONG_CLAIM"
    assert turn1["feedback"] is not None
    # Trail only has verified accepted steps, so trail is still empty
    assert len(w_data["trail"]) == 0

    # 3. Submit correct given extraction step
    correct_resp = client.post(
        f"/api/v1/sessions/{session_id}/step",
        json={"student_input": "Original value = ₹21000, Rate = 5%, Time = 1 year"}
    )
    assert correct_resp.status_code == 200
    c_data = correct_resp.json()
    assert len(c_data["history"]) == 2
    turn2 = c_data["history"][1]
    assert turn2["turn"] == 2
    assert turn2["is_correct"] is True
    assert turn2["verdict"] == "ACCEPT"
    # Trail has 1 verified step now
    assert len(c_data["trail"]) == 1

    # 4. Reset clears history
    reset_resp = client.post(f"/api/v1/sessions/{session_id}/reset")
    assert reset_resp.status_code == 200
    assert reset_resp.json()["history"] == []


def test_session_and_error_logging():
    import json
    from app.services.session_logger import SESSIONS_DIR, ERRORS_FILE

    # 1. Start session
    start_resp = client.post("/api/v1/sessions/start", json={"problem_id": "g08-hegp201-ex010"})
    assert start_resp.status_code == 200
    sess_id = start_resp.json()["session_id"]

    # 2. Verify session log file exists
    sess_file = SESSIONS_DIR / f"{sess_id}.json"
    assert sess_file.exists()

    # 3. Submit wrong step
    client.post(
        f"/api/v1/sessions/{sess_id}/step",
        json={"student_input": "1050 + 500 = 2000"}
    )

    # 4. Check session file content
    with open(sess_file, "r", encoding="utf-8") as f:
        sess_data = json.load(f)
    assert sess_data["session_id"] == sess_id
    assert sess_data["total_turns"] == 1
    assert sess_data["mistakes_count"] == 1
    assert sess_data["conversation"][0]["verdict"] == "WRONG_CLAIM"

    # 5. Check errors.jsonl contains the mistake
    assert ERRORS_FILE.exists()
    with open(ERRORS_FILE, "r", encoding="utf-8") as f:
        error_lines = f.readlines()
    assert any(sess_id in line and "1050 + 500 = 2000" in line for line in error_lines)


def test_api_early_conclusion_and_method_mismatch():
    # 1. Start Problem 1 session
    start_resp = client.post("/api/v1/sessions/start", json={"problem_id": "g08-hegp107-ex001"})
    assert start_resp.status_code == 200
    sess_id = start_resp.json()["session_id"]

    # 2. Direct conclusion on Turn 1 -> EARLY_CONCLUSION
    step1_resp = client.post(
        f"/api/v1/sessions/{sess_id}/step",
        json={"student_input": "yes they are proportional"}
    )
    assert step1_resp.status_code == 200
    d1 = step1_resp.json()
    assert d1["verdict"] == "EARLY_CONCLUSION"
    assert d1["completed"] is False
    assert "show your steps" in d1["feedback_message"].lower()

    # 3. Enter Step 1 of Simplification (Method 1)
    step2_resp = client.post(
        f"/api/v1/sessions/{sess_id}/step",
        json={"student_input": "24"}
    )
    assert step2_resp.status_code == 200
    d2 = step2_resp.json()
    assert d2["verdict"] == "ACCEPT"
    assert d2["method_id"] == "m1"

    # 4. Enter step belonging to Cross Multiplication (Method 5) -> METHOD_MISMATCH
    step3_resp = client.post(
        f"/api/v1/sessions/{sess_id}/step",
        json={"student_input": "3*96 = 288"}
    )
    assert step3_resp.status_code == 200
    d3 = step3_resp.json()
    assert d3["verdict"] == "METHOD_MISMATCH"
    assert "Cross Multiplication" in d3["feedback_message"]
    assert "Simplification" in d3["feedback_message"]
    assert d3["completed"] is False

    # 5. Start a new session and leap > 2 hops -> STEP_JUMP
    start_resp2 = client.post("/api/v1/sessions/start", json={"problem_id": "g08-hegp107-ex001"})
    sess_id2 = start_resp2.json()["session_id"]
    jump_resp = client.post(
        f"/api/v1/sessions/{sess_id2}/step",
        json={"student_input": "3:4 = 3:4"}
    )
    assert jump_resp.status_code == 200
    dj = jump_resp.json()
    assert dj["verdict"] == "STEP_JUMP"
    assert dj["jumped_node_id"] == "shared_ratio_comparison"
    assert "leaped ahead" in dj["feedback_message"].lower()
    assert dj["completed"] is False
    assert len(dj["trail"]) == 0


def test_probability_bag_balls_problem():
    # Start session for probability bag problem
    start_resp = client.post("/api/v1/sessions/start", json={"problem_id": "g10-prob-bag-balls"})
    assert start_resp.status_code == 200
    sess_id = start_resp.json()["session_id"]

    # Step 1: Total balls
    s1 = client.post(f"/api/v1/sessions/{sess_id}/step", json={"student_input": "8"}).json()
    assert s1["verdict"] == "ACCEPT"
    assert s1["active_node_id"] == "m1_s2"

    # Step 2: Red probability
    s2 = client.post(f"/api/v1/sessions/{sess_id}/step", json={"student_input": "3/8"}).json()
    assert s2["verdict"] == "ACCEPT"
    assert s2["active_node_id"] == "m1_s3"

    # Step 3: Not red probability
    s3 = client.post(f"/api/v1/sessions/{sess_id}/step", json={"student_input": "5/8"}).json()
    assert s3["verdict"] == "ACCEPT"
    assert s3["active_node_id"] == "conclusion"

    # Step 4: Final Conclusion
    s4 = client.post(f"/api/v1/sessions/{sess_id}/step", json={"student_input": "3/8 and 5/8"}).json()
    assert s4["verdict"] == "CONCLUSION_RIGHT"
    assert s4["completed"] is True


def test_probability_die_throw_problem():
    # Start session for die throw problem
    start_resp = client.post("/api/v1/sessions/start", json={"problem_id": "g10-prob-die-throw"})
    assert start_resp.status_code == 200
    sess_id = start_resp.json()["session_id"]

    # Step 1: Total outcomes
    s1 = client.post(f"/api/v1/sessions/{sess_id}/step", json={"student_input": "6"}).json()
    assert s1["verdict"] == "ACCEPT"
    assert s1["active_node_id"] == "m1_s2"

    # Step 2: Prime probability
    s2 = client.post(f"/api/v1/sessions/{sess_id}/step", json={"student_input": "1/2"}).json()
    assert s2["verdict"] == "ACCEPT"
    assert s2["active_node_id"] == "m1_s3"

    # Step 3: Number between 2 and 6 probability
    s3 = client.post(f"/api/v1/sessions/{sess_id}/step", json={"student_input": "1/2"}).json()
    assert s3["verdict"] == "ACCEPT"
    assert s3["active_node_id"] == "m1_s4"

    # Step 4: Odd number probability
    s4 = client.post(f"/api/v1/sessions/{sess_id}/step", json={"student_input": "1/2"}).json()
    assert s4["verdict"] == "ACCEPT"
    assert s4["active_node_id"] == "conclusion"

    # Step 5: Final Conclusion
    s5 = client.post(f"/api/v1/sessions/{sess_id}/step", json={"student_input": "1/2, 1/2, 1/2"}).json()
    assert s5["verdict"] == "CONCLUSION_RIGHT"
    assert s5["completed"] is True


def test_probability_marbles_sample_sessions_and_extra_effort():
    # 1. Sequential Socratic Flow as in sample_sessions.md
    s1 = client.post("/api/v1/sessions/start", json={"problem_id": "g10-prob-marbles"}).json()
    sess1 = s1["session_id"]
    assert "sample space" in s1["prompt"].lower()

    # Turn 1: sample space = 9
    t1 = client.post(f"/api/v1/sessions/{sess1}/step", json={"student_input": "9"}).json()
    assert t1["verdict"] == "ACCEPT"
    assert "event" in t1["next_prompt"].lower()

    # Turn 2: event = 2
    t2 = client.post(f"/api/v1/sessions/{sess1}/step", json={"student_input": "2"}).json()
    assert t2["verdict"] == "ACCEPT"
    assert "probability" in t2["next_prompt"].lower()

    # Turn 3: probability = 2/9
    t3 = client.post(f"/api/v1/sessions/{sess1}/step", json={"student_input": "2/9"}).json()
    assert t3["verdict"] == "ACCEPT"
    assert "explain" in t3["next_prompt"].lower()

    # Turn 4: reasoning
    t4 = client.post(
        f"/api/v1/sessions/{sess1}/step",
        json={"student_input": "2 favourable outcomes out of 9 possible outcomes"}
    ).json()
    assert t4["verdict"] == "CONCLUSION_RIGHT"
    assert t4["completed"] is True

    # 2. Combined Answer / Extra Effort Leap: Student gives both sample space and event
    s2 = client.post("/api/v1/sessions/start", json={"problem_id": "g10-prob-marbles"}).json()
    sess2 = s2["session_id"]
    t_combo = client.post(
        f"/api/v1/sessions/{sess2}/step",
        json={"student_input": "sample space is 9 and white is 2"}
    ).json()
    assert t_combo["verdict"] == "ACCEPT"
    assert "great effort" in t_combo["feedback_message"].lower()
    assert t_combo["active_node_id"] == "m1_s3"
    assert "probability" in t_combo["next_prompt"].lower()

    # 3. Redirection when input does not address the question
    s3 = client.post("/api/v1/sessions/start", json={"problem_id": "g10-prob-marbles"}).json()
    sess3 = s3["session_id"]
    t_unanswered = client.post(
        f"/api/v1/sessions/{sess3}/step",
        json={"student_input": "i like the colors"}
    ).json()
    assert t_unanswered["verdict"] == "GARBAGE"
    assert "does not address" in t_unanswered["feedback_message"].lower()
    assert s3["prompt"] in t_unanswered["feedback_message"]






