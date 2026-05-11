import { enNav, zhNav } from "./nav";
import { getSidebar } from "./sidebar";

export const locales = {
    zh_cn: {
        label: "简体中文",
        lang: "zh-CN",
        link: "/zh_cn/",
        themeConfig: {
            outline: {
                level: [2, 3],
                label: "在本页",
            },
            nav: zhNav,
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
            nav: enNav,
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
};
