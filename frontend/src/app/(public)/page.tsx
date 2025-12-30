import React from 'react';
import PublicHeader from '@/components/Landing/PublicHeader';
import Hero from '@/components/Landing/Hero';
import FeatureGrid from '@/components/Landing/FeatureGrid';

export default function LandingPage() {
    return (
        <div className="min-h-screen bg-black text-white selection:bg-cyan-500/30">
            <PublicHeader />
            <main>
                <Hero />
                <FeatureGrid />

                {/* Simple CTA Section */}
                <section className="py-24 relative overflow-hidden">
                    <div className="absolute inset-0 bg-linear-to-b from-black to-cyan-900/20" />
                    <div className="relative z-10 max-w-4xl mx-auto text-center px-6">
                        <h2 className="text-4xl md:text-5xl font-orbitron font-bold text-white mb-8">
                            READY TO ENTER THE <span className="text-cyan-500">UNDERWORLD</span>?
                        </h2>
                        <p className="text-xl text-gray-400 font-rajdhani mb-10">
                            Join the elite automation network. Access granted to authorized personnel only.
                        </p>
                        <a
                            href="/login"
                            className="inline-block px-12 py-4 bg-white text-black hover:bg-cyan-400 font-orbitron font-bold text-lg rounded-full shadow-[0_0_40px_rgba(255,255,255,0.3)] hover:shadow-[0_0_60px_rgba(6,182,212,0.5)] transition-all transform hover:scale-105"
                        >
                            INITIALIZE SYSTEM
                        </a>
                    </div>
                </section>

                {/* Footer */}
                <footer className="py-12 border-t border-white/10 bg-black/80">
                    <div className="max-w-7xl mx-auto px-6 flex flex-col md:flex-row justify-between items-center opacity-60">
                        <div className="mb-4 md:mb-0">
                            <span className="font-orbitron font-bold text-lg">LEDGER1.AI</span>
                            <span className="mx-2">|</span>
                            <span className="font-rajdhani">ANUBIS PROTOCOL v2.0</span>
                        </div>
                        <div className="flex gap-6 font-rajdhani text-sm">
                            <a href="#" className="hover:text-cyan-400 transition-colors">PRIVACY_POLICY</a>
                            <a href="#" className="hover:text-cyan-400 transition-colors">TERMS_OF_SERVICE</a>
                            <a href="#" className="hover:text-cyan-400 transition-colors">SYSTEM_STATUS</a>
                        </div>
                    </div>
                </footer>
            </main>
        </div>
    );
}
