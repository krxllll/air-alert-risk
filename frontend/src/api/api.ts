import axios from "axios";
import type {
  OblastRiskResponse,
  StatusItem,
  StatusesResponse,
  UaOblast,
  ApiOblastsRiskResponse,
  ApiRiskOblastItem,
  OblastRiskItem
} from "./types";

const baseURL = import.meta.env.VITE_API_BASE_URL ?? "/api";

export const api = axios.create({
  baseURL,
  timeout: 20000
});

export async function fetchOblastsList(): Promise<UaOblast[]> {
  const { data } = await api.get<UaOblast[]>("/ua/oblasts");
  return data;
}

export async function fetchOblastsRisk(horizonHours = 6): Promise<OblastRiskItem[]> {
  const r = await fetch(`${baseURL}/risk/oblasts?horizon_hours=${horizonHours}`);
  if (!r.ok) throw new Error(`API error: ${r.status}`);

  const data: ApiOblastsRiskResponse = await r.json();

  return (data.items ?? []).map((x: ApiRiskOblastItem) => ({
    uid: x.oblast_uid,
    name: x.oblast_name,
    risk: x.risk_any,
    expectedAlarmHours: x.expected_alarm_hours,
    peaks: (x.peak_hours ?? []).map(p => ({ ts: p.ts, pAlarm: p.p_alarm })),
    from: x.horizon_start,
    to: x.horizon_end,
    asOf: x.generated_at,
    hasData: x.has_data,
  }));
}

export async function fetchOblastRisk(
  uid: number,
  params: {
    horizons?: string;
    seriesHours?: number;
    modelVersion?: string;
  } = {}
): Promise<OblastRiskResponse> {
  const { horizons = "1,6,24,168", seriesHours = 168, modelVersion } = params;

  const { data } = await api.get<OblastRiskResponse>(`/risk/oblast/${uid}`, {
    params: {
      horizons,
      series_hours: seriesHours,
      model_version: modelVersion
    }
  });

  return data;
}

export async function fetchStatuses(): Promise<{
  meta: { origin?: string; mode?: string; updated_at?: number; ttl_seconds?: number };
  items: StatusItem[];
}> {
  const { data } = await api.get<StatusesResponse>("/ua/alerts/oblasts/statuses");

  if (Array.isArray(data)) {
    return { meta: {}, items: data };
  }

  return {
    meta: {
      origin: data.origin,
      mode: data.mode,
      updated_at: data.updated_at,
      ttl_seconds: (data as any).ttl_seconds
    },
    items: data.items
  };
}
