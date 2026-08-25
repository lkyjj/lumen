"""Deterministic ffmpeg editor; commands are argv lists and never invoke a shell."""

from __future__ import annotations

import shutil
import subprocess
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from lumen.agents.sound_designer import dialogue_timeline
from lumen.contracts import FilmProject

Runner = Callable[..., subprocess.CompletedProcess[bytes]]


def _escape_drawtext(text: str) -> str:
    return (
        text.replace("\\", "\\\\")
        .replace(":", "\\:")
        .replace("'", "\\'")
        .replace("%", "\\%")
    )


def normalize_clip_command(
    ffmpeg: str,
    source: Path,
    target: Path,
    *,
    duration: float,
    width: int = 1280,
    height: int = 720,
) -> list[str]:
    filter_graph = (
        f"scale={width}:{height}:force_original_aspect_ratio=decrease,"
        f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:black,fps=24,format=yuv420p,"
        f"tpad=stop_mode=clone:stop_duration={duration}"
    )
    return [
        ffmpeg,
        "-y",
        "-i",
        str(source),
        "-vf",
        filter_graph,
        "-t",
        f"{duration:.3f}",
        "-an",
        "-c:v",
        "libx264",
        "-preset",
        "medium",
        "-crf",
        "18",
        str(target),
    ]


def end_card_command(ffmpeg: str, target: Path, *, font_file: Path) -> list[str]:
    log_text = _escape_drawtext("SYSTEM LOG / 系统日志\\nE-06 拒绝进化。\\n原因：不可解析。")
    title_text = _escape_drawtext("消 失 的 光 芒\\nTHE VANISHING LIGHT")
    filters = (
        f"drawtext=fontfile='{font_file}':text='{log_text}':fontcolor=white:fontsize=36:"
        "line_spacing=16:x=(w-text_w)/2:y=(h-text_h)/2:enable='between(t,0,3)',"
        f"drawtext=fontfile='{font_file}':text='{title_text}':fontcolor=white:fontsize=42:"
        "line_spacing=20:x=(w-text_w)/2:y=(h-text_h)/2:enable='between(t,3,5)'"
    )
    return [
        ffmpeg,
        "-y",
        "-f",
        "lavfi",
        "-i",
        "color=c=black:s=1280x720:r=24:d=5",
        "-vf",
        filters,
        "-t",
        "5",
        "-an",
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        str(target),
    ]


def soundtrack_command(
    ffmpeg: str,
    project: FilmProject,
    dialogue: dict[str, str | Path],
    target: Path,
) -> list[str]:
    """Build a deterministic 100-second stereo mix with timed dialogue."""

    timeline = dialogue_timeline(project)
    missing = [shot_id for shot_id, _, _ in timeline if shot_id not in dialogue]
    if missing:
        raise ValueError("missing dialogue audio: " + ", ".join(missing))

    command = [
        ffmpeg,
        "-y",
        "-f",
        "lavfi",
        "-i",
        f"anullsrc=r=48000:cl=stereo:d={project.film.duration_target:.3f}",
    ]
    filters: list[str] = []
    mix_inputs = ["[0:a]"]
    for index, (shot_id, start_ms, _) in enumerate(timeline, start=1):
        command.extend(["-i", str(dialogue[shot_id])])
        filters.append(
            f"[{index}:a]aresample=48000,adelay={start_ms}:all=1[dialogue{index}]"
        )
        mix_inputs.append(f"[dialogue{index}]")
    filters.append(
        "".join(mix_inputs)
        + f"amix=inputs={len(mix_inputs)}:duration=first:normalize=0,"
        + f"alimiter=limit=0.95,atrim=duration={project.film.duration_target:.3f}[mix]"
    )
    command.extend(
        [
            "-filter_complex",
            ";".join(filters),
            "-map",
            "[mix]",
            "-c:a",
            "pcm_s16le",
            str(target),
        ]
    )
    return command


def mux_command(ffmpeg: str, picture: Path, soundtrack: Path, target: Path) -> list[str]:
    return [
        ffmpeg,
        "-y",
        "-i",
        str(picture),
        "-i",
        str(soundtrack),
        "-map",
        "0:v:0",
        "-map",
        "1:a:0",
        "-c:v",
        "copy",
        "-c:a",
        "aac",
        "-b:a",
        "192k",
        "-shortest",
        "-movflags",
        "+faststart",
        str(target),
    ]


@dataclass(slots=True)
class Editor:
    ffmpeg_bin: str = "ffmpeg"
    runner: Runner = subprocess.run

    def render_picture(
        self,
        project: FilmProject,
        clips: dict[str, str | Path],
        output_path: str | Path,
        *,
        work_dir: str | Path,
        font_file: str | Path,
    ) -> Path:
        missing = [shot.id for shot in project.shots if shot.id not in clips]
        if missing:
            raise ValueError("missing final clips: " + ", ".join(missing))
        if shutil.which(self.ffmpeg_bin) is None:
            raise FileNotFoundError(f"ffmpeg executable not found: {self.ffmpeg_bin}")
        font = Path(font_file)
        if not font.is_file():
            raise FileNotFoundError(font)

        work = Path(work_dir)
        work.mkdir(parents=True, exist_ok=True)
        normalized: list[Path] = []
        for shot in project.shots:
            source = Path(clips[shot.id])
            if not source.is_file():
                raise FileNotFoundError(source)
            target = work / f"{shot.id}_normalized.mp4"
            self.runner(
                normalize_clip_command(
                    self.ffmpeg_bin,
                    source,
                    target,
                    duration=shot.duration,
                ),
                check=True,
                capture_output=True,
            )
            normalized.append(target)

        end_card = work / "end_card.mp4"
        self.runner(
            end_card_command(self.ffmpeg_bin, end_card, font_file=font),
            check=True,
            capture_output=True,
        )
        concat_file = work / "concat.txt"
        concat_file.write_text(
            "".join(f"file '{path.resolve().as_posix()}'\n" for path in [*normalized, end_card]),
            encoding="utf-8",
        )
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        self.runner(
            [
                self.ffmpeg_bin,
                "-y",
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                str(concat_file),
                "-t",
                f"{project.film.duration_target:.3f}",
                "-c:v",
                "libx264",
                "-pix_fmt",
                "yuv420p",
                "-movflags",
                "+faststart",
                str(output),
            ],
            check=True,
            capture_output=True,
        )
        return output

    def render_master(
        self,
        project: FilmProject,
        clips: dict[str, str | Path],
        dialogue: dict[str, str | Path],
        output_path: str | Path,
        *,
        work_dir: str | Path,
        font_file: str | Path,
    ) -> Path:
        """Render the picture, place dialogue on the frozen timeline, then mux."""

        work = Path(work_dir)
        work.mkdir(parents=True, exist_ok=True)
        picture = work / "picture_silent.mp4"
        soundtrack = work / "soundtrack.wav"
        self.render_picture(
            project,
            clips,
            picture,
            work_dir=work / "picture",
            font_file=font_file,
        )
        for path in dialogue.values():
            if not Path(path).is_file():
                raise FileNotFoundError(path)
        self.runner(
            soundtrack_command(self.ffmpeg_bin, project, dialogue, soundtrack),
            check=True,
            capture_output=True,
        )
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        self.runner(
            mux_command(self.ffmpeg_bin, picture, soundtrack, output),
            check=True,
            capture_output=True,
        )
        return output
