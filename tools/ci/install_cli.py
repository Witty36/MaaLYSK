from pathlib import Path

import shutil
import sys
import re

try:
    import jsonc
except ModuleNotFoundError as e:
    raise ImportError(
        "Missing dependency 'json-with-comments' (imported as 'jsonc').\n"
        f"Install it with:\n  {sys.executable} -m pip install json-with-comments\n"
        "Or add it to your project's requirements."
    ) from e

ci_dir = Path(__file__).parent.resolve()
sys.path.insert(0, str(ci_dir))

from configure import configure_ocr_model

working_dir = Path(__file__).parent.parent.parent.resolve()
install_path = working_dir / Path("install-cli")
version = len(sys.argv) > 1 and sys.argv[1] or "v0.0.1"
os_name = len(sys.argv) > 2 and sys.argv[2] or ""


def strip_html_tags(text: str) -> str:
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", "", text)
    return text


def strip_html_from_interface(obj):
    if isinstance(obj, dict):
        for key, value in obj.items():
            if key == "description" and isinstance(value, str):
                obj[key] = strip_html_tags(value)
            elif isinstance(value, (dict, list)):
                strip_html_from_interface(value)
    elif isinstance(obj, list):
        for item in obj:
            if isinstance(item, (dict, list)):
                strip_html_from_interface(item)


def install_deps():
    if not (working_dir / "deps" / "bin").exists():
        print('Please download the MaaFramework to "deps" first.')
        print('请先下载 MaaFramework 到 "deps"。')
        sys.exit(1)

    shutil.copytree(
        working_dir / "deps" / "bin",
        install_path,
        ignore=shutil.ignore_patterns(
            "*MaaDbgControlUnit*",
            "*MaaThriftControlUnit*",
            "*MaaRpc*",
            "*MaaHttp*",
        ),
        dirs_exist_ok=True,
    )

    shutil.copytree(
        working_dir / "deps" / "share" / "MaaAgentBinary",
        install_path / "MaaAgentBinary",
        dirs_exist_ok=True,
    )


def install_resource():

    configure_ocr_model()

    shutil.copytree(
        working_dir / "assets" / "resource",
        install_path / "resource",
        dirs_exist_ok=True,
    )
    shutil.copy2(
        working_dir / "assets" / "interface.json",
        install_path,
    )

    with open(install_path / "interface.json", "r", encoding="utf-8") as f:
        interface = jsonc.load(f)

    interface["version"] = version
    interface["title"] = f"MaaLYSK | 恋与深空日常/肝活小助手 {version}"

    strip_html_from_interface(interface)

    with open(install_path / "interface.json", "w", encoding="utf-8") as f:
        jsonc.dump(interface, f, ensure_ascii=False, indent=4)

    tasks_dir = install_path / "resource" / "tasks"
    for json_file in tasks_dir.rglob("*.json"):
        with open(json_file, "r", encoding="utf-8") as f:
            data = jsonc.load(f)
        strip_html_from_interface(data)
        with open(json_file, "w", encoding="utf-8") as f:
            jsonc.dump(data, f, ensure_ascii=False, indent=4)


def install_chores():
    shutil.copy2(working_dir / "README.md", install_path)
    shutil.copy2(working_dir / "LICENSE", install_path)
    shutil.copy2(working_dir / "requirements.txt", install_path)


def install_agent():
    shutil.copytree(
        working_dir / "agent",
        install_path / "agent",
        dirs_exist_ok=True,
    )

    with open(install_path / "interface.json", "r", encoding="utf-8") as f:
        interface = jsonc.load(f)

    if os_name == "win":
        interface["agent"]["child_exec"] = "./python/python.exe"
    elif os_name == "macos":
        interface["agent"]["child_exec"] = "./python/bin/python3"
    elif os_name == "linux":
        interface["agent"]["child_exec"] = "python3"

    interface["agent"]["child_args"] = ["-u", "./agent/main.py"]

    with open(install_path / "interface.json", "w", encoding="utf-8") as f:
        jsonc.dump(interface, f, ensure_ascii=False, indent=4)


if __name__ == "__main__":
    install_deps()
    install_resource()
    install_chores()
    install_agent()

    print(f"Install PiCLI to {install_path} successfully.")
