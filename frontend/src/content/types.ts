export const ROLE_SLUGS = [
  "sde-1",
  "sde-2",
  "senior",
  "staff",
  "principal",
] as const;

export type RoleSlug = (typeof ROLE_SLUGS)[number];

export const TRACK_SLUGS = ["coding", "lld", "hld", "behavioral"] as const;

export type TrackSlug = (typeof TRACK_SLUGS)[number];

export type Difficulty = "foundation" | "core" | "stretch";

export type Role = {
  slug: RoleSlug;
  title: string;
  shortTitle: string;
  band: string;
  summary: string;
  interviewMix: { track: TrackSlug; weight: number }[];
  bar: string[];
};

export type Track = {
  slug: TrackSlug;
  title: string;
  shortTitle: string;
  summary: string;
};

export type Question = {
  slug: string;
  title: string;
  track: TrackSlug;
  summary: string;
  difficulty: Difficulty;
  roles: RoleSlug[];
  timeboxMinutes: number;
  prompt: string;
  outline: string[];
  levelBar: Partial<Record<RoleSlug, string>>;
  sources: string[];
  /** Optional structured breakdown for deep-dive pages */
  breakdown?: QuestionBreakdown;
};

/* ─── Structured Breakdown Types ──────────────────────────────── */

export type QuestionBreakdown = {
  sections: BreakdownSection[];
  focusAreas: string[];
  targetRole: string;
  totalSections: number;
  completedSections: number;
};

export type BreakdownSection = {
  id: string;
  stepNumber: number;
  label: string;
  title: string;
  content?: string;
  blocks: ContentBlock[];
};

/** Discriminated union for all renderable content blocks */
export type ContentBlock =
  | TextBlock
  | RequirementsBlock
  | FunctionalNonFunctionalBlock
  | EntityTableBlock
  | ApiTableBlock
  | EvolutionBlock
  | ArchitectureFlowBlock
  | ComparisonBlock
  | CalloutBlock
  | UploadComparisonBlock;

export type TextBlock = {
  type: "text";
  content: string;
};

export type RequirementsBlock = {
  type: "requirements";
  core: string[];
  outOfScope: string[];
};

export type FunctionalNonFunctionalBlock = {
  type: "functional-nonfunctional";
  functional: string[];
  nonFunctional: string[];
};

export type EntityTableBlock = {
  type: "entity-table";
  entities: { name: string; purpose: string }[];
};

export type ApiEndpoint = {
  method: "GET" | "POST" | "PUT" | "DELETE" | "PATCH";
  endpoint: string;
  description: string;
};

export type ApiTableBlock = {
  type: "api-table";
  endpoints: ApiEndpoint[];
};

export type EvolutionOption = {
  number: string;
  label: string;
  description: string;
  pros: string[];
  cons: string[];
  recommended?: boolean;
};

export type EvolutionBlock = {
  type: "evolution";
  options: EvolutionOption[];
};

export type ArchitectureNode = {
  label: string;
  type: "critical" | "supporting";
};

export type ArchitectureConnection = {
  from: string;
  to: string;
  style: "bidirectional" | "unidirectional";
};

export type ArchitectureFlowBlock = {
  type: "architecture-flow";
  nodes: ArchitectureNode[];
  connections: ArchitectureConnection[];
  explanation?: string;
};

export type ComparisonOption = {
  label: string;
  description: string;
};

export type ComparisonBlock = {
  type: "comparison";
  title: string;
  optionA: ComparisonOption;
  optionB: ComparisonOption;
  recommendation: string;
  rationale: string;
};

export type CalloutBlock = {
  type: "callout";
  variant: "warning" | "info" | "definition";
  title: string;
  content: string;
};

export type UploadComparisonBlock = {
  type: "upload-comparison";
  options: {
    label: string;
    description: string;
    details?: string;
    recommended?: boolean;
  }[];
};

/* ─── Navigation Categories ──────────────────────────────────── */

export type NavCategory = {
  label: string;
  items: NavItem[];
};

export type NavItem = {
  href: string;
  label: string;
  icon: string;
};
