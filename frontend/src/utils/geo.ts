
export async function detectDefaultOblastUid(): Promise<number | null> {
  try {
    const r = await fetch("https://ipapi.co/json/");
    if (!r.ok) return null;
    const j = await r.json();

    const region = String(j?.region ?? "").toLowerCase();
    const city = String(j?.city ?? "").toLowerCase();

    if (city.includes("kyiv") || city.includes("київ")) return 31;
    if (region.includes("kyiv") || region.includes("київ")) return 14;

    return null;
  } catch {
    return null;
  }
}
