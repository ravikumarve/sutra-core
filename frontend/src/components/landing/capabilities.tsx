const capabilities = [
  {
    id: "LOG_01 // CONVERSATIONAL NLP",
    title: "Voice-to-Order Processing",
    span: "col-span-8",
    description:
      "Process colloquial, localized dialect maps in Hinglish effortlessly. SUTRA Core cleans ambient background noise structures, runs asynchronous transcription tasks on standard CPU servers, and maps candidate phrases straight into structured catalog rows in under 30 seconds.",
  },
  {
    id: "LOG_02 // ACID RELIABILITY",
    title: "Auto Inventory",
    span: "col-span-4",
    description:
      "Stock balances are safely deducted from isolated transactional database models upon order confirmation, firing warning notifications before stockouts happen.",
  },
  {
    id: "LOG_03 // LIQUIDITY PROPERTIES",
    title: "Udhaar Credit Management",
    span: "col-span-6",
    description:
      "Tracks open client credit profiles, monitors ledger payment aging parameters, and deploys context-aware, polite outstanding reminders over WhatsApp conversations automatically.",
  },
  {
    id: "LOG_04 // LOCAL REGULATORY COMPLIANCE",
    title: "GST Invoicing Docs",
    span: "col-span-6",
    description:
      "Compiles complicated inventory line items and tax splits into legally verified, compliant business invoices, sending clean PDFs down the same active chat thread instantly.",
  },
];

export function Capabilities() {
  return (
    <section id="capabilities" className="py-20 border-b border-border-dim">
      <div className="mb-20">
        <h2 className="text-[3.2rem] font-bold leading-[1.1] mb-5 text-titanium">
          Built for the <span className="text-emerald drop-shadow-[0_0_25px_rgba(0,230,118,0.3)]">MSME Bazaar.</span>
        </h2>
        <p className="text-text-muted text-lg font-light max-w-2xl">
          Traditional ERP applications create workflow friction. SUTRA removes
          adoption friction by running complete enterprise tracking directly over
          chat tools.
        </p>
      </div>

      <div className="grid grid-cols-12 gap-6 max-md:flex max-md:flex-col">
        {capabilities.map((cap) => (
          <div
            key={cap.id}
            className={`${cap.span} bg-bg-surface border border-border-dim rounded-2xl p-14 transition-all duration-500 hover:border-border-glow hover:-translate-y-1 hover:shadow-[0_30px_60px_rgba(0,0,0,0.5)] max-md:p-10`}
          >
            <span className="font-mono text-xs text-text-faint block mb-8 tracking-wider">
              {cap.id}
            </span>
            <h3 className="text-[1.65rem] font-bold mb-4 text-titanium">
              {cap.title}
            </h3>
            <p className="text-text-muted text-base leading-relaxed font-light">
              {cap.description}
            </p>
          </div>
        ))}
      </div>
    </section>
  );
}
