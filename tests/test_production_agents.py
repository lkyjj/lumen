from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from lumen.agents.art_director import (
    AnchorApprovalRequired,
    ArtDirector,
    require_anchor_approval,
)
from lumen.agents.cinematographer import Cinematographer, ShotNeedsHumanReview
from lumen.agents.editor import (
    Editor,
    end_card_command,
    mux_command,
    normalize_clip_command,
    soundtrack_command,
)
from lumen.agents.sound_designer import SoundDesigner, dialogue_timeline
from lumen.config import load_project, project_paths
from lumen.contracts import CriticScores, CriticVerdict
from lumen.providers import FakeImageProvider, FakeTTSProvider, FakeVideoProvider

FILM = Path(__file__).parents[1] / "projects" / "vanishing-light" / "film.yaml"


class QueueCritic:
    def __init__(self, verdicts: list[CriticVerdict]) -> None:
        self.verdicts = list(verdicts)
        self.calls: list[tuple[str, str]] = []

    def review(self, shot, clip_path, anchor_description=""):
        self.calls.append((shot.id, str(clip_path)))
        return self.verdicts.pop(0)


def verdict(score: float, *, passed: bool) -> CriticVerdict:
    scores = CriticScores(
        character_consistency=score,
        composition=score,
        lighting=score,
        integrity=score,
    )
    return CriticVerdict(
        scores=scores,
        overall=score,
        passed=passed,
        critique="人物转头导致构图偏离",
        fix_hint="人物完全静止并保持背对镜头",
    )


def test_art_director_requires_explicit_approval(tmp_path: Path) -> None:
    project = load_project(FILM)
    with pytest.raises(AnchorApprovalRequired):
        require_anchor_approval(project)
    director = ArtDirector(FakeImageProvider())
    with pytest.raises(AnchorApprovalRequired):
        director.generate_keyframes(project, project_paths(FILM))


def test_art_director_generates_versioned_candidate(tmp_path: Path) -> None:
    project = load_project(FILM)
    for anchor in project.anchors:
        anchor.image = f"candidates/{anchor.id}.png"
    paths = project_paths(tmp_path / "film.yaml")
    provider = FakeImageProvider()
    results = ArtDirector(provider).generate_anchor_candidates(project, paths)
    assert len(results) == 4
    assert all(result.path.is_file() for result in results)
    assert all(anchor.approved is False for anchor in project.anchors)


def test_cinematographer_feeds_critique_into_second_attempt(tmp_path: Path) -> None:
    project = load_project(FILM)
    shot = next(item for item in project.shots if item.id == "S03")
    keyframe = tmp_path / "frame.png"
    keyframe.write_bytes(b"frame")
    video = FakeVideoProvider()
    critic = QueueCritic([verdict(5, passed=False), verdict(8, passed=True)])
    result = Cinematographer(video, critic, project.quality_gate).shoot(
        shot,
        keyframe,
        tmp_path / "clips",
        resolution="720P",
    )
    assert result.passed is True
    assert result.attempt == 2
    assert "【本次最优先修正】" in video.calls[1]["prompt"]
    assert (tmp_path / "clips" / "S03_attempt_01.mp4").is_file()
    assert (tmp_path / "clips" / "S03_attempt_02.mp4").is_file()


def test_cinematographer_stops_after_three_failures(tmp_path: Path) -> None:
    project = load_project(FILM)
    shot = project.shots[0]
    keyframe = tmp_path / "frame.png"
    keyframe.write_bytes(b"frame")
    video = FakeVideoProvider()
    critic = QueueCritic([verdict(5, passed=False) for _ in range(3)])
    with pytest.raises(ShotNeedsHumanReview) as caught:
        Cinematographer(video, critic, project.quality_gate).shoot(
            shot,
            keyframe,
            tmp_path / "clips",
            resolution="720P",
        )
    assert len(video.calls) == 3
    assert caught.value.result.attempt == 3
    assert (tmp_path / "clips" / "S01_needs_human_review.json").is_file()


def test_sound_designer_uses_only_frozen_dialogue(tmp_path: Path) -> None:
    project = load_project(FILM)
    provider = FakeTTSProvider()
    results = SoundDesigner(provider).synthesize_dialogue(
        project,
        tmp_path,
        voices={"system": "system-voice", "human": "human-voice"},
    )
    assert list(results) == ["S07", "S12"]
    assert len(provider.calls) == 2
    assert dialogue_timeline(project) == [
        ("S07", 36_000, "进化程序07已就绪。剩余能源：1。是否预演结果？"),
        ("S12", 71_000, "……万一呢。"),
    ]


def test_editor_builds_argv_commands_without_shell() -> None:
    normalized = normalize_clip_command(
        "ffmpeg", Path("source.mp4"), Path("target.mp4"), duration=5
    )
    card = end_card_command("ffmpeg", Path("card.mp4"), font_file=Path("font.ttf"))
    assert isinstance(normalized, list)
    assert "shell=True" not in normalized
    assert "-t" in normalized
    assert "SYSTEM LOG" in card[card.index("-vf") + 1]


def test_editor_places_dialogue_on_frozen_timeline() -> None:
    project = load_project(FILM)
    command = soundtrack_command(
        "ffmpeg",
        project,
        {"S07": Path("system.wav"), "S12": Path("human.wav")},
        Path("soundtrack.wav"),
    )
    graph = command[command.index("-filter_complex") + 1]
    assert "adelay=36000:all=1" in graph
    assert "adelay=71000:all=1" in graph
    assert "amix=inputs=3:duration=first" in graph
    assert mux_command(
        "ffmpeg", Path("picture.mp4"), Path("soundtrack.wav"), Path("final.mp4")
    )[0] == "ffmpeg"


def test_editor_requires_all_fourteen_clips(tmp_path: Path, monkeypatch) -> None:
    project = load_project(FILM)
    monkeypatch.setattr("lumen.agents.editor.shutil.which", lambda _: "/bin/ffmpeg")
    editor = Editor(runner=lambda *args, **kwargs: SimpleNamespace(returncode=0))
    with pytest.raises(ValueError, match="S01"):
        editor.render_picture(
            project,
            {},
            tmp_path / "final.mp4",
            work_dir=tmp_path / "work",
            font_file=tmp_path / "font.ttf",
        )
