import { latestReleaseMeta } from "./version";
import { qqGroupLink, githubRepoLink, qqIconSvg } from "./constants";

export const siteConfig = {
    base: "/",
    title: "MaaLYSK",
    description: "MaaLYSK Documentation",
    head: [
        ["link", { rel: "icon", href: "/logo.ico" }],
        [
            "link",
            {
                rel: "stylesheet",
                href: "https://cdn.jsdelivr.net/npm/remixicon@3.5.0/fonts/remixicon.css",
            },
        ],
    ],
};

export const sharedThemeConfig = {
    logo: "/logo.ico",
    latestReleaseMeta,
    socialLinks: [
        { icon: { svg: qqIconSvg }, link: qqGroupLink, ariaLabel: 'QQ群' },
        { icon: 'github', link: githubRepoLink },
    ],
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
                        modal: {
                            noResultsText: "No results for",
                        },
                    },
                },
            },
        },
    },
};
