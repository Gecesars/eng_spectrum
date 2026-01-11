import React, { useMemo } from "react";
import type { LinkProfileResponse } from "../types/linkProfile";
import { build_profile_series, derive_header_metrics } from "../lib/linkProfileMath";
import { LinkProfileChartCanvas } from "./LinkProfileChartCanvas";

type Props = {
  data: LinkProfileResponse;
  onClose?: () => void;
};

function fmt(n: number, digits = 2) {
  return Number.isFinite(n) ? n.toFixed(digits) : "—";
}

export function LinkProfilePanel({ data, onClose }: Props) {
  const series = useMemo(
    () =>
      build_profile_series({
        samples: data.samples,
        tx: data.tx,
        rx: data.rx,
        freq_mhz: data.freq_mhz,
        k_factor: data.k_factor,
      }),
    [data]
  );

  const header = useMemo(() => derive_header_metrics({ tx: data.tx, rx: data.rx, series }), [data, series]);

  const distKm = header.distance_m / 1000;

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        gap: 10,
        padding: 14,
        borderRadius: 14,
        border: "1px solid rgba(0,0,0,0.10)",
        background: "rgba(255,255,255,0.98)",
        boxShadow: "0 12px 30px rgba(0,0,0,0.12)",
      }}
    >
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 10 }}>
        <div style={{ display: "flex", flexWrap: "wrap", gap: 10, alignItems: "center" }}>
          <strong style={{ fontSize: 14 }}>Radio Link</strong>
          <span style={{ opacity: 0.7 }}>Azimuth: {fmt(header.azimuth_deg, 1)}°</span>
          <span style={{ opacity: 0.7 }}>Distance: {fmt(distKm, 2)} km</span>
          <span style={{ opacity: 0.7 }}>Elev: {fmt(header.elev_angle_deg, 3)}°</span>
          <span style={{ opacity: 0.7 }}>f: {fmt(data.freq_mhz, 1)} MHz</span>
          <span style={{ opacity: 0.7 }}>k: {fmt(data.k_factor, 3)}</span>

          {header.obstruction.exists && typeof header.obstruction.at_m === "number" ? (
            <>
              <span style={{ opacity: 0.85 }}>
                Obstruction: {fmt(header.obstruction.at_m / 1000, 2)} km
              </span>
              <span style={{ opacity: 0.85 }}>
                Worst Fresnel: {fmt(header.obstruction.worst_f1 ?? 0, 2)} F1
              </span>
            </>
          ) : (
            <span style={{ opacity: 0.85 }}>Obstruction: none</span>
          )}

          {data.model_results?.path_loss_db != null ? (
            <span style={{ opacity: 0.85 }}>PathLoss: {fmt(data.model_results.path_loss_db, 1)} dB</span>
          ) : null}
          {data.model_results?.field_strength_dbuVm != null ? (
            <span style={{ opacity: 0.85 }}>E: {fmt(data.model_results.field_strength_dbuVm, 1)} dBµV/m</span>
          ) : null}
          {data.model_results?.rx_level_dbm != null ? (
            <span style={{ opacity: 0.85 }}>Rx: {fmt(data.model_results.rx_level_dbm, 1)} dBm</span>
          ) : null}
          {data.model_results?.rx_relative_db != null ? (
            <span style={{ opacity: 0.85 }}>Rx Rel: {fmt(data.model_results.rx_relative_db, 1)} dB</span>
          ) : null}
        </div>

        {onClose ? (
          <button
            type="button"
            onClick={onClose}
            style={{
              border: "1px solid rgba(0,0,0,0.12)",
              background: "white",
              borderRadius: 10,
              padding: "6px 10px",
              cursor: "pointer",
            }}
          >
            Fechar
          </button>
        ) : null}
      </div>

      <LinkProfileChartCanvas data={data} showFresnel={true} verticalExaggeration={1} height={320} />
    </div>
  );
}
