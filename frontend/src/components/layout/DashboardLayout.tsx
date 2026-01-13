import { useState } from 'react';
import { Link, Outlet, useLocation, useNavigate } from 'react-router-dom';
import { useAuthStore } from '@/store/useAuthStore';
import {
    LayoutDashboard,
    Network,
    Radio,
    Settings,
    LogOut,
    Menu,
    X,
    ArrowLeft,
    Database,
    Map,
    Calculator,
    FileText
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

export default function DashboardLayout() {
    const [isSidebarOpen, setIsSidebarOpen] = useState(true);
    const location = useLocation();
    const logout = useAuthStore((state) => state.logout);
    const user = useAuthStore((state) => state.user);
    const navigate = useNavigate();

    const handleLogout = () => {
        logout();
        navigate('/login');
    };

    const isNetworkContext = location.pathname.includes('/app/network/');

    const globalNavItems = [
        { label: 'Dashboard', icon: LayoutDashboard, href: '/app/home' },
        { label: 'My Networks', icon: Network, href: '/app/networks' },
        { label: 'Analysis', icon: Radio, href: '/app/analysis' },
        { label: 'Settings', icon: Settings, href: '/app/settings' },
    ];

    const networkNavItems = [
        { label: 'Back to Networks', icon: ArrowLeft, href: '/app/networks', className: "text-blue-400" },
        // Groups will be rendered differently, this is a simplified flat list for now or we build groups
        { label: 'Objects', icon: Database, href: 'objects' },
        { label: 'Map', icon: Map, href: 'map' },
        { label: 'Calculations', icon: Calculator, href: 'calculations' },
        { label: 'Reports', icon: FileText, href: 'reports' },
    ];

    // Simple Render for now - we can improve grouping later
    const navItems = isNetworkContext ? networkNavItems : globalNavItems;

    return (
        <div className="flex h-screen bg-zinc-950 text-zinc-100 overflow-hidden font-sans">
            {/* Sidebar */}
            <aside
                className={cn(
                    "bg-zinc-900 border-r border-zinc-800 transition-all duration-300 flex flex-col z-20",
                    isSidebarOpen ? "w-64" : "w-16"
                )}
            >
                <div className="h-16 flex items-center justify-between px-4 border-b border-zinc-800">
                    {isSidebarOpen && <span className="font-bold text-lg tracking-tight text-green-500">Spectrum<span className="text-white">Eng</span></span>}
                    <Button variant="ghost" size="icon" onClick={() => setIsSidebarOpen(!isSidebarOpen)} className="text-zinc-400 hover:text-white">
                        {isSidebarOpen ? <X size={20} /> : <Menu size={20} />}
                    </Button>
                </div>

                <nav className="flex-1 py-4 flex flex-col gap-1 px-2">
                    {navItems.map((item) => {
                        const Icon = item.icon;
                        const isAbsolute = item.href.startsWith('/');
                        // If network context, relative links append to current URL (simplified)
                        // Actually better to reconstruct url if needed, but for "objects" tab params usually work better
                        // For now let's assume route /app/network/:id/:tab

                        const targetPath = isAbsolute
                            ? item.href
                            : location.pathname.split('/').slice(0, 4).join('/') + '/' + item.href;
                        // simplistic join, assuming /app/network/UUID is base

                        const isActive = isAbsolute
                            ? location.pathname.startsWith(item.href)
                            : location.pathname.includes(item.href);

                        return (
                            <Link
                                key={item.label}
                                to={targetPath}
                                className={cn(
                                    "flex items-center gap-3 px-3 py-2 rounded-md transition-colors text-sm font-medium",
                                    isActive
                                        ? "bg-green-500/10 text-green-500"
                                        : "text-zinc-400 hover:bg-zinc-800 hover:text-white",
                                    // @ts-ignore
                                    item.className
                                )}
                            >
                                <Icon size={20} />
                                {isSidebarOpen && <span>{item.label}</span>}
                            </Link>
                        )
                    })}
                </nav>

                <div className="p-4 border-t border-zinc-800">
                    <Button
                        variant="ghost"
                        className={cn("w-full justify-start text-red-400 hover:text-red-300 hover:bg-red-400/10", !isSidebarOpen && "px-2 justify-center")}
                        onClick={handleLogout}
                    >
                        <LogOut size={20} />
                        {isSidebarOpen && <span className="ml-3">Sign Out</span>}
                    </Button>
                </div>
            </aside>

            {/* Main Content */}
            <main className="flex-1 flex flex-col overflow-hidden relative">
                {/* Header */}
                <header className="h-16 bg-zinc-900/50 backdrop-blur border-b border-zinc-800 flex items-center justify-between px-8">
                    <h1 className="text-xl font-semibold capitalize">
                        {location.pathname.split('/').pop()?.replace('-', ' ') || 'Dashboard'}
                    </h1>
                    <div className="flex items-center gap-4">
                        <span className="text-sm text-zinc-400">
                            {user?.email || 'User'}
                        </span>
                        <div className="h-8 w-8 rounded-full bg-green-600 flex items-center justify-center text-xs font-bold">
                            {(user?.email?.[0] || 'U').toUpperCase()}
                        </div>
                    </div>
                </header>

                {/* Scrollable Content Area */}
                <div className="flex-1 overflow-auto p-8">
                    <Outlet />
                </div>
            </main>
        </div>
    );
}
