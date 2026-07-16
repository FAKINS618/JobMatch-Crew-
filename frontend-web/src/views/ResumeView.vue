<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { RouterLink } from "vue-router";
import { parseResume, saveResumeVersion, type ResumeProfile } from "@/api/workspace";
import { useCopilotStore } from "@/stores/copilot";

const store = useCopilotStore();
const expandedResumeId = ref<number | null>(null);
const rawText = ref("");
const versionName = ref("");
const targetRole = ref("");
const draftProfile = ref<ResumeProfile | null>(null);
const isParsing = ref(false);
const isSaving = ref(false);
const errorMessage = ref("");
const successMessage = ref("");
const canSave = computed(() => Boolean(draftProfile.value && versionName.value.trim()));

onMounted(() => store.loadResumeVersions());

async function parseDraft() {
  isParsing.value = true;
  errorMessage.value = "";
  successMessage.value = "";
  try {
    draftProfile.value = (await parseResume(rawText.value.trim())).profile;
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : "简历解析失败";
  } finally {
    isParsing.value = false;
  }
}

async function saveDraft() {
  if (!draftProfile.value) return;
  isSaving.value = true;
  errorMessage.value = "";
  try {
    await saveResumeVersion({
      version_name: versionName.value.trim(),
      target_role: targetRole.value.trim(),
      raw_text: rawText.value.trim(),
      profile: draftProfile.value,
    });
    await store.loadResumeVersions();
    successMessage.value = "简历版本已保存，可立即用于副驾分析。";
    draftProfile.value = null;
    versionName.value = "";
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : "保存简历版本失败";
  } finally {
    isSaving.value = false;
  }
}
</script>

<template>
  <div class="workspace">
    <header class="page-heading">
      <div>
        <p class="eyebrow">简历中心</p>
        <h1>选择有证据的简历版本</h1>
      </div>
      <p>分析会记录所使用的版本，避免不同版本的结果混在一起。</p>
    </header>
    <section class="artifact-section resume-import">
      <p class="eyebrow">导入简历</p>
      <h2>先由 AI 提取，再由你确认保存</h2>
      <textarea v-model="rawText" placeholder="粘贴不少于 80 字的简历内容..." />
      <div class="resume-actions">
        <button :disabled="isParsing || rawText.trim().length < 80" @click="parseDraft">
          {{ isParsing ? "正在解析" : "提取简历信息" }}
        </button>
      </div>
      <p v-if="errorMessage" class="error-message">{{ errorMessage }}</p>
      <p v-if="successMessage" class="success-message">{{ successMessage }}</p>
      <div v-if="draftProfile" class="resume-detail draft-profile">
        <p class="eyebrow">待确认档案</p>
        <section><h2>技能</h2><p>{{ draftProfile.skills.join(" · ") || "未提取" }}</p></section>
        <section><h2>项目</h2><p v-if="draftProfile.projects.length === 0">未提取项目经历</p><ul v-else><li v-for="project in draftProfile.projects" :key="project.name"><strong>{{ project.name }}</strong><span>{{ project.technologies.join(" · ") }}</span><p>{{ project.description }}</p></li></ul></section>
        <div class="intake-grid">
          <label>版本名称<input v-model="versionName" placeholder="例如：Python 后端实习 v1" /></label>
          <label>适用岗位方向<input v-model="targetRole" placeholder="例如：Python 后端开发实习" /></label>
        </div>
        <button :disabled="isSaving || !canSave" @click="saveDraft">{{ isSaving ? "正在保存" : "确认并保存版本" }}</button>
      </div>
    </section>
    <section class="artifact-section">
      <p v-if="store.resumeVersions.length === 0" class="helper-text">暂未保存简历版本。简历导入与区块确认将在此页面继续补齐。</p>
      <article v-for="resume in store.resumeVersions" :key="resume.id" class="resume-card">
        <div class="resume-row">
          <div><strong>{{ resume.version_name }}</strong><p>{{ resume.target_role || "未设置岗位方向" }}</p></div>
          <time>{{ resume.created_at || "" }}</time>
        </div>
        <div class="resume-actions">
          <button class="secondary" @click="expandedResumeId = expandedResumeId === resume.id ? null : resume.id">
            {{ expandedResumeId === resume.id ? "收起简历" : "查看简历" }}
          </button>
          <RouterLink class="link-button" :to="{ path: '/', query: { resume: resume.id } }">用此版本开始分析</RouterLink>
        </div>
        <div v-if="expandedResumeId === resume.id" class="resume-detail">
          <section><h2>技能</h2><p>{{ resume.profile.skills.join(" · ") || "未提取" }}</p></section>
          <section><h2>项目</h2><p v-if="resume.profile.projects.length === 0">未提取项目经历</p><ul v-else><li v-for="project in resume.profile.projects" :key="project.name"><strong>{{ project.name }}</strong><span>{{ project.technologies.join(" · ") }}</span><p>{{ project.description }}</p></li></ul></section>
          <details><summary>查看原始简历文本</summary><pre>{{ resume.raw_text }}</pre></details>
        </div>
      </article>
    </section>
  </div>
</template>
