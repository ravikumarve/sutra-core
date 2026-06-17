export function CTABand() {
  return (
    <section className="py-8 border-none">
      <div className="relative overflow-hidden bg-[linear-gradient(135deg,var(--bg-panel)_0%,var(--bg-void)_100%)] border border-border-dim rounded-2xl py-20 px-16 text-center max-md:py-14 max-md:px-8">
        {/* Ambient glow */}
        <div className="absolute -top-1/2 -left-1/2 w-[200%] h-[200%] bg-[radial-gradient(circle_at_center,rgba(0,230,118,0.03)_0%,transparent_60%)] pointer-events-none" />

        <h2 className="text-[2.75rem] font-bold leading-[1.1] mb-4 text-titanium relative">
          Deploy your node today.
        </h2>
        <p className="text-text-muted text-lg max-w-[600px] mx-auto mb-10 font-light relative">
          Run your headless ERP infrastructure over lightweight, cost-efficient
          nodes starting under ₹800/month in cloud overhead.
        </p>
        <div className="flex gap-4 justify-center flex-wrap relative">
          <a
            href="https://gumroad.com/l/sutra-core"
            className="inline-flex items-center justify-center px-8 py-3 bg-titanium text-bg-void font-mono text-xs uppercase tracking-wider rounded-full no-underline border border-transparent transition-all duration-500 hover:bg-transparent hover:text-titanium hover:border-titanium hover:-translate-y-0.5"
          >
            Deploy Instance Now
          </a>
          <a
            href="https://github.com/ravikumarve/sutra-core"
            className="inline-flex items-center justify-center px-8 py-3 bg-[rgba(255,255,255,0.02)] text-text-muted border border-border-dim rounded-full no-underline font-mono text-xs uppercase tracking-wider backdrop-blur-md transition-all duration-500 hover:border-emerald hover:text-emerald hover:bg-emerald-dim"
          >
            Explore Codebase
          </a>
        </div>
      </div>
    </section>
  );
}
