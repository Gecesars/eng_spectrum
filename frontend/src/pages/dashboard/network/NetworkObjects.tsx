import { useState } from 'react';
import { useParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/axios';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from '@/components/ui/table';
import { Upload, SlidersHorizontal, Plus, Loader2 } from 'lucide-react';
import ImportStationsModal from '@/components/modals/ImportStationsModal';
import AdjustParamsModal from '@/components/modals/AdjustParamsModal';

export default function NetworkObjects() {
    const { networkId } = useParams();
    const [isImportOpen, setIsImportOpen] = useState(false);
    const [isAdjustOpen, setIsAdjustOpen] = useState(false);
    const [selectedStations, setSelectedStations] = useState<string[]>([]);

    const { data: stations, isLoading, refetch } = useQuery({
        queryKey: ['stations', networkId],
        queryFn: async () => {
            const res = await api.get(`/v4/networks/${networkId}/stations`);
            return res.data.features.map((f: any) => ({
                id: f.properties.id,
                name: f.properties.name,
                service: f.properties.service,
                status: 'Licensed', // Placeholder/Default
                freq: f.properties.freq,
                erp: f.properties.erp
            }));
        },
        enabled: !!networkId
    });

    if (!networkId) return null;

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h2 className="text-2xl font-bold">Network Objects</h2>
                    <p className="text-zinc-400">Manage transmitters and receivers.</p>
                </div>
                <div className="flex gap-2">
                    <Button variant="outline" onClick={() => setIsImportOpen(true)}>
                        <Upload className="mr-2 h-4 w-4" /> Import (XML)
                    </Button>
                    <Button
                        variant="secondary"
                        onClick={() => setIsAdjustOpen(true)}
                        disabled={selectedStations.length === 0}
                    >
                        <SlidersHorizontal className="mr-2 h-4 w-4" /> Adjust Params
                    </Button>
                    <Button className="bg-blue-600 hover:bg-blue-500">
                        <Plus className="mr-2 h-4 w-4" /> Add Station
                    </Button>
                </div>
            </div>

            <div className="rounded-md border border-zinc-800 bg-zinc-900/50">
                <Table>
                    <TableHeader>
                        <TableRow className="border-zinc-800 hover:bg-zinc-800/50">
                            <TableHead className="w-[300px]">Name / Entity</TableHead>
                            <TableHead>Service</TableHead>
                            <TableHead>Status</TableHead>
                            <TableHead className="text-right">Frequency (MHz)</TableHead>
                            <TableHead className="text-right">ERP (dBm)</TableHead>
                        </TableRow>
                    </TableHeader>
                    <TableBody>
                        {isLoading ? (
                            <TableRow>
                                <TableCell colSpan={5} className="h-24 text-center">
                                    <Loader2 className="mx-auto h-6 w-6 animate-spin text-zinc-500" />
                                </TableCell>
                            </TableRow>
                        ) : stations?.length === 0 ? (
                            <TableRow>
                                <TableCell colSpan={5} className="h-24 text-center text-zinc-500">
                                    No objects found. Import XML or add manually.
                                </TableCell>
                            </TableRow>
                        ) : (
                            stations?.map((station: any) => (
                                <TableRow
                                    key={station.id}
                                    className="border-zinc-800 hover:bg-zinc-800/50 cursor-pointer"
                                    onClick={() => {
                                        if (selectedStations.includes(station.id)) {
                                            setSelectedStations(s => s.filter(id => id !== station.id));
                                        } else {
                                            setSelectedStations(s => [...s, station.id]);
                                        }
                                    }}
                                    data-state={selectedStations.includes(station.id) ? "selected" : undefined}
                                >
                                    <TableCell className="font-medium">
                                        {station.name}
                                        {selectedStations.includes(station.id) && <span className="ml-2 text-xs text-blue-400">(Selected)</span>}
                                    </TableCell>
                                    <TableCell>
                                        <Badge variant="secondary" className="bg-blue-900/30 text-blue-400 hover:bg-blue-900/50">
                                            {station.service}
                                        </Badge>
                                    </TableCell>
                                    <TableCell>
                                        <Badge variant="outline" className="border-zinc-700 text-zinc-400">
                                            {station.status}
                                        </Badge>
                                    </TableCell>
                                    <TableCell className="text-right">{station.freq?.toFixed(2)}</TableCell>
                                    <TableCell className="text-right">{station.erp?.toFixed(1)}</TableCell>
                                </TableRow>
                            ))
                        )}
                    </TableBody>
                </Table>
            </div>

            <ImportStationsModal
                isOpen={isImportOpen}
                onClose={() => setIsImportOpen(false)}
                networkId={networkId}
                onSuccess={() => refetch()}
            />

            <AdjustParamsModal
                isOpen={isAdjustOpen}
                onClose={() => setIsAdjustOpen(false)}
                networkId={networkId}
                stationIds={selectedStations}
                onSuccess={() => {
                    setSelectedStations([]);
                    refetch();
                }}
            />
        </div>
    );
}
