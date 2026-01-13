import { useState } from 'react';
import { useParams } from 'react-router-dom';
import { useQuery, useMutation } from '@tanstack/react-query';
import { api } from '@/lib/axios';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Loader2, Calculator } from 'lucide-react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

export default function NetworkCalculations() {
    const { networkId } = useParams();
    const [txId, setTxId] = useState<string>('');
    const [rxId, setRxId] = useState<string>('');
    const [jobId, setJobId] = useState<string | null>(null);

    // Fetch Stations
    const { data: stations } = useQuery({
        queryKey: ['stations', networkId],
        queryFn: async () => {
            const res = await api.get(`/v4/networks/${networkId}/stations`);
            return res.data.features.map((f: any) => ({
                id: f.properties.id,
                name: f.properties.name,
                service: f.properties.service
            }));
        },
        enabled: !!networkId
    });

    // Mutation to Start Calculation
    const { mutate: calculate, isPending: isStarting } = useMutation({
        mutationFn: async () => {
            const res = await api.post('/v4/jobs/link', {
                network_id: networkId,
                tx_id: txId,
                rx_id: rxId
            });
            return res.data;
        },
        onSuccess: (data) => {
            setJobId(data.job_id);
        }
    });

    // Poll for Results
    const { data: jobResult } = useQuery({
        queryKey: ['job', jobId],
        queryFn: async () => {
            const res = await api.get(`/v4/jobs/${jobId}`);
            return res.data;
        },
        enabled: !!jobId,
        refetchInterval: (query) => {
            const status = query.state.data?.status;
            return (status === 'completed' || status === 'failed') ? false : 1000;
        }
    });

    const isCalculating = jobResult?.status === 'pending' || jobResult?.status === 'processing';
    const profileData = jobResult?.result?.profile || [];
    const formattedData = profileData.map((p: any) => ({
        dist: p.dist_km.toFixed(1),
        elev: p.elev_m
    }));

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <h2 className="text-2xl font-bold">Calculations</h2>
            </div>

            {/* Control Panel */}
            <Card className="bg-zinc-900 border-zinc-800 text-zinc-100">
                <CardHeader>
                    <CardTitle className="text-lg flex items-center gap-2">
                        <Calculator className="h-5 w-5 text-blue-500" />
                        Link Profile Analysis
                    </CardTitle>
                </CardHeader>
                <CardContent className="flex flex-col md:flex-row gap-4 items-end">
                    <div className="space-y-2 w-full md:w-1/3">
                        <label className="text-sm font-medium text-zinc-400">Transmitter (TX)</label>
                        <Select value={txId} onValueChange={setTxId}>
                            <SelectTrigger className="bg-zinc-950 border-zinc-800">
                                <SelectValue placeholder="Select Station" />
                            </SelectTrigger>
                            <SelectContent className="bg-zinc-900 border-zinc-800">
                                {stations?.map((s: any) => (
                                    <SelectItem key={s.id} value={s.id}>{s.name} ({s.service})</SelectItem>
                                ))}
                            </SelectContent>
                        </Select>
                    </div>

                    <div className="space-y-2 w-full md:w-1/3">
                        <label className="text-sm font-medium text-zinc-400">Receiver (RX)</label>
                        <Select value={rxId} onValueChange={setRxId}>
                            <SelectTrigger className="bg-zinc-950 border-zinc-800">
                                <SelectValue placeholder="Select Station" />
                            </SelectTrigger>
                            <SelectContent className="bg-zinc-900 border-zinc-800">
                                {stations?.map((s: any) => (
                                    <SelectItem key={s.id} value={s.id}>{s.name} ({s.service})</SelectItem>
                                ))}
                            </SelectContent>
                        </Select>
                    </div>

                    <Button
                        onClick={() => calculate()}
                        disabled={!txId || !rxId || isStarting || isCalculating}
                        className="bg-blue-600 hover:bg-blue-500 w-full md:w-auto"
                    >
                        {(isStarting || isCalculating) && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                        Calculate Profile
                    </Button>
                </CardContent>
            </Card>

            {/* Results Area */}
            {jobResult && (
                <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <Card className="bg-zinc-900 border-zinc-800 text-zinc-100">
                            <CardContent className="pt-6 text-center">
                                <div className="text-3xl font-bold">{jobResult.result?.loss_db?.toFixed(1) || '--'} dB</div>
                                <p className="text-sm text-zinc-500">Total Diffraction Loss</p>
                            </CardContent>
                        </Card>
                        <Card className="bg-zinc-900 border-zinc-800 text-zinc-100">
                            <CardContent className="pt-6 text-center">
                                <div className="text-3xl font-bold">{jobResult.result?.fsl_db?.toFixed(1) || '--'} dB</div>
                                <p className="text-sm text-zinc-500">Free Space Loss</p>
                            </CardContent>
                        </Card>
                        <Card className="bg-zinc-900 border-zinc-800 text-zinc-100">
                            <CardContent className="pt-6 text-center">
                                <div className="text-3xl font-bold text-green-500">{jobResult.result?.margin_db ? jobResult.result.margin_db.toFixed(1) : '--'} dB</div>
                                <p className="text-sm text-zinc-500">Fade Margin</p>
                            </CardContent>
                        </Card>
                    </div>

                    <Card className="bg-zinc-900 border-zinc-800 text-zinc-100 h-[400px]">
                        <CardHeader>
                            <CardTitle>Terrain Profile</CardTitle>
                        </CardHeader>
                        <CardContent className="h-[320px]">
                            <ResponsiveContainer width="100%" height="100%">
                                <AreaChart data={formattedData}>
                                    <defs>
                                        <linearGradient id="colorElev" x1="0" y1="0" x2="0" y2="1">
                                            <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.8} />
                                            <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                                        </linearGradient>
                                    </defs>
                                    <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                                    <XAxis dataKey="dist" stroke="#666" />
                                    <YAxis stroke="#666" domain={['auto', 'auto']} />
                                    <Tooltip
                                        contentStyle={{ backgroundColor: '#18181b', border: '1px solid #27272a' }}
                                        labelStyle={{ color: '#a1a1aa' }}
                                    />
                                    <Area type="monotone" dataKey="elev" stroke="#3b82f6" fillOpacity={1} fill="url(#colorElev)" />
                                </AreaChart>
                            </ResponsiveContainer>
                        </CardContent>
                    </Card>
                </div>
            )}
        </div>
    );
}
