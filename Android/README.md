# Android 客户端（MaaFwApp）

安卓外壳使用 [Aliothmoon/MaaFwApp](https://github.com/Aliothmoon/MaaFwApp)。
MaaLYSK 的 `assets/interface.json` 不在仓库根，`agent/` 也不在 `assets/` 下，
所以构建前先用 `Android/prepare.py` 组装出一个完整的 PI payload，再交给 MaaFwApp 打包。

```text
Android/
├── profile.yaml                 # MaaFwApp 打包配方
├── prepare.py                   # 组装 .build/payload（interface/resource/agent/...）
├── verify_apk.py                # 出包后的结构与签名校验
├── patches/
│   └── maafwapp-maalysk.patch   # 竖屏 + BUILD_VERSION_CODE 适配
├── tests/test_prepare.py
└── .build/                      # 生成物，已 gitignore
    ├── payload/                 # PI 根目录
    └── agent-dist/              # build_agent_bundle.py 的输出
```

## 为什么需要补丁

MaaLYSK 的流水线是 **720×1280 竖屏**（全屏模板就是 720×1280，ROI 最大到 y≈1145）。
MaaFwApp 上游在构建期强制 `display.presets` 横屏，且内置档位是 1280×720 / 1920×1080。
[`patches/maafwapp-maalysk.patch`](patches/maafwapp-maalysk.patch) 基于锁定提交
`f29a0b0d5e5ebdc845368f0e98e8104911765c1a` 做四件事：

1. 允许 profile 声明竖屏 preset（只挡掉正方形）
2. 虚拟屏默认尺寸改成 720×1280
3. 全屏预览只在横屏画面时强制横屏
4. 支持 `BUILD_VERSION_CODE` 环境变量覆盖 versionCode

`profile.yaml` 同时声明竖屏和横屏档位，第一项是默认的 720P 竖屏。MaaFwApp 不支持按任务
自动旋转；横屏任务在 App 的「设置 - 分辨率」里手动切换档位，虚拟屏会在下一次运行前重建。
前台模式已关闭：它按手机物理分辨率截图且不缩放，和 720×1280 流水线对不上。

## 本地构建

需要 JDK 17、Android SDK（platform 37、build-tools 36.0.0、NDK 29、CMake 3.22.1）、Python 3.13。

```bash
# 1. 准备 MaaFwApp（任意 checkout 都可以，下面用 <MaaFwApp> 表示）
git clone https://github.com/Aliothmoon/MaaFwApp.git <MaaFwApp>
git -C <MaaFwApp> checkout f29a0b0d5e5ebdc845368f0e98e8104911765c1a

# 2. 应用竖屏/版本号补丁
git -C <MaaFwApp> apply --check "$PWD/Android/patches/maafwapp-maalysk.patch"
git -C <MaaFwApp> apply "$PWD/Android/patches/maafwapp-maalysk.patch"

# 3. OCR 模型（MaaCommonAssets 子模块，不进 git）
python tools/ci/configure.py

# 4. 组装 payload
python Android/prepare.py --version v0.4.6-beta1 \
    --version-code 10201 \
    --maafw-version 5.13.1 \
    --agent-core-tag 3.13.15-maafw5.13.1 \
    --abi arm64-v8a \
    --shell-source <MaaFwApp>

# 5. Python agent 运行时（内核 tag 与 requirements.txt 的 maafw==X 对齐）
python <MaaFwApp>/scripts/build_agent_bundle.py \
    --out Android/.build/agent-dist \
    --abi arm64-v8a \
    --core-tag 3.13.15-maafw5.13.1 \
    --requirements requirements.txt

# 6. MaaFramework 原生库（版本与 requirements.txt 的 maafw==X 对齐）
#    脚本通过 GitHub API 查 release，匿名请求容易 403；本地建议带 GITHUB_TOKEN
GITHUB_TOKEN=<token> python <MaaFwApp>/scripts/setup_maa_framework.py --tag v5.13.1 --abi arm64-v8a

# 7. local.properties（不进 git；pi.profile 也可以用 PI_PROFILE 环境变量）
cat > <MaaFwApp>/local.properties <<EOF
sdk.dir=/path/to/Android/Sdk
build.debugAbi=arm64-v8a
build.releaseAbi=arm64-v8a
EOF

# 8. 出包
cd <MaaFwApp>
PI_PROFILE="<MaaLYSK>/Android/profile.yaml" \
BUILD_VERSION_NAME=v0.4.6-beta1 \
BUILD_VERSION_CODE=10201 \
./gradlew :app:assembleDebug
```

APK 在 `<MaaFwApp>/app/build/outputs/apk/debug/app-debug.apk`（release 为
`.../apk/release/app-release.apk`）。出 x86_64 包时：第 4/5/6 步的 `--abi` 换成
`x86_64`，`--agent-core-tag` 不变，`local.properties` 里两个 ABI 也换成 `x86_64`。

本地想同时保留正式包和测试包时，在第 8 步额外给预览身份：

```bash
MAALYSK_APP_ID=maalysk.ci MAALYSK_APP_LABEL="MaaLYSK · CI" ...
```

包名会变成 `com.aliothmoon.maafw.maalysk.ci`，和正式包互不覆盖。

## CI

[`.github/workflows/android.yml`](../.github/workflows/android.yml)：

- 触发：`workflow_dispatch`（手动，默认 debug）和 `repository_dispatch[android-release]`
  （`install.yml` 建完 Release 后派发，payload 里带 tag）
- 矩阵：`arm64-v8a` → 资产名 `MaaLYSK-android-arm64-<version>.apk`；
  `x86_64` → `MaaLYSK-android-x64-<version>.apk`
- 发版：versionName / PI version 都取 tag（含 `v`），versionCode =
  `github.run_number * 100 + github.run_attempt`；构建成功后 `gh release upload` 到同一个 Release
- 手动：version 取 `ci.<run>-<sha>`，只上传 Actions artifact

签名 secrets（发版必需；手动 debug 包不需要）：

| Secret | 内容 |
| --- | --- |
| `KEYSTORE_BASE64` | release keystore 的 Base64 内容 |
| `KEYSTORE_PASSWORD` | keystore 密码 |
| `KEY_ALIAS` | 密钥别名 |
| `KEY_PASSWORD` | 密钥密码 |

可选仓库变量 `ANDROID_SIGNING_CERT_SHA256`：设置后校验 APK 签名证书指纹。
tag 发版缺签名材料会直接失败——未签名 APK 装不上。

### 内核解析

`Resolve versions` 步骤会用 [resolve_versions.py](resolve_versions.py) 解析 MaaFW / 内核配对：

- 从 `requirements.txt` 读 `maafw==X`
- 从 MaaFwApp 的 `scripts/build_agent_bundle.py` 读 `CORE_PY`（当前 `3.13.15`）
- 在 `MaaAgentCoreAndroid` 里找 `<CORE_PY>-maafwX`
- 精确配对优先；内核还没发 `X` 时自动退到“不高于 X 的最近配对”，打 warning
- 固定版本比内核全部配对都旧时直接失败，并列出现有配对

应急时可以在手动 dispatch 里填 `agent_core_tag`，或配置仓库变量 `AGENT_CORE_TAG`。
覆盖后 client 原生库会跟着内核走，和 `requirements.txt` 的固定版本可能不同，构建日志会打 warning。

### 预览包身份

非发版构建（手动 debug / 分支 CI）使用独立身份：

| | 正式包 | 预览包 |
| --- | --- | --- |
| 包名 | `com.aliothmoon.maafw.maalysk` | `com.aliothmoon.maafw.maalysk.ci` |
| 名称 | `MaaLYSK` | `MaaLYSK · CI` |
| 签名 | release keystore | debug keystore |

所以测试包和正式包可以同时安装，不会互相覆盖。实现上 profile 的 `app.id` / `app.label` 用了
`${MAALYSK_APP_ID:-maalysk}` / `${MAALYSK_APP_LABEL:-MaaLYSK}`，CI 按构建类型注入。

## 包名与升级

MaaFwApp 的包名固定为 `com.aliothmoon.maafw.` + `app.id`，本配方是
`com.aliothmoon.maafw.maalysk`，与旧 MFAAvalonia 安卓版的 `io.github.witty36.maalysk`
不同。首次切换需要卸载旧 App；两者可以并存，但应用内更新只认新包。
CI 预览包是 `com.aliothmoon.maafw.maalysk.ci`，可以和正式包同时安装。

应用内更新走 PI 的 `github` 字段（GitHub Releases），并按资产名里的 ABI 标记选包；
Android 目前没有 MirrorChyan 渠道，所以配方里没有 `update.mirrorchyanRid`。

## 更新 MaaFwApp

1. 改 CI 里的 `SHELL_REF`（和本文档的锁定提交）
2. 在 `f29a0b0` 的基础上重新生成 `patches/maafwapp-maalysk.patch`
3. 确认 `git apply --check` 通过后再发版；补丁失效时 CI 会在第一步就报错

## 许可

MaaLYSK 是 MIT；MaaFwApp 是 AGPL-3.0。打出的 APK 会同时带上两份许可证：
`LICENSE`、`LICENSE-MaaFwApp`，以及 `LICENSES.md` 说明。MaaFwApp 源码见
<https://github.com/Aliothmoon/MaaFwApp>。
