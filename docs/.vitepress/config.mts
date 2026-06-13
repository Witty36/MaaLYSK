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

export default defineConfig({
    ...siteConfig,
    themeConfig: sharedThemeConfig,
    rewrites: rewriteDocPath,
    locales,
    markdown: {
            dark: darkTheme as any,
        },
    },
    vite: {
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
        ],
    },
});
