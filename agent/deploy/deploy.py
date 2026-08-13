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


def load_requirements_from_file() -> list[str]:
    """从 requirements.txt 读取依赖列表（必须存在）。"""
    main_py_path = get_main_py_path()
    requirements_path = main_py_path.parent.parent / "requirements.txt"

    if not requirements_path.exists():
        raise FileNotFoundError(f"无法找到 requirements.txt 文件: {requirements_path}")

    packages: list[str] = []
    with open(requirements_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            # 跳过空行和注释
            if not line or line.startswith("#"):
                continue
            packages.append(line)

    if not packages:
        raise ValueError("requirements.txt 文件中没有找到任何依赖包")

    return packages


def install_package_with_fallback(package_spec: str) -> bool:
    """
    尝试使用多个源安装包，按顺序回退
    1. 阿里源
    2. 清华源
    3. PyPI 官方源
    """
    sources = [
        ("阿里源", "https://mirrors.aliyun.com/pypi/simple/"),
        ("清华源", "https://pypi.tuna.tsinghua.edu.cn/simple"),
        ("PyPI官方源", "https://pypi.org/simple"),
    ]

    for source_name, source_url in sources:
        try:
            logger.info(f"尝试使用 {source_name} 安装 {package_spec}...")
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "pip",
                    "install",
                    "--upgrade",
                    "-i",
                    source_url,
                    package_spec,
                ],
                capture_output=True,
                text=True,
                check=True,
            )
            logger.info(f"✓ {package_spec} 安装成功 (使用 {source_name})")
            if result.stdout:
                logger.debug(f"pip 输出: {result.stdout}")
                print(f"info: {result.stdout}")
            return True
        except subprocess.CalledProcessError as e:
            logger.warning(
                f"使用 {source_name} 安装 {package_spec} 失败，尝试下一个源..."
            )
            print(
                f"error: 使用 {source_name} 安装 {package_spec} 失败，尝试下一个源..."
            )
            if e.stderr:
                logger.debug(f"  错误输出: {e.stderr}")
            if e.stdout:
                logger.debug(f"  标准输出: {e.stdout}")

    logger.error(f"✗ {package_spec} 安装失败（所有源都尝试失败）")
    return False


def check_and_install_dependencies() -> bool:
    """检查并安装必要的依赖库。"""
    print("info: 开始安装依赖")
    required_packages = load_requirements_from_file()
    if not required_packages:
        raise ValueError("requirements.txt 中没有找到任何依赖包")

    all_installed = True

    for package_spec in required_packages:
        logger.info(f"正在安装 {package_spec}...")
        print(f"info: 正在安装 {package_spec}...")
        if not install_package_with_fallback(package_spec):
            all_installed = False

    return all_installed


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
        success = check_and_install_dependencies()

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
