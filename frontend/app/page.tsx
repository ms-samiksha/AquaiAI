'use client'

import { useState, useEffect } from 'react'
import UploadCard from '@/components/UploadCard'
import SearchCard from '@/components/SearchCard'

const PARTICLES = Array.from({ length: 30 }, (_, i) => ({
  id: i,
  x: Math.random() * 100,
  y: Math.random() * 100,
  size: Math.random() * 3 + 1,
  duration: Math.random() * 8 + 4,
  delay: Math.random() * 5,
}))

const TYPEWRITER_TEXTS = [
  'Identify marine species instantly.',
  'Assess coral reef health with AI.',
  "Explore the ocean's biodiversity.",
  'Powered by Amazon Nova & AWS.',
]

export default function HomePage() {
  const [activeTab, setActiveTab] = useState<'upload' | 'search'>('upload')
  const [displayText, setDisplayText] = useState('')
  const [textIndex, setTextIndex] = useState(0)
  const [charIndex, setCharIndex] = useState(0)
  const [deleting, setDeleting] = useState(false)
  const [mounted, setMounted] = useState(false)

  useEffect(() => { setMounted(true) }, [])

  useEffect(() => {
    const current = TYPEWRITER_TEXTS[textIndex]
    const timeout = setTimeout(() => {
      if (!deleting) {
        if (charIndex < current.length) {
          setDisplayText(current.slice(0, charIndex + 1))
          setCharIndex(c => c + 1)
        } else {
          setTimeout(() => setDeleting(true), 1800)
        }
      } else {
        if (charIndex > 0) {
          setDisplayText(current.slice(0, charIndex - 1))
          setCharIndex(c => c - 1)
        } else {
          setDeleting(false)
          setTextIndex(i => (i + 1) % TYPEWRITER_TEXTS.length)
        }
      }
    }, deleting ? 35 : 60)
    return () => clearTimeout(timeout)
  }, [charIndex, deleting, textIndex])

  return (
    <main className="relative min-h-screen overflow-hidden flex flex-col items-center justify-center px-4 py-16">

      {/* Animated particle field */}
      {mounted && (
        <div className="fixed inset-0 pointer-events-none overflow-hidden">
          {PARTICLES.map(p => (
            <div
              key={p.id}
              className="absolute rounded-full bg-cyan-400 opacity-0"
              style={{
                left: `${p.x}%`,
                top: `${p.y}%`,
                width: `${p.size}px`,
                height: `${p.size}px`,
                animation: `floatParticle ${p.duration}s ${p.delay}s ease-in-out infinite`,
              }}
            />
          ))}
        </div>
      )}

      {/* Glow orbs */}
      <div className="fixed inset-0 pointer-events-none">
        <div className="absolute top-[-20%] left-[-10%] w-[600px] h-[600px] rounded-full"
          style={{ background: 'radial-gradient(circle, rgba(6,182,212,0.12) 0%, transparent 70%)' }} />
        <div className="absolute bottom-[-20%] right-[-10%] w-[500px] h-[500px] rounded-full"
          style={{ background: 'radial-gradient(circle, rgba(14,116,144,0.15) 0%, transparent 70%)' }} />
        <div className="absolute top-[40%] left-[60%] w-[300px] h-[300px] rounded-full"
          style={{ background: 'radial-gradient(circle, rgba(8,145,178,0.08) 0%, transparent 70%)' }} />
      </div>

      {/* Header */}
      <div className="relative z-10 text-center mb-12 space-y-4">

        {/* Badge */}
        <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full border border-cyan-500/30 bg-cyan-500/5 mb-6">
          <span className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse" />
          <span className="text-cyan-400 text-xs font-mono tracking-widest uppercase">
            Marine Intelligence System v1.0
          </span>
        </div>

        {/* Logo */}
        <div className="flex items-center justify-center gap-3 mb-2">
          <div className="relative">
            <div className="w-14 h-14 rounded-2xl flex items-center justify-center text-3xl"
              style={{
                background: 'linear-gradient(135deg, rgba(6,182,212,0.2), rgba(14,116,144,0.3))',
                border: '1px solid rgba(6,182,212,0.4)',
                boxShadow: '0 0 30px rgba(6,182,212,0.2), inset 0 0 20px rgba(6,182,212,0.05)',
              }}>
              🌊
            </div>
            <div className="absolute -top-1 -right-1 w-4 h-4 rounded-full bg-cyan-400 flex items-center justify-center">
              <div className="w-2 h-2 rounded-full bg-slate-900" />
            </div>
          </div>
          <div>
            <h1 className="text-6xl md:text-7xl font-black tracking-tight"
              style={{
                fontFamily: "'Orbitron', monospace",
                background: 'linear-gradient(135deg, #ffffff 0%, #67e8f9 50%, #0891b2 100%)',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
                filter: 'drop-shadow(0 0 30px rgba(6,182,212,0.4))',
              }}>
              AquaAI
            </h1>
          </div>
        </div>

        {/* Typewriter */}
        <div className="h-8 flex items-center justify-center">
          <p className="text-lg md:text-xl font-mono text-cyan-300/80">
            {displayText}
            <span className="inline-block w-0.5 h-5 bg-cyan-400 ml-1 animate-pulse" />
          </p>
        </div>

        {/* Stats row */}
        <div className="flex items-center justify-center gap-8 mt-6 pt-6 border-t border-white/5">
          {[
            { value: '10K+', label: 'Species Database' },
            { value: '95%',  label: 'Avg Accuracy'    },
            { value: '<3s',  label: 'Analysis Time'   },
            { value: 'Live', label: 'AWS Bedrock'     },
          ].map(stat => (
            <div key={stat.label} className="text-center">
              <div className="text-xl font-black text-cyan-300"
                style={{ fontFamily: "'Orbitron', monospace" }}>
                {stat.value}
              </div>
              <div className="text-xs text-white/30 font-mono mt-0.5">{stat.label}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Main Card */}
      <div className="relative z-10 w-full max-w-2xl">
        <div className="rounded-2xl overflow-hidden"
          style={{
            background: 'rgba(2, 12, 27, 0.85)',
            border: '1px solid rgba(6,182,212,0.2)',
            boxShadow: '0 0 0 1px rgba(6,182,212,0.05), 0 25px 50px rgba(0,0,0,0.5), 0 0 80px rgba(6,182,212,0.05)',
          }}>

          {/* Tab bar */}
          <div className="flex border-b border-white/5">
            {[
              { key: 'upload', icon: '📸', label: 'Image Analysis' },
              { key: 'search', icon: '🔍', label: 'Species Search' },
            ].map(tab => (
              <button
                key={tab.key}
                onClick={() => setActiveTab(tab.key as 'upload' | 'search')}
                className="flex-1 flex items-center justify-center gap-2 py-4 text-sm font-mono transition-all duration-300 relative"
                style={{
                  color: activeTab === tab.key ? '#67e8f9' : 'rgba(255,255,255,0.3)',
                  background: activeTab === tab.key ? 'rgba(6,182,212,0.05)' : 'transparent',
                }}>
                <span>{tab.icon}</span>
                <span className="tracking-wider uppercase text-xs">{tab.label}</span>
                {activeTab === tab.key && (
                  <div className="absolute bottom-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-cyan-400 to-transparent" />
                )}
              </button>
            ))}
          </div>

          {/* Tab content */}
          <div className="p-6">
            {activeTab === 'upload' ? <UploadCard /> : <SearchCard />}
          </div>
        </div>

        {/* Bottom hint */}
        <p className="text-center text-white/20 text-xs font-mono mt-4 tracking-widest">
          POWERED BY AMAZON NOVA · AWS BEDROCK · NEXT.JS
        </p>
      </div>

      <style jsx global>{`
        @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@700;900&family=JetBrains+Mono:wght@400;500&display=swap');

        @keyframes floatParticle {
          0%, 100% { opacity: 0; transform: translateY(0px) scale(1); }
          20%       { opacity: 0.6; }
          50%       { opacity: 0.3; transform: translateY(-40px) scale(1.2); }
          80%       { opacity: 0.5; }
        }
      `}</style>
    </main>
  )
}