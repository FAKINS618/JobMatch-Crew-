<script setup lang="ts">
import { onMounted, ref } from "vue";
import {
  createActionEvidence,
  listActionItems,
  updateActionItem,
  type ActionItem,
} from "@/api/workspace";

const items = ref<ActionItem[]>([]);
const errorMessage = ref("");
const evidenceNotes = ref<Record<number, string>>({});
const evidenceUrls = ref<Record<number, string>>({});
const statusLabels: Record<ActionItem["status"], string> = {
  todo: "待开始",
  in_progress: "进行中",
  completed: "已完成",
  cancelled: "已取消",
};

async function loadItems() {
  try {
    items.value = await listActionItems();
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : "读取成长任务失败";
  }
}

async function updateStatus(item: ActionItem, status: ActionItem["status"]) {
  try {
    await updateActionItem(item.id, status);
    await loadItems();
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : "更新任务失败";
  }
}

function readStatus(event: Event): ActionItem["status"] {
  return (event.target as HTMLSelectElement).value as ActionItem["status"];
}

async function submitEvidence(item: ActionItem) {
  const content = evidenceNotes.value[item.id]?.trim() ?? "";
  const url = evidenceUrls.value[item.id]?.trim() ?? "";
  if (!content && !url) {
    errorMessage.value = "请填写成果说明或成果链接";
    return;
  }
  try {
    await createActionEvidence(item.id, content, url);
    evidenceNotes.value[item.id] = "";
    evidenceUrls.value[item.id] = "";
    await loadItems();
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : "提交成果证据失败";
  }
}

onMounted(loadItems);
</script>

<template>
  <div class="workspace">
    <header class="page-heading"><div><p class="eyebrow">成长计划</p><h1>把缺口变成可验证成果</h1></div><p>完成任务前先提交项目链接或复盘说明，避免“只勾选不产出”。</p></header>
    <p v-if="errorMessage" class="error-message">{{ errorMessage }}</p>
    <section v-if="items.length === 0" class="artifact-section"><p>暂无成长任务。副驾分析后点击“加入成长计划”即可创建。</p></section>
    <article v-for="item in items" :key="item.id" class="artifact-section action-card">
      <header class="artifact-heading"><div><p class="eyebrow">{{ item.priority }} priority · {{ statusLabels[item.status] }}</p><h2>{{ item.title }}</h2></div><strong>{{ item.evidence_count }} 份证据</strong></header>
      <p>{{ item.expected_output }}</p>
      <div class="action-controls"><select :value="item.status" @change="updateStatus(item, readStatus($event))"><option v-for="(label, status) in statusLabels" :key="status" :value="status">{{ label }}</option></select></div>
      <div v-if="item.status !== 'completed'" class="evidence-form"><input v-model="evidenceUrls[item.id]" placeholder="成果链接（可选）" /><textarea v-model="evidenceNotes[item.id]" placeholder="成果说明，例如完成了什么、验证了什么..." /><button @click="submitEvidence(item)">提交成果证据</button></div>
    </article>
  </div>
</template>
