<script setup lang="ts">
import { onMounted, ref } from "vue";
import { listJobTargets, updateJobTarget, type JobTarget } from "@/api/workspace";

const targets = ref<JobTarget[]>([]);
const errorMessage = ref("");
const statusLabels: Record<JobTarget["status"], string> = { saved: "待投递", applied: "已投递", written_test: "笔试", interview: "面试", offer: "Offer", rejected: "未通过", withdrawn: "已撤回" };

async function loadTargets() {
  try { targets.value = await listJobTargets(); } catch (error) { errorMessage.value = error instanceof Error ? error.message : "读取投递管道失败"; }
}

async function updateTarget(target: JobTarget, status: JobTarget["status"]) {
  try { await updateJobTarget(target.id, status, target.note); await loadTargets(); } catch (error) { errorMessage.value = error instanceof Error ? error.message : "更新投递状态失败"; }
}

function readStatus(event: Event): JobTarget["status"] {
  return (event.target as HTMLSelectElement).value as JobTarget["status"];
}

onMounted(loadTargets);
</script>

<template>
  <div class="workspace">
    <header class="page-heading"><div><p class="eyebrow">投递管道</p><h1>让每次投递都有后续</h1></div><p>岗位由市场收件箱进入；这里记录真实投递、笔试、面试和 Offer 状态。</p></header>
    <p v-if="errorMessage" class="error-message">{{ errorMessage }}</p>
    <section v-if="targets.length === 0" class="artifact-section"><p>暂无投递目标。市场岗位收件箱迁入后，可从推荐中加入这里。</p></section>
    <article v-for="target in targets" :key="target.id" class="artifact-section pipeline-card"><header class="artifact-heading"><div><p class="eyebrow">{{ target.priority }} 类 · 匹配 {{ target.match_score ?? "-" }}</p><h2>{{ target.title }}</h2><p>{{ target.company }}</p></div><a :href="target.url" target="_blank" rel="noreferrer">查看岗位</a></header><select :value="target.status" @change="updateTarget(target, readStatus($event))"><option v-for="(label, status) in statusLabels" :key="status" :value="status">{{ label }}</option></select></article>
  </div>
</template>
