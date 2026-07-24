<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import {
  createResumeVersionFromSuggestions,
  listResumeSuggestions,
  updateResumeSuggestion,
  type ResumeProfile,
  type ResumeSuggestion,
} from "@/api/workspace";

const props = defineProps<{
  reportId: number;
  sourceResumeVersionId: number;
  targetRole: string;
  sourceRawText: string;
  sourceProfile: ResumeProfile;
}>();
const emit = defineEmits<{ saved: [] }>();
const suggestions = ref<ResumeSuggestion[]>([]);
const draftText = ref(props.sourceRawText);
const versionName = ref(`${props.targetRole || "求职"} 优化版`);
const loading = ref(false);
const saving = ref(false);
const errorMessage = ref("");
const successMessage = ref("");

const confirmedSuggestions = computed(() => suggestions.value.filter((item) => ["accepted", "edited"].includes(item.status)));

async function load() {
  loading.value = true;
  errorMessage.value = "";
  try { suggestions.value = await listResumeSuggestions(props.reportId); }
  catch (error) { errorMessage.value = error instanceof Error ? error.message : "简历建议暂时无法加载"; }
  finally { loading.value = false; }
}

async function changeSuggestion(item: ResumeSuggestion, status: ResumeSuggestion["status"]) {
  try {
    const updated = await updateResumeSuggestion(item.id, { status, edited_text: item.edited_text });
    suggestions.value = suggestions.value.map((current) => current.id === updated.id ? updated : current);
  } catch (error) { errorMessage.value = error instanceof Error ? error.message : "简历建议保存失败"; }
}

async function createVersion() {
  if (!versionName.value.trim() || draftText.value.trim().length < 80 || confirmedSuggestions.value.length === 0) return;
  saving.value = true;
  errorMessage.value = "";
  successMessage.value = "";
  try {
    await createResumeVersionFromSuggestions({
      report_id: props.reportId,
      source_resume_version_id: props.sourceResumeVersionId,
      suggestion_ids: confirmedSuggestions.value.map((item) => item.id),
      version_name: versionName.value.trim(),
      target_role: props.targetRole,
      raw_text: draftText.value.trim(),
      profile: props.sourceProfile,
    });
    successMessage.value = "已创建新的简历版本，原版本保持不变。";
    emit("saved");
  } catch (error) { errorMessage.value = error instanceof Error ? error.message : "新简历版本创建失败"; }
  finally { saving.value = false; }
}

watch(() => props.reportId, load);
onMounted(load);
</script>

<template>
  <section class="suggestion-review">
    <div class="resume-row">
      <div><h2>简历建议确认</h2><p>先确认建议，再由你编辑完整简历文本；系统不会自动覆盖原版本。</p></div>
      <span class="helper-text">{{ confirmedSuggestions.length }} 条已确认</span>
    </div>
    <p v-if="loading" class="helper-text">正在加载建议...</p>
    <p v-if="errorMessage" class="error-message">{{ errorMessage }}</p>
    <p v-if="successMessage" class="success-message">{{ successMessage }}</p>
    <article v-for="item in suggestions" :key="item.id" class="suggestion-item">
      <div><strong>{{ item.suggestion_type === "resume_bullet" ? "简历 Bullet" : "简历优化建议" }}</strong><p>{{ item.suggested_text }}</p></div>
      <label>处理方式
        <select :value="item.status" @change="changeSuggestion(item, ($event.target as HTMLSelectElement).value as ResumeSuggestion['status'])">
          <option value="pending">待确认</option><option value="accepted">接受</option><option value="edited">已编辑</option><option value="rejected">拒绝</option>
        </select>
      </label>
      <input v-if="item.status === 'edited'" v-model="item.edited_text" placeholder="填写修改后的建议内容" @change="changeSuggestion(item, 'edited')" />
    </article>
    <p v-if="!loading && suggestions.length === 0" class="helper-text">这份报告暂无可确认的简历建议。</p>
    <div v-if="confirmedSuggestions.length" class="suggestion-apply">
      <label>新版本名称<input v-model="versionName" /></label>
      <label>编辑完整简历文本<textarea v-model="draftText" /></label>
      <button :disabled="saving || draftText.trim().length < 80" @click="createVersion">{{ saving ? "正在创建" : "创建确认后的新版本" }}</button>
    </div>
  </section>
</template>