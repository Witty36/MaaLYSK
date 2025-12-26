import DefaultTheme from "vitepress/theme";
import {h} from "vue";
import BackToTop from "./components/BackToTop.vue";

export default {
    extends: DefaultTheme,

    Layout() {
        return h(DefaultTheme.Layout, null, {
            "doc-bottom": () => h(BackToTop),
        });
    },
};
