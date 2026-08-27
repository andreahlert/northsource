export interface Category {
  key: "vehicles" | "machinery" | "electronics" | "steel" | "food" | "plastics" | "medical" | "wood";
  /** Representative HS6 with the largest Canadian imports from the US in that group (CIMT 2025-07..2026-06). */
  hs6: string;
}

export const CATEGORIES: Category[] = [
  { key: "vehicles", hs6: "870323" },
  { key: "machinery", hs6: "840734" },
  { key: "electronics", hs6: "851762" },
  { key: "steel", hs6: "760612" },
  { key: "food", hs6: "210690" },
  { key: "plastics", hs6: "392690" },
  { key: "medical", hs6: "300490" },
  { key: "wood", hs6: "481910" },
];
