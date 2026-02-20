"""
Unit tests for modules.microgpt.engine
"""

from pathlib import Path
from unittest.mock import patch

import pytest


@pytest.fixture(autouse=True)
def test_env(monkeypatch):
    monkeypatch.setenv("COMMITKIM_ENV", "test")

def test_value_addition_backward():
    from modules.microgpt.engine import Value
    a = Value(2.0)
    b = Value(3.0)
    c = a + b
    c.backward()
    assert c.data == 5.0
    assert a.grad == 1.0
    assert b.grad == 1.0

def test_value_complex_expression():
    from modules.microgpt.engine import Value
    a = Value(2.0)
    b = Value(3.0)
    c = a * b
    d = c + Value(4.0)
    e = d.relu()
    e.backward()
    assert e.data == 10.0
    assert a.grad == 3.0
    assert b.grad == 2.0

def test_microgpt_visualizer_run(tmp_path):
    from modules.microgpt.engine import MicroGPTVisualizer
    
    with patch("modules.microgpt.engine.PROJECT_ROOT", tmp_path), \
         patch("urllib.request.urlretrieve") as mock_retrieve:
        
        def mock_download(url, filename):
            Path(filename).write_text("a\\nb\\nc\\n", encoding="utf-8")
        mock_retrieve.side_effect = mock_download
        
        viz = MicroGPTVisualizer()
        viz.num_steps = 1
        
        trace = viz.run()
        
        assert trace is not None
        assert "final_loss" in trace
        assert "loss_history" in trace
        assert "samples" in trace
