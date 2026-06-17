const agents = [
  {
    num: "01",
    name: "The Liaison Agent",
    description:
      "Ingests message events from Meta webhooks, handles noise removal, and translates colloquial dialect maps asynchronously.",
  },
  {
    num: "02",
    name: "The Strategist Agent",
    description:
      "Evaluates incoming intent payloads across strict ACID parameters, auditing current inventory levels and Udhaar caps.",
  },
  {
    num: "03",
    name: "The Auditor Agent",
    description:
      "Logs final database updates, maps compliance metrics, compiles print-ready GST invoices, and signals the outbound gateway.",
  },
];

const stack = [
  { label: "Backend Core API", value: "FastAPI (Python 3.12+)" },
  { label: "Relational Ledger Store", value: "PostgreSQL 15 (Schema Multi-tenancy)" },
  { label: "Asynchronous Message Bus", value: "Redis Streams (Per-tenant namespaced)" },
  { label: "Acoustic NLP Service", value: "OpenAI Whisper (CPU Optimized)" },
  { label: "Review Dashboard Interface", value: "Next.js 14 + shadcn/ui" },
  { label: "Observability Suite", value: "Prometheus + Grafana + Alertmanager" },
];

export function Architecture() {
  return (
    <section
      id="architecture"
      className="grid grid-cols-[1fr_1.2fr] gap-20 items-start py-20 border-b border-border-dim max-lg:grid-cols-1"
    >
      {/* Left: Agent Flow */}
      <div>
        <h2 className="text-[3.2rem] font-bold leading-[1.1] mb-6 text-titanium">
          Asynchronous <br />
          <span className="text-emerald drop-shadow-[0_0_25px_rgba(0,230,118,0.3)]">Multi-Agent Mesh.</span>
        </h2>
        <p className="text-text-muted text-lg leading-relaxed mb-12 font-light">
          SUTRA Core acts as an event-driven system architecture. Components run
          detached from one another, passing lightweight messages over fast
          namespaced Redis Stream paths.
        </p>

        <div className="flex flex-col gap-5 relative mb-12">
          {/* Connector line */}
          <div className="absolute left-6 top-0 bottom-0 w-px bg-border-dim z-0" />

          {agents.map((agent) => (
            <div key={agent.num} className="flex gap-6 items-start relative z-10">
              <div className="w-12 h-12 bg-bg-void border border-border-dim rounded-lg flex items-center justify-center font-mono text-sm text-emerald font-bold transition-colors duration-300 hover:border-emerald flex-shrink-0">
                {agent.num}
              </div>
              <div>
                <h4 className="font-mono text-sm text-text-main uppercase mb-1 tracking-wider">
                  {agent.name}
                </h4>
                <p className="text-text-muted text-sm leading-relaxed font-light">
                  {agent.description}
                </p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Right: Tech Stack Card */}
      <div className="bg-[#020204] border border-border-dim rounded-xl p-10 shadow-[inset_0_0_40px_rgba(255,255,255,0.01)]">
        <h3 className="text-xl font-mono font-medium uppercase mb-6 tracking-wider text-emerald">
          Infrastructure Blueprint
        </h3>
        <ul className="space-y-0">
          {stack.map((item) => (
            <li
              key={item.label}
              className="flex justify-between py-[1.1rem] border-b border-dashed border-border-dim text-text-muted last:border-b-0 max-md:flex-col max-md:gap-1"
            >
              <span>{item.label}</span>
              <span className="text-text-main font-mono text-sm">{item.value}</span>
            </li>
          ))}
        </ul>
      </div>
    </section>
  );
}
