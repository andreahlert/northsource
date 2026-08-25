import type { MetadataRoute } from "next";
import { getSitemap } from "@/lib/api";
import { siteUrl } from "@/lib/site";

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const site = siteUrl();
  const ids = await getSitemap();
  return [
    { url: `${site}/`, changeFrequency: "daily", priority: 1 },
    ...ids.map((hs6) => ({ url: `${site}/hs/${hs6}`, changeFrequency: "monthly" as const, priority: 0.7 })),
  ];
}
