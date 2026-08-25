import type { MetadataRoute } from "next";
import { getSitemap } from "@/lib/api";

const SITE = process.env.NEXT_PUBLIC_SITE_URL ?? "http://localhost:3000";

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const ids = await getSitemap();
  return [
    { url: `${SITE}/`, changeFrequency: "daily", priority: 1 },
    ...ids.map((hs6) => ({ url: `${SITE}/hs/${hs6}`, changeFrequency: "monthly" as const, priority: 0.7 })),
  ];
}
