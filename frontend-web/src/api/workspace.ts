import { apiFetch } from "./client";
import type { ResumeVersion } from "./copilot";

export type ResumeProfile = ResumeVersion["profile"];

export interface ActionItem {
  id: number;
  report_id: number;
  skill: string;
  title: string;
  priority: "high" | "medium" | "low";
  status: "todo" | "in_progress" | "completed" | "cancelled";
  expected_output: string;
  evidence_count: number;
}

export interface JobTarget {
  id: number;
  title: string;
  company: string;
  url: string;
  priority: "A" | "B" | "C";
  match_score: number | null;
  status: "saved" | "applied" | "written_test" | "interview" | "offer" | "rejected" | "withdrawn";
  note: string;
  created_at: string;
}

export interface ReportSummary {
  id: number;
  target_role: string;
  score: number | null;
  parse_status: string;
  created_at: string;
  created_at_local: string | null;
  job_post_count: number;
}

export interface JobPost {
  id: number;
  report_id: number;
  title: string;
  company: string;
  url: string;
  content: string;
  source: string;
  status: string;
  freshness_score: number;
  invalid_reason: string;
  relevance_score: number;
  verification_status: string;
  verification_reason: string;
  deadline_at: string | null;
}

export interface ReportDetail extends ReportSummary {
  resume_text: string;
  jd_text: string;
  markdown_report: string;
  parsed_result: string;
  job_posts: JobPost[];
}

export function parseResume(rawText: string) {
  return apiFetch<{ profile: ResumeProfile }>("/api/resumes/parse", {
    method: "POST",
    body: JSON.stringify({ raw_text: rawText }),
  });
}

export function saveResumeVersion(payload: {
  version_name: string;
  target_role: string;
  raw_text: string;
  profile: ResumeProfile;
}) {
  return apiFetch<ResumeVersion>("/api/resumes/versions", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function listReports() {
  return apiFetch<{ reports: ReportSummary[] }>("/api/reports");
}

export function getReport(reportId: number) {
  return apiFetch<ReportDetail>(`/api/reports/${reportId}`);
}

export function createJobTarget(payload: { report_id: number; url: string; priority: "A" | "B" | "C" }) {
  return apiFetch<JobTarget>("/api/job-targets", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export interface MarketTaskCreateResponse {
  task_id: number;
  status: "pending" | "running" | "success" | "failed";
}

export interface MarketTask {
  id: number;
  task_type: string;
  status: "pending" | "running" | "success" | "failed";
  progress: number;
  report_id: number | null;
  error_message: string;
}

export function createMarketMatchTask(payload: {
  resume_text: string;
  target_role: string;
  city: string;
  max_results: number;
  resume_version_id: number;
}) {
  return apiFetch<MarketTaskCreateResponse>("/api/tasks/market-match", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function getMarketTask(taskId: number) {
  return apiFetch<MarketTask>(`/api/tasks/${taskId}`);
}

export function createActionItemsFromReport(reportId: number, skills: string[]) {
  return apiFetch<ActionItem[]>(`/api/action-items/from-report/${reportId}`, {
    method: "POST",
    body: JSON.stringify({ skills }),
  });
}

export function listActionItems() {
  return apiFetch<ActionItem[]>("/api/action-items");
}

export function updateActionItem(itemId: number, status: ActionItem["status"]) {
  return apiFetch<ActionItem>(`/api/action-items/${itemId}`, {
    method: "PATCH",
    body: JSON.stringify({ status }),
  });
}

export function createActionEvidence(itemId: number, content: string, url: string) {
  return apiFetch(`/api/action-items/${itemId}/evidence`, {
    method: "POST",
    body: JSON.stringify({
      evidence_type: url ? "link" : "note",
      content,
      url: url || null,
    }),
  });
}

export function listJobTargets() {
  return apiFetch<JobTarget[]>("/api/job-targets");
}

export function updateJobTarget(itemId: number, status: JobTarget["status"], note: string) {
  return apiFetch<JobTarget>(`/api/job-targets/${itemId}`, {
    method: "PATCH",
    body: JSON.stringify({ status, note }),
  });
}
