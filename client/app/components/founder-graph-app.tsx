"use client";

import { useState } from "react";
import type { Dispatch, SetStateAction } from "react";
import founderGraphData from "../data/founder-graph.json";
import { ActiveTab } from "./active-tab";
import { IconBell, IconSearch, IconSparkle } from "./icons";
import { PassiveTab } from "./passive-tab";
import type { FounderGraphData } from "./types";

function Logo() {
  return (
    <div className="logo-mark">
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
        <defs>
          <linearGradient id="lg" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stopColor="#0891B2" />
            <stop offset="100%" stopColor="#7C3AED" />
          </linearGradient>
        </defs>
        <path
          d="M6 6 L12 13 L18 6 M12 13 L6 19 M12 13 L18 18"
          stroke="rgba(15,23,42,0.18)"
          strokeWidth="0.9"
        />
        <circle cx="6" cy="6" r="2.2" fill="#0891B2" />
        <circle cx="18" cy="6" r="1.8" fill="#2563EB" />
        <circle cx="12" cy="13" r="2.8" fill="url(#lg)" />
        <circle cx="6" cy="19" r="1.8" fill="#0891B2" />
        <circle cx="18" cy="18" r="2.2" fill="#7C3AED" />
      </svg>
      <span className="logo-text">FounderGraph</span>
    </div>
  );
}

function TopNav({
  tab,
  setTab,
}: {
  tab: "active" | "passive";
  setTab: Dispatch<SetStateAction<"active" | "passive">>;
}) {
  return (
    <header className="topnav">
      <div className="nav-left">
        <Logo />
        <div className="org-pill">
          <span className="org-dot" /> Sequoia · seed fund
          <span className="chev">⌄</span>
        </div>
      </div>

      <nav className="nav-tabs">
        <button
          className={`tab ${tab === "active" ? "on" : ""}`}
          onClick={() => setTab("active")}
        >
          <span className="tab-dot" /> Active
        </button>
        <button
          className={`tab ${tab === "passive" ? "on" : ""}`}
          onClick={() => setTab("passive")}
        >
          <span className="tab-dot p" /> Passive
        </button>
      </nav>

      <div className="nav-right">
        <div className="search">
          <IconSearch size={13} stroke="#9CA3AF" />
          <input placeholder="Search founders, startups, signals…" />
          <span className="kbd">⌘K</span>
        </div>
        <button className="icon-btn">
          <IconBell size={15} stroke="#9CA3AF" />
        </button>
        <button className="ai-btn">
          <IconSparkle size={14} stroke="#FFFFFF" />
          <span>Ask AI</span>
        </button>
      </div>
    </header>
  );
}

export function FounderGraphApp() {
  const [tab, setTab] = useState<"active" | "passive">("active");
  const data = founderGraphData as unknown as FounderGraphData;

  return (
    <div className="app">
      <TopNav tab={tab} setTab={setTab} />
      <main className="main">
        {tab === "active" ? (
          <ActiveTab
            startups={data.STARTUPS}
            founders={data.FOUNDERS}
            edges={data.EDGES}
          />
        ) : (
          <PassiveTab
            applications={data.APPLICATIONS}
            appFounders={data.APP_FOUNDERS}
          />
        )}
      </main>
    </div>
  );
}
