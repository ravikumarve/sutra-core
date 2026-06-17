const footerSections = [
  {
    title: "Platform Spec",
    links: [
      { label: "Capabilities Matrix", href: "#capabilities" },
      { label: "Orchestration Mesh", href: "#architecture" },
      { label: "Commercial Retainers", href: "#pricing" },
    ],
  },
  {
    title: "Development",
    links: [
      { label: "GitHub Repository", href: "https://github.com/ravikumarve/sutra-core" },
      { label: "Deployment PRD Guide", href: "docs/PRODUCTION_DEPLOYMENT_EXECUTION_GUIDE.md" },
      { label: "Security Engineering", href: "docs/PRODUCTION_SECURITY_HARDENING.md" },
      { label: "Telemetry Setup", href: "docs/PRODUCTION_MONITORING_SETUP.md" },
    ],
  },
  {
    title: "Compliance",
    links: [
      { label: "Executive Summary", href: "docs/EXECUTIVE_SUMMARY.md" },
      { label: "Contribution Guide", href: "CONTRIBUTING.md" },
      { label: "MIT License Agreement", href: "LICENSE" },
    ],
  },
];

export function Footer() {
  return (
    <footer>
      <div className="grid grid-cols-[2fr_1fr_1fr_1fr] gap-16 py-16 border-t border-border-dim max-lg:grid-cols-2 max-md:grid-cols-1">
        {/* Brand column */}
        <div>
          <a href="#" className="flex items-center gap-3 text-lg font-bold text-text-main no-underline tracking-tight">
            <div className="w-3.5 h-3.5 border-2 border-emerald rounded-full shadow-[0_0_10px_var(--emerald-dim)]" />
            SUTRA Core
          </a>
          <p className="text-text-muted text-sm mt-6 max-w-[320px] leading-relaxed font-light">
            Systematic Unstructured Text & Resource Allocator. Built for the
            bazaar, deployable anywhere. Empowering local trading networks with
            transaction infrastructure.
          </p>
        </div>

        {/* Link columns */}
        {footerSections.map((section) => (
          <div key={section.title}>
            <h5 className="font-mono text-xs text-text-faint mb-7 tracking-wider uppercase">
              {section.title}
            </h5>
            <ul className="space-y-3">
              {section.links.map((link) => (
                <li key={link.label}>
                  <a
                    href={link.href}
                    className="text-text-muted text-sm no-underline transition-colors duration-200 font-light hover:text-text-main"
                  >
                    {link.label}
                  </a>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>

      {/* Bottom bar */}
      <div className="flex justify-between py-8 border-t border-border-dim font-mono text-xs text-text-faint max-md:flex-col max-md:gap-4 max-md:text-center">
        <div>© 2026 SUTRA CORE NETWORKS. COMPLIANT WITH THE APACHE 2.0 AND MIT SCHEMAS.</div>
        <div>STATUS: NOMINAL</div>
      </div>
    </footer>
  );
}
