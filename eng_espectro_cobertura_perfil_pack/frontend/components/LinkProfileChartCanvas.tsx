import React, { useEffect, useMemo, useRef } from "react";
import type { LinkProfileResponse } from "../types/linkProfile";
import { build_profile_series } from "../lib/linkProfileMath";

type Props = {
  data: LinkProfileResponse;
  /** Visual vertical exaggeration (1 = true scale). */
  verticalExaggeration?: number;
  /** Show Fresnel zone curves. */
  showFresnel?: boolean;
  /** Canvas height in px */
  height?: number;
};

type Bounds = {
  xMin: number;
  xMax: number;
  yMin: number;
  yMax: number;
};

function clamp(v: number, a: number, b: number): number {
  return Math.max(a, Math.min(b, v));
}

function niceTicks(min: number, max: number, targetTicks: number): number[] {
  const span = max - min;
  if (!(span > 0)) return [min];

  const raw = span / targetTicks;
  const pow10 = Math.pow(10, Math.floor(Math.log10(raw)));
  const candidates = [1, 2, 5, 10].map((m) => m * pow10);
  const step = candidates.reduce((best, c) => (Math.abs(c - raw) < Math.abs(best - raw) ? c : best), candidates[0]);

  const start = Math.ceil(min / step) * step;
  const ticks: number[] = [];
  for (let v = start; v <= max + 1e-9; v += step) ticks.push(v);
  return ticks;
}

export function LinkProfileChartCanvas({
  data,
  verticalExaggeration = 1,
  showFresnel = true,
  height = 320,
}: Props) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  const series = useMemo(() => {
    return build_profile_series({
      samples: data.samples,
      tx: data.tx,
      rx: data.rx,
      freq_mhz: data.freq_mhz,
      k_factor: data.k_factor,
      y_base_padding_m: 60,
    });
  }, [data]);

  const bounds: Bounds = useMemo(() => {
    const n = series.x_m.length;
    const xMin = 0;
    const xMax = series.distance_m;

    let yMin = Infinity;
    let yMax = -Infinity;

    for (let i = 0; i < n; i++) {
      yMin = Math.min(yMin, series.y_earth_m[i], series.y_terrain_m[i]);
      yMax = Math.max(yMax, series.y_terrain_m[i], series.y_los_m[i]);
      if (showFresnel) {
        yMax = Math.max(yMax, series.y_f1_top_m[i]);
        yMin = Math.min(yMin, series.y_f1_bot_m[i]);
      }
    }

    // Expand a bit for aesthetics
    const pad = Math.max(20, 0.05 * (yMax - yMin));
    return { xMin, xMax, yMin: yMin - pad, yMax: yMax + pad };
  }, [series, showFresnel]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    // Handle HiDPI
    const parent = canvas.parentElement;
    const widthCss = parent ? parent.clientWidth : 800;
    const dpr = window.devicePixelRatio || 1;

    canvas.width = Math.floor(widthCss * dpr);
    canvas.height = Math.floor(height * dpr);
    canvas.style.width = `${widthCss}px`;
    canvas.style.height = `${height}px`;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);

    const W = widthCss;
    const H = height;

    // Layout
    const mL = 56;
    const mR = 18;
    const mT = 18;
    const mB = 32;
    const plotW = W - mL - mR;
    const plotH = H - mT - mB;

    const xScale = (x: number) => mL + ((x - bounds.xMin) / (bounds.xMax - bounds.xMin)) * plotW;

    // Apply vertical exaggeration around the midline to keep things stable:
    const yMid = 0.5 * (bounds.yMin + bounds.yMax);
    const yEx = (y: number) => yMid + (y - yMid) * verticalExaggeration;

    const yScale = (y: number) => {
      const yy = yEx(y);
      return mT + (1 - (yy - bounds.yMin) / (bounds.yMax - bounds.yMin)) * plotH;
    };

    // Background
    ctx.clearRect(0, 0, W, H);
    ctx.fillStyle = "#ffffff";
    ctx.fillRect(0, 0, W, H);

    // Grid & axes
    const xTicksKm = niceTicks(bounds.xMin / 1000, bounds.xMax / 1000, 6);
    const yTicks = niceTicks(bounds.yMin, bounds.yMax, 5);

    // Grid lines
    ctx.lineWidth = 1;

    // X grid
    ctx.strokeStyle = "rgba(0,0,0,0.08)";
    for (const tKm of xTicksKm) {
      const x = xScale(tKm * 1000);
      ctx.beginPath();
      ctx.moveTo(x, mT);
      ctx.lineTo(x, mT + plotH);
      ctx.stroke();
    }

    // Y grid
    for (const t of yTicks) {
      const y = yScale(t);
      ctx.beginPath();
      ctx.moveTo(mL, y);
      ctx.lineTo(mL + plotW, y);
      ctx.stroke();
    }

    // Axes
    ctx.strokeStyle = "rgba(0,0,0,0.35)";
    ctx.beginPath();
    ctx.moveTo(mL, mT);
    ctx.lineTo(mL, mT + plotH);
    ctx.lineTo(mL + plotW, mT + plotH);
    ctx.stroke();

    // Tick labels
    ctx.fillStyle = "rgba(0,0,0,0.75)";
    ctx.font = "12px system-ui, -apple-system, Segoe UI, Roboto, Arial";
    ctx.textAlign = "center";
    ctx.textBaseline = "top";
    for (const tKm of xTicksKm) {
      const x = xScale(tKm * 1000);
      ctx.fillText(`${tKm.toFixed(0)} km`, x, mT + plotH + 6);
    }

    ctx.textAlign = "right";
    ctx.textBaseline = "middle";
    for (const t of yTicks) {
      const y = yScale(t);
      ctx.fillText(`${Math.round(t)} m`, mL - 8, y);
    }

    const n = series.x_m.length;

    // --- Fill: earth bulge (dark) ---
    ctx.beginPath();
    // Start at left base
    ctx.moveTo(xScale(series.x_m[0]), yScale(bounds.yMin));
    for (let i = 0; i < n; i++) {
      ctx.lineTo(xScale(series.x_m[i]), yScale(series.y_earth_m[i]));
    }
    // Close to right base
    ctx.lineTo(xScale(series.x_m[n - 1]), yScale(bounds.yMin));
    ctx.closePath();
    ctx.fillStyle = "rgba(110, 70, 35, 0.55)";
    ctx.fill();

    // --- Fill: terrain above earth (light) ---
    ctx.beginPath();
    ctx.moveTo(xScale(series.x_m[0]), yScale(series.y_earth_m[0]));
    for (let i = 0; i < n; i++) {
      ctx.lineTo(xScale(series.x_m[i]), yScale(series.y_terrain_m[i]));
    }
    for (let i = n - 1; i >= 0; i--) {
      ctx.lineTo(xScale(series.x_m[i]), yScale(series.y_earth_m[i]));
    }
    ctx.closePath();
    ctx.fillStyle = "rgba(185, 120, 55, 0.55)";
    ctx.fill();

    // Terrain outline
    ctx.strokeStyle = "rgba(90,60,30,0.65)";
    ctx.lineWidth = 1.2;
    ctx.beginPath();
    ctx.moveTo(xScale(series.x_m[0]), yScale(series.y_terrain_m[0]));
    for (let i = 1; i < n; i++) {
      ctx.lineTo(xScale(series.x_m[i]), yScale(series.y_terrain_m[i]));
    }
    ctx.stroke();

    // Fresnel (optional)
    if (showFresnel) {
      ctx.strokeStyle = "rgba(0,0,0,0.25)";
      ctx.lineWidth = 1;

      ctx.beginPath();
      ctx.moveTo(xScale(series.x_m[0]), yScale(series.y_f1_top_m[0]));
      for (let i = 1; i < n; i++) ctx.lineTo(xScale(series.x_m[i]), yScale(series.y_f1_top_m[i]));
      ctx.stroke();

      ctx.beginPath();
      ctx.moveTo(xScale(series.x_m[0]), yScale(series.y_f1_bot_m[0]));
      for (let i = 1; i < n; i++) ctx.lineTo(xScale(series.x_m[i]), yScale(series.y_f1_bot_m[i]));
      ctx.stroke();
    }

    // LOS line (red)
    ctx.strokeStyle = "rgba(210, 40, 40, 0.95)";
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(xScale(series.x_m[0]), yScale(series.y_los_m[0]));
    ctx.lineTo(xScale(series.x_m[n - 1]), yScale(series.y_los_m[n - 1]));
    ctx.stroke();

    // Obstruction marker
    if (series.obstruction.exists && typeof series.obstruction.at_m === "number") {
      const xObs = series.obstruction.at_m;
      const px = xScale(xObs);

      // Vertical line
      ctx.strokeStyle = "rgba(0,0,0,0.35)";
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.moveTo(px, mT);
      ctx.lineTo(px, mT + plotH);
      ctx.stroke();

      // Label
      const km = xObs / 1000;
      const worst = series.obstruction.worst_f1 ?? 0;

      ctx.fillStyle = "rgba(0,0,0,0.8)";
      ctx.font = "12px system-ui, -apple-system, Segoe UI, Roboto, Arial";
      ctx.textAlign = "left";
      ctx.textBaseline = "top";
      ctx.fillText(`Obstruction @ ${km.toFixed(2)} km`, clamp(px + 8, mL + 4, mL + plotW - 4), mT + 4);
      ctx.fillText(`Worst Fresnel: ${worst.toFixed(2)} F1`, clamp(px + 8, mL + 4, mL + plotW - 4), mT + 18);
    }

    // Title (small)
    ctx.fillStyle = "rgba(0,0,0,0.75)";
    ctx.font = "13px system-ui, -apple-system, Segoe UI, Roboto, Arial";
    ctx.textAlign = "left";
    ctx.textBaseline = "bottom";
    ctx.fillText("Perfil do Enlace (com curvatura efetiva da Terra)", mL, mT - 4);
  }, [series, bounds, verticalExaggeration, showFresnel, height]);

  return (
    <div style={{ width: "100%" }}>
      <canvas ref={canvasRef} />
    </div>
  );
}
