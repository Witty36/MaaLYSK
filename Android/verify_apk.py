#!/usr/bin/env python3
"""校验 MaaFwApp 打出来的 MaaLYSK APK，避免「能装但跑不起来」。

检查项：
- aapt2 badging：包名、versionName / versionCode、minSdk、native-code、label
- lib/<abi>/：MaaFramework、agent、bridge、launcher、agentexec 等原生库
- assets/pi.zip：interface 版本、agent、.version、OCR 模型、android-build.json，且无构建垃圾
- assets/agent/agent-runtime.json / bundle.zip：运行时描述、Python、loguru、_multiprocessing 补丁
- apksigner：必须签名；可选证书指纹比对

通过后把 APK 复制到 --output，并写出 .sha256 与 validation.json。
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import zipfile
from pathlib import Path

REQUIRED_LIBS = (
    "libMaaFramework.so",
    "libMaaUtils.so",
    "libMaaAndroidNativeControlUnit.so",
    "libMaaAgentServer.so",
    "libbridge.so",
    "liblauncher.so",
    "libagentexec.so",
    "libc++_shared.so",
)

OCR_FILES = ("det.onnx", "rec.onnx", "keys.txt")

FORBIDDEN = re.compile(
    r"(^|/)(\.git|__pycache__|\.venv|tests)/|\.(pyc|pyo|log)$", re.IGNORECASE
)


def _same_version(left: object, right: object) -> bool:
    """内核清单可能写 5.15.0b1，tag 原文是 5.15.0-beta.1，按 PEP 440 比。"""
    try:
        from packaging.version import Version
    except ImportError:
        from pip._vendor.packaging.version import Version
    try:
        return Version(str(left)) == Version(str(right))
    except Exception:
        return str(left) == str(right)


def _exe(name: str) -> str:
    return name + ".exe" if os.name == "nt" else name


def _build_tool(sdk: Path, relative: str) -> Path:
    build_tools = sdk / "build-tools"
    if not build_tools.is_dir():
        raise FileNotFoundError(f"找不到 Android build-tools：{build_tools}")
    for version in sorted(build_tools.iterdir(), reverse=True):
        candidate = version / relative
        if candidate.is_file():
            return candidate
    raise FileNotFoundError(f"build-tools 里找不到 {relative}")


def _run(command: list[str]) -> str:
    return subprocess.check_output(
        command, text=True, encoding="utf-8", errors="replace"
    )


def _check_badging(sdk: Path, apk: Path, args) -> None:
    aapt2 = _build_tool(sdk, _exe("aapt2"))
    badging = _run([str(aapt2), "dump", "badging", str(apk)])

    match = re.search(
        r"package: name='([^']+)' versionCode='([^']+)' versionName='([^']*)'",
        badging,
    )
    if match is None:
        raise ValueError("aapt2 badging 里解析不到 package 行")
    package_id, version_code, version_name = match.groups()
    if package_id != args.package_id:
        raise ValueError(f"包名不符：{package_id} != {args.package_id}")
    if version_code != str(args.version_code):
        raise ValueError(f"versionCode 不符：{version_code} != {args.version_code}")
    if version_name != args.version:
        raise ValueError(f"versionName 不符：{version_name} != {args.version}")

    if "minSdkVersion:'28'" not in badging:
        raise ValueError("minSdkVersion 不是 28")

    native = re.search(r"native-code: (.*)", badging)
    if native is None or args.abi not in native.group(1):
        raise ValueError(f"native-code 不含 {args.abi}：{native.group(1) if native else '缺失'}")

    if f"application-label:'{args.label}'" not in badging:
        raise ValueError(f"application-label 不是 {args.label}")


def _signature(sdk: Path, apk: Path) -> str:
    jar = _build_tool(sdk, "lib/apksigner.jar")
    java = Path(os.environ.get("JAVA_HOME", "")) / "bin" / _exe("java")
    command = [str(java) if java.is_file() else _exe("java"), "-jar", str(jar)]
    command += ["verify", "--verbose", "--print-certs", str(apk)]
    output = _run(command)
    match = re.search(r"Signer #1 certificate SHA-256 digest: ([0-9a-fA-F]+)", output)
    if match is None:
        raise ValueError("apksigner 没有输出证书指纹")
    return match.group(1).lower()


def _check_pi(apk: zipfile.ZipFile, args) -> None:
    if "assets/pi.zip" not in apk.namelist():
        raise ValueError("APK 缺少 assets/pi.zip")
    with zipfile.ZipFile(io.BytesIO(apk.read("assets/pi.zip"))) as pi:
        if pi.testzip() is not None:
            raise ValueError("assets/pi.zip 已损坏")
        names = pi.namelist()
        for required in ("interface.json", "agent/main.py", "agent/deploy/.version"):
            if required not in names:
                raise ValueError(f"pi.zip 缺少 {required}")

        interface = json.loads(pi.read("interface.json"))
        if interface.get("version") != args.version:
            raise ValueError(
                f"interface.version 不符：{interface.get('version')} != {args.version}"
            )
        if interface.get("mirrorchyan_rid") is not None:
            raise ValueError("Android interface 不应带 mirrorchyan_rid")
        agent = interface.get("agent") or {}
        if agent.get("child_args") != ["-u", "agent/main.py"]:
            raise ValueError(f"interface.agent.child_args 不符：{agent.get('child_args')}")
        if not any(
            isinstance(item, dict) and item.get("type") == "Adb"
            for item in interface.get("controller") or []
        ):
            raise ValueError("interface 缺少 type=Adb 的 controller")

        version_file = pi.read("agent/deploy/.version").decode("utf-8").strip()
        if version_file != args.version:
            raise ValueError(
                f"agent/deploy/.version 不符：{version_file} != {args.version}"
            )

        for name in OCR_FILES:
            path = f"resource/base/model/ocr/{name}"
            if path not in names or pi.getinfo(path).file_size <= 0:
                raise ValueError(f"pi.zip 缺少 OCR 模型 {path}")

        if "android-build.json" not in names:
            raise ValueError("pi.zip 缺少 android-build.json")
        metadata = json.loads(pi.read("android-build.json"))
        for key, expected in (
            ("version", args.version),
            ("versionCode", args.version_code),
            ("abi", args.abi),
        ):
            if metadata.get(key) != expected:
                raise ValueError(
                    f"android-build.json {key} 不符：{metadata.get(key)} != {expected}"
                )
        if not _same_version(metadata.get("maafwVersion"), args.maafw_version):
            raise ValueError(
                "android-build.json maafwVersion 不符："
                f"{metadata.get('maafwVersion')} != {args.maafw_version}"
            )

        bad = [name for name in names if FORBIDDEN.search(name)]
        if bad:
            raise ValueError(f"pi.zip 含有不该打包的文件：{bad[:5]}")


def _check_agent(apk: zipfile.ZipFile, args) -> None:
    runtime_path = "assets/agent/agent-runtime.json"
    if runtime_path not in apk.namelist():
        raise ValueError(f"APK 缺少 {runtime_path}")
    runtime = json.loads(apk.read(runtime_path))
    runtimes = runtime.get("runtimes") or []
    if len(runtimes) != 1:
        raise ValueError(f"agent-runtime.json 应有 1 条 runtime，实际 {len(runtimes)}")
    entry = runtimes[0]
    if entry.get("location") != "bundle":
        raise ValueError(f"agent runtime location 不是 bundle：{entry.get('location')}")
    if entry.get("args") != ["-u", "agent/main.py"]:
        raise ValueError(f"agent runtime args 不符：{entry.get('args')}")
    env = entry.get("env") or {}
    if env.get("MAAFW_BINARY_PATH") != "{nativeLibs}":
        raise ValueError("agent runtime 缺少 MAAFW_BINARY_PATH={nativeLibs}")

    bundle_path = "assets/agent/bundle.zip"
    if bundle_path not in apk.namelist():
        raise ValueError(f"APK 缺少 {bundle_path}")
    with zipfile.ZipFile(io.BytesIO(apk.read(bundle_path))) as bundle:
        if bundle.testzip() is not None:
            raise ValueError("assets/agent/bundle.zip 已损坏")
        names = bundle.namelist()
        prefix = f"{args.abi}/"
        for required in (
            f"{prefix}bin/python3",
            f"{prefix}agent-core.json",
            f"{prefix}site-packages/_multiprocessing.py",
        ):
            if required not in names:
                raise ValueError(f"bundle.zip 缺少 {required}")
        if not any(
            re.fullmatch(rf"{re.escape(prefix)}prefix/lib/libpython3\.\d+\.so", name)
            for name in names
        ):
            raise ValueError(f"bundle.zip 缺少 {prefix}prefix/lib/libpython3.X.so")

        core = json.loads(bundle.read(f"{prefix}agent-core.json"))
        provided = core.get("provides", {}).get("maafw")
        if not _same_version(provided, args.maafw_version):
            raise ValueError(
                f"agent 内核绑定版本不符：{provided} != {args.maafw_version}"
            )

        pure = f"{prefix}site-packages/pure.zip"
        if pure not in names:
            raise ValueError(f"bundle.zip 缺少 {pure}")
        with zipfile.ZipFile(io.BytesIO(bundle.read(pure))) as packages:
            if "loguru/__init__.py" not in packages.namelist():
                raise ValueError("pure.zip 里没有 loguru")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("apk", type=Path)
    parser.add_argument("--abi", required=True)
    parser.add_argument("--version", required=True)
    parser.add_argument("--version-code", type=int, required=True)
    parser.add_argument("--package-id", required=True)
    parser.add_argument("--label", default="MaaLYSK")
    parser.add_argument("--maafw-version", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--name", required=True)
    parser.add_argument("--sdk", type=Path, required=True)
    parser.add_argument("--certificate-sha256", default="")
    args = parser.parse_args()

    apk = args.apk.resolve()
    if not apk.is_file():
        raise FileNotFoundError(f"APK 不存在：{apk}")

    with zipfile.ZipFile(apk) as archive:
        names = archive.namelist()
        for lib in REQUIRED_LIBS:
            required = f"lib/{args.abi}/{lib}"
            if required not in names:
                raise ValueError(f"APK 缺少 {required}")
        if "assets/shizuku.apk" not in names:
            raise ValueError("APK 缺少内置的 assets/shizuku.apk")
        _check_pi(archive, args)
        _check_agent(archive, args)

    _check_badging(args.sdk, apk, args)
    certificate = _signature(args.sdk, apk)
    if args.certificate_sha256:
        expected = args.certificate_sha256.lower().replace(":", "")
        if certificate != expected:
            raise ValueError(
                f"签名证书不符：{certificate} != {expected}"
            )

    args.output.mkdir(parents=True, exist_ok=True)
    target = args.output / args.name
    shutil.copy2(apk, target)
    digest = hashlib.sha256(target.read_bytes()).hexdigest()
    (args.output / f"{args.name}.sha256").write_text(
        f"{digest}  {args.name}\n", encoding="ascii"
    )

    report = {
        "apk": args.name,
        "sha256": digest,
        "certificateSha256": certificate,
        "version": args.version,
        "versionCode": args.version_code,
        "packageId": args.package_id,
        "abi": args.abi,
        "maafwVersion": args.maafw_version,
        "verified": True,
    }
    (args.output / "validation.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
