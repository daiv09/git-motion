"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";

export default function Home() {
  const [url, setUrl] = useState("");
  const [quality, setQuality] = useState("low");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  const handleGenerate = async () => {
    if (!url) return;
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const res = await fetch("/api/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url, quality }),
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Failed to generate data");
      setResult(data);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="min-h-screen bg-[#030303] text-slate-200 flex flex-col items-center px-6 overflow-hidden relative">
      
      {/* --- BACKGROUND ELEMENTS --- */}
      <div className="absolute inset-0 z-0 pointer-events-none">
        <div className="absolute inset-0 bg-[linear-gradient(to_right,#80808012_1px,transparent_1px),linear-gradient(to_bottom,#80808012_1px,transparent_1px)] bg-[size:40px_40px] [mask-image:radial-gradient(ellipse_60%_50%_at_50%_0%,#000_70%,transparent_100%)]" />
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[1000px] h-[600px] bg-blue-600/10 blur-[120px] rounded-full" />
      </div>

      <div className="relative z-10 w-full max-w-5xl pt-32 pb-20 flex flex-col items-center">
        
        {/* --- HERO SECTION --- */}
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, ease: "easeOut" }}
          className="text-center mb-12"
        >
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-500/10 border border-blue-500/20 text-blue-400 text-xs font-medium mb-8">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-blue-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-blue-500"></span>
            </span>
            Now supporting Manim v0.18
          </div>

          <h1 className="text-6xl md:text-8xl font-bold tracking-tighter mb-8 bg-clip-text text-transparent bg-gradient-to-b from-white to-white/40">
            Git <span className="text-blue-500">Motion</span>
          </h1>

          <p className="max-w-xl mx-auto text-slate-400 text-lg md:text-xl leading-relaxed mb-10">
            Generate high-fidelity <span className="text-slate-200">technical videos</span> from your code history.  
            Automated repository biographies powered by the <span className="text-blue-400">Manim</span> animation engine.
          </p>

          {/* --- INPUT AREA --- */}
          <div className="w-full max-w-2xl mx-auto relative group">
            <div className="absolute -inset-1 bg-gradient-to-r from-blue-600 to-cyan-500 rounded-2xl blur opacity-20 group-focus-within:opacity-40 transition duration-1000"></div>
            
            <div className="relative flex flex-col md:flex-row gap-2 bg-[#0A0A0A] border border-white/10 p-2 rounded-2xl shadow-2xl overflow-hidden">
              <input
                type="text"
                placeholder="Paste GitHub Repo URL..."
                className="flex-1 bg-transparent px-5 py-3 text-white placeholder-slate-600 focus:outline-none text-lg"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
              />

              <div className="flex items-center gap-2 p-1">
                <select
                  className="bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-sm focus:outline-none hover:bg-white/10 transition"
                  value={quality}
                  onChange={(e) => setQuality(e.target.value)}
                >
                  <option value="low">480p (Fast)</option>
                  <option value="high">1080p (Pro)</option>
                </select>

                <button
                  onClick={handleGenerate}
                  disabled={loading || !url}
                  className="relative overflow-hidden bg-blue-600 hover:bg-blue-500 disabled:bg-white/5 disabled:text-slate-600 text-white font-semibold rounded-xl px-8 py-3 transition-all active:scale-95 min-w-[140px]"
                >
                  <span className="relative z-10">{loading ? "Rendering..." : "Generate"}</span>
                  {loading && (
                    <motion.div 
                      className="absolute inset-0 bg-white/20"
                      initial={{ x: "-100%" }}
                      animate={{ x: "100%" }}
                      transition={{ repeat: Infinity, duration: 1, ease: "linear" }}
                    />
                  )}
                </button>
              </div>
            </div>
          </div>
        </motion.div>

        {/* --- ERROR MESSAGE --- */}
        {error && (
          <motion.div 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="mb-8 bg-red-500/10 border border-red-500/20 text-red-400 px-6 py-3 rounded-xl text-sm"
          >
            {error}
          </motion.div>
        )}

        {/* --- PREVIEW / RESULTS SECTION --- */}
        <div className="w-full max-w-4xl">
          <AnimatePresence mode="wait">
            {result ? (
              <motion.div 
                key="results"
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                className="space-y-12"
              >
                {/* 1. Video Player */}
                {result.videoUrl && (
                  <div className="relative rounded-2xl overflow-hidden border border-white/10 bg-black shadow-2xl aspect-video">
                    <video
                      controls
                      autoPlay
                      className="w-full h-full"
                      src={result.videoUrl}
                    />
                  </div>
                )}

                {/* 2. Stats Grid */}
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                  <StatCard label="Repository" value={result.repo_name || "N/A"} />
                  <StatCard label="Commits" value={result.total_commits_fetched || 0} />
                  <StatCard label="Authors" value={result.global_stats?.top_contributors?.length || 0} />
                  <StatCard label="Lead" value={result.global_stats?.top_contributors?.[0]?.name || "N/A"} />
                </div>

                {/* 3. Data Logs */}
                <details className="group border-t border-white/5 pt-8">
                  <summary className="cursor-pointer text-center text-xs text-slate-500 hover:text-slate-300 transition list-none">
                    [ VIEW RAW METADATA ]
                  </summary>
                  <div className="mt-4 bg-black/40 border border-white/10 rounded-xl p-4 max-h-60 overflow-auto">
                    <pre className="text-[10px] text-blue-400 font-mono leading-tight">
                      {JSON.stringify(result, null, 2)}
                    </pre>
                  </div>
                </details>
              </motion.div>
            ) : (
              /* Placeholder Mockup */
              <motion.div 
                key="placeholder"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="aspect-video rounded-2xl border border-white/5 bg-gradient-to-b from-white/5 to-transparent p-1 shadow-2xl"
              >
                <div className="w-full h-full rounded-[14px] bg-[#050505] flex items-center justify-center border border-white/5 relative overflow-hidden group">
                   <div className="absolute inset-0 bg-blue-500/5 opacity-0 group-hover:opacity-100 transition-opacity" />
                   <p className="text-slate-600 font-mono text-sm animate-pulse tracking-widest">
                     {loading ? "INITIALIZING MANIM ENGINE..." : "WAITING FOR REPOSITORY DATA"}
                   </p>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </main>
  );
}

function StatCard({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="bg-white/[0.02] border border-white/5 rounded-xl p-4 hover:border-white/10 transition">
      <p className="text-[9px] uppercase tracking-[0.2em] text-slate-500 mb-2">
        {label}
      </p>
      <p className="text-white font-semibold truncate text-lg">{value}</p>
    </div>
  );
}