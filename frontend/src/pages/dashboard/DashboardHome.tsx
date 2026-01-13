import { Card, CardHeader, CardTitle, CardContent, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Plus, Activity, Server } from 'lucide-react';
import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/axios';

export default function DashboardHome() {
    const { data: metrics, isLoading } = useQuery({
        queryKey: ['dashboard-metrics'],
        queryFn: async () => {
            // Mock metrics derived from networks list for now, or real endpoint if exists
            // Real App would have /api/v4/dashboard/metrics
            // Here we fetch networks to count them
            const res = await api.get('/v4/networks');
            const networks = res.data as any[];
            const totalNetworks = networks.length;
            const activeStations = networks.reduce((acc, n) => acc + (n.station_count || 0), 0);
            return { totalNetworks, activeStations };
        }
    });

    return (
        <div className="space-y-8">
            {/* Welcome Section */}
            <div className="flex items-center justify-between">
                <div>
                    <h2 className="text-3xl font-bold tracking-tight">Overview</h2>
                    <p className="text-zinc-400 mt-2">Welcome to your spectrum engineering workspace.</p>
                </div>
                <div className="flex gap-2">
                    <Link to="/app/networks">
                        <Button className="bg-green-600 hover:bg-green-500">
                            <Plus className="mr-2 h-4 w-4" /> New Project
                        </Button>
                    </Link>
                </div>
            </div>

            {/* Stats Grid */}
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                <Card className="bg-zinc-900 border-zinc-800 text-zinc-100">
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">Total Networks</CardTitle>
                        <Server className="h-4 w-4 text-zinc-500" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">{isLoading ? '...' : metrics?.totalNetworks || 0}</div>
                        <p className="text-xs text-zinc-500">Active projects</p>
                    </CardContent>
                </Card>
                <Card className="bg-zinc-900 border-zinc-800 text-zinc-100">
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">Total Stations</CardTitle>
                        <Activity className="h-4 w-4 text-zinc-500" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">{isLoading ? '...' : metrics?.activeStations || 0}</div>
                        <p className="text-xs text-zinc-500">Transmitters managed</p>
                    </CardContent>
                </Card>
            </div>

            {/* Recent Projects Placeholder */}
            <Card className="bg-zinc-900 border-zinc-800 text-zinc-100">
                <CardHeader>
                    <CardTitle>Recent Activity</CardTitle>
                    <CardDescription className="text-zinc-400">Your recently accessed system events.</CardDescription>
                </CardHeader>
                <CardContent>
                    <div className="flex h-32 items-center justify-center border-2 border-dashed border-zinc-800 rounded-lg text-zinc-500">
                        No recent activity found.
                    </div>
                </CardContent>
            </Card>
        </div>
    )
}
