export function Hero() {
  return (
    <section className="min-h-[85dvh] grid grid-cols-[1fr_1.1fr] gap-16 items-center pb-20 pt-10 max-lg:grid-cols-1 max-lg:gap-16">
      {/* Left: Text + CTA */}
      <div>
        <div className="inline-flex items-center gap-2 px-4 py-1.5 bg-bg-panel border border-border-dim text-text-muted text-xs font-mono mb-10 rounded">
          AI-Powered WhatsApp ERP
        </div>
        <h1 className="text-gradient text-[clamp(3rem,5vw,4.5rem)] font-bold leading-[1.1] mb-8">
          The Headless ERP <br />for Bharat.
        </h1>
        <p className="text-text-muted text-lg leading-relaxed mb-14 font-light max-w-[520px]">
          Voice. Text. Hinglish. Zero training. SUTRA Core transforms colloquial
          chat input into perfectly clean, synchronized enterprise ledger
          parameters safely on a minimal single-node VPS.
        </p>
        <div className="flex gap-4">
          <a href="#capabilities" className="btn-primary">
            Explore Platform
          </a>
          <a
            href="docs/PRODUCTION_DEPLOYMENT_EXECUTION_GUIDE.md"
            className="btn-outline"
          >
            Deployment Spec
          </a>
        </div>
      </div>

      {/* Right: Dual Visual (WhatsApp + Terminal) */}
      <div className="flex items-center justify-end relative w-full max-lg:justify-center max-lg:h-[420px] max-md:flex-col max-md:h-auto max-md:gap-10">
        {/* WhatsApp Mockup */}
        <div className="glass-pane wa-mockup">
          <div className="flex items-center gap-2 pb-3 mb-5 border-b border-border-dim text-sm font-semibold">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="var(--emerald)">
              <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51a12.8 12.8 0 0 0-.57-.01c-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 0 1-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 0 1-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 0 1 2.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0 0 12.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 0 0 5.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 0 0-3.48-8.413Z" />
            </svg>
            <span>SUTRA Active Chat</span>
          </div>

          {/* Incoming voice note */}
          <div className="bg-[#075E54] p-3 rounded-t-xl rounded-bl-xl rounded-br-none text-sm mb-4 ml-auto w-[85%]">
            <div className="flex items-center gap-2">
              <span className="text-sm">▶</span>
              <div className="h-3 w-[90px] bg-[repeating-linear-gradient(90deg,var(--emerald),var(--emerald)_2px,transparent_2px,transparent_4px)]" />
              <span className="text-xs opacity-60">0:08</span>
            </div>
          </div>

          {/* Outgoing order confirmation */}
          <div className="bg-bg-surface border border-border-dim p-3 rounded-tl-xl rounded-br-xl rounded-tr-none text-sm w-[90%]">
            <strong className="text-emerald text-sm">Order Confirmed ✅</strong>
            <span className="block mt-1 text-xs leading-relaxed">
              • 50x Silk Saree (Red)<br />
              • Stock Remaining: 120<br />
              <span className="opacity-50 block mt-1">📄 Invoice_INV001.pdf attached</span>
            </span>
          </div>
        </div>

        {/* Terminal Trace Panel */}
        <div className="glass-pane trace-panel">
          <div className="flex justify-between border-b border-border-dim pb-4 mb-5 text-text-faint">
            <span>EVENT_STREAM // REDIS_BUS</span>
            <span>NOMINAL</span>
          </div>
          {[
            { time: "[00:01]", actor: "LIAISON:", msg: "Audio stream ingested (audio/ogg)" },
            { time: "[00:04]", actor: "LIAISON:", msg: <>STT complete → <span className="text-text-main">"50 piece silk saree red bhej dena"</span></> },
            { time: "[00:06]", actor: "STRATEGIST:", msg: "Inventory schema lock allocated: SKU_SILK_RED (-50)" },
            { time: "[00:08]", actor: "STRATEGIST:", msg: "Credit validation verified. Ledger balances safe." },
            { time: "[00:10]", actor: "AUDITOR:", msg: "Tax rules matched. Dispatching GST PDF receipt." },
          ].map((line, i) => (
            <div key={i} className="font-mono text-xs leading-relaxed text-text-muted">
              <span className="opacity-30 mr-2.5">{line.time}</span>
              <span className="text-emerald font-semibold mr-2.5">{line.actor}</span>
              {line.msg}
            </div>
          ))}
          <div className="mt-2 text-emerald font-mono text-xs">
            <span className="opacity-30 mr-2.5">&gt;</span>
            Pipeline task returned 200 OK. <span className="animate-blinking">_</span>
          </div>
        </div>
      </div>
    </section>
  );
}
