import type { ProfileSample, LinkEndpoint, LinkProfileDerived, ObstructionInfo } from "../types/linkProfile";

const C = 299_792_458; // m/s
const R_EARTH = 6_371_000; // m

export type LinkProfileSeries = {
  x_m: Float64Array;           // distance axis (m)
  bulge_m: Float64Array;       // earth bulge (m)
  y_earth_m: Float64Array;     // y_base + bulge
  y_terrain_m: Float64Array;   // y_earth + ground
  y_los_m: Float64Array;       // LOS (includes antenna heights and earth)
  r1_m: Float64Array;          // Fresnel radius (m)
  y_f1_top_m: Float64Array;    // LOS + r1
  y_f1_bot_m: Float64Array;    // LOS - r1
  obstruction: ObstructionInfo;
  distance_m: number;
};

export function deg2rad(d: number): number {
  return (d * Math.PI) / 180.0;
}

export function rad2deg(r: number): number {
  return (r * 180.0) / Math.PI;
}

/**
 * Initial bearing from point A to B (degrees, 0..360).
 * Uses a standard spherical model sufficient for UI bearings.
 */
export function bearing_deg(a: LinkEndpoint, b: LinkEndpoint): number {
  const φ1 = deg2rad(a.lat);
  const φ2 = deg2rad(b.lat);
  const Δλ = deg2rad(b.lon - a.lon);

  const y = Math.sin(Δλ) * Math.cos(φ2);
  const x = Math.cos(φ1) * Math.sin(φ2) - Math.sin(φ1) * Math.cos(φ2) * Math.cos(Δλ);
  let θ = Math.atan2(y, x);
  θ = (rad2deg(θ) + 360) % 360;
  return θ;
}

/** Great-circle distance (meters), haversine. */
export function haversine_m(a: LinkEndpoint, b: LinkEndpoint): number {
  const φ1 = deg2rad(a.lat);
  const φ2 = deg2rad(b.lat);
  const Δφ = φ2 - φ1;
  const Δλ = deg2rad(b.lon - a.lon);

  const s = Math.sin(Δφ / 2) ** 2 + Math.cos(φ1) * Math.cos(φ2) * (Math.sin(Δλ / 2) ** 2);
  const c = 2 * Math.atan2(Math.sqrt(s), Math.sqrt(1 - s));
  return R_EARTH * c;
}

export function wavelength_m(freq_mhz: number): number {
  if (!(freq_mhz > 0)) throw new Error("freq_mhz must be > 0");
  return C / (freq_mhz * 1e6);
}

export function earth_bulge_m(x_m: number, D_m: number, k_factor: number): number {
  const R_eff = k_factor * R_EARTH;
  return (x_m * (D_m - x_m)) / (2 * R_eff);
}

export function build_profile_series(args: {
  samples: ProfileSample[];
  tx: LinkEndpoint;
  rx: LinkEndpoint;
  freq_mhz: number;
  k_factor: number;
  y_base_padding_m?: number; // how much to extend below min ground
}): LinkProfileSeries {
  const { samples, tx, rx, freq_mhz, k_factor } = args;
  const pad = args.y_base_padding_m ?? 50;

  if (samples.length < 2) throw new Error("Need at least 2 samples");
  const n = samples.length;

  // Validate monotonic distances
  for (let i = 1; i < n; i++) {
    if (!(samples[i].d_m > samples[i - 1].d_m)) {
      throw new Error("samples.d_m must be strictly increasing");
    }
  }

  const D = samples[n - 1].d_m;
  const λ = wavelength_m(freq_mhz);

  const x = new Float64Array(n);
  const bulge = new Float64Array(n);
  const y_earth = new Float64Array(n);
  const y_terrain = new Float64Array(n);
  const y_los = new Float64Array(n);
  const r1 = new Float64Array(n);
  const y_f1_top = new Float64Array(n);
  const y_f1_bot = new Float64Array(n);

  let minGround = Infinity;
  let maxGround = -Infinity;
  for (const s of samples) {
    minGround = Math.min(minGround, s.ground_m);
    maxGround = Math.max(maxGround, s.ground_m);
  }

  // Base line used only for visualization / fills.
  const y_base = (isFinite(minGround) ? minGround : 0) - pad;

  for (let i = 0; i < n; i++) {
    x[i] = samples[i].d_m;
    bulge[i] = earth_bulge_m(x[i], D, k_factor);
    y_earth[i] = y_base + bulge[i];
    y_terrain[i] = y_earth[i] + samples[i].ground_m;
  }

  // Antenna heights above ground at endpoints:
  const Htx = samples[0].ground_m + tx.h_ant_agl_m;
  const Hrx = samples[n - 1].ground_m + rx.h_ant_agl_m;

  const Ytx = y_earth[0] + Htx;
  const Yrx = y_earth[n - 1] + Hrx;

  for (let i = 0; i < n; i++) {
    const t = x[i] / D;
    y_los[i] = Ytx + (Yrx - Ytx) * t;

    const d1 = x[i];
    const d2 = D - x[i];
    // Fresnel radius only defined for interior points (d1>0, d2>0)
    if (d1 <= 0 || d2 <= 0) {
      r1[i] = 0;
    } else {
      r1[i] = Math.sqrt((λ * d1 * d2) / (d1 + d2));
    }
    y_f1_top[i] = y_los[i] + r1[i];
    y_f1_bot[i] = y_los[i] - r1[i];
  }

  // Obstruction / worst Fresnel
  let clearanceMin = Infinity;
  let idxMin = -1;
  for (let i = 0; i < n; i++) {
    const clearance = y_los[i] - r1[i] - y_terrain[i];
    if (clearance < clearanceMin) {
      clearanceMin = clearance;
      idxMin = i;
    }
  }

  const obstruction: ObstructionInfo = { exists: clearanceMin < 0 };
  if (idxMin >= 0) {
    obstruction.at_m = x[idxMin];
    obstruction.clearance_min_m = clearanceMin;
    const denom = r1[idxMin] || 1e-9;
    obstruction.worst_f1 = clearanceMin / denom;
  }

  return {
    x_m: x,
    bulge_m: bulge,
    y_earth_m: y_earth,
    y_terrain_m: y_terrain,
    y_los_m: y_los,
    r1_m: r1,
    y_f1_top_m: y_f1_top,
    y_f1_bot_m: y_f1_bot,
    obstruction,
    distance_m: D,
  };
}

export function derive_header_metrics(args: {
  tx: LinkEndpoint;
  rx: LinkEndpoint;
  series: LinkProfileSeries;
}): LinkProfileDerived {
  const { tx, rx, series } = args;

  const az = bearing_deg(tx, rx);
  const D = series.distance_m;
  const elev = rad2deg(Math.atan2(series.y_los_m[series.y_los_m.length - 1] - series.y_los_m[0], D));

  return {
    distance_m: D,
    azimuth_deg: az,
    elev_angle_deg: elev,
    obstruction: series.obstruction,
  };
}
