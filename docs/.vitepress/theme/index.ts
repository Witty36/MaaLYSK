import DefaultTheme from "vitepress/theme";
import {h} from "vue";
import {useData} from "vitepress";
import BackToTop from "./components/BackToTop.vue";
import NavContactGroup from "./components/NavContactGroup.vue";
import "./custom.css";
import Mermaid from "./components/Mermaid.vue";
import Flowchart from './components/Flowchart.vue'

export default {
    extends: DefaultTheme,

    Layout() {
        const { theme } = useData();
        return h(DefaultTheme.Layout, null, {
            "nav-bar-content-before": () => {
                const meta = theme.value.latestReleaseMeta;
                return meta ? h('a', {
                    class: 'nav-version-mobile',
                    href: meta.link,
                    target: '_blank',
                    rel: 'noopener',
                    innerHTML: `<span class="nav-version-badge"><span class="nav-version-spark">✦</span><span>${meta.version}</span></span>`
                }) : null;
            },
            "nav-screen-content-after": () => h(NavContactGroup),
            "doc-bottom": () => h(BackToTop),
        });
    },

    enhanceApp({ app }: { app: any }) {
        app.component('Mermaid', Mermaid);
        app.component('Flowchart', Flowchart);
    },
};
