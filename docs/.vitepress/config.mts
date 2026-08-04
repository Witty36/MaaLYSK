import path from "path";
import fs from "fs";
import https from "https";
import { defineConfig } from "vitepress";

// 功能：站点基础信息、公共主题配置、搜索与社交链接。
import { sharedThemeConfig, siteConfig } from "./config/site";
// 功能：文档路径重写规则，负责把编号文件名映射为简洁路由。
import { rewriteDocPath } from "./config/rewrites";
// 功能：多语言入口、导航与侧边栏配置。
import { locales } from "./config/locales";

// 自定义 Shiki 主题：JSON/JSONC 代码高亮使用主题紫色
import lightTheme from "./theme/shiki/light.json";
import darkTheme from "./theme/shiki/dark.json";

const noticeDir = path.resolve(process.cwd(), "docs", "zh_cn", "notice");
const emojiUsageJson = path.resolve(process.cwd(), "docs", "public", "zh_cn", "develop", "2.2-emoji-usage.json");

export default defineConfig({
    ...siteConfig,
    themeConfig: sharedThemeConfig,
    rewrites: rewriteDocPath,
    locales,
    markdown: {
        theme: {
            light: lightTheme as any,
            dark: darkTheme as any,
        },
    },
    vite: {
        define: {
            'import.meta.env.VITE_EMOJI_TOKEN': JSON.stringify(
                process.env.EMOJI_SAVE_TOKEN || process.env.GITHUB_TOKEN || ''
            ),
        },
        server: {
            watch: {
                usePolling: true,
                interval: 1000,
            },
        },
        plugins: [
            {
                name: "notice-reload",
                configureServer(server) {
                    const pattern = path.join(noticeDir, "*.md");
                    server.watcher.add(pattern);
                    server.watcher.on("add", (file) => {
                        if (file.endsWith(".md")) {
                            server.ws.send({ type: "full-reload" });
                        }
                    });
                    server.watcher.on("unlink", (file) => {
                        if (file.endsWith(".md")) {
                            server.ws.send({ type: "full-reload" });
                        }
                    });
                },
            },
            {
                name: "emoji-save-endpoint",
                configureServer(server) {
                    server.middlewares.use("/__emoji-save__", (req, res, next) => {
                        if (req.method !== "POST") {
                            next();
                            return;
                        }
                        let body = "";
                        req.on("data", (chunk: string) => { body += chunk; });
                        req.on("end", async () => {
                            const filePath = "docs/public/zh_cn/develop/2.2-emoji-usage.json";
                            const localPath = path.resolve(process.cwd(), filePath);

                            // 1. Always write to local file first
                            try {
                                const dir = path.dirname(localPath);
                                if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
                                fs.writeFileSync(localPath, body, "utf-8");
                            } catch { /* local write failure is non-fatal */ }

                            // 2. Try to commit to GitHub via API
                            const token = process.env.GITHUB_TOKEN || process.env.EMOJI_SAVE_TOKEN;
                            const owner = "Witty36";
                            const repo = "MaaLYSK";

                            if (token) {
                                try {
                                    const result = await commitToGitHub(token, owner, repo, filePath, body);
                                    res.writeHead(200, { "Content-Type": "application/json" });
                                    res.end(JSON.stringify({
                                        ok: true,
                                        method: "github",
                                        message: `已保存到 GitHub 仓库！${result.newFile ? "(新建)" : "(更新)"}`,
                                    }));
                                } catch (err: any) {
                                    // GitHub failed, but local save succeeded
                                    res.writeHead(200, { "Content-Type": "application/json" });
                                    res.end(JSON.stringify({
                                        ok: true,
                                        method: "local",
                                        message: "已保存到本地（GitHub 提交失败: " + (err.message || err) + "），请手动 git commit",
                                    }));
                                }
                            } else {
                                // No token, local save only
                                res.writeHead(200, { "Content-Type": "application/json" });
                                res.end(JSON.stringify({
                                    ok: true,
                                    method: "local",
                                    message: "已保存到本地，请手动 git commit 提交。配置 GITHUB_TOKEN 环境变量可自动提交。",
                                }));
                            }
                        });
                    });
                },
            },
        ],
    },
});

// ============================================================
// GitHub API helper: commit a file directly to the repo
// ============================================================
function githubRequest(
    token: string,
    method: string,
    path: string,
    body?: string,
): Promise<{ status: number; data: any }> {
    return new Promise((resolve, reject) => {
        const options: https.RequestOptions = {
            hostname: "api.github.com",
            path,
            method,
            headers: {
                Authorization: `Bearer ${token}`,
                "User-Agent": "MaaLYSK-Emoji-Save",
                Accept: "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
                ...(body ? { "Content-Type": "application/json" } : {}),
            },
        };

        const req = https.request(options, (res) => {
            let data = "";
            res.on("data", (chunk: string) => { data += chunk; });
            res.on("end", () => {
                try {
                    resolve({ status: res.statusCode || 500, data: JSON.parse(data) });
                } catch {
                    resolve({ status: res.statusCode || 500, data: { message: data } });
                }
            });
        });

        req.on("error", reject);
        if (body) req.write(body);
        req.end();
    });
}

async function commitToGitHub(
    token: string,
    owner: string,
    repo: string,
    filePath: string,
    content: string,
): Promise<{ newFile: boolean }> {
    const apiPath = `/repos/${owner}/${repo}/contents/${encodeURIComponent(filePath)}`;

    // 1. Try to get the file's current SHA (if it exists)
    let sha: string | null = null;
    try {
        const get = await githubRequest(token, "GET", apiPath);
        if (get.status === 200 && get.data.sha) {
            sha = get.data.sha;
        }
    } catch {
        // File doesn't exist yet — that's fine
    }

    // 2. Create or update the file
    const payload = JSON.stringify({
        message: "chore: update emoji usage state\n\n[auto] via EmojiTable save",
        content: Buffer.from(content).toString("base64"),
        ...(sha ? { sha } : {}),
        branch: "main",
    });

    const put = await githubRequest(token, "PUT", apiPath, payload);
    if (put.status !== 200 && put.status !== 201) {
        throw new Error(put.data.message || `GitHub API returned ${put.status}`);
    }

    return { newFile: !sha };
}
