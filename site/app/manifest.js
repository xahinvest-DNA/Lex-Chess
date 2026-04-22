import { SITE } from "@/lib/site-data";

export default function manifest() {
  return {
    name: SITE.name,
    short_name: SITE.name,
    description: "Юридическая помощь физическим лицам",
    start_url: "/",
    display: "standalone",
    background_color: "#050505",
    theme_color: "#cfd3d9",
    icons: [
      {
        src: "/logo.jpg",
        sizes: "512x512",
        type: "image/jpeg"
      }
    ]
  };
}
