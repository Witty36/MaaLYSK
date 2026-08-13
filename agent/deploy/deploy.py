"""
部署前检查和依赖安装模块
在运行 main 之前检查并安装必要的 Python 库
"""

import io
import json
import logging
import subprocess
import sys
import traceback
from pathlib import Path

# 强制 stdout/stderr 使用 UTF-8，避免 Windows cp1252 下中文日志/print 报 UnicodeEncodeError
if hasattr(sys.stdout, "buffer") and getattr(
    sys.stdout, "encoding", ""
).lower() not in ("utf-8", "utf8"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "buffer") and getattr(
    sys.stderr, "encoding", ""
).lower() not in ("utf-8", "utf8"):
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")


def setup_logger():
    """配置日志系统，同时输出到控制台和 debug/deploy.log。"""
    # __file__ = ./agent/deploy/deploy.py
    # parent = ./agent/deploy/
    # parent.parent = ./agent/
    # parent.parent.parent = ./
    log_dir = Path(__file__).parent.parent.parent / "debug"
    log_file = log_dir / "deploy.log"

    logger = logging.getLogger("deploy")
    logger.setLevel(logging.INFO)

    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )

    log_dir.mkdir(parents=True, exist_ok=True)
    file_handler = logging.FileHandler(log_file, mode="a", encoding="utf-8")
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


logger = setup_logger()


def get_main_py_path() -> Path:
    """获取 main.py 的路径（作为基准路径）。"""
    current_file = Path(__file__).resolve()
    # 当前文件在 agent/deploy/deploy.py，main.py 在 agent/main.py，即 ../main.py
    return current_file.parent.parent / "main.py"


def get_interface_version() -> str:
    """从 interface.json 中读取版本号。"""
    main_py_path = get_main_py_path()
    interface_path = main_py_path.parent.parent / "interface.json"

    if not interface_path.exists():
        raise FileNotFoundError(f"无法找到 interface.json 文件: {interface_path}")

    with open(interface_path, "r", encoding="utf-8") as f:
        interface_data = json.load(f)

    version = interface_data.get("version")
    if version is None:
        raise ValueError("interface.json 中未找到 version 字段")

    return str(version)


def get_saved_version() -> str | None:
    """读取已保存的版本号。"""
    version_file = Path(__file__).parent / ".version"

    if not version_file.exists():
        return None

    try:
        with open(version_file, "r", encoding="utf-8") as f:
            return f.read().strip()
    except Exception as e:
        logger.warning(f"读取版本文件失败: {e}")
        return None


def save_version(version: str) -> None:
    """保存版本号到文件。"""
    version_file = Path(__file__).parent / ".version"

    try:
        with open(version_file, "w", encoding="utf-8") as f:
            f.write(version)
    except Exception as e:
        logger.warning(f"保存版本文件失败: {e}")


PIP_MIRRORS = [
    "https://mirrors.ustc.edu.cn/pypi/simple",
    "https://pypi.tuna.tsinghua.edu.cn/simple",
    "https://mirrors.cloud.tencent.com/pypi/simple/",
    "https://pypi.org/simple",
]


def get_available_mirror(mirrors: list[str]) -> str | None:
    """逐个探测镜像源，返回第一个可用的。"""
    for mirror in mirrors:
        try:
            subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "pip",
                    "list",
                    "--local",
                    "--format=json",
                    "-i",
                    mirror,
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=10,
                check=True,
            )
            logger.info(f"当前镜像源可用: {mirror}")
            return mirror
        except subprocess.TimeoutExpired:
            logger.warning(f"镜像源连接超时: {mirror}")
        except subprocess.CalledProcessError:
            logger.warning(f"镜像源返回错误: {mirror}")
        except Exception as e:
            logger.warning(f"检查镜像源 {mirror} 时发生未知错误: {e}")

    logger.error("所有镜像源都不可用")
    return None


def _run_pip_command(cmd_args: list[str], operation_name: str) -> bool:
    """执行 pip 命令；成功只记一行，失败打印完整错误。"""
    logger.info(f"开始 {operation_name}...")
    try:
        process = subprocess.Popen(
            cmd_args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        stdout, stderr = process.communicate()
    except Exception as e:
        logger.error(f"{operation_name} 时发生未知异常: {e}")
        return False

    if process.returncode == 0:
        logger.info(f"{operation_name} 完成")
        return True

    logger.error(f"{operation_name} 时出错。返回码: {process.returncode}")
    if stdout and stdout.strip():
        print(f"info: {stdout.strip()}")
    if stderr and stderr.strip():
        print(f"error: {stderr.strip()}")
    return False


def install_requirements(mirrors: list[str]) -> bool:
    """一次性安装 requirements.txt 中所有依赖。"""
    main_py_path = get_main_py_path()
    requirements_path = main_py_path.parent.parent / "requirements.txt"

    if not requirements_path.exists():
        logger.error(f"requirements.txt 文件不存在于 {requirements_path.resolve()}")
        return False

    mirror = get_available_mirror(mirrors)
    if not mirror:
        logger.error("没有可用的镜像源，安装依赖失败")
        return False

    cmd = [
        sys.executable,
        "-m",
        "pip",
        "install",
        "-U",
        "-r",
        str(requirements_path),
        "--no-warn-script-location",
        "-i",
        mirror,
    ]
    return _run_pip_command(cmd, f"从 {requirements_path.name} 安装依赖")


def deploy() -> bool:
    """主部署检查函数。"""
    logger.info("=" * 50)
    logger.info("开始部署前检查...")
    logger.info("=" * 50)
    print("info: 开始部署检查")

    try:
        # 读取当前版本
        current_version = get_interface_version()
        logger.info(f"当前 interface_version: {current_version}")

        # 读取已保存的版本
        saved_version = get_saved_version()

        if saved_version == current_version:
            logger.info(f"版本一致 (v{saved_version})，跳过依赖检查")
            logger.info("=" * 50)
            print("info: 版本一致，跳过依赖检查")
            return True

        if saved_version:
            logger.info(f"版本已更新: {saved_version} -> {current_version}")
        else:
            logger.info("首次运行，开始依赖检查...")

        # 检查并安装依赖
        success = install_requirements(PIP_MIRRORS)

        if success:
            save_version(current_version)
            logger.info(f"✓ 依赖检查完成，版本已更新为: {current_version}")
        else:
            logger.error("✗ 依赖安装失败，请手动安装后重试")

        logger.info("=" * 50)
        return success

    except Exception as e:
        logger.error(f"✗ 部署检查过程中发生错误: {e}")
        logger.error(traceback.format_exc())
        return False


if __name__ == "__main__":
    sys.exit(0 if deploy() else 1)
