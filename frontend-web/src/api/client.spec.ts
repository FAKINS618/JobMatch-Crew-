import { afterEach, describe, expect, it, vi } from "vitest";
import { apiFetch } from "./client";

afterEach(() => vi.unstubAllGlobals());

describe("apiFetch", () => {
  it("returns typed JSON for a successful response", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response('{"id": 1}', { status: 200 })));

    await expect(apiFetch<{ id: number }>("/api/test")).resolves.toEqual({ id: 1 });
  });

  it("preserves the FastAPI detail for a failed response", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(new Response('{"detail":"简历版本不存在"}', { status: 422 })),
    );

    await expect(apiFetch("/api/test")).rejects.toMatchObject({
      message: "简历版本不存在",
      status: 422,
    });
  });
});
