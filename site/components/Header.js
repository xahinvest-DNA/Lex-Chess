import Image from "next/image";
import Link from "next/link";

import { SITE, navigation } from "@/lib/site-data";

export default function Header() {
  return (
    <header className="site-header">
      <Link className="brand" href="/" aria-label="На главную">
        <Image src="/logo.jpg" alt="" width={54} height={54} priority />
        <span>
          <strong>{SITE.name}</strong>
          <small>{SITE.tagline}</small>
        </span>
      </Link>

      <nav className="desktop-nav" aria-label="Основная навигация">
        {navigation.map((item) => (
          <Link key={item.href} href={item.href}>
            {item.label}
          </Link>
        ))}
      </nav>

      <a className="header-phone" href={`tel:${SITE.phone.replace(/\D/g, "")}`}>
        {SITE.phone}
      </a>
    </header>
  );
}
