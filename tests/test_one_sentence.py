from __future__ import annotations

import socket
from pathlib import Path

from lumen.cli import main
from lumen.one_sentence import plan_one_sentence

FILM = Path(__file__).parents[1] / "projects" / "vanishing-light" / "film.yaml"


def test_one_sentence_plan_is_zero_network(monkeypatch) -> None:
    def forbidden_socket(*args, **kwargs):
        raise AssertionError("plan attempted network access")

    monkeypatch.setattr(socket, "socket", forbidden_socket)
    result = plan_one_sentence("最后一座灯塔熄灭前，守塔人看见海面升起第二个太阳。", film=FILM)
    assert result["network_called"] is False
    assert [step["agent"] for step in result["task_plan"]] == [
        "producer",
        "cinematographer",
        "critic",
    ]
    assert result["worst_case_cost_cny"] > 0


def test_one_sentence_cli_defaults_to_plan(capsys) -> None:
    assert main(["create", "一个人在黑暗中追逐最后一束会记忆的光。", "--film", str(FILM)]) == 0
    output = capsys.readouterr().out
    assert '"mode": "dry-run"' in output
    assert '"network_called": false' in output


def test_one_sentence_live_requires_confirmation(capsys) -> None:
    result = main(
        ["create", "一个人在黑暗中追逐最后一束会记忆的光。", "--film", str(FILM), "--execute"]
    )
    assert result == 2
    assert "--confirm-spend" in capsys.readouterr().err
