"use client";

import { useEffect, useRef } from "react";

export function SwarmCanvas() {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let width = 0;
    let height = 0;
    let time = 0;
    let mouseX = 0;
    let mouseY = 0;
    let animationId: number;

    interface Particle {
      x: number;
      y: number;
      z: number;
      phase: number;
      speed: number;
    }

    let particles: Particle[] = [];

    function init() {
      width = canvas!.width = window.innerWidth;
      height = canvas!.height = window.innerHeight;
      particles = [];

      const numParticles = Math.floor((width * height) / 12000);

      for (let i = 0; i < numParticles; i++) {
        particles.push({
          x: (Math.random() - 0.5) * width,
          y: (Math.random() - 0.5) * height,
          z: Math.random() * 300,
          phase: Math.random() * Math.PI * 2,
          speed: 0.004 + Math.random() * 0.008,
        });
      }
    }

    function handleMouse(e: MouseEvent) {
      mouseX = (e.clientX - width / 2) * 0.08;
      mouseY = (e.clientY - height / 2) * 0.08;
    }

    function animate() {
      animationId = requestAnimationFrame(animate);
      ctx!.clearRect(0, 0, width, height);
      time += 0.0015;

      const centerX = width / 2;
      const centerY = height / 2;
      const fov = 650;

      for (const p of particles) {
        p.phase += p.speed;
        const orbit = 220 + Math.sin(p.phase + time) * 60;

        const cx = orbit * Math.cos(p.phase + mouseX * 0.01);
        const cz = orbit * Math.sin(p.phase) + mouseY * 1.5;
        const cy = 120 * Math.sin(p.phase * 1.4 + time);

        const z3d = cz + 450;
        const scale = fov / (fov + z3d);
        const sx = cx * scale + centerX;
        const sy = cy * scale + centerY;

        ctx!.beginPath();
        ctx!.arc(sx, sy, 1.25 * scale, 0, Math.PI * 2);
        const opacity = Math.max(0.1, Math.min(0.5, 750 / z3d));
        ctx!.fillStyle = `rgba(255, 255, 255, ${opacity})`;
        ctx!.fill();
      }
    }

    window.addEventListener("mousemove", handleMouse);
    window.addEventListener("resize", init);
    init();
    animate();

    return () => {
      window.removeEventListener("mousemove", handleMouse);
      window.removeEventListener("resize", init);
      cancelAnimationFrame(animationId);
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      id="swarm-canvas"
      className="fixed top-0 left-0 w-screen h-screen z-0 pointer-events-none opacity-75"
    />
  );
}
