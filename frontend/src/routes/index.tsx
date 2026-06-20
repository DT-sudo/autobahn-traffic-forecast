import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useMemo, useState } from "react";
import {
  ROADS,
  SLOT_LABELS,
  TRAFFIC_COLORS,
  TRAFFIC_LABELS,
  bavariaHolidays,
  fetchRoadData,
  formatDateKey,
  isHolidayOrWeekend,
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
  // input type=date returns YYYY-MM-DD
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

const MAX_DATE = new Date(2027, 5, 30);
const MAX_STR = "2027-06-30";

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
  const MIN_DATE = useMemo(() => {
    const t = new Date();
    return new Date(t.getFullYear(), t.getMonth(), t.getDate());
  }, []);
  const MIN_STR = formatInputDate(MIN_DATE);

  const initialStart = MIN_DATE;
  const initialEnd = new Date(
    Math.min(
      new Date(initialStart.getFullYear(), initialStart.getMonth() + 1, initialStart.getDate()).getTime(),
      MAX_DATE.getTime(),
    ),
  );

  const [road, setRoad] = useState<RoadId>("A8east");
  const [startStr, setStartStr] = useState(formatInputDate(initialStart));
  const [endStr, setEndStr] = useState(formatInputDate(initialEnd));
  const [submitted, setSubmitted] = useState<{
    road: RoadId;
    start: Date;
    end: Date;
  } | null>({
    road: "A8east",
    start: initialStart,
    end: initialEnd,
  });
  const [rows, setRows] = useState<Map<string, TrafficRow>>(new Map());
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedDay, setSelectedDay] = useState<Date | null>(null);

  useEffect(() => {
    if (!submitted) return;
    setLoading(true);
    setError(null);
    fetchRoadData(submitted.road, submitted.start, submitted.end)
      .then((data) => setRows(data))
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
    if (!s || !en || s > en) {
      setError("Please pick a valid date range.");
      return;
    }
    if (s < MIN_DATE) {
      setError("Start date cannot be in the past.");
      return;
    }
    if (en > MAX_DATE) {
      setError("End date cannot be after 30 June 2027 (last available data).");
      return;
    }
    setError(null);
    setSelectedDay(null);
    setSubmitted({ road, start: s, end: en });
  };

  const selectedRow = selectedDay ? rows.get(formatDateKey(selectedDay)) : null;

  return (
    <div className="min-h-screen bg-background text-foreground">
      <header className="border-b border-border bg-card">
        <div className="mx-auto flex max-w-6xl items-center gap-4 px-6 py-4">
          <img src="/Logo.svg" alt="Logo" className="h-10 w-auto" />
          <div>
            <h1 className="text-lg font-semibold">Bavaria Highway Traffic</h1>
            <p className="text-xs text-muted-foreground">
              A8 &amp; A93 daily and time-slot forecast
            </p>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-6xl px-6 py-8">
        <form
          onSubmit={onSearch}
          className="grid gap-4 rounded-xl border border-border bg-card p-5 shadow-sm sm:grid-cols-[1fr_1fr_1fr_auto]"
        >
          <label className="flex flex-col gap-1 text-sm">
            <span className="font-medium">Road</span>
            <select
              value={road}
              onChange={(e) => setRoad(e.target.value as RoadId)}
              className="h-10 rounded-md border border-input bg-background px-3 text-sm"
            >
              {ROADS.map((r) => (
                <option key={r.id} value={r.id}>
                  {r.label}
                </option>
              ))}
            </select>
          </label>
          <label className="flex flex-col gap-1 text-sm">
            <span className="font-medium">From</span>
            <input
              type="date"
              value={startStr}
              min={MIN_STR}
              max={MAX_STR}
              onChange={(e) => setStartStr(e.target.value)}
              className="h-10 rounded-md border border-input bg-background px-3 text-sm"
            />
          </label>
          <label className="flex flex-col gap-1 text-sm">
            <span className="font-medium">To</span>
            <input
              type="date"
              value={endStr}
              min={startStr || MIN_STR}
              max={MAX_STR}
              onChange={(e) => setEndStr(e.target.value)}
              className="h-10 rounded-md border border-input bg-background px-3 text-sm"
            />
          </label>
          <div className="flex items-end">
            <button
              type="submit"
              className="h-10 rounded-md bg-primary px-5 text-sm font-medium text-primary-foreground hover:bg-primary/90"
            >
              Search
            </button>
          </div>
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
                  start={submitted.start}
                  end={submitted.end}
                  rows={rows}
                  holidaysByYear={holidaysByYear}
                  selectedDay={selectedDay}
                  onSelect={setSelectedDay}
                />
              ))}
            </div>
            <aside className="lg:sticky lg:top-6 lg:self-start">
              <DayDetail day={selectedDay} row={selectedRow ?? null} />
            </aside>
          </div>
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
          <span
            className="inline-block h-3 w-3 rounded-sm"
            style={{ backgroundColor: TRAFFIC_COLORS[l] }}
          />
          {TRAFFIC_LABELS[l]}
        </span>
      ))}
      <span className="inline-flex items-center gap-1.5">
        <span className="inline-block h-3 w-3 rounded-sm border-2 border-blue-500" />
        Weekend / Bavarian holiday
      </span>
    </div>
  );
}

function MonthCalendar({
  month,
  start,
  end,
  rows,
  holidaysByYear,
  selectedDay,
  onSelect,
}: {
  month: Date;
  start: Date;
  end: Date;
  rows: Map<string, TrafficRow>;
  holidaysByYear: Map<number, Set<string>>;
  selectedDay: Date | null;
  onSelect: (d: Date) => void;
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
    <section className="rounded-xl border border-border bg-card p-5 shadow-sm">
      <h2 className="mb-4 text-base font-semibold">{monthLabel(month)}</h2>
      <div className="grid grid-cols-7 gap-1.5 text-xs font-medium text-muted-foreground">
        {weekDays.map((d) => (
          <div key={d} className="px-1 py-1 text-center">
            {d}
          </div>
        ))}
      </div>
      <div className="mt-1 grid grid-cols-7 gap-1.5">
        {cells.map((d, i) => {
          if (!d) return <div key={i} />;
          const inRange = d >= stripTime(start) && d <= stripTime(end);
          const key = formatDateKey(d);
          const row = rows.get(key);
          const holidays = holidaysByYear.get(d.getFullYear()) ?? new Set<string>();
          const flagged = isHolidayOrWeekend(d, holidays);
          const bg = inRange && row ? TRAFFIC_COLORS[row.traffic] : "transparent";
          const isSelected = selectedDay && formatDateKey(selectedDay) === key;
          const darkText = row && (row.traffic === "heavy" || row.traffic === "extreme");
          return (
            <button
              key={i}
              type="button"
              onClick={() => inRange && onSelect(d)}
              disabled={!inRange}
              className={[
                "relative aspect-square rounded-md text-sm transition",
                inRange
                  ? "cursor-pointer hover:ring-2 hover:ring-foreground/30"
                  : "cursor-not-allowed opacity-30",
                flagged ? "ring-2 ring-blue-500 ring-offset-1 ring-offset-card" : "",
                isSelected ? "outline outline-2 outline-foreground" : "",
              ].join(" ")}
              style={{
                backgroundColor: inRange ? (row ? bg : "var(--muted)") : "var(--muted)",
                color: inRange && darkText ? "white" : undefined,
              }}
              title={row ? TRAFFIC_LABELS[row.traffic] : "No traffic data available."}
            >
              <span className="absolute left-1.5 top-1 text-[11px] font-semibold">
                {d.getDate()}
              </span>
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

function DayDetail({ day, row }: { day: Date | null; row: TrafficRow | null }) {
  if (!day) {
    return (
      <div className="rounded-xl border border-dashed border-border p-6 text-sm text-muted-foreground">
        Click a day on the calendar to see its time-slot breakdown.
      </div>
    );
  }
  const title = day.toLocaleDateString("en-GB", {
    weekday: "long",
    day: "2-digit",
    month: "long",
    year: "numeric",
  });
  return (
    <div className="rounded-xl border border-border bg-card p-5 shadow-sm">
      <h3 className="text-sm font-semibold">{title}</h3>
      {!row ? (
        <p className="mt-3 text-sm text-muted-foreground">No traffic data available.</p>
      ) : (
        <>
          <div className="mt-2 inline-flex items-center gap-2 text-xs">
            <span
              className="inline-block h-3 w-3 rounded-sm"
              style={{ backgroundColor: TRAFFIC_COLORS[row.traffic] }}
            />
            <span className="text-muted-foreground">Daily average:</span>
            <span className="font-medium">{TRAFFIC_LABELS[row.traffic]}</span>
          </div>
          <ul className="mt-4 space-y-1.5">
            {row.parts.map((p, i) => (
              <li
                key={i}
                className="flex items-center justify-between rounded-md px-3 py-2 text-sm"
                style={{
                  backgroundColor: TRAFFIC_COLORS[p],
                  color: p === "heavy" || p === "extreme" ? "white" : "#111",
                }}
              >
                <span className="font-medium">{SLOT_LABELS[i]}</span>
                <span className="text-xs opacity-90">{TRAFFIC_LABELS[p]}</span>
              </li>
            ))}
          </ul>
        </>
      )}
    </div>
  );
}
