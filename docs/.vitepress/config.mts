import {defineConfig} from "vitepress";
import fs from "fs";
import path from "path";

// 侧边栏生成函数
function getSidebar(langDir: string, subDir: string) {
    // 物理路径：docs/zh_cn/manual
    const absPath = path.resolve(process.cwd(), "docs", langDir, subDir);
    if (!fs.existsSync(absPath)) return [];

    return fs
        .readdirSync(absPath)
        .filter((f) => f.endsWith(".md"))
        .sort()
        .map((f) => {
            const fullPath = path.join(absPath, f);
            const content = fs.readFileSync(fullPath, "utf-8");

            // 提取一级标题作为侧边栏显示的文字
            const match = content.match(/^#\s+(.*)/m);
            const title = match ? match[1].trim() : f;

            // 提取 ID 用于生成链接
            // 假设文件名格式为 "1.1-xxxx.md"
            const idMatch = f.match(/^(\d+\.\d+)-/);
            const id = idMatch ? idMatch[1] : f.replace(".md", "");

            return {
                text: title,
                link: `/${langDir}/${subDir}/${id}`,
            };
        });
}

export default defineConfig({
    base: "/MaaLYSK/",
    title: "MaaLYSK",
    description: "MaaLYSK Documentation",
    // 静态资源引用
    head: [
        ["link", {rel: "icon", href: "/MaaLYSK/logo.ico"}],
        // 引入 RemixIcon 图标库 CSS
        [
            "link",
            {
                rel: "stylesheet",
                href: "https://cdn.jsdelivr.net/npm/remixicon@3.5.0/fonts/remixicon.css",
            },
        ],
    ],
    themeConfig: {
        logo: "/logo.ico",
        search: {
            provider: "local",

            options: {
                locales: {
                    zh_cn: {
                        translations: {
                            button: {
                                buttonText: "搜索文档",
                                buttonAriaLabel: "搜索文档",
                            },
                            modal: {
                                noResultsText: "无法找到相关结果",
                                resetButtonTitle: "清除查询条件",
                                footer: {
                                    selectText: "选择",
                                    navigateText: "切换",
                                    closeText: "关闭",
                                },
                            },
                        },
                    },
                    en_us: {
                        translations: {
                            button: {
                                buttonText: "Search",
                                buttonAriaLabel: "Search",
                            },
                            modal: {noResultsText: "No results for"},
                        },
                    },
                },
            },
        },
        socialLinks: [
            // 等待链接补充
            // {
            //     icon: {
            //         svg: '<svg viewBox="0 0 1024 1024" xmlns="http://www.w3.org/2000/svg"><path d="M824.8 613.2c-16-51.4-34.4-94.6-62.7-165.3C766.5 262.2 689.3 112 511.5 112 331.7 112 256.2 265.2 261 447.9c-28.4 70.8-46.7 113.6-62.7 165.3-34 109.5-23 154.8-14.6 155.8 18 2.2 70.1-82.4 70.1-82.4 0 49 25.2 112.9 79.8 159-26.4 8.1-85.7 29.9-71.6 53.8 11.4 19.3 196.2 12.3 249.5 6.3 53.3 6 238.1 13 249.5-6.3 14.1-23.8-45.3-45.7-71.6-53.8 54.6-46.2 79.8-110.1 79.8-159 0 0 52.1 84.6 70.1 82.4 8.5-1.1 19.5-46.4-14.5-155.8z" fill="currentColor"></path></svg>',
            //     },
            //     link: "https://qm.qq.com/cgi-bin/qm/qr?k=1065676561",
            // },
            {icon: "github", link: "https://github.com/Witty36/MaaLYSK"},
        ],
    },

    // URL 重写规则
    rewrites: (srcPath) => {
        // 正则表达式：路径开头(zh_cn或en_us) / 中间文件夹 / (数字ID)-任意文字.md
        const match = srcPath.match(
            /^(zh_cn|en_us)\/(.+?)\/(\d+\.\d+)-.*\.md$/,
        );

        if (match) {
            const [_, lang, dir, id] = match;
            return `${lang}/${dir}/${id}.md`;
        }

        return srcPath;
    },

    // 多语言配置
    locales: {
        zh_cn: {
            label: "简体中文",
            lang: "zh-CN",
            link: "/zh_cn/",
            themeConfig: {
                outline: {
                    label: "在本页",
                },
                nav: [
                    {
                        text: '<i class="ri-book-read-line"></i> 用户手册',
                        link: "/zh_cn/manual/1.1",
                    },
                    {
                        text: '<i class="ri-code-s-slash-line"></i> 开发文档',
                        link: "/zh_cn/develop/0.0",
                    },
                ],
                sidebar: {
                    "/zh_cn/manual/": [
                        {
                            text: '<i class="ri-book-read-line"></i> 用户手册',
                            items: getSidebar("zh_cn", "manual"),
                        },
                    ],
                    "/zh_cn/develop/": [
                        {
                            text: '<i class="ri-code-s-slash-line"></i> 开发文档',
                            items: getSidebar("zh_cn", "develop"),
                        },
                    ],
                },
            },
        },
        en_us: {
            label: "English",
            lang: "en-US",
            link: "/en_us/",
            themeConfig: {
                nav: [
                    {
                        text: '<i class="ri-book-read-line"></i> User Manual',
                        link: "/en_us/manual/1.1",
                    },
                    {
                        text: '<i class="ri-code-s-slash-line"></i> Developer Guide',
                        link: "/en_us/develop/0.0",
                    },
                ],
                sidebar: {
                    "/en_us/manual/": [
                        {
                            text: '<i class="ri-book-read-line"></i> User Manual',
                            items: getSidebar("en_us", "manual"),
                        },
                    ],
                    "/en_us/develop/": [
                        {
                            text: '<i class="ri-code-s-slash-line"></i> Developer Guide',
                            items: getSidebar("en_us", "develop"),
                        },
                    ],
                },
            },
        },
    },
});
