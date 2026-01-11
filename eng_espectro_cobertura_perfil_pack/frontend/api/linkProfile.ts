import type { LinkEndpoint, LinkProfileResponse } from "../types/linkProfile";

export type LinkProfileRequest = {
  tx: LinkEndpoint;
  rx: LinkEndpoint;
  freq_mhz: number;
  k_factor: number;
  step_m: number;
};

/**
 * Fetch link profile from backend. Backend must return samples from DEM + derived metrics.
 * This function contains no mock data. It will throw on non-2xx responses.
 */
export async function fetchLinkProfile(req: LinkProfileRequest): Promise<LinkProfileResponse> {
  const res = await fetch("/api/links/profile", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req),
  });

  if (!res.ok) {
    const msg = await res.text().catch(() => "");
    throw new Error(`fetchLinkProfile failed (${res.status}): ${msg || res.statusText}`);
  }

  const data = (await res.json()) as LinkProfileResponse;
  return data;
}
