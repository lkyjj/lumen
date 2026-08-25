from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

import pytest

from lumen.agents import critic as critic_module
from lumen.agents.critic import review_clip
from lumen.agents.screenwriter import Screenwriter, write_script
from lumen.agents.storyboarder import Storyboarder, build_storyboard
from lumen.config import load_project
from lumen.contracts import FilmProject, QualityGate, Script


@pytest.fixture(scope="module")
def project() -> FilmProject:
    root = Path(__file__).resolve().parents[1]
    return load_project(root / "projects" / "vanishing-light" / "film.yaml")


class NeverCalled:
    def __call__(self, *_args: Any, **_kwargs: Any) -> Any:
        raise AssertionError("injected model must not be called in frozen mode")


def test_screenwriter_frozen_is_offline_and_uses_contracts(project: FilmProject) -> None:
    script = write_script(project, frozen=True, llm=NeverCalled())

    assert isinstance(script, Script)
    assert len(script.beats) == 14
    assert [beat.shot_id for beat in script.beats] == [shot.id for shot in project.shots]
    assert script.beats[6].dialogue == project.shots[6].audio.voice
    assert script.beats[11].dialogue == "……万一呢。"
    assert Screenwriter(llm=NeverCalled()).from_frozen_project(project) == script


def test_screenwriter_live_uses_injected_llm_and_validates(project: FilmProject) -> None:
    expected = write_script(project)
    calls: list[tuple[str, str]] = []

    def llm(system_prompt: str, user_prompt: str) -> dict[str, Any]:
        calls.append((system_prompt, user_prompt))
        return expected.model_dump(mode="json")

    actual = write_script(project, frozen=False, llm=llm)

    assert actual == expected
    assert len(calls) == 1
    assert "output_schema" in calls[0][1]


def test_screenwriter_live_rejects_changed_frozen_ids(project: FilmProject) -> None:
    payload = write_script(project).model_dump(mode="json")
    payload["beats"][0]["shot_id"] = "S99"

    with pytest.raises(ValueError, match="must match frozen shot ids"):
        write_script(project, frozen=False, llm=lambda _system, _user: payload)


def test_storyboarder_preserves_frozen_shots_without_model(project: FilmProject) -> None:
    script = write_script(project)
    shots = build_storyboard(project, script, regenerate=False, llm=NeverCalled())

    assert len(shots) == 14
    assert shots == project.shots
    assert all(actual is not frozen for actual, frozen in zip(shots, project.shots, strict=True))
    assert Storyboarder(llm=NeverCalled()).from_frozen_project(project) == shots


def test_storyboarder_regenerates_only_explicitly_and_strictly(project: FilmProject) -> None:
    script = write_script(project)
    payload = {"shots": [shot.model_dump(mode="json") for shot in project.shots]}
    calls = 0

    def llm(_system_prompt: str, _user_prompt: str) -> dict[str, Any]:
        nonlocal calls
        calls += 1
        return payload

    shots = build_storyboard(project, script, regenerate=True, llm=llm)

    assert calls == 1
    assert shots == project.shots


def test_storyboarder_rejects_invalid_regenerated_duration(project: FilmProject) -> None:
    script = write_script(project)
    payload = {"shots": [shot.model_dump(mode="json") for shot in project.shots]}
    payload["shots"][0]["duration"] = 8

    with pytest.raises(ValueError, match="duration_target"):
        build_storyboard(
            project,
            script,
            regenerate=True,
            llm=lambda _system, _user: payload,
        )


class FakeMediaTools:
    def __init__(self, *, duration: float = 8.0) -> None:
        self.duration = duration
        self.calls: list[list[str]] = []
        self.temp_directories: set[Path] = set()

    def __call__(self, command: list[str], **_kwargs: Any) -> subprocess.CompletedProcess[str]:
        self.calls.append(command)
        executable = Path(command[0]).name
        if executable == "ffprobe":
            return subprocess.CompletedProcess(command, 0, stdout=f"{self.duration}\n", stderr="")
        if executable == "ffmpeg":
            output = Path(command[-1])
            self.temp_directories.add(output.parent)
            output.write_bytes(b"offline-jpeg-frame")
            return subprocess.CompletedProcess(command, 0, stdout="", stderr="")
        raise AssertionError(f"unexpected executable: {executable}")


def test_critic_extracts_three_even_frames_and_ignores_model_passed(
    project: FilmProject,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    clip = tmp_path / "shot.mp4"
    clip.write_bytes(b"offline-video")
    media_tools = FakeMediaTools(duration=8.0)
    monkeypatch.setattr(critic_module.subprocess, "run", media_tools)
    vlm_calls: list[tuple[str, ...]] = []

    def vlm(_shot: Any, frames: tuple[str, ...], _anchor: str) -> dict[str, Any]:
        vlm_calls.append(frames)
        return {
            "scores": {
                "角色一致性": 9,
                "构图符合分镜": 9,
                "光线氛围": 9,
                "无明显崩坏": 5.5,
            },
            "overall": 10,
            "passed": True,
            "critique": "末帧存在明显形变。",
            "fix_hint": "固定人物姿态并减少末帧运动。",
        }

    verdict = review_clip(
        project.shots[2],
        clip,
        vlm=vlm,
        gate=QualityGate(min_score=7, min_dimension_score=6),
    )

    assert verdict.overall == 8.12
    assert verdict.passed is False
    assert len(vlm_calls) == 1
    assert len(vlm_calls[0]) == 3
    assert all(frame.startswith("data:image/jpeg;base64,") for frame in vlm_calls[0])

    ffmpeg_calls = [call for call in media_tools.calls if Path(call[0]).name == "ffmpeg"]
    timestamps = [float(call[call.index("-ss") + 1]) for call in ffmpeg_calls]
    assert timestamps == pytest.approx([2.0, 4.0, 6.0])
    assert media_tools.temp_directories
    assert all(not directory.exists() for directory in media_tools.temp_directories)


def test_critic_can_pass_despite_model_passed_false(
    project: FilmProject,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    clip = tmp_path / "shot.mp4"
    clip.write_bytes(b"offline-video")
    media_tools = FakeMediaTools()
    monkeypatch.setattr(critic_module.subprocess, "run", media_tools)

    verdict = review_clip(
        project.shots[2],
        clip,
        vlm=lambda _shot, _frames, _anchor: {
            "scores": {
                "character_consistency": 8,
                "composition": 8,
                "lighting": 8,
                "integrity": 8,
            },
            "overall": 1,
            "passed": False,
            "critique": "符合分镜。",
            "fix_hint": "无需修改。",
        },
    )

    assert verdict.overall == 8
    assert verdict.passed is True
    assert all(not directory.exists() for directory in media_tools.temp_directories)
