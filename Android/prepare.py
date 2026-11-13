#!/usr/bin/env python3
"""把 MaaLYSK 组装成 MaaFwApp 需要的 PI 根目录，并写入 Android 构建元数据。

MaaFwApp 的 profile.assets 必须指向「interface.json 所在的那一层」。MaaLYSK 的
interface.json 在 assets/ 下，而 agent/ 与 requirements.txt 在仓库根，所以这里先
复制出一个完整的 payload，不改动源文件：

    Android/.build/payload/
    ├── interface.json
    ├── android-build.json
    ├── resource/**
    ├── agent/**              (含 agent/deploy/.version)
    ├── requirements.txt
    ├── README.md
    ├── LICENSE
    ├── LICENSE-MaaFwApp
    └── LICENSES.md

Android 上没有 pip；预写 agent/deploy/.version 与 interface.json 的 version 一致，
agent/main.py 里的 deploy() 才会跳过依赖安装。
"""

from __future__ import annotations

import argparse
import copy
import json
import re
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_WORK = ROOT / "Android" / ".build"

VERSION_RE = re.compile(
    r"^(?:v?\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?|ci\.[0-9A-Za-z._-]+)$"
)

RESOURCE_IGNORE = shutil.ignore_patterns(
    "__pycache__", "*.pyc", "*.pyo", ".pytest_cache", "*.log", ".DS_Store"
)
AGENT_IGNORE = shutil.ignore_patterns(
    "__pycache__",
    "*.pyc",
    "*.pyo",
    ".pytest_cache",
    ".venv",
    "debug",
    "tests",
    "*.log",
    ".DS_Store",
)

OCR_FILES = ("det.onnx", "rec.onnx", "keys.txt")

LICENSES_MD = """# 许可证

本 APK 同时包含以下两部分：

- **MaaLYSK** 的资源与 agent：MIT License，见 [LICENSE](LICENSE)。
- **MaaFwApp** Android 外壳：GNU Affero General Public License v3.0，见
  [LICENSE-MaaFwApp](LICENSE-MaaFwApp)。

MaaFwApp 的源码：https://github.com/Aliothmoon/MaaFwApp
"""


def validate_version(version: str) -> str:
    """发版 tag（vX.Y.Z...）或 CI 版本（ci.<run>-<sha>）。"""
    if not VERSION_RE.fullmatch(version):
        raise ValueError(f"不支持的 Android 版本号：{version!r}")
    return version


def android_interface(source: dict, version: str) -> dict:
    """生成 Android 专用 interface.json，不改动源文件。

    控制器列表原样保留：任务的 controller[] 引用的是 "ADB模拟器" 这个名字，
    MaaFwApp 加载时会自己筛出 type=Adb 的项。
    """
    interface = copy.deepcopy(source)
    interface["version"] = validate_version(version)

    # Android 没有 MirrorChyan 渠道；留着会让应用内更新去查桌面资源流。
    interface.pop("mirrorchyan_rid", None)
    interface.pop("mirrorchyan_multiplatform", None)

    # MaaFwApp 实际用 profile 的 agent.runtimes 启动，不看这两个字段；
    # 改成 payload 相对路径，方便调试时阅读。
    interface["agent"] = {
        "child_exec": "python3",
        "child_args": ["-u", "agent/main.py"],
    }
    interface["license"] = "LICENSES.md"

    controllers = interface.get("controller") or []
    if not any(
        isinstance(item, dict) and item.get("type") == "Adb" for item in controllers
    ):
        raise ValueError("interface.json 没有 type=Adb 的 controller")
    return interface


def write_json(path: Path, value: dict) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def shell_revision(shell_source: Path) -> str:
    try:
        return subprocess.check_output(
            ["git", "-C", str(shell_source), "rev-parse", "HEAD"],
            text=True,
            encoding="utf-8",
            stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:
        return ""


def stage(
    work: Path,
    version: str,
    version_code: int,
    maafw_version: str,
    agent_core_tag: str,
    abi: str,
    shell_source: Path,
) -> dict:
    work = work.resolve()
    root = ROOT.resolve()
    if work == root or not work.is_relative_to(root):
        raise ValueError(f"构建目录必须位于仓库内：{work}")

    payload = work / "payload"
    if payload.is_symlink():
        raise ValueError(f"拒绝使用被重定向的 payload 目录：{payload}")
    if payload.exists():
        shutil.rmtree(payload)
    payload.mkdir(parents=True)

    shutil.copytree(
        ROOT / "assets" / "resource", payload / "resource", ignore=RESOURCE_IGNORE
    )
    shutil.copytree(ROOT / "agent", payload / "agent", ignore=AGENT_IGNORE)
    for name in ("requirements.txt", "README.md", "LICENSE"):
        shutil.copy2(ROOT / name, payload / name)

    source = json.loads((ROOT / "assets" / "interface.json").read_text(encoding="utf-8"))
    write_json(payload / "interface.json", android_interface(source, version))

    # Android 没有 pip：版本一致时 deploy() 直接跳过依赖检查。
    (payload / "agent" / "deploy").mkdir(parents=True, exist_ok=True)
    (payload / "agent" / "deploy" / ".version").write_text(
        version + "\n", encoding="utf-8", newline="\n"
    )

    ocr = payload / "resource" / "base" / "model" / "ocr"
    for name in OCR_FILES:
        path = ocr / name
        if not path.is_file() or path.stat().st_size == 0:
            raise FileNotFoundError(
                f"OCR 模型缺失或为空：{path}\n"
                "先在仓库根执行 python tools/ci/configure.py"
            )

    shell_license = shell_source / "LICENSE"
    if not shell_license.is_file():
        raise FileNotFoundError(f"MaaFwApp LICENSE 不存在：{shell_license}")
    shutil.copy2(shell_license, payload / "LICENSE-MaaFwApp")
    (payload / "LICENSES.md").write_text(
        LICENSES_MD, encoding="utf-8", newline="\n"
    )

    metadata = {
        "project": "MaaLYSK",
        "version": validate_version(version),
        "versionCode": version_code,
        "maafwVersion": maafw_version,
        "agentCoreTag": agent_core_tag,
        "abi": abi,
        "shellRepository": "Aliothmoon/MaaFwApp",
        "shellRevision": shell_revision(shell_source),
    }
    write_json(payload / "android-build.json", metadata)

    print(f"payload        : {payload}")
    print(f"version        : {version} ({version_code})")
    print(f"maafw          : {maafw_version} / {agent_core_tag}")
    print(f"profile        : {ROOT / 'Android' / 'profile.yaml'}")
    return metadata


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", required=True, help="发版 tag 或 ci.<run>-<sha>")
    parser.add_argument("--version-code", type=int, default=1)
    parser.add_argument("--maafw-version", default="")
    parser.add_argument("--agent-core-tag", default="")
    parser.add_argument("--abi", default="")
    parser.add_argument(
        "--shell-source",
        type=Path,
        required=True,
        help="MaaFwApp checkout，用于复制 LICENSE 并记录提交",
    )
    parser.add_argument("--work", type=Path, default=DEFAULT_WORK)
    parser.add_argument("--github-output", type=Path)
    args = parser.parse_args()

    if not 1 <= args.version_code <= 2_100_000_000:
        raise SystemExit("versionCode 必须在 1..2100000000 之间")

    shell_source = args.shell_source.resolve()
    if not shell_source.is_dir():
        raise SystemExit(f"MaaFwApp checkout 不存在：{shell_source}")

    metadata = stage(
        work=args.work,
        version=args.version,
        version_code=args.version_code,
        maafw_version=args.maafw_version,
        agent_core_tag=args.agent_core_tag,
        abi=args.abi,
        shell_source=shell_source,
    )

    if args.github_output:
        with args.github_output.open("a", encoding="utf-8") as output:
            output.write(f"version={metadata['version']}\n")
            output.write(f"version_code={metadata['versionCode']}\n")
            output.write(f"payload={args.work.resolve() / 'payload'}\n")
            output.write(f"profile={ROOT / 'Android' / 'profile.yaml'}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
