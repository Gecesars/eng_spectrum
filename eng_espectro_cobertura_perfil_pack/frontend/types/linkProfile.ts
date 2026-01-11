export type ProfileSample = {
  /** Distance from TX along the path (meters). Must be monotonic increasing. */
  d_m: number;
  /** Ground elevation (meters) relative to mean sea level (or consistent reference). */
  ground_m: number;
};

export type LinkEndpoint = {
  lat: number;
  lon: number;
  /** Antenna height above local ground (AGL), in meters. */
  h_ant_agl_m: number;
};

export type ObstructionInfo = {
  exists: boolean;
  /** Distance from TX (meters) where clearance is minimum. */
  at_m?: number;
  /** Clearance minimum in meters (negative if obstructed). */
  clearance_min_m?: number;
  /** Worst Fresnel as a fraction of F1 radius at the critical point. Negative means intrusion. */
  worst_f1?: number;
};

export type LinkProfileDerived = {
  distance_m: number;
  azimuth_deg: number;
  elev_angle_deg: number;
  obstruction: ObstructionInfo;
};

export type LinkProfileResponse = {
  tx: LinkEndpoint;
  rx: LinkEndpoint;
  freq_mhz: number;
  k_factor: number;
  step_m: number;
  samples: ProfileSample[];
  derived: LinkProfileDerived;
  /** Optional results from propagation model(s). */
  model_results?: {
    path_loss_db?: number;
    field_strength_dbuVm?: number;
    rx_level_dbm?: number;
    rx_relative_db?: number;
  };
};
