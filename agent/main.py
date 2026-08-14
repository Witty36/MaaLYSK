import os
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")  # pyright: ignore[reportAttributeAccessIssue]
except AttributeError:
    pass

current_file_path = os.path.abspath(__file__)
agent_dir = os.path.dirname(current_file_path)
project_root_dir = os.path.dirname(agent_dir)

if os.getcwd() != project_root_dir:
    os.chdir(project_root_dir)

if agent_dir not in sys.path:
    sys.path.insert(0, agent_dir)

from deploy.deploy import deploy  # noqa: E402


def _is_android_runtime() -> bool:
    """Return whether the Agent is running inside MFA's Android P4A service."""
    return bool(
        sys.platform == "android"
        or os.environ.get("ANDROID_ARGUMENT")
        or os.environ.get("MAA_LIBRARY_DIR")
    )


def _configure_android_native_binding() -> None:
    """Point Maa's pure-Python binding at the APK's matching native libraries."""
    android_native_dir = os.environ.get("MAA_LIBRARY_DIR")
    if android_native_dir:
        os.environ.setdefault("MAAFW_BINARY_PATH", android_native_dir)


def run_agent() -> int:
    from maa.agent.agent_server import AgentServer
    from maa.toolkit import Toolkit

    import custom

    custom.register_all()
    Toolkit.init_option("./")

    socket_id = sys.argv[-1]
    print(f"socket_id: {socket_id}")

    AgentServer.start_up(socket_id)
    AgentServer.join()
    AgentServer.shut_down()
    return 0


def main() -> int:
    _configure_android_native_binding()

    # Android payload 已内置 Python runtime 与依赖，跳过桌面的部署 / 联网 pip 检查。
    if not _is_android_runtime():
        # 源码/测试模式（存在 .git）跳过部署检查
        if not (Path(project_root_dir) / ".git").exists():
            if not deploy():
                print("error: 部署检查失败，程序退出", file=sys.stderr)
                return 1

    return run_agent()


if __name__ == "__main__":
    sys.exit(main())
