"use client";

import React from "react";
import Link from "next/link";
import { 
  Shield, Eye, EyeOff, Lock, Server, 
  Database, Activity, ArrowRight, Check, 
  Terminal, Globe, Cpu, AlertTriangle, ChevronRight
} from "lucide-react";
import { motion } from "framer-motion";

export default function LandingPage() {
  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: { staggerChildren: 0.15 }
    }
  };

  const itemVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: { opacity: 1, y: 0, transition: { duration: 0.6 } }
  };

  return (
    <div className="min-h-screen bg-[#030712] text-gray-200 grid-bg selection:bg-cyan-500 selection:text-black">
      {/* Top Navbar */}
      <header className="fixed top-0 left-0 right-0 h-20 border-b border-glass-border bg-gray-950/80 backdrop-blur-md z-50 flex items-center justify-between px-8 md:px-16">
        <div className="flex items-center gap-2">
          <Shield className="w-7 h-7 text-accent-cyan" />
          <span className="text-lg font-bold tracking-widest text-white">BLINDWATCH <span className="text-accent-cyan font-light">AI</span></span>
        </div>
        <nav className="hidden md:flex items-center gap-8 text-xs font-semibold uppercase tracking-wider text-gray-400">
          <a href="#problem" className="hover:text-white transition-colors">The Problem</a>
          <a href="#solution" className="hover:text-white transition-colors">The Solution</a>
          <a href="#architecture" className="hover:text-white transition-colors">OS Architecture</a>
          <a href="#features" className="hover:text-white transition-colors">Features</a>
          <a href="#pricing" className="hover:text-white transition-colors">Pricing</a>
        </nav>
        <Link 
          href="/portal"
          className="bg-accent-cyan hover:bg-cyan-500 text-black font-bold text-xs uppercase tracking-wider px-5 py-3 rounded-md transition-all shadow-[0_0_15px_rgba(6,182,212,0.3)] hover:shadow-[0_0_25px_rgba(6,182,212,0.6)] cursor-pointer"
        >
          Launch Operating System
        </Link>
      </header>

      {/* Hero Section */}
      <section className="pt-40 pb-24 px-8 md:px-16 text-center max-w-5xl mx-auto flex flex-col items-center">
        <motion.div 
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.8 }}
          className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-cyan-950/40 border border-cyan-800/40 text-[10px] uppercase font-bold tracking-widest text-cyan-400 mb-8"
        >
          <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-pulse" />
          PRIVACY-FIRST SURVEILLANCE OPERATING SYSTEM
        </motion.div>
        
        <motion.h1 
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.1 }}
          className="text-4xl md:text-7xl font-extrabold text-white tracking-tight leading-[1.1] mb-6"
        >
          Protect People. <br />
          <span className="text-transparent bg-clip-text bg-gradient-to-r from-accent-cyan to-cyan-400">Not Identities.</span>
        </motion.h1>

        <motion.p 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.2 }}
          className="text-base md:text-xl text-gray-400 max-w-2xl leading-relaxed mb-10"
        >
          BlindWatch AI is the world&apos;s first privacy-first surveillance operating system. Destroy identity, track anonymous behavior signatures, and safeguard public infrastructure without compromised trust.
        </motion.p>

        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.3 }}
          className="flex flex-col sm:flex-row gap-4"
        >
          <Link 
            href="/portal"
            className="bg-accent-cyan hover:bg-cyan-500 text-black font-extrabold text-sm uppercase tracking-widest px-8 py-4 rounded-md transition-all flex items-center gap-2 shadow-[0_0_20px_rgba(6,182,212,0.3)] hover:shadow-[0_0_30px_rgba(6,182,212,0.6)] cursor-pointer"
          >
            <span>Initialize Portal Node</span>
            <ArrowRight className="w-4 h-4" />
          </Link>
          <a 
            href="#architecture"
            className="bg-gray-900/50 hover:bg-gray-950/80 border border-glass-border text-gray-300 hover:text-white font-bold text-sm uppercase tracking-widest px-8 py-4 rounded-md transition-all flex items-center justify-center cursor-pointer"
          >
            Explore System Architecture
          </a>
        </motion.div>
      </section>

      {/* Problem Section */}
      <section id="problem" className="py-24 border-t border-glass-border bg-gray-950/40">
        <div className="max-w-6xl mx-auto px-8 md:px-16 grid grid-cols-1 lg:grid-cols-2 gap-16 items-center">
          <div>
            <div className="inline-block text-[10px] uppercase font-bold tracking-widest text-rose-500 mb-4">THE RETROSPECTIVE SURVEILLANCE RISK</div>
            <h2 className="text-3xl md:text-5xl font-bold text-white tracking-tight mb-6">Traditional Surveillance is a Liability.</h2>
            <p className="text-gray-400 leading-relaxed mb-8">
              Legacy CCTV and facial recognition engines record biometric identities continuously. Storing unencrypted face contours creates catastrophic database leak vectors, violates GDPR/CCPA compliance laws, and compromises public trust.
            </p>
            <div className="space-y-4">
              {[
                "Persistent raw biometric storage (Faces saved forever)",
                "Continuous mass demographic tracking without consent",
                "Opaque access auditing and bypass risks",
                "Excessive and unmonitored data retention timelines"
              ].map((err, i) => (
                <div key={i} className="flex gap-3 items-start">
                  <AlertTriangle className="w-5 h-5 text-rose-500 flex-shrink-0 mt-0.5" />
                  <span className="text-sm text-gray-300">{err}</span>
                </div>
              ))}
            </div>
          </div>
          
          <div className="glass-panel p-8 rounded-xl border border-glass-border relative overflow-hidden cyber-scanlines">
            <h3 className="text-lg font-bold text-white uppercase tracking-wider mb-6 flex items-center gap-2 border-b border-glass-border pb-4">
              <Terminal className="w-5 h-5 text-rose-500" />
              <span>Identity Exposure Analytics</span>
            </h3>
            <div className="space-y-4 font-mono text-xs">
              <div className="text-rose-400">[WARN] Biometric leak detected. Subject profiles in cleartext.</div>
              <div className="text-gray-500">[LOG] IP-Camera Node 14: Exporting raw face signatures.</div>
              <div className="text-gray-500">[LOG] Frame payload cached at local storage: 1.4TB.</div>
              <div className="text-rose-400">[WARN] CCPA section 1798.100 compliance violation.</div>
              <div className="border border-rose-950 bg-rose-950/20 p-4 rounded text-rose-300 leading-relaxed">
                🚨 Security Vulnerability: Raw image captures are accessible via standard network layers. Stored identities lack cryptographic encryption leases.
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Solution Section */}
      <section id="solution" className="py-24 border-t border-glass-border">
        <div className="max-w-6xl mx-auto px-8 md:px-16 grid grid-cols-1 lg:grid-cols-2 gap-16 items-center">
          <div className="order-2 lg:order-1 glass-panel p-8 rounded-xl border border-glass-border relative overflow-hidden">
            <h3 className="text-lg font-bold text-white uppercase tracking-wider mb-6 flex items-center gap-2 border-b border-glass-border pb-4">
              <Shield className="w-5 h-5 text-accent-cyan" />
              <span>Anonymized Entity Sandbox</span>
            </h3>
            <div className="space-y-4 text-xs">
              <div className="flex justify-between items-center bg-gray-950 p-3 rounded border border-glass-border">
                <span className="font-mono text-cyan-400 font-bold">Entity_93A7</span>
                <span className="text-[10px] text-accent-cyan bg-cyan-950/30 border border-cyan-800 px-2 py-0.5 rounded uppercase font-bold">SHIELD ACTIVE</span>
              </div>
              <div className="bg-gray-950 p-3 rounded border border-glass-border space-y-2">
                <span className="block text-[10px] text-gray-500 uppercase font-semibold">Behavior Signature</span>
                <span className="block font-mono text-white">SIG-892F1A9BC (Standard pace, backpack)</span>
              </div>
              <div className="bg-gray-950 p-3 rounded border border-glass-border space-y-2">
                <span className="block text-[10px] text-gray-500 uppercase font-semibold">Biometric Status</span>
                <span className="block text-accent-emerald font-bold flex items-center gap-1.5">
                  <Check className="w-4 h-4" />
                  <span>Face vector payload destroyed permanently</span>
                </span>
              </div>
            </div>
          </div>

          <div className="order-1 lg:order-2">
            <div className="inline-block text-[10px] uppercase font-bold tracking-widest text-accent-cyan mb-4">THE PRIVACY-FIRST SOLUTION</div>
            <h2 className="text-3xl md:text-5xl font-bold text-white tracking-tight mb-6">Security and Privacy. Hand in Hand.</h2>
            <p className="text-gray-400 leading-relaxed mb-8">
              BlindWatch AI processes live frame nodes locally, blurs face quadrants immediately, and compiles behaviors into anonymous signature IDs. Biometrics are destroyed by default. Decrypting real identities requires dual-key approval workflows from auditors and administrators.
            </p>
            <div className="space-y-4">
              {[
                "Realtime face blurring and biometric payload destruction",
                "Anonymous entity behavior profiling (Velocity, path, zone)",
                "Bypass-proof dual-key decryption vaults for compliance audits",
                "Full immutable audit logs keeping operators accountable"
              ].map((item, i) => (
                <div key={i} className="flex gap-3 items-start">
                  <Check className="w-5 h-5 text-accent-emerald flex-shrink-0 mt-0.5" />
                  <span className="text-sm text-gray-300">{item}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* Architecture Section */}
      <section id="architecture" className="py-24 border-t border-glass-border bg-gray-950/40">
        <div className="max-w-6xl mx-auto px-8 md:px-16 text-center">
          <div className="inline-block text-[10px] uppercase font-bold tracking-widest text-accent-cyan mb-4">SYSTEM PIPELINE FLOW</div>
          <h2 className="text-3xl md:text-5xl font-bold text-white tracking-tight mb-16">The 10 Engine Operating System</h2>

          <div className="grid grid-cols-2 md:grid-cols-5 gap-6 text-left">
            {[
              { num: "01", name: "Vision Engine", desc: "Ingests RTSP/video, runs YOLO bounding coordinates" },
              { num: "02", name: "Privacy Engine", desc: "Applies immediate face blur and generates anonymous entities" },
              { num: "03", name: "Behavior Engine", desc: "Constructs spatial movement and zone traffic signatures" },
              { num: "04", name: "Risk Engine", desc: "Calculates anomalies and restricted area access risk (0-100)" },
              { num: "05", name: "Event Engine", desc: "Emits alerts (Violence, Weapon, Panic) to dashboard console" },
              { num: "06", name: "Explainable AI", desc: "Provides factor weight breakdowns for every alert decision" },
              { num: "07", name: "Governance Engine", desc: "Orchestrates dual-key decryption approval rules" },
              { num: "08", name: "Audit Engine", desc: "Logs system actions in bypass-proof ledger" },
              { num: "09", name: "Analytics Engine", desc: "Calculates historical threat trends and camera effectiveness" },
              { num: "10", name: "Simulator Sandbox", desc: "Models safety-privacy tradeoffs under custom parameters" }
            ].map((eng, i) => (
              <div key={i} className="glass-panel p-6 rounded-lg border border-glass-border flex flex-col justify-between">
                <div>
                  <span className="text-xs font-mono font-bold text-cyan-500 block mb-2">{eng.num}</span>
                  <h4 className="text-xs font-bold text-white uppercase tracking-wider mb-2">{eng.name}</h4>
                  <p className="text-[10px] text-gray-500 leading-normal">{eng.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="py-24 border-t border-glass-border">
        <div className="max-w-6xl mx-auto px-8 md:px-16">
          <div className="text-center mb-16">
            <div className="inline-block text-[10px] uppercase font-bold tracking-widest text-accent-cyan mb-4">OS FEATURES</div>
            <h2 className="text-3xl md:text-5xl font-bold text-white tracking-tight">Enterprise Infrastructure Defense</h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {[
              { title: "RTSP Video Ingest", desc: "Connect RTSP network security cameras or upload raw footage. Run custom GPU/CPU inference engines.", icon: Globe },
              { title: "AI Explainability", desc: "AI alerts are completely explainable. Display factor weights and bounding pixel contours on demand.", icon: Cpu },
              { title: "Governance Vault", desc: "Dual keys required to unlock identity. Administrative and compliance approval leases expire automatically.", icon: Lock }
            ].map((feat, i) => (
              <div key={i} className="glass-panel p-8 rounded-lg border border-glass-border hover:border-cyan-500/20 transition-all">
                <feat.icon className="w-8 h-8 text-accent-cyan mb-6" />
                <h3 className="text-sm font-bold text-white uppercase tracking-wider mb-3">{feat.title}</h3>
                <p className="text-xs text-gray-400 leading-relaxed">{feat.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Pricing Section */}
      <section id="pricing" className="py-24 border-t border-glass-border bg-gray-950/40">
        <div className="max-w-6xl mx-auto px-8 md:px-16 text-center">
          <div className="inline-block text-[10px] uppercase font-bold tracking-widest text-accent-cyan mb-4">SUBSCRIPTION ACCESS</div>
          <h2 className="text-3xl md:text-5xl font-bold text-white tracking-tight mb-16">Strategic Surveillance Scales</h2>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 text-left max-w-4xl mx-auto">
            {[
              { plan: "Corporate Node", price: "$1,490", range: "per camera / yr", features: ["Up to 12 Camera Ingests", "Realtime Identity Shield", "14 Day Data Retention", "Auditor Panel Access"] },
              { plan: "Airport & Transport", price: "$2,890", range: "per camera / yr", features: ["Unlimited Camera Nodes", "Behavior Signature Modeling", "30 Day Data Retention", "Dual-Key Governance Vault"] },
              { plan: "Smart City Grid", price: "Custom Integration", range: "SLA agreements", features: ["Regional camera mesh nodes", "High-density crowd anomaly logs", "Custom data lifecycle rules", "24/7 dedicated security daemon"] }
            ].map((tier, i) => (
              <div key={i} className={`glass-panel p-8 rounded-lg border flex flex-col justify-between ${i === 1 ? 'border-accent-cyan shadow-[0_0_20px_rgba(6,182,212,0.1)]' : 'border-glass-border'}`}>
                <div>
                  <h4 className="text-xs font-bold text-white uppercase tracking-wider mb-4">{tier.plan}</h4>
                  <div className="mb-6">
                    <span className="text-3xl font-black text-white">{tier.price}</span>
                    <span className="text-[10px] text-gray-500 ml-2">{tier.range}</span>
                  </div>
                  <ul className="space-y-3 mb-8">
                    {tier.features.map((f, idx) => (
                      <li key={idx} className="flex gap-2.5 items-center text-xs text-gray-300">
                        <Check className="w-3.5 h-3.5 text-accent-cyan" />
                        <span>{f}</span>
                      </li>
                    ))}
                  </ul>
                </div>
                <Link 
                  href="/portal"
                  className={`w-full text-center font-bold text-xs uppercase tracking-wider py-3 rounded transition-all cursor-pointer ${
                    i === 1 
                      ? 'bg-accent-cyan text-black hover:bg-cyan-500' 
                      : 'bg-gray-900 border border-glass-border hover:border-white/30 text-gray-300'
                  }`}
                >
                  Configure OS Node
                </Link>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-24 border-t border-glass-border text-center max-w-4xl mx-auto px-8">
        <h2 className="text-3xl md:text-5xl font-bold text-white tracking-tight mb-6">Initialize Privacy-First Security.</h2>
        <p className="text-gray-400 leading-relaxed mb-10 max-w-xl mx-auto text-xs md:text-sm">
          Join airports, smart cities, smart corporate campuses, and smart universities that trust BlindWatch AI to secure physical spaces while respecting civil privacy.
        </p>
        <Link 
          href="/portal"
          className="bg-accent-cyan hover:bg-cyan-500 text-black font-extrabold text-sm uppercase tracking-widest px-8 py-4 rounded-md transition-all shadow-[0_0_20px_rgba(6,182,212,0.3)] cursor-pointer inline-flex items-center gap-2"
        >
          <span>Establish Guard Console Node</span>
          <ArrowRight className="w-4 h-4" />
        </Link>
      </section>

      {/* Footer */}
      <footer className="border-t border-glass-border py-12 px-8 md:px-16 bg-gray-950 flex flex-col md:flex-row justify-between items-center gap-6 text-xs text-gray-500">
        <div>&copy; 2026 BlindWatch AI, Inc. Protected by cryptographic surveillance patents.</div>
        <div className="flex gap-6">
          <a href="#" className="hover:text-gray-300">Privacy Charter</a>
          <a href="#" className="hover:text-gray-300">Governance Compliance</a>
          <a href="#" className="hover:text-gray-300">Daemon Documentation</a>
        </div>
      </footer>
    </div>
  );
}
