import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fastapi.testclient import TestClient
from main import app, create_stage_plan, MASTER


def test_health():
    r = TestClient(app).get('/api/health')
    assert r.status_code == 200
    assert r.json()['status'] == 'ok'


def test_stage_plan_deterministic():
    assert create_stage_plan(1) == create_stage_plan(1)
    assert create_stage_plan(12)['boss']['id'] == 'sunflower'
    assert create_stage_plan(13)['boss']['id'] == 'knight'


def test_all_bosses_and_monotonic_waves():
    for stage in range(1, 13):
        data = create_stage_plan(stage)
        assert data['boss']['id'] == MASTER['bosses'][stage - 1]['id']
        assert data['boss']['hp'] > 0
        assert all(w['hp'] > 0 for w in data['enemy_waves'])
        times = [w['spawn_delay_ms'] for w in data['enemy_waves']]
        assert times == sorted(times)


def test_invalid_stage():
    c = TestClient(app)
    assert c.get('/api/stage-start?stage=0').status_code == 422
    assert c.get('/api/stage-start?stage=121').status_code == 422
    assert c.get('/api/stage-start?stage=12').status_code == 200
