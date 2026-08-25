import { describe, expect, it } from "vitest";
import { desc, fmtCad, fmtUsd, monthLabel, periodLabel, shortName } from "./format";

describe("money", () => {
  it("formats CAD compactly in English", () => {
    expect(fmtCad(36_000_000, "en")).toBe("CA$36M");
    expect(fmtCad(10_800_000, "en")).toBe("CA$10.8M");
    expect(fmtCad(0, "en")).toBe("CA$0");
  });
  it("formats CAD in French", () => {
    expect(fmtCad(36_000_000, "fr")).toMatch(/36\s?M\s?CAD/);
  });
  it("formats USD or returns null", () => {
    expect(fmtUsd(1.5e9, "en")).toBe("US$1.5B");
    expect(fmtUsd(null, "en")).toBeNull();
  });
  it("preserves a leading minus sign in English", () => {
    expect(fmtCad(-1_234_567, "en")).toBe("-CA$1.2M");
  });
  it("labels CAD and USD with distinct currency codes in French", () => {
    expect(fmtCad(36_000_000, "fr")).toMatch(/CAD/);
    expect(fmtUsd(1.5e9, "fr")).toMatch(/USD/);
    expect(fmtCad(36_000_000, "fr")).not.toBe(fmtUsd(36_000_000, "fr"));
  });
});

describe("dates", () => {
  it("labels months", () => {
    expect(monthLabel(2025, 7, "en")).toBe("Jul 2025");
    expect(monthLabel(2025, 7, "fr").toLowerCase()).toContain("juil");
    expect(periodLabel("2026-06", "en")).toBe("Jun 2026");
  });
});

describe("text", () => {
  it("builds a short product name for titles", () => {
    expect(shortName("Cheese, fresh, unripened or uncured, including whey cheese and curd")).toBe("cheese");
    expect(shortName("Iron and non-alloy steel in ingots")).toBe("iron and non-alloy steel in ingots");
    expect(shortName("Motor cars; of a cylinder capacity exceeding 1,000 cc")).toBe("motor cars");
    expect(shortName("Parts of aircraft")).toBe("parts");
    expect(shortName("A".repeat(60)).length).toBe(40);
  });
  it("picks the description for the locale", () => {
    expect(desc({ desc_en: "Cheese", desc_fr: "Fromage" }, "fr")).toBe("Fromage");
    expect(desc({ desc_en: "Cheese", desc_fr: "" }, "fr")).toBe("Cheese");
  });
});
