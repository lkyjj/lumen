"""Art director agent for versioned anchor candidates and per-shot keyframes."""

from __future__ import annotations

from dataclasses import dataclass

from lumen.contracts import FilmProject, ProjectPaths, Shot, VisualAnchor
from lumen.providers.base import ImageProvider, ImageResult


class AnchorApprovalRequired(RuntimeError):
    def __init__(self, anchor_ids: list[str]) -> None:
        self.anchor_ids = tuple(anchor_ids)
        super().__init__(
            "以下视觉锚点尚未获创作者批准：" + ", ".join(anchor_ids)
        )


STYLE_PREFIX = "电影感，低照度，冷蓝灰色调，单一光源，轻微胶片颗粒，16:9。"
NEGATIVE_PROMPT = (
    "多人同框，对白口型，快速动作，手指精细操作，既有影视IP，真人肖像，"
    "霓虹赛博朋克，文字，水印，标志"
)


def unapproved_anchors(project: FilmProject) -> list[str]:
    return [anchor.id for anchor in project.anchors if not anchor.approved]


def require_anchor_approval(project: FilmProject) -> None:
    pending = unapproved_anchors(project)
    if pending:
        raise AnchorApprovalRequired(pending)


def anchor_prompt(project: FilmProject, anchor: VisualAnchor) -> str:
    return (
        f"{STYLE_PREFIX}\n"
        f"为原创科幻短片《{project.film.title}》生成视觉连续性锚点。{anchor.prompt}\n"
        "保持原创、克制、工业现实主义；不要模仿真人、明星或现有影视角色。"
    )


def keyframe_prompt(project: FilmProject, shot: Shot) -> str:
    anchor_text = ""
    if shot.anchor:
        anchor = next(item for item in project.anchors if item.id == shot.anchor)
        anchor_text = f"连续性锚点 {anchor.id}：{anchor.prompt}\n"
    return (
        f"{STYLE_PREFIX}\n"
        f"镜头 {shot.id}；景别：{shot.size}；运镜起始构图：{shot.movement}。\n"
        f"{anchor_text}导演意图：{shot.intent}\n画面：{shot.prompt_seed}\n"
        "生成可直接作为图生视频首帧的静止构图，无文字、无水印。"
    )


@dataclass(slots=True)
class ArtDirector:
    provider: ImageProvider

    def generate_anchor_candidates(
        self,
        project: FilmProject,
        paths: ProjectPaths,
        *,
        force: bool = False,
        api_key: str | None = None,
    ) -> list[ImageResult]:
        results: list[ImageResult] = []
        for anchor in project.anchors:
            output = paths.root / anchor.image
            if output.exists() and not force:
                continue
            results.append(
                self.provider.generate(
                    anchor_prompt(project, anchor),
                    output,
                    negative_prompt=NEGATIVE_PROMPT,
                    api_key=api_key,
                )
            )
        return results

    def generate_keyframes(
        self,
        project: FilmProject,
        paths: ProjectPaths,
        *,
        force: bool = False,
        api_key: str | None = None,
    ) -> dict[str, ImageResult]:
        require_anchor_approval(project)
        output_dir = paths.bible / "generated"
        output_dir.mkdir(parents=True, exist_ok=True)
        results: dict[str, ImageResult] = {}
        for shot in project.shots:
            output = output_dir / f"{shot.id}_keyframe.png"
            if output.exists() and not force:
                continue
            results[shot.id] = self.provider.generate(
                keyframe_prompt(project, shot),
                output,
                negative_prompt=NEGATIVE_PROMPT,
                api_key=api_key,
            )
        return results
