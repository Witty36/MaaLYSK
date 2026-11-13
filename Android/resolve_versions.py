#!/usr/bin/env python3
"""解析 Android 构建要用的 MaaFW / MaaAgentCoreAndroid 配对版本。

版本链条：
    requirements.txt  maafw==X
        ↓
    build_agent_bundle.py  CORE_PY（例如 3.13.15）
        ↓
    MaaAgentCoreAndroid release  <CORE_PY>-maafw<版本>

规则（与 M9A 的 resolver 同思路，去掉纯 pipeline 分支）：
1. 有精确配对 → 直接用
2. 内核还没出精确配对 → 退到“不高于 requirements 固定版本的最近配对”，打 warning
3. 固定版本比内核全部配对都旧 → 报错并列出现有配对
4. AGENT_CORE_TAG 可应急指定内核；若它的 maafw 版本与 requirements 不同，
   以它为准（client 原生库会跟着内核走），打 warning

输出（--github-output）：
    core_py, core_tag, maafw_version, maafw_tag, degraded
"""

from __future__ import annotations

import argparse
import os
import re
from dataclasses import dataclass
from pathlib import Path

try:
    from packaging.version import InvalidVersion, Version
except ImportError:  # CI 已安装 packaging；本地退到 pip 自带的那份
    from pip._vendor.packaging.version import InvalidVersion, Version

REQUIREMENT_RE = re.compile(r"^maafw==([0-9][^\s;#]*)", re.MULTILINE)
CORE_PY_RE = re.compile(r'^CORE_PY\s*=\s*"([^"]+)"', re.MULTILINE)
# 3.13.15-maafw5.13.1 / 3.13.15-maafw5.15.0-beta.1
CORE_TAG_RE = re.compile(
    r"^(\d[0-9A-Za-z.]*)-maafw([0-9A-Za-z][0-9A-Za-z.+-]*)$"
)

ENV_OVERRIDE = "AGENT_CORE_TAG"


@dataclass(frozen=True)
class Resolution:
    core_tag: str
    maafw_version: str
    degraded: bool
    warnings: tuple[str, ...]


def read_pin(text: str) -> str:
    match = REQUIREMENT_RE.search(text)
    if match is None:
        raise ValueError("requirements.txt 缺少精确的 maafw==X")
    return match.group(1)


def read_core_py(text: str) -> str:
    match = CORE_PY_RE.search(text)
    if match is None:
        raise ValueError("build_agent_bundle.py 里找不到 CORE_PY")
    return match.group(1)


def parse_version(text: str) -> Version:
    try:
        return Version(text)
    except InvalidVersion as error:
        raise ValueError(f"无法解析版本 {text!r}: {error}") from error


def pairings(tags: list[str], core_py: str) -> dict[Version, tuple[str, str]]:
    """按 CPython 版本过滤，返回 {归一化版本: (完整 tag, tag 里的原文版本)}。"""
    result: dict[Version, tuple[str, str]] = {}
    for tag in tags:
        tag = tag.strip()
        match = CORE_TAG_RE.fullmatch(tag)
        if match is None or match.group(1) != core_py:
            continue
        raw = match.group(2)
        try:
            version = Version(raw)
        except InvalidVersion:
            continue
        # 同一版本可能有 -beta.1 / b1 两种拼写；保留先出现的那个
        result.setdefault(version, (tag, raw))
    return result


def maafw_release_tag(version: str, maafw_tags: list[str]) -> tuple[str, str | None]:
    """MaaFramework 的 release tag 可能用预发布原文（v5.15.0-beta.1），
    而 requirements 里是归一形式（5.15.0b1）；按 PEP 440 找原文 tag。"""
    target = parse_version(version)
    for tag in maafw_tags:
        tag = tag.strip()
        raw = tag.removeprefix("v")
        try:
            if Version(raw) == target:
                return tag, None
        except InvalidVersion:
            continue
    return f"v{version}", (
        f"MaaFramework release 里找不到与 maafw{version} 对应的 tag，回退到 v{version}"
    )


def resolve(
    pin: str,
    core_py: str,
    tags: list[str],
    override: str = "",
) -> Resolution:
    pin_version = parse_version(pin)
    warnings: list[str] = []

    if override:
        match = CORE_TAG_RE.fullmatch(override.strip())
        if match is None:
            raise ValueError(f"{ENV_OVERRIDE} 格式不对：{override!r}")
        if override.strip() not in {tag.strip() for tag in tags}:
            raise ValueError(f"{ENV_OVERRIDE} 不在内核 release 列表里：{override}")
        if match.group(1) != core_py:
            raise ValueError(
                f"{ENV_OVERRIDE} 的 CPython 是 {match.group(1)}，"
                f"但 build_agent_bundle.py 的 CORE_PY 是 {core_py}"
            )
        raw = match.group(2)
        version = parse_version(raw)
        if version != pin_version:
            warnings.append(
                f"{ENV_OVERRIDE} 的内核绑定是 maafw{raw}，"
                f"与 requirements 的 maafw{pin} 不一致；按应急覆盖处理，"
                "client 原生库会跟着内核走"
            )
        return Resolution(override.strip(), raw, False, tuple(warnings))

    available = pairings(tags, core_py)
    if not available:
        raise ValueError(f"没有 CPython {core_py} 的内核 release")

    exact = available.get(pin_version)
    if exact is not None:
        tag, raw = exact
        return Resolution(tag, raw, False, ())

    eligible = {version: item for version, item in available.items() if version <= pin_version}
    if not eligible:
        existing = "、".join(item[1] for _, item in sorted(available.items()))
        raise ValueError(
            f"内核没有不高于 maafw{pin} 的配对；"
            f"现有 CPython {core_py} 配对：{existing}。"
            "确认 requirements.txt 没写错，或等内核发版；"
            f"应急可以用 {ENV_OVERRIDE}"
        )

    version = max(eligible)
    tag, raw = eligible[version]
    warnings.append(
        f"内核还没出 maafw{pin} 的配对，降级到 maafw{raw}；"
        "APK 内 Python 绑定与原生库仍同版本，只是比 requirements 固定的版本旧"
    )
    return Resolution(tag, raw, True, tuple(warnings))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--requirements", type=Path, required=True)
    parser.add_argument(
        "--shell-source",
        type=Path,
        required=True,
        help="MaaFwApp checkout；从 scripts/build_agent_bundle.py 读 CORE_PY",
    )
    parser.add_argument(
        "--core-tags",
        type=Path,
        required=True,
        help="MaaAgentCoreAndroid release tag 列表，一行一个",
    )
    parser.add_argument(
        "--maafw-tags",
        type=Path,
        help="MaaFramework release tag 列表（可选）；用于找回预发布版本的原文 tag",
    )
    parser.add_argument(
        "--agent-core-tag",
        default=os.environ.get(ENV_OVERRIDE, ""),
        help=f"应急覆盖内核 tag；默认读环境变量 {ENV_OVERRIDE}",
    )
    parser.add_argument("--github-output", type=Path)
    args = parser.parse_args()

    try:
        pin = read_pin(args.requirements.read_text(encoding="utf-8"))
        shell_script = (
            args.shell_source / "scripts" / "build_agent_bundle.py"
        ).read_text(encoding="utf-8")
        core_py = read_core_py(shell_script)
        tags = args.core_tags.read_text(encoding="utf-8").splitlines()
        resolution = resolve(pin, core_py, tags, args.agent_core_tag)
        maafw_tags = (
            args.maafw_tags.read_text(encoding="utf-8").splitlines()
            if args.maafw_tags
            else []
        )
        maafw_tag, tag_warning = maafw_release_tag(
            resolution.maafw_version, maafw_tags
        )
    except (OSError, ValueError) as error:
        print(f"::error::{error}")
        return 1

    for warning in (*resolution.warnings, tag_warning):
        if warning:
            print(f"::warning::{warning}")
    print(f"requirements pin : maafw{pin}")
    print(f"core CPython     : {core_py}")
    print(f"agent core tag   : {resolution.core_tag}")
    print(f"maafw version    : {resolution.maafw_version}")
    print(f"maafw tag        : {maafw_tag}")
    print(f"degraded         : {resolution.degraded}")

    if args.github_output:
        with args.github_output.open("a", encoding="utf-8") as output:
            output.write(f"core_py={core_py}\n")
            output.write(f"core_tag={resolution.core_tag}\n")
            output.write(f"maafw_version={resolution.maafw_version}\n")
            output.write(f"maafw_tag={maafw_tag}\n")
            output.write(f"degraded={'true' if resolution.degraded else 'false'}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
