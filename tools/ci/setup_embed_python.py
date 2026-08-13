"""
下载并配置嵌入式 Python 到 install/python/。
使用 python-build-standalone（全量 CPython，自带 pip），针对 MaaLYSK 的 ubuntu 交叉打包，
接收 argv 传入目标 os/arch（而非 platform.system()）。

用法: python tools/ci/setup_embed_python.py <os> <arch>
  os   : win | macos | linux
  arch : x86_64 | aarch64
"""

import glob
import os
import shutil
import stat
import sys
import tarfile
import urllib.request

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]

PYTHON_VERSION = "3.12.12"
RELEASE_TAG = "20251209"

DEST_DIR = os.path.join("install", "python")


def normalize_os(raw: str) -> str | None:
    s = (raw or "").lower().strip()
    if s in ("win", "windows", "win32", "win64"):
        return "win"
    if s in ("macos", "osx", "darwin", "mac"):
        return "macos"
    if s == "linux":
        return "linux"
    return None


def normalize_arch(raw: str) -> str | None:
    s = (raw or "").lower().strip()
    if s in ("x86_64", "amd64", "x64"):
        return "x86_64"
    if s in ("aarch64", "arm64"):
        return "aarch64"
    return None


def download_file(url: str, dest_path: str) -> None:
    print(f"正在下载: {url}")
    print(f"到: {dest_path}")
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    with urllib.request.urlopen(url) as response, open(dest_path, "wb") as out_file:
        shutil.copyfileobj(response, out_file)
    print("下载完成。")


def extract_tar(tar_path: str, dest_dir: str) -> None:
    print(f"正在解压 TAR: {tar_path} 到 {dest_dir}")
    with tarfile.open(tar_path, "r:*") as tar_ref:
        tar_ref.extractall(path=dest_dir)
    print("TAR 解压完成。")


def get_python_executable(os_type: str) -> str | None:
    if os_type == "win":
        return os.path.join(DEST_DIR, "python.exe")
    if os_type == "macos":
        py3 = os.path.join(DEST_DIR, "bin", "python3")
        py = os.path.join(DEST_DIR, "bin", "python")
        return py3 if os.path.exists(py3) else (py if os.path.exists(py) else None)
    return None


def setup(os_type: str, arch: str) -> bool:
    """下载并解压 python-build-standalone（自带 pip）。"""
    if os_type == "win":
        target = f"{arch}-pc-windows-msvc"
    else:  # macos
        target = f"{arch}-apple-darwin"

    filename = (
        f"cpython-{PYTHON_VERSION}+{RELEASE_TAG}-{target}-install_only_stripped.tar.gz"
    )
    download_url = (
        "https://github.com/indygreg/python-build-standalone/releases/download/"
        f"{RELEASE_TAG}/{filename}"
    )
    tar_filepath = os.path.join(DEST_DIR, filename)
    temp_extract_dir = os.path.join(DEST_DIR, "_temp_extract")

    try:
        download_file(download_url, tar_filepath)
        os.makedirs(temp_extract_dir, exist_ok=True)
        extract_tar(tar_filepath, temp_extract_dir)

        extracted_root = os.path.join(temp_extract_dir, "python")
        if not os.path.isdir(extracted_root):
            print(f"错误: 解压后未找到预期的 'python' 子目录于 {temp_extract_dir}")
            shutil.rmtree(temp_extract_dir)
            return False

        print(f"正在移动 {extracted_root} 的内容到 {DEST_DIR}")
        for item_name in os.listdir(extracted_root):
            s = os.path.join(extracted_root, item_name)
            d = os.path.join(DEST_DIR, item_name)
            shutil.move(s, d)
        shutil.rmtree(temp_extract_dir)
    finally:
        if os.path.exists(tar_filepath):
            os.remove(tar_filepath)

    # macOS 需要为 bin/ 下的可执行文件设置执行权限
    if os_type == "macos":
        bin_dir = os.path.join(DEST_DIR, "bin")
        if os.path.isdir(bin_dir):
            print(f"正在为 {bin_dir} 中的文件设置执行权限...")
            for item_name in os.listdir(bin_dir):
                item_path = os.path.join(bin_dir, item_name)
                if os.path.isfile(item_path):
                    os.chmod(
                        item_path,
                        os.stat(item_path).st_mode
                        | stat.S_IXUSR
                        | stat.S_IXGRP
                        | stat.S_IXOTH,
                    )
    return True


def main() -> None:
    if len(sys.argv) < 3:
        print("Usage: python tools/ci/setup_embed_python.py <os> <arch>")
        print("Example: python tools/ci/setup_embed_python.py win x86_64")
        sys.exit(1)

    os_type = normalize_os(sys.argv[1])
    arch = normalize_arch(sys.argv[2])
    if os_type is None or arch is None:
        print(f"不支持的 os/arch: {sys.argv[1]} {sys.argv[2]}")
        sys.exit(1)

    print(f"目标: {os_type} / {arch}, Python {PYTHON_VERSION}")
    print(f"安装目录: {DEST_DIR}")

    if os_type == "linux":
        print("Linux 使用系统 python3，跳过嵌入式 Python 安装。")
        return

    python_exe = get_python_executable(os_type)
    if python_exe and os.path.exists(python_exe):
        print(f"Python 已存在于 {DEST_DIR} (找到: {python_exe})，跳过。")
        return

    if os.path.exists(DEST_DIR):
        shutil.rmtree(DEST_DIR)
    os.makedirs(DEST_DIR, exist_ok=True)

    if not setup(os_type, arch):
        sys.exit(1)

    python_exe = get_python_executable(os_type)
    if not python_exe or not os.path.exists(python_exe):
        print("错误: Python 可执行文件在安装后未找到。")
        sys.exit(1)

    # 交叉打包：不能在 ubuntu 上运行目标平台的 python，改用文件存在性校验 pip
    pip_dirs = glob.glob(
        os.path.join(DEST_DIR, "**", "site-packages", "pip"), recursive=True
    )
    if pip_dirs:
        print("嵌入式 Python 安装完成，pip 已包含。")
    else:
        print("警告: 未在提取产物中找到 pip 目录，请确认 build-standalone 产物包含 pip。")


if __name__ == "__main__":
    main()
