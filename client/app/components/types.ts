export type Trend = "up" | "down" | "flat";

export type FounderLevel = "baseline" | "discovered" | "startup" | "high";

export type Startup = {
  id: string;
  name: string;
  logo: string;
  industry: string;
  stage: string;
  score: number;
  founded: string;
  location: string;
  traction: string;
  trend: Trend;
  color: string;
};

export type Founder = {
  id: string;
  name: string;
  role: string;
  startup: string | null;
  score: number;
  network: number;
  expertise: string[];
  prev: string;
  level: FounderLevel;
  x: number;
  y: number;
};

export type Application = {
  id: string;
  name: string;
  logo: string;
  industry: string;
  stage: string;
  score: number;
  trend: Trend;
  delta: string;
  color: string;
  submitted: string;
};

export type ShapSignal = {
  dir: "up" | "down";
  text: string;
  value: number;
};

export type IntentSignal = {
  label: string;
  when: string;
};

export type DimensionalScore = {
  label: string;
  value: number;
};

export type AppFounder = {
  id: string;
  name: string;
  initials?: string;
  role: string;
  education?: string;
  prevCompanies?: string;
  badge?: string;
  score: number;
  network: number;
  technical: number;
  business: number;
  leadership: number;
  ai: number;
  ops: number;
  expertise: string[];
  prev: string;
  individualScore?: number;
  dataCompleteness?: number;
  firstSignalMonths?: number;
  dimensions?: DimensionalScore[];
  shapSignals?: ShapSignal[];
  intentSignals?: IntentSignal[];
  missingData?: string[];
  projectedScoreRange?: [number, number];
};

export type FounderGraphData = {
  STARTUPS: Startup[];
  FOUNDERS: Founder[];
  EDGES: [string, string][];
  APPLICATIONS: Application[];
  APP_FOUNDERS: Record<string, AppFounder[]>;
};
