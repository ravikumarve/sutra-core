import Link from "next/link";

export function Navbar() {
  return (
    <nav className="flex justify-between items-center py-8 border-b border-border-dim relative z-20">
      <Link href="#" className="flex items-center gap-3 text-lg font-bold text-text-main no-underline tracking-tight">
        <div className="w-3.5 h-3.5 border-2 border-emerald rounded-full shadow-[0_0_10px_var(--emerald-dim)]" />
        SUTRA Core
      </Link>

      <div className="flex gap-14 max-md:hidden">
        {["Capabilities", "Architecture", "Pricing"].map((item) => (
          <a
            key={item}
            href={`#${item.toLowerCase()}`}
            className="text-text-muted no-underline text-sm font-medium transition-colors duration-300 font-mono uppercase tracking-wider hover:text-text-main"
          >
            {item}
          </a>
        ))}
      </div>

      <div className="flex gap-4">
        <a
          href="https://github.com/ravikumarve/sutra-core"
          className="btn-outline"
        >
          GitHub
        </a>
        <a
          href="https://gumroad.com/l/sutra-core"
          className="btn-primary"
        >
          Deploy Instance
        </a>
      </div>
    </nav>
  );
}
