export type IsoTs = string;

/* =========================
 * API (backend responses)
 * ========================= */

export type ApiPeakHour = { ts: IsoTs; p_alarm: number };

export type ApiRiskSeriesPoint = { ts: IsoTs; p_alarm: number };

export type ApiOblastRiskSummaryItem = {
  risk_any: number;
  expected_alarm_hours: number;
  peak_hours: ApiPeakHour[];
};

export type ApiOblastRiskResponse = {
  oblast_uid: number;
  model_version: string;
  generated_at: IsoTs | null;

  horizon_start: IsoTs;
  horizon_end: IsoTs;

  series: ApiRiskSeriesPoint[];
  summary: Record<string, ApiOblastRiskSummaryItem>;
};

export type ApiRiskOblastItem = {
  oblast_uid: number;
  oblast_name: string;

  model_version: string;
  generated_at: IsoTs | null;

  horizon_start: IsoTs;
  horizon_end: IsoTs;

  risk_any: number | null;
  expected_alarm_hours: number | null;
  peak_hours: ApiPeakHour[];

  has_data: boolean;
};

export type ApiOblastsRiskResponse = {
  model_version: string;
  horizon_hours: number;
  horizon_start: IsoTs;
  horizon_end: IsoTs;
  items: ApiRiskOblastItem[];
};

export type UaOblast = { uid: number; name: string };

export type StatusItem = {
  uid: number;
  name: string;
  status: "active" | "inactive" | "unknown";
};

export type StatusesResponse =
  | StatusItem[]
  | {
      origin: string;
      mode: string;
      updated_at: number;
      ttl_seconds?: number;
      items: StatusItem[];
    };

/* =========================
 * UI (frontend models)
 * ========================= */

export type PeakHour = { ts: IsoTs; pAlarm: number };

export type HourlyPoint = { ts: IsoTs; p: number };

export type OblastRiskItem = {
  uid: number;
  name: string;

  risk: number | null;
  expectedAlarmHours: number | null;
  peaks: PeakHour[];

  from: IsoTs;
  to: IsoTs;
  asOf: IsoTs | null;

  hasData: boolean;
};

export type OblastRiskWindow = {
  hours: number;
  risk: number;
  expectedAlarmHours: number;
  peaks: PeakHour[];
  from: IsoTs;
  to: IsoTs;
};

export type OblastRiskResponse = {
  uid: number;
  modelVersion: string;
  generatedAt: IsoTs | null;

  name: string;
  nowStatus: StatusItem["status"] | "unknown";

  from: IsoTs;
  to: IsoTs;

  hourly: HourlyPoint[]; // з series
  windows: OblastRiskWindow[];
};