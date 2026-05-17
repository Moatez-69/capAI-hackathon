import { useEffect, useMemo, useRef, useState } from "react";
import type { Dispatch, SetStateAction } from "react";
import {
  IconDown,
  IconExpand,
  IconFlat,
  IconRecenter,
  IconUp,
  IconZoomIn,
  IconZoomOut,
} from "./icons";
import type { Founder, Startup, Trend } from "./types";

const LEVEL_COLOR: Record<Founder["level"], string> = {
  baseline: "#0891B2",
  discovered: "#2563EB",
  startup: "#7C3AED",
  high: "#0891B2",
};

type FiltersState = {
  stages: string[];
  industries: string[];
  minScore: number;
  depth: number;
  signals: string[];
};

function Filters({
  filters,
  setFilters,
}: {
  filters: FiltersState;
  setFilters: Dispatch<SetStateAction<FiltersState>>;
}) {
  const stages = ["Pre-seed", "Seed", "Series A"];
  const industries = [
    "AI Infra",
    "Bio × AI",
    "Dev Tools",
    "Climate",
    "Robotics",
    "Healthtech",
  ];
  const signals = ["Network warmth", "Repeat founder", "Stealth"];

  const toggle = (key: "stages" | "industries" | "signals", val: string) => {
    setFilters((current) => {
      const arr = current[key];
      return {
        ...current,
        [key]: arr.includes(val) ? arr.filter((x) => x !== val) : [...arr, val],
      };
    });
  };

  const activeCount =
    filters.industries.length + filters.stages.length + filters.signals.length;

  return (
    <div className="card filters">
      <div className="card-head">
        <div>
          <div className="card-title">Filters</div>
          <div className="card-sub">{activeCount} active</div>
        </div>
        <button className="ghost-btn">Reset</button>
      </div>

      <div className="filter-section">
        <div className="filter-label">Stage</div>
        <div className="chips">
          {stages.map((stage) => (
            <button
              key={stage}
              className={`chip ${filters.stages.includes(stage) ? "on" : ""}`}
              onClick={() => toggle("stages", stage)}
            >
              {stage}
            </button>
          ))}
        </div>
      </div>

      <div className="filter-section">
        <div className="filter-label">Industry</div>
        <div className="chips">
          {industries.map((industry) => (
            <button
              key={industry}
              className={`chip ${filters.industries.includes(industry) ? "on" : ""}`}
              onClick={() => toggle("industries", industry)}
            >
              {industry}
            </button>
          ))}
        </div>
      </div>

      <div className="filter-section">
        <div className="filter-label-row">
          <div className="filter-label">AI Score</div>
          <div className="filter-value">{filters.minScore}+</div>
        </div>
        <input
          type="range"
          min="50"
          max="99"
          value={filters.minScore}
          onChange={(e) =>
            setFilters((current) => ({
              ...current,
              minScore: Number(e.target.value),
            }))
          }
          className="slider"
        />
        <div className="slider-rail">
          <div
            className="slider-fill"
            style={{ width: `${((filters.minScore - 50) / 49) * 100}%` }}
          />
        </div>
      </div>

      <div className="filter-section">
        <div className="filter-label-row">
          <div className="filter-label">Network depth</div>
          <div className="filter-value">{filters.depth} hops</div>
        </div>
        <div className="seg">
          {[1, 2, 3].map((depth) => (
            <button
              key={depth}
              className={`seg-btn ${filters.depth === depth ? "on" : ""}`}
              onClick={() => setFilters((current) => ({ ...current, depth }))}
            >
              {depth}
            </button>
          ))}
        </div>
      </div>

      <div className="filter-section">
        <div className="filter-label">Signals</div>
        <div className="chips">
          {signals.map((signal) => (
            <button
              key={signal}
              className={`chip ${filters.signals.includes(signal) ? "on" : ""}`}
              onClick={() => toggle("signals", signal)}
            >
              {signal}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}

function StartupList({
  items,
  selectedId,
  onSelect,
}: {
  items: Startup[];
  selectedId: string;
  onSelect: (id: string) => void;
}) {
  const TrendIcon = ({ trend }: { trend: Trend }) => {
    if (trend === "up") {
      return <IconUp size={11} stroke="#10B981" />;
    }
    if (trend === "down") {
      return <IconDown size={11} stroke="#EF4444" />;
    }
    return <IconFlat size={11} stroke="#9CA3AF" />;
  };

  return (
    <div className="card startup-list">
      <div className="card-head">
        <div>
          <div className="card-title">
            Startups <span className="count">{items.length}</span>
          </div>
          <div className="card-sub">Sorted by AI Score</div>
        </div>
        <button className="ghost-btn">Sort</button>
      </div>
      <div className="list">
        {items.map((startup) => (
          <button
            key={startup.id}
            className={`startup-card ${selectedId === startup.id ? "sel" : ""}`}
            onClick={() => onSelect(startup.id)}
          >
            <div
              className="logo"
              style={{
                background: `linear-gradient(135deg, ${startup.color}40, ${startup.color}10)`,
                color: startup.color,
                borderColor: `${startup.color}55`,
              }}
            >
              {startup.logo}
            </div>
            <div className="grow">
              <div className="row1">
                <div className="name">{startup.name}</div>
                <div className="score-badge">{startup.score}</div>
              </div>
              <div className="row2">
                <span>{startup.industry}</span>
                <span className="dot">·</span>
                <span>{startup.stage}</span>
                <span className="dot">·</span>
                <span className="trend">
                  <TrendIcon trend={startup.trend} /> {startup.traction}
                </span>
              </div>
            </div>
          </button>
        ))}
      </div>
    </div>
  );
}

type GraphProps = {
  founders: Founder[];
  startups: Startup[];
  edges: [string, string][];
  selectedStartup: string;
  hoverNode: string | null;
  setHoverNode: Dispatch<SetStateAction<string | null>>;
  setExpandedIds: Dispatch<SetStateAction<Set<string>>>;
};

function Graph({
  founders,
  startups,
  edges,
  selectedStartup,
  hoverNode,
  setHoverNode,
  setExpandedIds,
}: GraphProps) {
  const wrapRef = useRef<HTMLDivElement | null>(null);
  const [size, setSize] = useState({ w: 800, h: 600 });
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [zoom, setZoom] = useState(1);
  const [dragging, setDragging] = useState(false);
  const dragStart = useRef({ x: 0, y: 0 });

  useEffect(() => {
    if (!wrapRef.current) {
      return;
    }

    const observer = new ResizeObserver(() => {
      if (!wrapRef.current) {
        return;
      }

      const rect = wrapRef.current.getBoundingClientRect();
      setSize({ w: rect.width, h: rect.height });
    });

    observer.observe(wrapRef.current);
    return () => observer.disconnect();
  }, []);

  const particles = useMemo(
    () =>
      Array.from({ length: 28 }, (_, index) => {
        const x = ((index * 37 + 13) % 1000) / 1000;
        const y = ((index * 53 + 29) % 1000) / 1000;
        return {
          x,
          y,
          r: 0.6 + ((index * 7) % 10) / 10,
          dur: 14 + ((index * 11) % 16),
          delay: -(index % 20),
        };
      }),
    [],
  );

  const nodeMap = useMemo(
    () => Object.fromEntries(founders.map((founder) => [founder.id, founder])),
    [founders],
  );

  const pos = (founder: Founder) => ({
    x: pan.x + (founder.x * size.w - size.w / 2) * zoom + size.w / 2,
    y: pan.y + (founder.y * size.h - size.h / 2) * zoom + size.h / 2,
  });

  const onMouseDown = (e: React.MouseEvent<HTMLDivElement>) => {
    const target = e.target as HTMLElement;
    if (target.closest(".node-hit")) {
      return;
    }

    setDragging(true);
    dragStart.current = { x: e.clientX - pan.x, y: e.clientY - pan.y };
  };

  const onMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!dragging) {
      return;
    }

    setPan({
      x: e.clientX - dragStart.current.x,
      y: e.clientY - dragStart.current.y,
    });
  };

  const onMouseUp = () => setDragging(false);

  const onWheel = (e: React.WheelEvent<HTMLDivElement>) => {
    e.preventDefault();
    setZoom((current) =>
      Math.max(0.5, Math.min(2.4, current + (e.deltaY < 0 ? 0.08 : -0.08))),
    );
  };

  return (
    <div
      className="graph-wrap"
      ref={wrapRef}
      onMouseDown={onMouseDown}
      onMouseMove={onMouseMove}
      onMouseUp={onMouseUp}
      onMouseLeave={onMouseUp}
      onWheel={onWheel}
      style={{ cursor: dragging ? "grabbing" : "grab" }}
    >
      <div className="graph-bg" />
      <svg className="graph-svg" width={size.w} height={size.h}>
        <defs>
          <filter id="softGlow" x="-50%" y="-50%" width="200%" height="200%">
            <feGaussianBlur stdDeviation="3" />
          </filter>
        </defs>

        {particles.map((particle, index) => (
          <circle
            key={`particle-${index}`}
            cx={particle.x * size.w}
            cy={particle.y * size.h}
            r={particle.r}
            fill="rgba(37,99,235,0.18)"
          >
            <animate
              attributeName="opacity"
              values="0.0;0.45;0.0"
              dur={`${particle.dur}s`}
              begin={`${particle.delay}s`}
              repeatCount="indefinite"
            />
            <animate
              attributeName="cy"
              values={`${particle.y * size.h};${particle.y * size.h - 30};${particle.y * size.h}`}
              dur={`${particle.dur}s`}
              begin={`${particle.delay}s`}
              repeatCount="indefinite"
            />
          </circle>
        ))}

        {edges.map(([a, b], index) => {
          const first = nodeMap[a];
          const second = nodeMap[b];
          if (!first || !second) {
            return null;
          }

          const p1 = pos(first);
          const p2 = pos(second);
          const isHover = hoverNode === a || hoverNode === b;

          return (
            <g
              key={`edge-${index}`}
              className={`edge ${isHover ? "edge-on" : ""}`}
            >
              <line
                x1={p1.x}
                y1={p1.y}
                x2={p2.x}
                y2={p2.y}
                stroke={
                  isHover ? "rgba(8,145,178,0.55)" : "rgba(15,23,42,0.08)"
                }
                strokeWidth={isHover ? 1.3 : 0.7}
              />
              {isHover && (
                <circle r="2.2" fill="#0891B2" opacity="0.9">
                  <animateMotion
                    dur="2.2s"
                    repeatCount="indefinite"
                    path={`M${p1.x},${p1.y} L${p2.x},${p2.y}`}
                  />
                </circle>
              )}
            </g>
          );
        })}

        {founders.map((founder) => {
          const p = pos(founder);
          const color = LEVEL_COLOR[founder.level];
          const isHover = hoverNode === founder.id;
          const isAffiliated =
            Boolean(selectedStartup) && founder.startup === selectedStartup;
          const ringW = founder.level === "startup" || isAffiliated ? 2.4 : 1.5;
          const ringColor = isAffiliated ? "#7C3AED" : color;
          const radius = 18 + (isHover ? 2 : 0);

          return (
            <g
              key={founder.id}
              className="node-hit"
              style={{ cursor: "pointer" }}
              onMouseEnter={() => setHoverNode(founder.id)}
              onMouseLeave={() => setHoverNode(null)}
              onClick={(e) => {
                e.stopPropagation();
                setExpandedIds((current) => new Set([...current, founder.id]));
              }}
              transform={`translate(${p.x},${p.y})`}
            >
              <circle
                r={radius + 6}
                fill={ringColor}
                opacity={isHover ? 0.12 : 0.05}
                filter="url(#softGlow)"
              />

              {founder.level === "high" && (
                <circle
                  r={radius}
                  fill="none"
                  stroke={color}
                  strokeWidth="1"
                  opacity="0.5"
                >
                  <animate
                    attributeName="r"
                    values={`${radius};${radius + 10}`}
                    dur="2.6s"
                    repeatCount="indefinite"
                  />
                  <animate
                    attributeName="opacity"
                    values="0.5;0"
                    dur="2.6s"
                    repeatCount="indefinite"
                  />
                </circle>
              )}

              <circle
                r={radius}
                fill="#FFFFFF"
                stroke={ringColor}
                strokeWidth={ringW}
              />

              <defs>
                <radialGradient
                  id={`avatar-${founder.id}`}
                  cx="40%"
                  cy="35%"
                  r="80%"
                >
                  <stop offset="0%" stopColor={`${color}33`} />
                  <stop offset="100%" stopColor="#FFFFFF" />
                </radialGradient>
              </defs>

              <circle r={radius - 4} fill={`url(#avatar-${founder.id})`} />
              <text
                textAnchor="middle"
                dy="4"
                fontSize="11"
                fontWeight="600"
                fill={ringColor}
                fontFamily="Geist, Inter, sans-serif"
              >
                {founder.name
                  .split(" ")
                  .map((token) => token[0])
                  .join("")}
              </text>
            </g>
          );
        })}
      </svg>

      {hoverNode && nodeMap[hoverNode] ? (
        <FounderTip
          founder={nodeMap[hoverNode]}
          pos={pos(nodeMap[hoverNode])}
          startups={startups}
        />
      ) : null}

      <div className="graph-controls">
        <button
          onClick={() => setZoom((current) => Math.min(2.4, current + 0.15))}
        >
          <IconZoomIn size={14} />
        </button>
        <button
          onClick={() => setZoom((current) => Math.max(0.5, current - 0.15))}
        >
          <IconZoomOut size={14} />
        </button>
        <button
          onClick={() => {
            setPan({ x: 0, y: 0 });
            setZoom(1);
          }}
        >
          <IconRecenter size={14} />
        </button>
        <button>
          <IconExpand size={14} />
        </button>
      </div>

      <div className="graph-legend">
        <div>
          <span className="dot-cyan" /> Baseline
        </div>
        <div>
          <span className="dot-blue" /> Discovered
        </div>
        <div>
          <span className="dot-purple" /> Affiliated
        </div>
        <div>
          <span className="dot-pulse" /> High-potential
        </div>
      </div>

      <div className="graph-stats">
        <div className="stat-row">
          <span>Nodes</span>
          <b>{founders.length}</b>
        </div>
        <div className="stat-row">
          <span>Edges</span>
          <b>{edges.length}</b>
        </div>
        <div className="stat-row">
          <span>Depth</span>
          <b>2 hops</b>
        </div>
        <div className="stat-row">
          <span>Avg score</span>
          <b>85.3</b>
        </div>
      </div>
    </div>
  );
}

function FounderTip({
  founder,
  pos,
  startups,
}: {
  founder: Founder;
  pos: { x: number; y: number };
  startups: Startup[];
}) {
  const startupName = startups.find((s) => s.id === founder.startup)?.name;

  return (
    <div className="founder-tip" style={{ left: pos.x + 26, top: pos.y - 30 }}>
      <div className="tip-head">
        <div
          className="tip-avatar"
          style={{ borderColor: LEVEL_COLOR[founder.level] }}
        >
          {founder.name
            .split(" ")
            .map((token) => token[0])
            .join("")}
        </div>
        <div>
          <div className="tip-name">{founder.name}</div>
          <div className="tip-sub">
            {founder.role}
            {startupName ? ` · ${startupName}` : ""}
          </div>
        </div>
      </div>

      <div className="tip-grid">
        <div>
          <span>AI score</span>
          <b style={{ color: "#22D3EE" }}>{founder.score}</b>
        </div>
        <div>
          <span>Network</span>
          <b>{founder.network}</b>
        </div>
      </div>

      <div className="tip-tags">
        {founder.expertise.slice(0, 3).map((tag) => (
          <span key={tag} className="mini-tag">
            {tag}
          </span>
        ))}
      </div>

      <div className="tip-foot">{founder.prev}</div>
    </div>
  );
}

export function ActiveTab({
  startups,
  founders,
  edges,
}: {
  startups: Startup[];
  founders: Founder[];
  edges: [string, string][];
}) {
  const [filters, setFilters] = useState<FiltersState>({
    stages: ["Seed", "Pre-seed"],
    industries: ["AI Infra", "Bio × AI"],
    minScore: 80,
    depth: 2,
    signals: ["Network warmth"],
  });
  const [selectedStartup, setSelectedStartup] = useState("s1");
  const [hoverNode, setHoverNode] = useState<string | null>(null);
  const [, setExpandedIds] = useState<Set<string>>(new Set());

  const filteredStartups = startups.filter(
    (startup) => startup.score >= filters.minScore - 5,
  );

  return (
    <div className="active-grid">
      <aside className="left-col">
        <Filters filters={filters} setFilters={setFilters} />
        <StartupList
          items={filteredStartups}
          selectedId={selectedStartup}
          onSelect={setSelectedStartup}
        />
      </aside>

      <section className="graph-col">
        <div className="graph-header">
          <div className="bread">
            <span className="muted">Network</span>
            <span className="sep">/</span>
            <span>
              {startups.find((s) => s.id === selectedStartup)?.name ?? "—"}
            </span>
          </div>
          <div className="graph-actions">
            <button className="pill-btn">
              <span className="kbd">G</span> Graph
            </button>
            <button className="pill-btn ghost">Cluster</button>
            <button className="pill-btn ghost">List</button>
          </div>
        </div>

        <Graph
          founders={founders}
          startups={startups}
          edges={edges}
          selectedStartup={selectedStartup}
          hoverNode={hoverNode}
          setHoverNode={setHoverNode}
          setExpandedIds={setExpandedIds}
        />
      </section>
    </div>
  );
}
