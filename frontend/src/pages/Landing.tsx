import { Link } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { ArrowRight, Box, Waves, Zap, Database } from 'lucide-react';

export default function Landing() {
    return (
        <div className="min-h-screen bg-slate-950 text-white selection:bg-blue-500/30">

            {/* Navigation */}
            <nav className="fixed w-full z-50 bg-slate-950/50 backdrop-blur-md border-b border-white/10">
                <div className="container mx-auto px-6 h-16 flex items-center justify-between">
                    <div className="flex items-center space-x-2 font-bold text-xl tracking-tight">
                        <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
                            <Waves className="w-5 h-5 text-white" />
                        </div>
                        <span>Engenharia de Espectro</span>
                    </div>
                    <div className="flex items-center gap-4">
                        <Link to="/login">
                            <Button variant="ghost" className="text-slate-300 hover:text-white hover:bg-white/10">
                                Entrar
                            </Button>
                        </Link>
                        <Link to="/register">
                            <Button className="bg-blue-600 hover:bg-blue-500 text-white font-medium px-6">
                                Cadastrar
                            </Button>
                        </Link>
                    </div>
                </div>
            </nav>

            {/* Hero Section */}
            <section className="relative pt-32 pb-20 lg:pt-48 overflow-hidden">
                {/* Background Effects */}
                <div className="absolute inset-0 z-0">
                    <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[1000px] h-[500px] bg-blue-500/20 rounded-full blur-[100px] opacity-50 animate-pulse" />
                    <div className="absolute inset-0 bg-[url('https://grainy-gradients.vercel.app/noise.svg')] opacity-20" />

                    {/* SVG Contours Animation (Simulated) */}
                    <svg className="absolute w-full h-full opacity-30" preserveAspectRatio="none">
                        <path d="M0,100 C150,200 350,0 500,100 C650,200 850,0 1000,100 L1000,500 L0,500 Z" fill="none" stroke="rgba(59, 130, 246, 0.5)" strokeWidth="2" className="animate-[wiggle_10s_ease-in-out_infinite]" />
                        <path d="M0,150 C200,50 400,250 600,150 C800,50 1000,250 1200,150" fill="none" stroke="rgba(147, 197, 253, 0.3)" strokeWidth="1" className="animate-[wiggle_15s_ease-in-out_infinite_reverse]" />
                    </svg>
                </div>

                <div className="container relative z-10 mx-auto px-6 text-center">
                    <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-900/30 border border-blue-500/30 text-blue-400 text-sm font-medium mb-8">
                        <span className="relative flex h-2 w-2">
                            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-blue-400 opacity-75"></span>
                            <span className="relative inline-flex rounded-full h-2 w-2 bg-blue-500"></span>
                        </span>
                        V4 Agora Disponível
                    </div>

                    <h1 className="text-5xl md:text-7xl font-extrabold tracking-tight mb-8 bg-clip-text text-transparent bg-gradient-to-b from-white to-white/60">
                        Precisão em Engenharia <br /> de Radiofrequência
                    </h1>

                    <p className="text-lg md:text-xl text-slate-400 max-w-2xl mx-auto mb-12 leading-relaxed">
                        Plataforma avançada para cálculo de cobertura e enlaces, compatível com atos da <strong className="text-slate-200">Anatel</strong>.
                        Utilizando modelos <strong>ITU-R P.1546</strong> e <strong>Deygout-Assis</strong> acelerados por GPU/Numba.
                    </p>

                    <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
                        <Link to="/register">
                            <Button size="lg" className="h-12 px-8 text-base bg-white text-slate-950 hover:bg-slate-200 w-full sm:w-auto">
                                Começar Agora
                                <ArrowRight className="ml-2 w-5 h-5" />
                            </Button>
                        </Link>
                        <Link to="/login">
                            <Button size="lg" variant="outline" className="h-12 px-8 text-base border-white/20 hover:bg-white/10 hover:text-white w-full sm:w-auto">
                                Acessar Portal
                            </Button>
                        </Link>
                    </div>
                </div>
            </section>

            {/* Features Grid */}
            <section className="py-24 bg-slate-950 relative">
                <div className="container mx-auto px-6">
                    <div className="grid md:grid-cols-3 gap-8">
                        {/* Feature 1 */}
                        <div className="p-8 rounded-2xl bg-white/5 border border-white/10 hover:border-blue-500/50 transition-colors group">
                            <div className="w-12 h-12 bg-blue-600/20 rounded-lg flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
                                <Zap className="w-6 h-6 text-blue-400" />
                            </div>
                            <h3 className="text-xl font-bold mb-3">Alta Performance</h3>
                            <p className="text-slate-400 leading-relaxed">
                                Núcleo matemático reescrito em Python com Numba (JIT), processando matrizes de elevação em milissegundos.
                            </p>
                        </div>

                        {/* Feature 2 */}
                        <div className="p-8 rounded-2xl bg-white/5 border border-white/10 hover:border-purple-500/50 transition-colors group">
                            <div className="w-12 h-12 bg-purple-600/20 rounded-lg flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
                                <Box className="w-6 h-6 text-purple-400" />
                            </div>
                            <h3 className="text-xl font-bold mb-3">Modelos Determinísticos</h3>
                            <p className="text-slate-400 leading-relaxed">
                                Implementação rigorosa de Deygout-Assis para difração em múltiplos gumes, ideal para relevos complexos (Brasil).
                            </p>
                        </div>

                        {/* Feature 3 */}
                        <div className="p-8 rounded-2xl bg-white/5 border border-white/10 hover:border-emerald-500/50 transition-colors group">
                            <div className="w-12 h-12 bg-emerald-600/20 rounded-lg flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
                                <Database className="w-6 h-6 text-emerald-400" />
                            </div>
                            <h3 className="text-xl font-bold mb-3">Dados Oficiais</h3>
                            <p className="text-slate-400 leading-relaxed">
                                Integração nativa com bases do Mosaico (Anatel) e malha censitária (IBGE 2022) com SRID 4674 (SIRGAS 2000).
                            </p>
                        </div>
                    </div>
                </div>
            </section>

            {/* Footer */}
            <footer className="py-12 border-t border-white/10 text-center text-slate-500 text-sm">
                <p>&copy; 2026 Engenharia de Espectro. Todos os direitos reservados.</p>
                <div className="flex justify-center gap-6 mt-4">
                    <a href="#" className="hover:text-white">Termos</a>
                    <a href="#" className="hover:text-white">Privacidade</a>
                    <a href="#" className="hover:text-white">Suporte</a>
                </div>
            </footer>
        </div>
    );
}
