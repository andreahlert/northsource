import { cookies } from "next/headers";
import { getRequestConfig } from "next-intl/server";
import type { Lang } from "@/lib/types";

export async function currentLang(): Promise<Lang> {
  const store = await cookies();
  return store.get("NEXT_LOCALE")?.value === "fr" ? "fr" : "en";
}

export default getRequestConfig(async () => {
  const locale = await currentLang();
  return {
    locale,
    messages: (await import(`../messages/${locale}.json`)).default,
  };
});
