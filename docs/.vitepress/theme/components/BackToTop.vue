<script setup lang="ts">
import {ref, onMounted, onUnmounted} from "vue";

const progress = ref(0);
const show = ref(false);

const handleScroll = () => {
    // 获取滚动高度、可视高度、文档总高度
    const scrollTop = window.scrollY;
    const docHeight = document.documentElement.scrollHeight;
    const winHeight = window.innerHeight;

    // 计算百分比 (0-100)
    const scrollPercent = scrollTop / (docHeight - winHeight);
    const percent = Math.round(scrollPercent * 100);

    // 限制在 0-100 之间
    progress.value = Math.min(100, Math.max(0, percent));

    // 滚动超过 200px 才显示按钮
    show.value = scrollTop > 200;
};

const scrollToTop = () => {
    window.scrollTo({top: 0, behavior: "smooth"});
};

onMounted(() => {
    window.addEventListener("scroll", handleScroll);
});

onUnmounted(() => {
    window.removeEventListener("scroll", handleScroll);
});
</script>

<template>
    <Transition name="fade">
        <div
            v-if="show"
            class="back-to-top"
            @click="scrollToTop"
            :title="`阅读进度: ${progress}% - 点击回到顶部`">
            <div class="progress-ring">
                <svg class="ring-svg" viewBox="0 0 36 36">
                    <path
                        class="ring-bg"
                        d="M18 2.0845
              a 15.9155 15.9155 0 0 1 0 31.831
              a 15.9155 15.9155 0 0 1 0 -31.831" />
                    <path
                        class="ring-progress"
                        :stroke-dasharray="`${progress}, 100`"
                        d="M18 2.0845
              a 15.9155 15.9155 0 0 1 0 31.831
              a 15.9155 15.9155 0 0 1 0 -31.831" />
                </svg>
                <span class="value"
                    >{{ progress }}<span class="percent">%</span></span
                >
                <div class="icon-arrow">↑</div>
            </div>
        </div>
    </Transition>
</template>

<style scoped>
.back-to-top {
    position: fixed;
    bottom: 40px;
    right: 20px;
    z-index: 100;
    cursor: pointer;
    width: 60px;
    height: 60px;
    background: var(--vp-c-bg);
    border-radius: 50%;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    display: flex;
    align-items: center;
    justify-content: center;
    transition:
        transform 0.3s,
        box-shadow 0.3s;
    border: 1px solid var(--vp-c-divider);
}

.back-to-top:hover {
    transform: translateY(-3px);
    box-shadow: 0 8px 16px rgba(0, 0, 0, 0.2);
}

.progress-ring {
    position: relative;
    width: 50px;
    height: 50px;
    display: flex;
    align-items: center;
    justify-content: center;
}

.ring-svg {
    transform: rotate(-90deg);
    width: 100%;
    height: 100%;
}

.ring-bg {
    fill: none;
    stroke: var(--vp-c-gray-soft);
    stroke-width: 3;
}

.ring-progress {
    fill: none;
    stroke: var(--vp-c-brand); /* 使用主题色 */
    stroke-width: 3;
    stroke-linecap: round;
    transition: stroke-dasharray 0.3s ease;
}

.value {
    position: absolute;
    font-size: 12px;
    font-weight: bold;
    color: var(--vp-c-text-1);
    transition: opacity 0.2s;
}

.percent {
    font-size: 8px;
    margin-left: 1px;
}

.icon-arrow {
    position: absolute;
    font-size: 18px;
    font-weight: bold;
    color: var(--vp-c-brand);
    opacity: 0;
    transition: opacity 0.2s;
}

/* 悬停时隐藏数字，显示箭头 */
.back-to-top:hover .value {
    opacity: 0;
}
.back-to-top:hover .icon-arrow {
    opacity: 1;
}

/* 进场动画 */
.fade-enter-active,
.fade-leave-active {
    transition:
        opacity 0.3s,
        transform 0.3s;
}

.fade-enter-from,
.fade-leave-to {
    opacity: 0;
    transform: translateY(20px);
}
</style>
