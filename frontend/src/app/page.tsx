import { Navbar } from "@/components/landing/navbar";
import { Hero } from "@/components/landing/hero";
import { Capabilities } from "@/components/landing/capabilities";
import { Architecture } from "@/components/landing/architecture";
import { Pricing } from "@/components/landing/pricing";
import { CTABand } from "@/components/landing/cta-band";
import { Footer } from "@/components/landing/footer";
import { SwarmCanvas } from "@/components/landing/swarm-canvas";

export default function Home() {
  return (
    <>
      {/* Fixed Background */}
      <SwarmCanvas />
      <div className="dot-matrix-overlay" />
      <div className="ambient-core" />

      <div className="max-w-[1240px] mx-auto px-8 relative z-10 w-full">
        <Navbar />
        <Hero />
        <Capabilities />
        <Architecture />
        <Pricing />
        <CTABand />
        <Footer />
      </div>
    </>
  );
}
