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
    head: [["link", {rel: "icon", href: "/MaaLYSK/doc_image/logo.ico"}]],
    themeConfig: {
        logo: "/doc_image/logo.ico",
        socialLinks: [
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
                    {text: "用户手册", link: "/zh_cn/manual/1.1"},
                    {text: "开发文档", link: "/zh_cn/develop/0.0"},
                ],
                sidebar: {
                    "/zh_cn/manual/": [
                        {
                            text: "用户手册",
                            items: getSidebar("zh_cn", "manual"),
                        },
                    ],
                    "/zh_cn/develop/": [
                        {
                            text: "开发文档",
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
                    {text: "User Manual", link: "/en_us/manual/1.1"},
                    {text: "Developer Guide", link: "/en_us/develop/0.0"},
                ],
                sidebar: {
                    "/en_us/manual/": [
                        {
                            text: "User Manual",
                            items: getSidebar("en_us", "manual"),
                        },
                    ],
                    "/en_us/develop/": [
                        {
                            text: "Developer Guide",
                            items: getSidebar("en_us", "develop"),
                        },
                    ],
                },
            },
        },
    },
});
