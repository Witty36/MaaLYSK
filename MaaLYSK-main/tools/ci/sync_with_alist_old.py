import os
import re
import requests
import sys
import time
from datetime import datetime

# 创建一个带 ngrok 跳过头的会话
session = requests.Session()
session.headers.update({"ngrok-skip-browser-warning": "true"})

# 从环境变量中获取 Alist 的配置
ALIST_URL = os.getenv("ALIST_URL")
ALIST_USERNAME = os.getenv("ALIST_USERNAME")
ALIST_PASSWORD = os.getenv("ALIST_PASSWORD")

# 【优化】确保 URL 末尾没有斜杠
if ALIST_URL:
    ALIST_URL = ALIST_URL.rstrip("/")

# ---- 配置 ----
SOURCE_DIR = "/Github"  # Alist 中挂载 GitHub Release 的路径
MAX_RETRIES = 5  # 刷新缓存后的最大重试次数
RETRY_DELAY = 30  # 每次重试的间隔时间（秒）

# 定义你的分发规则
# 规则格式：( (一个包含所有关键词的元组), [一个或多个目标目录的列表] )
# 脚本会为每个匹配的文件，将其复制到列表中的所有目标目录
DISTRIBUTION_RULES = [
    # 稳定版 - macOS
    (
        ("macos",),
        ["/apps/MaaLYSK/正式版/Mac系统/"],
    ),
    # 稳定版 - Windows
    (
        ("win",),
        ["/apps/MaaLYSK/正式版/Win系统/"],
    ),
    # 公测版 - macOS
    (
        ("beta", "macos"),
        ["/apps/MaaLYSK/公测版/Mac系统/"],
    ),
    # 公测版 - Windows
    (
        ("beta", "win"),
        ["/apps/MaaLYSK/公测版/Win系统/"],
    ),
]

# ---- 脚本核心逻辑 ----


def login():
    """登录 Alist 并返回认证 token"""
    login_url = f"{ALIST_URL}/api/auth/login"
    payload = {"username": ALIST_USERNAME, "password": ALIST_PASSWORD}
    try:
        resp = requests.post(login_url, json=payload, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        if data.get("code") == 200 and data.get("data", {}).get("token"):
            print("✓ Alist 登录成功")
            return data["data"]["token"]
        else:
            print(f"✗ Alist 登录失败: {data.get('message')}")
            sys.exit(1)
    except requests.exceptions.RequestException as e:
        print(f"✗ 请求 Alist 登录接口时发生错误: {e}")
        sys.exit(1)


def get_storage_id(token, path):
    """根据挂载路径获取存储 ID"""
    list_url = f"{ALIST_URL}/api/admin/storage/list"
    headers = {"Authorization": token, "ngrok-skip-browser-warning": "true"}
    try:
        resp = requests.get(list_url, headers=headers, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        if data.get("code") == 200:
            for storage in data.get("data", {}).get("content", []):
                if storage.get("mount_path") == path:
                    print(f"  ✓ 找到 '{path}' 的存储 ID: {storage.get('id')}")
                    return storage.get("id")
            print(f"  ✗ 未找到挂载路径为 '{path}' 的存储。")
            return None
        else:
            print(f"  ✗ 获取存储列表失败: {data.get('message')}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"  ✗ 请求 Alist 存储列表接口时发生错误: {e}")
        return None


def get_storage_detail(token, storage_id):
    """pull the current config"""
    detail_url = f"{ALIST_URL}/api/admin/storage/get"
    headers = {"Authorization": token, "ngrok-skip-browser-warning": "true"}
    try:
        resp = requests.get(
            detail_url, headers=headers, params={"id": storage_id}, timeout=15
        )
        resp.raise_for_status()
        data = resp.json()
        if data.get("code") == 200 and data.get("data"):
            return data["data"]
        else:
            print(f"  ✗ 无法获取存储配置: {data.get('message')}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"  ✗ 获取存储配置时发生错误: {e}")
        return None


def refresh_storage(token, storage_id):
    """Refresh storage by re-saving it through update API"""
    if not storage_id:
        return

    detail = get_storage_detail(token, storage_id)
    if not detail:
        return

    update_url = f"{ALIST_URL}/api/admin/storage/update"
    headers = {"Authorization": token, "ngrok-skip-browser-warning": "true"}
    fields = [
        "mount_path",
        "order",
        "driver",
        "remark",
        "cache_expiration",
        "status",
        "web_proxy",
        "webdav_policy",
        "down_proxy_url",
        "order_by",
        "extract_folder",
        "order_direction",
        "addition",
        "enable_sign",
    ]
    payload = {"id": storage_id}
    for field in fields:
        payload[field] = detail.get(field)

    try:
        print(f"  > 正在更新存储 ID: {storage_id} ...")
        resp = requests.post(update_url, headers=headers, json=payload, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        if data.get("code") == 200:
            print("  ✓ 存储已刷新")
        else:
            print(f"  ✗ 刷新存储失败: {data.get('message')}")
    except requests.exceptions.RequestException as e:
        print(f"  ✗ 刷新存储时发生错误: {e}")


def list_files(token, path):
    """获取指定路径下的文件列表"""
    list_url = f"{ALIST_URL}/api/fs/list"
    headers = {"Authorization": token}
    payload = {"path": path, "page": 1, "per_page": 0}
    print(f"  [DEBUG] 请求文件列表: {path}")
    try:
        resp = session.post(list_url, headers=headers, json=payload, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        if data.get("code") == 200:
            content = data.get("data", {}).get("content", [])
            print(f"  [DEBUG] 找到 {len(content)} 个项目")
            return content
        else:
            print(f"✗ 获取文件列表失败: {data.get('message')}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"✗ 请求 Alist 文件列表接口时发生错误: {e}")
        return None


def create_dir(token, path):
    """在 Alist 中创建目录"""
    create_dir_url = f"{ALIST_URL}/api/fs/mkdir"
    headers = {"Authorization": token, "ngrok-skip-browser-warning": "true"}
    payload = {"path": path}
    try:
        resp = requests.post(create_dir_url, headers=headers, json=payload, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        if data.get("code") == 200:
            print(f"  ✓ 成功创建目录: {path}")
            return True
        elif "exist" in data.get("message", ""):
            return True
        else:
            print(f"  ✗ 创建目录失败: {data.get('message')}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"  ✗ 请求 Alist 创建目录接口时发生错误: {e}")
        return False


def copy_file(token, src_dir, dest_dir, filename):
    """在 Alist 内部复制单个文件"""
    copy_url = f"{ALIST_URL}/api/fs/copy"
    headers = {"Authorization": token, "ngrok-skip-browser-warning": "true"}
    payload = {"src_dir": src_dir, "dst_dir": dest_dir, "names": [filename]}
    print(f"  > 正在复制 '{src_dir}/{filename}' 到 '{dest_dir}' ...")
    try:
        resp = requests.post(copy_url, headers=headers, json=payload, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        if data.get("code") == 200:
            print(f"  ✓ 复制成功")
        elif "exist" in data.get("message", ""):
            print(f"  ✓ 目标文件已存在，视为成功。")
        else:
            print(f"  ✗ 复制失败: {data.get('message')}")
    except requests.exceptions.RequestException as e:
        print(f"  ✗ 请求 Alist 复制接口时发生错误: {e}")


def extract_version(filename):
    """从文件名中提取版本号"""
    match = re.search(r"(v\d+\.\d+\.\d+.*?)(?=\.zip|\.tar\.gz)", filename)
    return match.group(1) if match else None


def safe_folder_name(name: str) -> str:
    """将文件夹名中的空格替换为空格（保持原样），只移除不安全字符"""
    # 允许的字符：字母、数字、空格、点、短横线、括号
    # 将其他特殊字符替换为空格
    cleaned = re.sub(r"[^\w\s.\-\(\)]", " ", name)
    # 移除多余空格
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


def get_latest_release_tag():
    """从环境变量中获取最新的 Release 标签名"""
    # 优先使用 workflow 中显式传入的 DISTRIBUTE_TAG（避免与 runner 的 GITHUB_REF_NAME 冲突）
    tag = os.getenv("DISTRIBUTE_TAG") or os.getenv("GITHUB_REF_NAME")
    if not tag:
        print(
            "! 警告: 无法从环境变量 DISTRIBUTE_TAG 或 GITHUB_REF_NAME 中获取 Release 标签。"
        )
        print("! 将尝试分发源目录中的所有文件。")
    return tag


def main():
    if not all([ALIST_URL, ALIST_USERNAME, ALIST_PASSWORD]):
        print("✗ 必需的环境变量 ALIST_URL, ALIST_USERNAME, ALIST_PASSWORD 未设置")
        sys.exit(1)

    token = login()

    print("\n--- 准备分发环境 ---")
    storage_id = get_storage_id(token, SOURCE_DIR)
    if storage_id:
        refresh_storage(token, storage_id)
    else:
        print("! 无法刷新存储，将继续尝试...")

    latest_tag = get_latest_release_tag()
    files_to_process = []

    # 获取 Release 的发布日期（需要在获取文件列表前获取）
    release_published_at = None
    if latest_tag:
        # 从 GitHub API 获取 Release 信息
        github_api_url = (
            f"https://api.github.com/repos/Witty36/MaaLYSK/releases/tags/{latest_tag}"
        )
        try:
            import urllib.request
            import json

            with urllib.request.urlopen(github_api_url) as response:
                release_data = json.loads(response.read().decode())
                release_published_at = release_data.get("published_at", "")
                if release_published_at:
                    # 格式化为 yyyy-MM-dd
                    release_date = release_published_at.split("T")[0]
                    print(f"✓ Release 发布日期: {release_date}")
        except Exception as e:
            print(f"! 获取 Release 发布日期失败: {e}，将使用当前日期")

    for i in range(MAX_RETRIES):
        print(f"\n--- 正在获取文件列表 (尝试 {i+1}/{MAX_RETRIES}) ---")
        all_files = list_files(token, SOURCE_DIR)

        if all_files is None:
            sys.exit(1)

        if latest_tag:
            # 打印 all_files 内容用于调试
            print(f"  [DEBUG] all_files 中的项目: {[f.get('name') for f in all_files]}")

            # 找到版本文件夹
            version_folder = None
            for f in all_files:
                print(f"  [DEBUG] 检查: {f.get('name')}, is_dir: {f.get('is_dir')}")
                if f.get("is_dir") and latest_tag in f.get("name", ""):
                    version_folder = f.get("name")
                    break

            if version_folder:
                print(f"✓ 找到版本文件夹: {version_folder}")
                folder_path = f"{SOURCE_DIR}/{version_folder}"
                print(f"  正在获取 {folder_path} 中的文件列表...")
                files_to_process = list_files(token, folder_path)
                if files_to_process:
                    print(
                        f"✓ 找到 {len(files_to_process)} 个文件: {[f['name'] for f in files_to_process]}"
                    )
                    break
                else:
                    print(f"! 版本文件夹 '{version_folder}' 中没有找到文件")
            else:
                print(f"! 未找到包含标签 '{latest_tag}' 的版本文件夹")
        else:
            files_to_process = all_files
            break

        if i < MAX_RETRIES - 1:
            print(f"  > 等待 {RETRY_DELAY} 秒后重试...")
            time.sleep(RETRY_DELAY)

    if not files_to_process:
        print("\n! 最终未能找到任何需要分发的文件，脚本结束。")
        return

    print("\n--- 开始处理文件分发 ---")
    for file_info in files_to_process:
        if file_info.get("is_dir"):
            continue

        filename = file_info["name"]
        filename_lower = filename.lower()

        print(f"\n处理文件: {filename}")

        # 规则 1: 排除 win-aarch
        if "win-aarch" in filename_lower:
            print("  - 满足排除规则，跳过。")
            continue

        version = extract_version(filename)
        if not version:
            print("  - 无法从文件名中提取版本号，跳过。")
            continue

        # 使用 Release 的实际发布日期，如果没有则用当前日期
        if release_published_at:
            date_str = release_published_at.split("T")[0]  # 取 yyyy-MM-dd 部分
        else:
            date_str = datetime.now().strftime("%Y-%m-%d")

        new_folder_name = safe_folder_name(f"{version} (发布于{date_str})")
        print(
            f"  - 版本: {version}, 发布日期: {date_str}, 目标文件夹: {new_folder_name}"
        )

        matched = False
        for keywords, dest_paths in DISTRIBUTION_RULES:
            if all(keyword.lower() in filename_lower for keyword in keywords):
                is_stable_rule = "beta" not in [k.lower() for k in keywords]
                if is_stable_rule and "beta" in filename_lower:
                    continue

                print(f"  * 匹配规则: {keywords}, 将分发到 {len(dest_paths)} 个位置。")

                for base_path in dest_paths:
                    versioned_dest_path = f"{base_path.rstrip('/')}/{new_folder_name}"

                    if create_dir(token, versioned_dest_path):
                        # 源路径：版本文件夹路径
                        src_dir = f"{SOURCE_DIR}/{latest_tag}"
                        copy_file(token, src_dir, versioned_dest_path, filename)
                    else:
                        print(
                            f"  ✗ 未能创建目标目录 {versioned_dest_path}，跳过此目标的上传。"
                        )

                matched = True
                break

        if not matched:
            print("  - 未匹配到任何分发规则，跳过。")

    print("\n--- 所有文件处理完毕 ---")


if __name__ == "__main__":
    main()
