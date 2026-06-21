export type TrafficLevel = "low" | "increased" | "moderate" | "heavy" | "extreme";

export interface TrafficRow {
  day: string; // DD.MM.YYYY
  traffic: TrafficLevel;
  parts: TrafficLevel[]; // length 6
  historical?: boolean;
}

const API_URL = "http://localhost:8000";

export const ROADS = [
  { id: "A8east",  label: "A8 East (→ Salzburg)",   corridor: "A8E",  direction: "outbound" },
  { id: "A8west",  label: "A8 West (→ Munich)",      corridor: "A8E",  direction: "inbound"  },
  { id: "A93south",label: "A93 South (→ Kufstein)",  corridor: "A93S", direction: "outbound" },
  { id: "A93north",label: "A93 North (→ Rosenheim)", corridor: "A93S", direction: "inbound"  },
] as const;

export type RoadId = (typeof ROADS)[number]["id"];

// Vivid forecast colours
export const TRAFFIC_COLORS: Record<TrafficLevel, string> = {
  low:       "#AFCCAA",
  increased: "#FADC81",
  moderate:  "#E67E22",
  heavy:     "#D83528",
  extreme:   "#A01919",
};

// Historical colours — faded toward white, bleached version of vivid palette
export const TRAFFIC_COLORS_HISTORICAL: Record<TrafficLevel, string> = {
  low:       "#DAECD8",
  increased: "#EDE8C8",
  moderate:  "#E4D0B4",
  heavy:     "#DBBCBC",
  extreme:   "#C8A0A0",
};

export const TRAFFIC_LABELS: Record<TrafficLevel, string> = {
  low:       "Low",
  increased: "Increased",
  moderate:  "Moderate",
  heavy:     "Heavy",
  extreme:   "Extreme",
};

export const SLOT_LABELS = [
  "00:00 – 06:00",
  "06:00 – 10:00",
  "10:00 – 14:00",
  "14:00 – 18:00",
  "18:00 – 22:00",
  "22:00 – 24:00",
] as const;

function categoryToLevel(cat: number): TrafficLevel {
  if (cat <= 1) return "low";
  if (cat === 2) return "increased";
  if (cat === 3) return "moderate";
  if (cat === 4) return "heavy";
  return "extreme";
}

function isoToKey(iso: string): string {
  const [y, m, d] = iso.split("-");
  return `${d}.${m}.${y}`;
}

const toISO = (d: Date) =>
  `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;

export async function fetchRoadData(
  roadId: RoadId,
  start: Date,
  end: Date,
): Promise<Map<string, TrafficRow>> {
  const road = ROADS.find((r) => r.id === roadId)!;

  const res = await fetch(`${API_URL}/api/forecast`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      corridor: road.corridor,
      direction: road.direction,
      date_from: toISO(start),
      date_to: toISO(end),
    }),
  });

  if (!res.ok) throw new Error(`Backend returned ${res.status}: ${res.statusText}`);
  const json = await res.json();
  if (!json.success) throw new Error("Backend forecast failed");

  const map = new Map<string, TrafficRow>();
  for (const day of json.forecast as Array<Record<string, unknown>>) {
    const dateKey = isoToKey(day.date as string);
    const dailyCat = day.daily_category as number;
    const slots = day.time_slots as Array<{ category: number }>;
    map.set(dateKey, {
      day: dateKey,
      traffic: categoryToLevel(dailyCat),
      parts: slots.map((s) => categoryToLevel(s.category)),
      historical: false,
    });
  }
  return map;
}

export async function fetchHistoricalData(
  roadId: RoadId,
  start: Date,
  end: Date,
): Promise<Map<string, TrafficRow>> {
  const road = ROADS.find((r) => r.id === roadId)!;
  const params = new URLSearchParams({
    corridor: road.corridor,
    direction: road.direction,
    date_from: toISO(start),
    date_to: toISO(end),
  });

  const res = await fetch(`${API_URL}/api/historical?${params}`);
  if (!res.ok) throw new Error(`Backend returned ${res.status}: ${res.statusText}`);
  const json = await res.json();
  if (!json.success) throw new Error("Historical data fetch failed");

  const map = new Map<string, TrafficRow>();
  for (const day of json.forecast as Array<Record<string, unknown>>) {
    const dateKey = isoToKey(day.date as string);
    const dailyCat = day.daily_category as number;
    const slots = day.time_slots as Array<{ category: number }>;
    map.set(dateKey, {
      day: dateKey,
      traffic: categoryToLevel(dailyCat),
      parts: slots.map((s) => categoryToLevel(s.category)),
      historical: true,
    });
  }
  return map;
}

export function formatDateKey(d: Date): string {
  const dd = String(d.getDate()).padStart(2, "0");
  const mm = String(d.getMonth() + 1).padStart(2, "0");
  const yyyy = d.getFullYear();
  return `${dd}.${mm}.${yyyy}`;
}

// Bavaria public holidays (fixed + computed)
function easterSunday(year: number): Date {
  const a = year % 19;
  const b = Math.floor(year / 100);
  const c = year % 100;
  const d = Math.floor(b / 4);
  const e = b % 4;
  const f = Math.floor((b + 8) / 25);
  const g = Math.floor((b - f + 1) / 3);
  const h = (19 * a + b - d - g + 15) % 30;
  const i = Math.floor(c / 4);
  const k = c % 4;
  const l = (32 + 2 * e + 2 * i - h - k) % 7;
  const m = Math.floor((a + 11 * h + 22 * l) / 451);
  const month = Math.floor((h + l - 7 * m + 114) / 31);
  const day = ((h + l - 7 * m + 114) % 31) + 1;
  return new Date(year, month - 1, day);
}

function addDays(d: Date, days: number): Date {
  const r = new Date(d);
  r.setDate(r.getDate() + days);
  return r;
}

export function bavariaHolidays(year: number): Set<string> {
  const easter = easterSunday(year);
  const set = new Set<string>();
  const add = (d: Date) => set.add(formatDateKey(d));
  add(new Date(year, 0, 1));
  add(new Date(year, 0, 6));
  add(addDays(easter, -2));
  add(addDays(easter, 1));
  add(new Date(year, 4, 1));
  add(addDays(easter, 39));
  add(addDays(easter, 50));
  add(addDays(easter, 60));
  add(new Date(year, 7, 15));
  add(new Date(year, 9, 3));
  add(new Date(year, 10, 1));
  add(new Date(year, 11, 25));
  add(new Date(year, 11, 26));
  return set;
}

export function isHolidayOrWeekend(d: Date, holidays: Set<string>): boolean {
  const day = d.getDay();
  if (day === 0 || day === 6) return true;
  return holidays.has(formatDateKey(d));
}
