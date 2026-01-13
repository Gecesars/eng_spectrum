import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/axios';
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow
} from '@/components/ui/table';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
    Dialog,
    DialogContent,
    DialogHeader,
    DialogTitle,
    DialogTrigger,
    DialogFooter
} from '@/components/ui/dialog';
import { Label } from '@/components/ui/label';
import { Plus, Search, Loader2 } from 'lucide-react';

interface Network {
    id: string;
    name: string;
    created_at?: string;
    station_count?: number; // Backend needs to provide this
}

export default function Networks() {
    const [searchTerm, setSearchTerm] = useState('');
    const [isCreateOpen, setIsCreateOpen] = useState(false);
    const [newNetworkName, setNewNetworkName] = useState('');
    const queryClient = useQueryClient();

    const { data: networks, isLoading } = useQuery({
        queryKey: ['networks'],
        queryFn: async () => {
            const res = await api.get('/v4/networks');
            return res.data as Network[];
        }
    });

    const createMutation = useMutation({
        mutationFn: async (name: string) => {
            await api.post('/v4/networks', { name });
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['networks'] });
            setIsCreateOpen(false);
            setNewNetworkName('');
        }
    });

    const handleCreate = () => {
        if (!newNetworkName.trim()) return;
        createMutation.mutate(newNetworkName);
    };

    const filteredNetworks = networks?.filter(n =>
        n.name.toLowerCase().includes(searchTerm.toLowerCase())
    ) || [];

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h2 className="text-3xl font-bold tracking-tight">Networks</h2>
                    <p className="text-zinc-400">Manage your radio frequency networks.</p>
                </div>
                <Dialog open={isCreateOpen} onOpenChange={setIsCreateOpen}>
                    <DialogTrigger asChild>
                        <Button className="bg-green-600 hover:bg-green-500">
                            <Plus className="mr-2 h-4 w-4" /> Create Network
                        </Button>
                    </DialogTrigger>
                    <DialogContent className="bg-zinc-900 border-zinc-800 text-zinc-100">
                        <DialogHeader>
                            <DialogTitle>Create New Network</DialogTitle>
                        </DialogHeader>
                        <div className="grid gap-4 py-4">
                            <div className="grid gap-2">
                                <Label htmlFor="name">Network Name</Label>
                                <Input
                                    id="name"
                                    value={newNetworkName}
                                    onChange={(e) => setNewNetworkName(e.target.value)}
                                    className="bg-zinc-950 border-zinc-800"
                                />
                            </div>
                        </div>
                        <DialogFooter>
                            <Button onClick={handleCreate} disabled={createMutation.isPending}>
                                {createMutation.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                                Create
                            </Button>
                        </DialogFooter>
                    </DialogContent>
                </Dialog>
            </div>

            <div className="flex gap-2 mb-4">
                <div className="relative flex-1 max-w-sm">
                    <Search className="absolute left-2 top-2.5 h-4 w-4 text-zinc-500" />
                    <Input
                        placeholder="Search networks..."
                        className="pl-8 bg-zinc-900 border-zinc-800"
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                    />
                </div>
            </div>

            <div className="rounded-md border border-zinc-800">
                <Table>
                    <TableHeader>
                        <TableRow className="border-zinc-800 hover:bg-zinc-900/50">
                            <TableHead className="text-zinc-400">Name</TableHead>
                            <TableHead className="text-zinc-400">Stations</TableHead>
                            <TableHead className="text-zinc-400">Created At</TableHead>
                            <TableHead className="text-right text-zinc-400">Actions</TableHead>
                        </TableRow>
                    </TableHeader>
                    <TableBody>
                        {isLoading ? (
                            <TableRow>
                                <TableCell colSpan={4} className="h-24 text-center">
                                    <Loader2 className="h-6 w-6 animate-spin mx-auto text-zinc-500" />
                                </TableCell>
                            </TableRow>
                        ) : filteredNetworks.length === 0 ? (
                            <TableRow>
                                <TableCell colSpan={4} className="h-24 text-center text-zinc-500">
                                    No networks found.
                                </TableCell>
                            </TableRow>
                        ) : (
                            filteredNetworks.map((network) => (
                                <TableRow key={network.id} className="border-zinc-800 hover:bg-zinc-900/50">
                                    <TableCell className="font-medium">{network.name}</TableCell>
                                    <TableCell>{network.station_count || 0}</TableCell>
                                    <TableCell>{network.created_at || 'n/a'}</TableCell>
                                    <TableCell className="text-right">
                                        <Button variant="ghost" size="sm" onClick={() => window.location.href = `/app/network/${network.id}`}>
                                            Open
                                        </Button>
                                    </TableCell>
                                </TableRow>
                            ))
                        )}
                    </TableBody>
                </Table>
            </div>
        </div>
    )
}
