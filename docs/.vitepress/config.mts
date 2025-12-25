import {defineConfig} from "vitepress";

// https://vitepress.dev/reference/site-config
export default defineConfig({
    title: "MaaLYSK_Docs",
    description: "MaaLYSK_Docs",
    themeConfig: {
        // https://vitepress.dev/reference/default-theme-config
        nav: [
            {text: "用户手册", link: "/user/1.1-快速开始.md"},
            {
                text: "开发手册",
                link: "/code/zh_cn/0.0-MaaLYSK零基础开发指南.md",
            },
        ],

        sidebar: [],

        socialLinks: [
            {icon: "github", link: "https://github.com/Witty36/MaaLYSK"},
        ],
    },
});
