import Image from "next/image";
import { getTranslations } from "next-intl/server";
import doors from "@/public/img/hero-doors.jpg";
import importer from "@/public/img/hero-importer.jpg";

export async function DoorsBand() {
  const t = await getTranslations("home");
  return (
    <section className="mt-24 -mx-4 bg-ink px-4 py-16 text-paper sm:rounded-lg sm:px-10">
      <div className="grid items-center gap-10 md:grid-cols-2">
        <div className="relative">
          <Image
            src={doors}
            alt={t("doorsAlt")}
            placeholder="blur"
            sizes="(min-width: 768px) 480px, 100vw"
            className="relative z-10 aspect-[4/3] w-full rounded-md object-cover"
          />
          <span aria-hidden className="absolute -bottom-3 -left-3 h-full w-full rounded-md border-2 border-maple" />
        </div>
        <div>
          <p className="eyebrow">northsource</p>
          <h2 className="mt-3 text-balance font-display text-4xl font-medium leading-tight sm:text-5xl">
            {t("doorsTitle")}
          </h2>
          <p className="mt-5 max-w-prose text-lg leading-relaxed text-paper/80">{t("doorsBody")}</p>
          <a
            href="#top"
            className="mt-8 inline-flex h-12 items-center rounded-md bg-maple px-6 font-semibold text-white transition-colors hover:bg-maple-dark"
          >
            {t("doorsCta")}
          </a>
        </div>
      </div>
    </section>
  );
}

export async function ImporterBlock() {
  const t = await getTranslations("home");
  const bullets = [t("importer1"), t("importer2"), t("importer3")];
  return (
    <section className="mt-24 grid items-center gap-10 md:grid-cols-2">
      <div className="md:order-2">
        <Image
          src={importer}
          alt={t("importerAlt")}
          placeholder="blur"
          sizes="(min-width: 768px) 480px, 100vw"
          className="aspect-[4/3] w-full rounded-md object-cover"
        />
      </div>
      <div className="md:order-1">
        <h2 className="text-balance font-display text-3xl font-medium tracking-tight text-ink sm:text-4xl">
          {t("importerTitle")}
        </h2>
        <p className="mt-4 text-lg text-ink-2">{t("importerBody")}</p>
        <ul className="mt-6 space-y-3">
          {bullets.map((b) => (
            <li key={b} className="flex gap-3">
              <span aria-hidden className="mt-2 h-2 w-2 shrink-0 rounded-full bg-maple" />
              <span className="text-ink">{b}</span>
            </li>
          ))}
        </ul>
      </div>
    </section>
  );
}
