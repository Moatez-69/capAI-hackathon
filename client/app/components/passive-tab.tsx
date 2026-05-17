import { useId, useMemo, useState } from "react";
import { IconDown, IconFlat, IconUp } from "./icons";
import type { AppFounder, Application, DimensionalScore, IntentSignal, ShapSignal, Trend } from "./types";

function ApplicationsList({
  apps,
  selectedId,
  onSelect,
}: {
  apps: Application[];
  selectedId: string;
  onSelect: (id: string) => void;
}) {
  const TrendIcon = ({ trend }: { trend: Trend }) => {
    if (trend === "up") {
      return <IconUp size={11} stroke="#059669" />;
    }
    if (trend === "down") {
      return <IconDown size={11} stroke="#DC2626" />;
    }
    return <IconFlat size={11} stroke="#8B95A4" />;
  };

  return (
    <div className="card apps-card">
      <div className="card-head">
        <div>
          <div className="card-title">
            Applications <span className="count">{apps.length}</span>
          </div>
          <div className="card-sub">Inbound · last 30d</div>
        </div>
        <button className="ghost-btn">Filter</button>
      </div>
      <div className="apps-list">
        {apps.map((app) => (
          <button
            key={app.id}
            className={`app-card ${selectedId === app.id ? "sel" : ""}`}
            onClick={() => onSelect(app.id)}
          >
            <div className="app-top">
              <div
                className="logo sm"
                style={{
                  background: `${app.color}18`,
                  color: app.color,
                  borderColor: `${app.color}40`,
                }}
              >
                {app.logo}
              </div>
              <div className="grow">
                <div className="app-name-row">
                  <div className="name">{app.name}</div>
                  <div className="app-score">{app.score}</div>
                </div>
                <div className="app-meta">
                  <span>{app.industry}</span>
                  <span className="dot">·</span>
                  <span>{app.stage}</span>
                </div>
              </div>
            </div>
            <div className="app-foot">
              <div className="trend-delta">
                <TrendIcon trend={app.trend} />
                <span className={`delta ${app.trend}`}>{app.delta}</span>
                <span className="muted">vs avg</span>
              </div>
              <div className="muted small">{app.submitted}</div>
            </div>
          </button>
        ))}
      </div>
    </div>
  );
}

function Sparkline({
  data,
  color = "#0891B2",
  height = 28,
}: {
  data: number[];
  color?: string;
  height?: number;
}) {
  const gradientId = useId();
  const width = 100;
  const min = Math.min(...data);
  const max = Math.max(...data);
  const normalize = (value: number) =>
    height - 2 - ((value - min) / (max - min || 1)) * (height - 4);
  const step = width / (data.length - 1);
  const path = data
    .map(
      (value, index) =>
        `${index === 0 ? "M" : "L"}${(index * step).toFixed(1)},${normalize(value).toFixed(1)}`,
    )
    .join(" ");
  const area = `${path} L${width},${height} L0,${height} Z`;

  return (
    <svg
      viewBox={`0 0 ${width} ${height}`}
      preserveAspectRatio="none"
      width="100%"
      height={height}
    >
      <defs>
        <linearGradient id={gradientId} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={color} stopOpacity="0.22" />
          <stop offset="100%" stopColor={color} stopOpacity="0" />
        </linearGradient>
      </defs>
      <path d={area} fill={`url(#${gradientId})`} />
      <path
        d={path}
        fill="none"
        stroke={color}
        strokeWidth="1.4"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

function MetricCard({
  title,
  value,
  unit,
  sub,
  delta,
  color,
  spark,
}: {
  title: string;
  value: string;
  unit: string;
  sub: string;
  delta: string;
  color: string;
  spark: number[];
}) {
  return (
    <div className="metric-card">
      <div className="metric-top">
        <div className="metric-title">{title}</div>
        <div
          className={`metric-delta ${delta.startsWith("-") ? "neg" : "pos"}`}
        >
          {delta}
        </div>
      </div>
      <div className="metric-value">
        {value}
        <span className="metric-unit">{unit}</span>
      </div>
      <div className="metric-sub">{sub}</div>
      <div className="metric-spark">
        <Sparkline data={spark} color={color} height={32} />
      </div>
    </div>
  );
}

function ScoreRing({
  value,
  size = 48,
  color = "#0891B2",
  stroke = 2.5,
}: {
  value: number;
  size?: number;
  color?: string;
  stroke?: number;
}) {
  const radius = (size - stroke - 2) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (value / 100) * circumference;

  return (
    <svg
      width={size}
      height={size}
      viewBox={`0 0 ${size} ${size}`}
      className="score-ring"
    >
      <circle
        cx={size / 2}
        cy={size / 2}
        r={radius}
        fill="none"
        stroke="rgba(15,23,42,0.06)"
        strokeWidth={stroke}
      />
      <circle
        cx={size / 2}
        cy={size / 2}
        r={radius}
        fill="none"
        stroke={color}
        strokeWidth={stroke}
        strokeLinecap="round"
        strokeDasharray={circumference}
        strokeDashoffset={offset}
        transform={`rotate(-90 ${size / 2} ${size / 2})`}
        style={{ transition: "stroke-dashoffset 0.6s ease" }}
      />
    </svg>
  );
}

function FStat({
  label,
  value,
  color,
}: {
  label: string;
  value: number;
  color: string;
}) {
  return (
    <div className="fstat">
      <div className="fstat-head">
        <span className="fstat-label">{label}</span>
        <span className="fstat-val">{value}</span>
      </div>
      <div className="bar">
        <div
          className="bar-fill"
          style={{ width: `${value}%`, background: color }}
        />
      </div>
    </div>
  );
}

function dimColor(val: number) {
  if (val >= 7) return "#1D9E75";
  if (val >= 4) return "#378ADD";
  return "#E24B4A";
}

function IndividualFounderCard({ founder }: { founder: AppFounder }) {
  const initials =
    founder.initials ??
    founder.name
      .split(" ")
      .map((p) => p[0])
      .join("");

  const completeness = founder.dataCompleteness ?? 0;
  const compColor =
    completeness >= 75 ? "#1D9E75" : completeness >= 50 ? "#EF9F27" : "#E24B4A";
  const compLabel =
    completeness >= 75
      ? "Good confidence"
      : completeness >= 50
        ? "Low confidence"
        : "Very low confidence";

  const posShap = (founder.shapSignals as ShapSignal[] | undefined)?.filter(
    (s) => s.dir === "up",
  );
  const negShap = (founder.shapSignals as ShapSignal[] | undefined)?.filter(
    (s) => s.dir === "down",
  );

  return (
    <div className="ic-card">
      {/* header */}
      <div className="ic-header">
        <div className="ic-avatar">{initials}</div>
        <div className="ic-identity">
          <div className="ic-name">{founder.name}</div>
          <div className="ic-sub">
            {founder.role}
            {founder.education ? ` · ${founder.education}` : ""}
            {founder.prevCompanies ? ` · ${founder.prevCompanies}` : ""}
          </div>
        </div>
        {founder.badge && <span className="ic-badge">{founder.badge}</span>}
      </div>

      {/* top metrics */}
      <div className="ic-metrics">
        <div className="ic-metric">
          <div className="ic-metric-val">
            {founder.individualScore ?? founder.score}
            <span className="ic-metric-denom">/100</span>
          </div>
          <div className="ic-metric-lbl">Individual score</div>
        </div>
        <div className="ic-metric">
          <div className="ic-metric-val" style={{ color: compColor }}>
            {completeness}%
          </div>
          <div className="ic-metric-lbl">Data completeness</div>
        </div>
        <div className="ic-metric">
          <div className="ic-metric-val">
            {founder.firstSignalMonths ?? "—"} mo
          </div>
          <div className="ic-metric-lbl">Since first signal</div>
        </div>
      </div>

      {/* dimensional profile */}
      {(founder.dimensions as DimensionalScore[] | undefined)?.length ? (
        <>
          <div className="ic-divider" />
          <div className="ic-section-title">Dimensional profile</div>
          <div className="ic-dims">
            {(founder.dimensions as DimensionalScore[]).map((dim) => (
              <div key={dim.label} className="ic-bar-row">
                <div className="ic-bar-label">{dim.label}</div>
                <div className="ic-bar-track">
                  <div
                    className="ic-bar-fill"
                    style={{
                      width: `${dim.value * 10}%`,
                      background: dimColor(dim.value),
                    }}
                  />
                </div>
                <div className="ic-bar-score">{dim.value.toFixed(1)}</div>
              </div>
            ))}
          </div>
        </>
      ) : null}

      {/* SHAP signals */}
      {(posShap?.length || negShap?.length) ? (
        <>
          <div className="ic-divider" />
          <div className="ic-section-title">SHAP signals</div>
          <div className="ic-shap-list">
            {posShap?.map((sig, i) => (
              <div key={i} className="ic-shap-row ic-shap-up">
                <span className="ic-shap-arrow">↑</span>
                <span className="ic-shap-text">{sig.text}</span>
                <span className="ic-shap-val">+{sig.value.toFixed(1)}</span>
              </div>
            ))}
            {negShap?.length ? <div className="ic-shap-gap" /> : null}
            {negShap?.map((sig, i) => (
              <div key={i} className="ic-shap-row ic-shap-down">
                <span className="ic-shap-arrow">↓</span>
                <span className="ic-shap-text">{sig.text}</span>
                <span className="ic-shap-val">−{Math.abs(sig.value).toFixed(1)}</span>
              </div>
            ))}
          </div>
        </>
      ) : null}

      {/* intent signals */}
      {(founder.intentSignals as IntentSignal[] | undefined)?.length ? (
        <>
          <div className="ic-divider" />
          <div className="ic-section-title">Founding intent signals</div>
          <div className="ic-intent-tags">
            {(founder.intentSignals as IntentSignal[]).map((sig, i) => (
              <span key={i} className="ic-intent-tag">
                ✓ {sig.label} · {sig.when}
              </span>
            ))}
          </div>
        </>
      ) : null}

      {/* data completeness */}
      <div className="ic-divider" />
      <div className="ic-section-title">Data completeness</div>
      <div className="ic-completeness-row">
        <div className="ic-comp-bar">
          <div
            className="ic-comp-fill"
            style={{ width: `${completeness}%`, background: compColor }}
          />
        </div>
        <span className="ic-comp-label" style={{ color: compColor }}>
          {completeness}% · {compLabel}
        </span>
      </div>
      {(founder.missingData as string[] | undefined)?.length ? (
        <div className="ic-missing">
          {(founder.missingData as string[]).map((m, i) => (
            <span key={i} className="ic-missing-pill">
              ⚠ {m}
            </span>
          ))}
        </div>
      ) : null}
      {founder.projectedScoreRange ? (
        <div className="ic-projection">
          → Score projected to reach {founder.projectedScoreRange[0]}–
          {founder.projectedScoreRange[1]} with full data.
        </div>
      ) : null}
    </div>
  );
}

function FounderRow({
  founder,
  selected,
  expanded,
  onToggle,
  onExpand,
}: {
  founder: AppFounder;
  selected: boolean;
  expanded: boolean;
  onToggle: () => void;
  onExpand: () => void;
}) {
  const hasRichProfile = Boolean(
    founder.dimensions?.length ||
      founder.shapSignals?.length ||
      founder.intentSignals?.length,
  );

  return (
    <div className={`founder-row-wrap ${expanded ? "expanded" : ""}`}>
      <div
        role="button"
        tabIndex={0}
        className={`founder-row ${selected ? "sel" : ""}`}
        onClick={onToggle}
        onKeyDown={(e) => { if (e.key === "Enter" || e.key === " ") onToggle(); }}
      >
        <div className="fr-top">
          <div className="fr-avatar-wrap">
            <ScoreRing
              value={founder.score}
              size={52}
              color={selected ? "#0891B2" : "#2563EB"}
            />
            <div className="fr-initials">
              {founder.initials ??
                founder.name
                  .split(" ")
                  .map((part) => part[0])
                  .join("")}
            </div>
          </div>
          <div className="grow">
            <div className="fr-name">{founder.name}</div>
            <div className="fr-role">{founder.role}</div>
            <div className="fr-prev">{founder.prev}</div>
          </div>
          <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-end", gap: 6 }}>
            <div className={`fr-check ${selected ? "on" : ""}`}>
              {selected ? "✓ Selected" : "Select"}
            </div>
            {hasRichProfile && (
              <button
                className="ic-expand-btn"
                onClick={(e) => { e.stopPropagation(); onExpand(); }}
              >
                {expanded ? "▲ Hide profile" : "▼ Full profile"}
              </button>
            )}
          </div>
        </div>
        <div className="fr-stats">
          <FStat label="Technical" value={founder.technical} color="#2563EB" />
          <FStat label="Business" value={founder.business} color="#7C3AED" />
          <FStat label="Network" value={founder.network} color="#0891B2" />
        </div>
        <div className="fr-tags">
          {founder.expertise.map((tag) => (
            <span key={tag} className="mini-tag">
              {tag}
            </span>
          ))}
        </div>
      </div>
      {expanded && hasRichProfile && <IndividualFounderCard founder={founder} />}
    </div>
  );
}

function Radar({
  axes,
  values,
  color = "#0891B2",
  size = 220,
}: {
  axes: string[];
  values: number[];
  color?: string;
  size?: number;
}) {
  const cx = size / 2;
  const cy = size / 2;
  const radius = size / 2 - 28;
  const count = axes.length;

  const point = (index: number, value: number) => {
    const angle = (Math.PI * 2 * index) / count - Math.PI / 2;
    return [
      cx + Math.cos(angle) * radius * (value / 100),
      cy + Math.sin(angle) * radius * (value / 100),
    ] as const;
  };

  const polygonPoints = (valuesToDraw: number[]) =>
    valuesToDraw.map((value, index) => point(index, value).join(",")).join(" ");

  return (
    <svg
      width={size}
      height={size}
      viewBox={`0 0 ${size} ${size}`}
      className="radar"
    >
      {[0.25, 0.5, 0.75, 1].map((grid, index) => (
        <polygon
          key={`grid-${index}`}
          points={polygonPoints(axes.map(() => grid * 100))}
          fill="none"
          stroke="rgba(15,23,42,0.06)"
        />
      ))}
      {axes.map((_, index) => {
        const [x, y] = point(index, 100);
        return (
          <line
            key={`axis-${index}`}
            x1={cx}
            y1={cy}
            x2={x}
            y2={y}
            stroke="rgba(15,23,42,0.06)"
          />
        );
      })}
      <polygon
        points={polygonPoints(values)}
        fill={`${color}22`}
        stroke={color}
        strokeWidth="1.6"
        style={{ transition: "all 0.5s ease" }}
      />
      {values.map((value, index) => {
        const [x, y] = point(index, value);
        return (
          <circle key={`dot-${index}`} cx={x} cy={y} r="2.6" fill={color} />
        );
      })}
      {axes.map((axis, index) => {
        const [x, y] = point(index, 118);
        return (
          <text
            key={`label-${axis}`}
            x={x}
            y={y}
            textAnchor="middle"
            dominantBaseline="middle"
            fontSize="9.5"
            fill="#5B6472"
            fontWeight="500"
          >
            {axis}
          </text>
        );
      })}
    </svg>
  );
}

function average(items: AppFounder[], key: keyof AppFounder) {
  if (!items.length) {
    return 0;
  }

  const sum = items.reduce((acc, item) => {
    const value = item[key];
    return typeof value === "number" ? acc + value : acc;
  }, 0);

  return sum / items.length;
}

function MetaRow({
  label,
  value,
  color,
}: {
  label: string;
  value: number;
  color: string;
}) {
  return (
    <div className="meta-row">
      <div className="meta-row-head" style={{ gridColumn: "1/-1" }}>
        <span className="meta-label">{label}</span>
        <span className="meta-val">{value}</span>
      </div>
      <div className="meta-bar">
        <div
          className="meta-fill"
          style={{ width: `${value}%`, background: color }}
        />
      </div>
    </div>
  );
}

function SynergyLines({ count }: { count: number }) {
  if (count < 2) {
    return null;
  }

  const points = Array.from({ length: count }, (_, index) => 80 + index * 32);
  const lines: [number, number][] = [];

  for (let i = 0; i < points.length; i += 1) {
    for (let j = i + 1; j < points.length; j += 1) {
      lines.push([points[i], points[j]]);
    }
  }

  return (
    <svg
      className="synergy-svg"
      viewBox="0 0 400 24"
      preserveAspectRatio="none"
    >
      {lines.map(([a, b], index) => (
        <g key={`line-${index}`}>
          <path
            d={`M${a},12 Q${(a + b) / 2},22 ${b},12`}
            fill="none"
            stroke="rgba(8,145,178,0.35)"
            strokeWidth="0.8"
          />
          <circle r="1.4" fill="#0891B2">
            <animateMotion
              dur="2.6s"
              repeatCount="indefinite"
              path={`M${a},12 Q${(a + b) / 2},22 ${b},12`}
            />
          </circle>
        </g>
      ))}
    </svg>
  );
}

function SelectedRow({
  founders,
  selectedFounders,
}: {
  founders: AppFounder[];
  selectedFounders: AppFounder[];
}) {
  const shown = selectedFounders.slice(0, 5);
  const empty = Math.max(0, 3 - shown.length);

  return (
    <div className="selected-row">
      <span className="sel-label">Selected</span>
      <div className="selected-stack">
        {shown.map((founder) => (
          <div
            key={founder.id}
            className="stack-avatar"
            style={{ background: "#FFFFFF", color: "#0891B2" }}
          >
            {founder.name
              .split(" ")
              .map((part) => part[0])
              .join("")}
          </div>
        ))}
        {Array.from({ length: empty }).map((_, index) => (
          <div key={`empty-${index}`} className="stack-avatar empty">
            ·
          </div>
        ))}
      </div>
      <div className="selected-count">
        {selectedFounders.length} of {founders.length}
      </div>
      <SynergyLines count={selectedFounders.length} />
    </div>
  );
}

function TeamPanel({
  founders,
  selectedFounders,
}: {
  founders: AppFounder[];
  selectedFounders: AppFounder[];
}) {
  if (!selectedFounders.length) {
    return (
      <div className="team-panel-v2">
        <SelectedRow founders={founders} selectedFounders={selectedFounders} />
        <div className="team-empty">
          <div className="empty-title">Select founders to model the team</div>
          <div className="empty-sub">
            Compatibility, balance and execution strength update live as you add
            or remove founders.
          </div>
        </div>
      </div>
    );
  }

  const tech = average(selectedFounders, "technical");
  const biz = average(selectedFounders, "business");
  const lead = average(selectedFounders, "leadership");
  const ai = average(selectedFounders, "ai");
  const ops = average(selectedFounders, "ops");
  const net = average(selectedFounders, "network");
  const balance = Math.round(100 - Math.abs(tech - biz));
  const compatibility = Math.round(
    tech * 0.25 + biz * 0.2 + lead * 0.2 + ops * 0.15 + net * 0.2,
  );
  const execution = Math.round(compatibility * 0.6 + balance * 0.4);

  return (
    <div className="team-panel-v2">
      <SelectedRow founders={founders} selectedFounders={selectedFounders} />

      <div className="team-summary">
        <div className="summary-card">
          <div className="label">Compatibility</div>
          <div className="value" style={{ color: "#0891B2" }}>
            {compatibility}
          </div>
          <div className="delta-sm" style={{ color: "#059669" }}>
            +4 vs solo
          </div>
        </div>
        <div className="summary-card">
          <div className="label">Execution</div>
          <div className="value" style={{ color: "#7C3AED" }}>
            {execution}
          </div>
          <div className="delta-sm muted">predicted</div>
        </div>
        <div className="summary-card">
          <div className="label">Balance</div>
          <div className="value" style={{ color: "#059669" }}>
            {balance}
          </div>
          <div className="delta-sm muted">tech ↔ biz</div>
        </div>
      </div>

      <div className="radar-block">
        <div className="radar-title-row">
          <span className="radar-mini-title">Capability profile</span>
          <span className="radar-mini-title muted">
            {selectedFounders.length} founder
            {selectedFounders.length !== 1 ? "s" : ""}
          </span>
        </div>
        <Radar
          axes={[
            "Technical",
            "Business",
            "Leadership",
            "AI Depth",
            "Operations",
            "Network",
          ]}
          values={[tech, biz, lead, ai, ops, net]}
          color="#0891B2"
          size={220}
        />
      </div>

      <div className="meta-list">
        <MetaRow
          label="Tech / Business balance"
          value={balance}
          color="#2563EB"
        />
        <MetaRow
          label="Experience overlap"
          value={selectedFounders.length > 1 ? 62 : 0}
          color="#7C3AED"
        />
        <MetaRow
          label="Diversity index"
          value={selectedFounders.length > 1 ? 78 : 45}
          color="#0891B2"
        />
        <MetaRow
          label="Network reach"
          value={Math.round(net)}
          color="#059669"
        />
        <MetaRow
          label="Predicted execution"
          value={execution}
          color="#D97706"
        />
      </div>

      <div className="team-flags">
        {tech > 70 ? (
          <span className="flag good">✓ Strong technical core</span>
        ) : null}
        {biz > 70 ? <span className="flag good">✓ GTM coverage</span> : null}
        {net > 70 ? <span className="flag good">✓ Deep network</span> : null}
        {selectedFounders.length === 1 ? (
          <span className="flag warn">! Solo founder risk</span>
        ) : null}
        {selectedFounders.length > 3 ? (
          <span className="flag info">i Larger team — slower decisions</span>
        ) : null}
        {balance < 60 && selectedFounders.length > 1 ? (
          <span className="flag warn">! Skill imbalance</span>
        ) : null}
      </div>
    </div>
  );
}

export function PassiveTab({
  applications,
  appFounders,
}: {
  applications: Application[];
  appFounders: Record<string, AppFounder[]>;
}) {
  const [selected, setSelected] = useState("a1");
  const [picked, setPicked] = useState<Set<string>>(new Set(["p1", "p2"]));
  const [expanded, setExpanded] = useState<string | null>(null);

  const toggleExpand = (id: string) =>
    setExpanded((current) => (current === id ? null : id));

  const app = useMemo(
    () =>
      applications.find((application) => application.id === selected) ??
      applications[0],
    [applications, selected],
  );

  const founders = appFounders[selected] ?? appFounders.a1 ?? [];
  const selectedFounders = founders.filter((founder) => picked.has(founder.id));

  const togglePick = (id: string) => {
    setPicked((current) => {
      const next = new Set(current);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  };

  const sparkA = [12, 14, 13, 16, 18, 22, 28, 31, 38, 44, 52, 61];
  const sparkB = [40, 42, 38, 44, 51, 58, 62, 60, 67, 72, 78, 82];
  const sparkC = [80, 78, 82, 84, 86, 89, 88, 91, 92, 93, 94, 96];

  if (!app) {
    return null;
  }

  return (
    <div className="passive-grid">
      <aside className="left-col">
        <ApplicationsList
          apps={applications}
          selectedId={selected}
          onSelect={setSelected}
        />
      </aside>

      <section className="passive-detail">
        <div className="detail-header">
          <div className="detail-id">
            <div
              className="logo md"
              style={{
                background: `${app.color}18`,
                color: app.color,
                borderColor: `${app.color}40`,
              }}
            >
              {app.logo}
            </div>
            <div>
              <div className="detail-name">{app.name}</div>
              <div className="detail-sub">
                {app.industry} · {app.stage} · Applied {app.submitted}
              </div>
            </div>
          </div>
          <div className="detail-actions">
            <button className="pill-btn ghost">Reject</button>
            <button className="pill-btn ghost">Save</button>
            <button className="pill-btn primary">Move to IC</button>
          </div>
        </div>

        <div className="metrics-row">
          <MetricCard
            title="Market Size"
            value="42"
            unit="B"
            delta="+12%"
            sub="TAM · biotech AI · 2028 est."
            color="#0891B2"
            spark={sparkB}
          />
          <MetricCard
            title="Timing"
            value="92"
            unit=""
            delta="+8"
            sub="Regulatory tailwind · talent inflow"
            color="#7C3AED"
            spark={sparkC}
          />
          <MetricCard
            title="KPIs"
            value="3.8"
            unit="x"
            delta="+38%"
            sub="Growth MoM · pilot conversion 41%"
            color="#059669"
            spark={sparkA}
          />
        </div>

        <div className="analysis-split">
          <div className="analysis-col">
            <div className="analysis-head">
              <div>
                <div className="analysis-title">Founders</div>
                <div className="analysis-sub">
                  {founders.length} founders · individual analysis
                </div>
              </div>
              <button className="ghost-btn">Compare</button>
            </div>
            <div className="analysis-body">
              {founders.map((founder) => (
                <FounderRow
                  key={founder.id}
                  founder={founder}
                  selected={picked.has(founder.id)}
                  expanded={expanded === founder.id}
                  onToggle={() => togglePick(founder.id)}
                  onExpand={() => toggleExpand(founder.id)}
                />
              ))}
            </div>
          </div>

          <div className="analysis-col">
            <div className="analysis-head">
              <div>
                <div className="analysis-title">Team analysis</div>
                <div className="analysis-sub">
                  {picked.size} of {founders.length} selected · synergy modeled
                  live
                </div>
              </div>
              <button className="ghost-btn">Reset</button>
            </div>
            <div className="analysis-body">
              <TeamPanel
                founders={founders}
                selectedFounders={selectedFounders}
              />
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
