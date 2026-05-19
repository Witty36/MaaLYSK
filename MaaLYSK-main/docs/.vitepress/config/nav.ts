import { latestReleaseMeta } from "./version";

const versionBadgeHtml = `<span class="nav-version-badge"><span class="nav-version-spark">✦</span><span>${latestReleaseMeta.version}</span></span>`;

const versionNavItem = {
    text: versionBadgeHtml,
    link: latestReleaseMeta.link,
    activeMatch: "^$",
    class: "nav-version-link",
};

export const zhNav = [
    versionNavItem,
    {
        text: '<i class="ri-book-read-line"></i> 用户手册',
        link: "/zh_cn/manual/1.1",
    },
    {
        text: '<i class="ri-code-s-slash-line"></i> 开发文档',
        link: "/zh_cn/develop/0.0",
    },
    {
        text: '<i class="ri-link"></i> 友情链接',
        items: [
            { text: "MAA", link: "https://maa.plus/" },
            { text: "Mirror酱", link: "https://mirrorchyan.com/zh/projects?source=MaaLYSKtop&rid=MaaLYSK" },
            { text: "MaaYuan", link: "https://maayuan.top/" },
        ],
    },
];

export const enNav = [
    versionNavItem,
    {
        text: '<i class="ri-book-read-line"></i> User Manual',
        link: "/en_us/manual/1.1",
    },
    {
        text: '<i class="ri-code-s-slash-line"></i> Developer Guide',
        link: "/en_us/develop/0.0",
    },
    {
        text: "Links",
        items: [
            { text: "MAA", link: "https://maa.plus/" },
            { text: "Mirror酱", link: "https://mirrorchyan.com/zh/projects?source=MaaLYSKtop&rid=MaaLYSK" },
            { text: "MaaYuan", link: "https://maayuan.top/" },
        ],
    },
];
