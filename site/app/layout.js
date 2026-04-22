import "./globals.css";

import Footer from "@/components/Footer";
import Header from "@/components/Header";
import JsonLd from "@/components/JsonLd";
import { legalServiceSchema } from "@/lib/schema";
import { SITE } from "@/lib/site-data";

export const metadata = {
  metadataBase: new URL(SITE.url),
  title: {
    default: `${SITE.name} — банкротство, разводы, раздел имущества`,
    template: `%s | ${SITE.name}`
  },
  description:
    "Юридическая помощь физическим лицам: банкротство, развод, раздел имущества. Онлайн-диагностика, стратегия и сопровождение.",
  applicationName: SITE.name,
  alternates: {
    canonical: "/"
  },
  openGraph: {
    type: "website",
    locale: "ru_RU",
    url: SITE.url,
    siteName: SITE.name,
    title: `${SITE.name} — стратегия защиты для частных клиентов`,
    description:
      "Банкротство физлиц, разводы и раздел имущества. Сайт с первичной диагностикой и SEO-ready архитектурой.",
    images: ["/logo.jpg"]
  },
  robots: {
    index: true,
    follow: true
  }
};

export default function RootLayout({ children }) {
  return (
    <html lang="ru">
      <body>
        <JsonLd data={legalServiceSchema()} />
        <Header />
        {children}
        <Footer />
      </body>
    </html>
  );
}
