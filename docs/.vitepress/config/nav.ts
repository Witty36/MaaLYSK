import { qqGroupLink, qqIconSvg } from "./constants";
import { latestReleaseMeta } from "./version";

const latestVersionBadge = `<span class="nav-version-badge"><span class="nav-version-spark">✦</span><span>${latestReleaseMeta.version}</span></span>`;
const contactLinkText = `<span class="nav-contact-link"><span>联系我们</span>${qqIconSvg}</span>`;
const contactLinkTextEn = `<span class="nav-contact-link"><span>Contact Us</span>${qqIconSvg}</span>`;

function createVersionNavItem() {
    return {
        text: latestVersionBadge,
        link: latestReleaseMeta.link,
        activeMatch: "^$",
        class: "nav-version-link",
    };
}

export const zhNav = [
    createVersionNavItem(),
    {
        text: '<i class="ri-book-read-line"></i> 用户手册',
        link: "/zh_cn/manual/1.1",
    },
    {
        text: '<i class="ri-code-s-slash-line"></i> 开发文档',
        link: "/zh_cn/develop/0.0",
    },
    {
        text: contactLinkText,
        link: qqGroupLink,
    },
];

export const enNav = [
    createVersionNavItem(),
    {
        text: '<i class="ri-book-read-line"></i> User Manual',
        link: "/en_us/manual/1.1",
    },
    {
        text: '<i class="ri-code-s-slash-line"></i> Developer Guide',
        link: "/en_us/develop/0.0",
    },
    {
        text: contactLinkTextEn,
        link: qqGroupLink,
    },
];
