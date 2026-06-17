const tiers = [
  {
    name: "Starter",
    price: "₹499",
    volume: "500 orders / month ceiling",
    popular: false,
    features: [
      "1 Connected WhatsApp Line",
      "Standard Hinglish STT Translation",
      "Basic PDF Invoice Structuring",
      "Community Support Channel",
    ],
    cta: "Provision Tier",
    href: "https://gumroad.com/l/sutra-core",
    variant: "outline" as const,
  },
  {
    name: "Growth",
    price: "₹1,499",
    volume: "2,000 orders / month ceiling",
    popular: true,
    features: [
      "3 Connected WhatsApp Lines",
      "3 Active Dashboard Review Seats",
      "Full Udhaar & Credit Balances Engine",
      "Priority Server Support SLA",
    ],
    cta: "Provision Tier",
    href: "https://gumroad.com/l/sutra-core",
    variant: "primary" as const,
  },
  {
    name: "Business",
    price: "₹4,999",
    volume: "Unlimited Volume",
    popular: false,
    features: [
      "Infinite Phone Inbound Integrations",
      "Bespoke Legacy ERP Adapters",
      "99.9% Infrastructure SLA Guarantee",
      "24/7 Dedicated Support Loops",
    ],
    cta: "Contact Operations",
    href: "#",
    variant: "outline" as const,
  },
];

export function Pricing() {
  return (
    <section id="pricing" className="py-20 border-b border-border-dim">
      <div className="text-center max-w-[600px] mx-auto mb-16">
        <h2 className="text-[3.2rem] font-bold leading-[1.1] mb-5 text-titanium">
          Commercial Models.
        </h2>
        <p className="text-text-muted text-lg font-light">
          Simple consumption pricing tiers. Scale your instance effortlessly as
          your transaction throughput grows.
        </p>
      </div>

      <div className="grid grid-cols-3 gap-8 mt-16 items-start max-lg:flex max-lg:flex-col">
        {tiers.map((tier) => (
          <div
            key={tier.name}
            className={`relative overflow-hidden bg-bg-surface border rounded-xl p-12 transition-all duration-300 hover:border-border-glow hover:-translate-y-1 hover:shadow-[0_30px_60px_rgba(0,0,0,0.5)] ${
              tier.popular
                ? "border-[rgba(0,230,118,0.25)] bg-[linear-gradient(180deg,rgba(0,230,118,0.04)_0%,transparent_100%)]"
                : "border-border-dim"
            }`}
          >
            {tier.popular && (
              <div className="absolute top-0 left-0 right-0 bg-emerald text-black font-mono text-[0.65rem] font-bold text-center py-1.5 tracking-wider">
                MOST POPULAR
              </div>
            )}

            <div className={`text-lg font-semibold mb-4 uppercase tracking-wider ${tier.popular ? "text-emerald" : "text-titanium"}`}>
              {tier.name}
            </div>
            <div className="font-mono text-[2.5rem] font-bold text-text-main mb-1 tracking-tight">
              {tier.price}
              <span className="text-sm text-text-muted font-sans font-normal tracking-normal">
                /mo
              </span>
            </div>
            <div className="text-emerald text-sm font-mono mb-10 font-medium">
              {tier.volume}
            </div>

            <ul className="space-y-3 mb-12">
              {tier.features.map((f) => (
                <li
                  key={f}
                  className="text-text-muted text-sm flex gap-2.5 font-light"
                >
                  <span className="text-text-faint font-mono">→</span>
                  {f}
                </li>
              ))}
            </ul>

            <a
              href={tier.href}
              className={`block text-center w-full py-3 px-6 font-mono text-xs uppercase tracking-wider rounded-full border transition-all duration-500 no-underline ${
                tier.variant === "primary"
                  ? "bg-titanium text-bg-void border-transparent hover:bg-transparent hover:text-titanium hover:border-titanium hover:-translate-y-0.5"
                  : "bg-[rgba(255,255,255,0.02)] text-text-muted border-border-dim backdrop-blur-md hover:border-emerald hover:text-emerald hover:bg-emerald-dim"
              }`}
            >
              {tier.cta}
            </a>
          </div>
        ))}

        {/* Self-hosted box */}
        <div className="col-span-3 bg-[rgba(255,255,255,0.01)] border border-dashed border-border-dim rounded-xl p-8 mt-8 flex justify-between items-center max-lg:flex-col max-lg:text-center max-lg:gap-6">
          <div>
            <h4 className="font-mono text-sm text-text-main uppercase mb-1">
              Looking for full operational independence?
            </h4>
            <p className="text-text-muted text-sm font-light">
              SUTRA Core is open-source under the MIT license schema, allowing
              self-hosted deployments.
            </p>
          </div>
          <a
            href="https://github.com/ravikumarve/sutra-core"
            className="px-6 py-3 bg-[rgba(255,255,255,0.02)] text-text-muted border border-border-dim rounded backdrop-blur-md font-mono text-xs uppercase tracking-wider no-underline transition-all duration-300 hover:border-emerald hover:text-emerald hover:bg-emerald-dim"
          >
            Get Open Source Code
          </a>
        </div>
      </div>
    </section>
  );
}
