import { defineConfig } from "vitepress";

// 功能：站点基础信息、公共主题配置、搜索与社交链接。
import { sharedThemeConfig, siteConfig } from "./config/site";
// 功能：文档路径重写规则，负责把编号文件名映射为简洁路由。
import { rewriteDocPath } from "./config/rewrites";
// 功能：多语言入口、导航与侧边栏配置。
import { locales } from "./config/locales";

export default defineConfig({
    ...siteConfig,
    themeConfig: sharedThemeConfig,
    rewrites: rewriteDocPath,
    locales,
});
