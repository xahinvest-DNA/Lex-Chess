import { SITE } from "@/lib/site-data";

export default function robots() {
  return {
    rules: {
      userAgent: "*",
      allow: "/"
    },
    sitemap: `${SITE.url}/sitemap.xml`,
    host: SITE.url
  };
}
