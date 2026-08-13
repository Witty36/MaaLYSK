"""
下载并配置嵌入式 Python 到 install/python/。
针对 MaaLYSK 的 ubuntu 交叉打包：接收 argv 传入的目标 os/arch（而非 platform.system()）。

用法: python tools/ci/setup_embed_python.py <os> <arch>
  os   : win | macos | linux
  arch : x86_64 | aarch64
"""

import os
import shutil
import stat
import subprocess
import sys
import tarfile
import urllib.request
import zipfile

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]

PYTHON_VERSION_TARGET = "3.12.10"
PYTHON_BUILD_STANDALONE_RELEASE_TAG = "20250409"

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


def extract_zip(zip_path: str, dest_dir: str) -> None:
    print(f"正在解压 ZIP: {zip_path} 到 {dest_dir}")
    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall(dest_dir)
    print("ZIP 解压完成。")


def extract_tar(tar_path: str, dest_dir: str) -> None:
    print(f"正在解压 TAR: {tar_path} 到 {dest_dir}")
    with tarfile.open(tar_path, "r:*") as tar_ref:
        tar_ref.extractall(path=dest_dir)
    print("TAR 解压完成。")


def get_python_executable_path(base_dir: str, os_type: str) -> str | None:
    if os_type == "win":
        return os.path.join(base_dir, "python.exe")
    if os_type == "macos":
        py3 = os.path.join(base_dir, "bin", "python3")
        py = os.path.join(base_dir, "bin", "python")
        return py3 if os.path.exists(py3) else (py if os.path.exists(py) else None)
    return None


def ensure_pip(python_executable: str, python_install_dir: str) -> bool:
    """为 python.org embeddable（Windows）安装 pip。"""
    if not python_executable or not os.path.exists(python_executable):
        print("错误: Python 可执行文件未找到，无法安装 pip。")
        return False

    get_pip_url = "https://bootstrap.pypa.io/get-pip.py"
    get_pip_script_path = os.path.join(python_install_dir, "get-pip.py")

    print(f"正在下载 get-pip.py 从 {get_pip_url}")
    download_file(get_pip_url, get_pip_script_path)

    print("正在使用 get-pip.py 安装 pip...")
    try:
        subprocess.run([python_executable, get_pip_script_path], check=True)
        print("pip 安装成功。")
        return True
    except (subprocess.CalledProcessError, OSError) as e:
        print(f"pip 安装失败: {e}")
        return False
    finally:
        if os.path.exists(get_pip_script_path):
            os.remove(get_pip_script_path)


def setup_windows(arch: str) -> bool:
    arch_mapping = {"x86_64": "amd64", "aarch64": "arm64"}
    win_arch = arch_mapping[arch]

    download_url = (
        f"https://www.python.org/ftp/python/{PYTHON_VERSION_TARGET}/"
        f"python-{PYTHON_VERSION_TARGET}-embed-{win_arch}.zip"
    )
    zip_filename = f"python-{PYTHON_VERSION_TARGET}-embed-{win_arch}.zip"
    zip_filepath = os.path.join(DEST_DIR, zip_filename)

    try:
        download_file(download_url, zip_filepath)
        extract_zip(zip_filepath, DEST_DIR)
    finally:
        if os.path.exists(zip_filepath):
            os.remove(zip_filepath)

    # 修改 ._pth 文件（python312._pth 等）
    version_nodots = PYTHON_VERSION_TARGET.replace(".", "")[:3]
    pth_file_path = os.path.join(DEST_DIR, f"python{version_nodots}._pth")
    if not os.path.exists(pth_file_path):
        found = [
            f
            for f in os.listdir(DEST_DIR)
            if f.startswith("python") and f.endswith("._pth")
        ]
        if not found:
            print(f"错误: 未在 {DEST_DIR} 中找到 ._pth 文件。")
            return False
        pth_file_path = os.path.join(DEST_DIR, found[0])

    print(f"正在修改 ._pth 文件: {pth_file_path}")
    with open(pth_file_path, "r+", encoding="utf-8") as f:
        content = f.read()
        # 取消注释 import site
        content = content.replace("#import site", "import site").replace(
            "# import site", "import site"
        )
        # 添加必要的相对路径 (相对于 DEST_DIR)
        required_paths = [".", "Lib", "Lib\\site-packages", "DLLs"]
        for p in required_paths:
            if p not in content.splitlines():
                content += f"\n{p}"
        f.seek(0)
        f.write(content)
        f.truncate()
    print("._pth 文件修改完成。")
    return True


def setup_macos(arch: str) -> bool:
    arch_mapping = {"x86_64": "x86_64", "aarch64": "aarch64"}
    pbs_arch = arch_mapping[arch]

    pbs_filename = (
        f"cpython-{PYTHON_VERSION_TARGET}+{PYTHON_BUILD_STANDALONE_RELEASE_TAG}-"
        f"{pbs_arch}-apple-darwin-install_only.tar.gz"
    )
    download_url = (
        "https://github.com/indygreg/python-build-standalone/releases/download/"
        f"{PYTHON_BUILD_STANDALONE_RELEASE_TAG}/{pbs_filename}"
    )
    tar_filepath = os.path.join(DEST_DIR, pbs_filename)
    temp_extract_dir = os.path.join(DEST_DIR, "_temp_extract")

    try:
        download_file(download_url, tar_filepath)
        os.makedirs(temp_extract_dir, exist_ok=True)
        extract_tar(tar_filepath, temp_extract_dir)

        extracted_python_root = os.path.join(temp_extract_dir, "python")
        if os.path.isdir(extracted_python_root):
            print(f"正在移动 {extracted_python_root} 的内容到 {DEST_DIR}")
            for item_name in os.listdir(extracted_python_root):
                s = os.path.join(extracted_python_root, item_name)
                d = os.path.join(DEST_DIR, item_name)
                shutil.move(s, d)
            shutil.rmtree(temp_extract_dir)
        else:
            print(f"错误: 解压后未找到预期的 'python' 子目录于 {temp_extract_dir}")
            shutil.rmtree(temp_extract_dir)
            return False
    finally:
        if os.path.exists(tar_filepath):
            os.remove(tar_filepath)

    # 为 bin 目录下的可执行文件设置执行权限
    bin_dir = os.path.join(DEST_DIR, "bin")
    if os.path.isdir(bin_dir):
        print(f"正在为 {bin_dir} 中的文件设置执行权限...")
        for item_name in os.listdir(bin_dir):
            item_path = os.path.join(bin_dir, item_name)
            if os.path.isfile(item_path) and not os.access(item_path, os.X_OK):
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

    print(f"目标: {os_type} / {arch}, Python {PYTHON_VERSION_TARGET}")
    print(f"安装目录: {DEST_DIR}")

    if os_type == "linux":
        print("Linux 使用系统 python3，跳过嵌入式 Python 安装。")
        return

    # 已存在则跳过
    python_exe_check = get_python_executable_path(DEST_DIR, os_type)
    if python_exe_check and os.path.exists(python_exe_check):
        print(f"Python 已存在于 {DEST_DIR} (找到: {python_exe_check})，跳过。")
        return

    if os.path.exists(DEST_DIR):
        shutil.rmtree(DEST_DIR)
    os.makedirs(DEST_DIR, exist_ok=True)

    if os_type == "win":
        ok = setup_windows(arch)
    elif os_type == "macos":
        ok = setup_macos(arch)
    else:
        ok = False

    if not ok:
        sys.exit(1)

    python_executable = get_python_executable_path(DEST_DIR, os_type)
    if not python_executable or not os.path.exists(python_executable):
        print("错误: Python 可执行文件在安装后未找到。")
        sys.exit(1)

    print(f"Python 环境已初步设置在: {DEST_DIR}")
    print(f"Python 可执行文件: {python_executable}")

    # 仅 python.org embeddable（Windows）需要手动装 pip；build-standalone 自带 pip
    if os_type == "win":
        if ensure_pip(python_executable, DEST_DIR):
            print("嵌入式 Python 环境安装和 pip 配置完成。")
        else:
            print("嵌入式 Python 环境安装完成，但 pip 配置失败。")
    else:
        print("嵌入式 Python 环境安装完成。")


if __name__ == "__main__":
    main()
