import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useMemo, useState } from "react";
import {
  ROADS,
  SLOT_LABELS,
  TRAFFIC_COLORS,
  TRAFFIC_COLORS_HISTORICAL,
  TRAFFIC_LABELS,
  bavariaHolidays,
  fetchRoadData,
  formatDateKey,
  type RoadId,
  type TrafficRow,
} from "@/lib/traffic";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "Bavaria Highway Traffic Calendar" },
      {
        name: "description",
        content:
          "Plan your trips on A8 and A93 with a daily and 6-hour interval traffic forecast across Bavaria.",
      },
    ],
  }),
  component: TrafficPage,
});

function parseInputDate(s: string): Date | null {
  if (!s) return null;
  const [y, m, d] = s.split("-").map(Number);
  if (!y || !m || !d) return null;
  return new Date(y, m - 1, d);
}

function formatInputDate(d: Date): string {
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${y}-${m}-${day}`;
}

const TODAY = (() => {
  const t = new Date();
  return new Date(t.getFullYear(), t.getMonth(), t.getDate());
})();

const UNIFIED_MIN = new Date(2023, 0, 1);
const UNIFIED_MIN_STR = "2023-01-01";
const UNIFIED_MAX = new Date(2027, 5, 30);
const UNIFIED_MAX_STR = "2027-06-30";

function monthLabel(d: Date): string {
  return d.toLocaleDateString("en-US", { month: "long", year: "numeric" });
}

function monthsBetween(start: Date, end: Date): Date[] {
  const out: Date[] = [];
  let cur = new Date(start.getFullYear(), start.getMonth(), 1);
  const last = new Date(end.getFullYear(), end.getMonth(), 1);
  while (cur <= last) {
    out.push(new Date(cur));
    cur = new Date(cur.getFullYear(), cur.getMonth() + 1, 1);
  }
  return out;
}

function TrafficPage() {
  const [road, setRoad] = useState<RoadId>("A8east");
  const [startStr, setStartStr] = useState(formatInputDate(TODAY));
  const [endStr, setEndStr] = useState(() => {
    const d = new Date(TODAY.getFullYear(), TODAY.getMonth() + 1, TODAY.getDate());
    return formatInputDate(d < UNIFIED_MAX ? d : UNIFIED_MAX);
  });

  const [submitted, setSubmitted] = useState<{
    road: RoadId;
    start: Date;
    end: Date;
  } | null>(null);

  const [rows, setRows] = useState<Map<string, TrafficRow>>(new Map());
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedDay, setSelectedDay] = useState<Date | null>(null);
  const [hoveredDay, setHoveredDay] = useState<Date | null>(null);
  const [popupAnchor, setPopupAnchor] = useState<{ top: number; left: number } | null>(null);

  useEffect(() => {
    if (!submitted) return;
    setLoading(true);
    setError(null);

    // Expand to the 1st of the start month so every day in the first visible
    // calendar month gets a colour, even days before the chosen "From" date.
    const monthStart = new Date(submitted.start.getFullYear(), submitted.start.getMonth(), 1);

    fetchRoadData(submitted.road, monthStart, submitted.end)
      .then(setRows)
      .catch((e: Error) =>
        setError(
          e.message.includes("fetch")
            ? "Cannot reach the backend. Make sure it's running on http://localhost:8000."
            : e.message,
        ),
      )
      .finally(() => setLoading(false));
  }, [submitted]);

  const holidaysByYear = useMemo(() => {
    if (!submitted) return new Map<number, Set<string>>();
    const m = new Map<number, Set<string>>();
    for (let y = submitted.start.getFullYear(); y <= submitted.end.getFullYear(); y++) {
      m.set(y, bavariaHolidays(y));
    }
    return m;
  }, [submitted]);

  const months = useMemo(
    () => (submitted ? monthsBetween(submitted.start, submitted.end) : []),
    [submitted],
  );

  const onSearch = (e: React.FormEvent) => {
    e.preventDefault();
    const s = parseInputDate(startStr);
    const en = parseInputDate(endStr);
    if (!s || !en || s > en) { setError("Please pick a valid date range."); return; }
    if (s < UNIFIED_MIN) { setError(`Start date cannot be before ${UNIFIED_MIN_STR}.`); return; }
    if (en > UNIFIED_MAX) { setError(`End date cannot be after ${UNIFIED_MAX_STR}.`); return; }
    if ((en.getTime() - s.getTime()) / 86400000 > 366) {
      setError("Date range must not exceed 366 days."); return;
    }
    setError(null);
    setSelectedDay(null);
    setHoveredDay(null);
    setPopupAnchor(null);
    setSubmitted({ road, start: s, end: en });
  };

  const selectedRow = selectedDay ? rows.get(formatDateKey(selectedDay)) : null;
  const hoveredRow = hoveredDay ? rows.get(formatDateKey(hoveredDay)) : null;

  const onHover = (d: Date | null, rect: DOMRect | null) => {
    if (!d || !rect) { setHoveredDay(null); setPopupAnchor(null); return; }
    const POPUP_W = 288;
    const POPUP_H = 300;
    const spaceRight = window.innerWidth - rect.right;
    const left = spaceRight > POPUP_W + 16 ? rect.right + 8 : rect.left - POPUP_W - 8;
    const top = Math.max(8, Math.min(rect.top, window.innerHeight - POPUP_H - 8));
    setHoveredDay(d);
    setPopupAnchor({ top, left });
  };

  return (
    <div className="min-h-screen bg-background text-foreground">
      <header className="border-b border-border bg-card">
        <div className="mx-auto flex max-w-6xl items-center gap-3 px-4 py-2">
          <img src="/Logo.svg" alt="Logo" className="h-8 w-auto" />
          <div>
            <h1 className="text-base font-semibold leading-tight">Bavaria Highway Traffic</h1>
            <p className="text-xs text-muted-foreground leading-tight">Alpine corridor</p>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-6xl px-4 py-3">
        <form
          onSubmit={onSearch}
          className="flex flex-wrap items-center gap-3 rounded-xl border border-border bg-card px-4 py-3 shadow-sm"
        >
          <select
            value={road}
            onChange={(e) => setRoad(e.target.value as RoadId)}
            className="h-8 flex-1 min-w-[160px] rounded-md border border-input bg-background px-2 text-sm"
          >
            {ROADS.map((r) => (
              <option key={r.id} value={r.id}>{r.label}</option>
            ))}
          </select>
          <input
            type="date"
            value={startStr}
            min={UNIFIED_MIN_STR}
            max={UNIFIED_MAX_STR}
            onChange={(e) => setStartStr(e.target.value)}
            className="h-8 rounded-md border border-input bg-background px-2 text-sm"
          />
          <span className="text-xs text-muted-foreground">—</span>
          <input
            type="date"
            value={endStr}
            min={startStr || UNIFIED_MIN_STR}
            max={UNIFIED_MAX_STR}
            onChange={(e) => setEndStr(e.target.value)}
            className="h-8 rounded-md border border-input bg-background px-2 text-sm"
          />
          <button
            type="submit"
            className="h-8 rounded-md bg-primary px-4 text-sm font-medium text-primary-foreground hover:bg-primary/90"
          >
            Search
          </button>
        </form>

        <Legend />

        {error && (
          <div className="mt-4 rounded-md border border-destructive/30 bg-destructive/10 p-3 text-sm text-destructive">
            {error}
          </div>
        )}
        {loading && <p className="mt-4 text-sm text-muted-foreground">Loading traffic data…</p>}

        {submitted && !loading && (
          <div className="mt-6 grid gap-6 lg:grid-cols-[1fr_320px]">
            <div className="space-y-6">
              {months.map((m) => (
                <MonthCalendar
                  key={m.toISOString()}
                  month={m}
                  end={submitted.end}
                  rows={rows}
                  holidaysByYear={holidaysByYear}
                  selectedDay={selectedDay}
                  onSelect={setSelectedDay}
                  onHover={onHover}
                />
              ))}
            </div>
            <aside className="lg:sticky lg:top-6 lg:self-start">
              <DayDetail day={selectedDay} row={selectedRow ?? null} />
            </aside>
          </div>
        )}

        {hoveredDay && hoveredRow && popupAnchor && (
          <DayPopup day={hoveredDay} row={hoveredRow} anchor={popupAnchor} />
        )}
      </main>
    </div>
  );
}

function Legend() {
  return (
    <div className="mt-4 flex flex-wrap items-center gap-3 text-xs text-muted-foreground">
      {(["low", "increased", "moderate", "heavy", "extreme"] as const).map((l) => (
        <span key={l} className="inline-flex items-center gap-1.5">
          <span className="inline-block h-3 w-3 rounded-sm" style={{ backgroundColor: TRAFFIC_COLORS[l] }} />
          {TRAFFIC_LABELS[l]}
        </span>
      ))}
      <span className="inline-flex items-center gap-1.5">
        <span className="relative inline-block h-3 w-3 rounded-sm bg-muted">
          <span className="absolute right-0 top-0 flex h-[9px] w-[9px] -translate-y-px translate-x-px items-center justify-center rounded-full text-[6px] font-bold leading-none" style={{ backgroundColor: "rgba(255,255,255,0.45)", color: "rgba(0,0,0,0.75)" }}>7</span>
        </span>
        Weekend / holiday
      </span>
    </div>
  );
}

function MonthCalendar({
  month, end, rows, holidaysByYear, selectedDay, onSelect, onHover,
}: {
  month: Date;
  end: Date;
  rows: Map<string, TrafficRow>;
  holidaysByYear: Map<number, Set<string>>;
  selectedDay: Date | null;
  onSelect: (d: Date) => void;
  onHover: (d: Date | null, rect: DOMRect | null) => void;
}) {
  const year = month.getFullYear();
  const mon = month.getMonth();
  const first = new Date(year, mon, 1);
  const last = new Date(year, mon + 1, 0);
  const startOffset = (first.getDay() + 6) % 7;
  const totalCells = Math.ceil((startOffset + last.getDate()) / 7) * 7;

  const cells: Array<Date | null> = [];
  for (let i = 0; i < totalCells; i++) {
    const dayNum = i - startOffset + 1;
    if (dayNum < 1 || dayNum > last.getDate()) cells.push(null);
    else cells.push(new Date(year, mon, dayNum));
  }

  const weekDays = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];

  return (
    <section className="rounded-xl border border-border bg-card px-4 pt-3 pb-4 shadow-sm">
      <h2 className="mb-2 text-sm font-semibold">{monthLabel(month)}</h2>
      <div className="grid grid-cols-7 gap-1 text-xs font-medium text-muted-foreground">
        {weekDays.map((d) => (
          <div key={d} className="py-0.5 text-center">{d}</div>
        ))}
      </div>
      <div className="mt-1 grid grid-cols-7 gap-1">
        {cells.map((d, i) => {
          if (!d) return <div key={i} />;
          const afterEnd = d > stripTime(end);
          const isPast = d < TODAY;
          const colors = isPast ? TRAFFIC_COLORS_HISTORICAL : TRAFFIC_COLORS;
          const key = formatDateKey(d);
          const row = rows.get(key);
          const holidays = holidaysByYear.get(d.getFullYear()) ?? new Set<string>();
          const isWeekend = d.getDay() === 0 || d.getDay() === 6;
          const isHoliday = holidays.has(key);
          const isSpecial = (isWeekend || isHoliday) && !afterEnd;
          const bg = !afterEnd && row ? colors[row.traffic] : "transparent";
          const isSelected = selectedDay && formatDateKey(selectedDay) === key;
          const darkText = !isPast && row && (row.traffic === "heavy" || row.traffic === "extreme");
          return (
            <button
              key={i}
              type="button"
              onClick={() => !afterEnd && onSelect(d)}
              onMouseEnter={
                !afterEnd && row
                  ? (e) => onHover(d, (e.currentTarget as HTMLElement).getBoundingClientRect())
                  : undefined
              }
              onMouseLeave={!afterEnd && row ? () => onHover(null, null) : undefined}
              disabled={afterEnd}
              className={[
                "relative aspect-square rounded-md transition",
                !afterEnd ? "cursor-pointer hover:brightness-95" : "cursor-not-allowed opacity-30",
                isSelected ? "outline outline-2 outline-foreground" : "",
              ].join(" ")}
              style={{
                backgroundColor: afterEnd ? "var(--muted)" : (row ? bg : "var(--muted)"),
                color: !afterEnd && darkText ? "white" : undefined,
              }}
              title={row ? TRAFFIC_LABELS[row.traffic] : "No traffic data available."}
            >
              {isSpecial ? (
                <span
                  className="absolute left-1 top-0.5 flex h-[18px] w-[18px] items-center justify-center rounded-full text-[10px] font-bold leading-none"
                  style={{ backgroundColor: "rgba(255,255,255,0.45)", color: "rgba(0,0,0,0.75)" }}
                >
                  {d.getDate()}
                </span>
              ) : (
                <span className="absolute left-1.5 top-1 text-[11px] font-semibold">{d.getDate()}</span>
              )}
            </button>
          );
        })}
      </div>
    </section>
  );
}

function stripTime(d: Date): Date {
  return new Date(d.getFullYear(), d.getMonth(), d.getDate());
}

function SlotList({ parts, isPast }: { parts: TrafficRow["parts"]; isPast: boolean }) {
  const colors = isPast ? TRAFFIC_COLORS_HISTORICAL : TRAFFIC_COLORS;
  return (
    <ul className="mt-3 space-y-1.5">
      {parts.map((p, i) => (
        <li
          key={i}
          className="flex items-center justify-between rounded-md px-3 py-2 text-sm"
          style={{
            backgroundColor: colors[p],
            color: !isPast && (p === "heavy" || p === "extreme") ? "white" : "#111",
          }}
        >
          <span className="font-medium">{SLOT_LABELS[i]}</span>
          <span className="text-xs opacity-90">{TRAFFIC_LABELS[p]}</span>
        </li>
      ))}
    </ul>
  );
}

function DayDetail({ day, row }: { day: Date | null; row: TrafficRow | null }) {
  const isPast = day ? day < TODAY : false;
  const colors = isPast ? TRAFFIC_COLORS_HISTORICAL : TRAFFIC_COLORS;
  if (!day) {
    return (
      <div className="rounded-xl border border-dashed border-border p-6 text-sm text-muted-foreground">
        Click a day on the calendar to pin it here. Hover any day to preview it.
      </div>
    );
  }
  const title = day.toLocaleDateString("en-GB", {
    weekday: "long", day: "2-digit", month: "long", year: "numeric",
  });
  return (
    <div className="rounded-xl border border-border bg-card p-5 shadow-sm">
      <div className="mb-1 text-[10px] font-semibold uppercase tracking-widest text-muted-foreground">
        {isPast ? "Pinned — historical" : "Pinned day"}
      </div>
      <h3 className="text-sm font-semibold">{title}</h3>
      {!row ? (
        <p className="mt-3 text-sm text-muted-foreground">No traffic data available.</p>
      ) : (
        <>
          <div className="mt-2 inline-flex items-center gap-2 text-xs">
            <span className="inline-block h-3 w-3 rounded-sm" style={{ backgroundColor: colors[row.traffic] }} />
            <span className="text-muted-foreground">Daily average:</span>
            <span className="font-medium">{TRAFFIC_LABELS[row.traffic]}</span>
          </div>
          <SlotList parts={row.parts} isPast={isPast} />
        </>
      )}
    </div>
  );
}

function DayPopup({
  day, row, anchor,
}: {
  day: Date;
  row: TrafficRow;
  anchor: { top: number; left: number };
}) {
  const isPast = day < TODAY;
  const colors = isPast ? TRAFFIC_COLORS_HISTORICAL : TRAFFIC_COLORS;
  const title = day.toLocaleDateString("en-GB", {
    weekday: "long", day: "2-digit", month: "long", year: "numeric",
  });
  return (
    <div
      className="pointer-events-none fixed z-50 w-72 rounded-xl border border-border bg-card p-4 shadow-2xl"
      style={{ top: anchor.top, left: anchor.left }}
    >
      <div className="mb-1 text-[10px] font-semibold uppercase tracking-widest text-muted-foreground">
        {isPast ? "Historical preview" : "Hover preview"}
      </div>
      <h3 className="text-sm font-semibold">{title}</h3>
      <div className="mt-1.5 inline-flex items-center gap-2 text-xs">
        <span className="inline-block h-3 w-3 rounded-sm" style={{ backgroundColor: colors[row.traffic] }} />
        <span className="text-muted-foreground">Daily average:</span>
        <span className="font-medium">{TRAFFIC_LABELS[row.traffic]}</span>
      </div>
      <SlotList parts={row.parts} isPast={isPast} />
    </div>
  );
}
