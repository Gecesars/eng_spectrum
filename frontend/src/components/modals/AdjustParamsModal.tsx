import { useState } from 'react';
import {
    Dialog,
    DialogContent,
    DialogHeader,
    DialogTitle,
    DialogFooter,
    DialogDescription
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { api } from '@/lib/axios';
import { Loader2 } from 'lucide-react';

interface AdjustParamsModalProps {
    isOpen: boolean;
    onClose: () => void;
    networkId: string;
    stationIds: string[];
    onSuccess: () => void;
}

export default function AdjustParamsModal({ isOpen, onClose, networkId, stationIds, onSuccess }: AdjustParamsModalProps) {
    const [erp, setErp] = useState('');
    const [htx, setHtx] = useState('');
    const [isLoading, setIsLoading] = useState(false);

    const handleApply = async () => {
        setIsLoading(true);
        try {
            await api.patch(`/v4/networks/${networkId}/stations/bulk`, {
                station_ids: stationIds,
                erp_dbm: erp ? parseFloat(erp) : undefined,
                htx: htx ? parseFloat(htx) : undefined,
            });
            onSuccess();
            onClose();
        } catch (error) {
            console.error("Bulk update failed", error);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <Dialog open={isOpen} onOpenChange={onClose}>
            <DialogContent className="bg-zinc-900 border-zinc-800 text-zinc-100 sm:max-w-md">
                <DialogHeader>
                    <DialogTitle>Adjust Parameters</DialogTitle>
                    <DialogDescription className="text-zinc-400">
                        Bulk update {stationIds.length} selected stations. Leave blank to keep current values.
                    </DialogDescription>
                </DialogHeader>

                <div className="grid gap-4 py-4">
                    <div className="grid grid-cols-2 gap-4">
                        <div className="space-y-2">
                            <Label htmlFor="erp">ERP (dBm)</Label>
                            <Input
                                id="erp"
                                type="number"
                                placeholder="No Change"
                                value={erp}
                                onChange={(e) => setErp(e.target.value)}
                                className="bg-zinc-950 border-zinc-800"
                            />
                        </div>
                        <div className="space-y-2">
                            <Label htmlFor="htx">TX Height (m)</Label>
                            <Input
                                id="htx"
                                type="number"
                                placeholder="No Change"
                                value={htx}
                                onChange={(e) => setHtx(e.target.value)}
                                className="bg-zinc-950 border-zinc-800"
                            />
                        </div>
                    </div>
                </div>

                <DialogFooter>
                    <Button variant="ghost" onClick={onClose} disabled={isLoading}>
                        Cancel
                    </Button>
                    <Button onClick={handleApply} disabled={isLoading} className="bg-green-600 hover:bg-green-500">
                        {isLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                        Apply Changes
                    </Button>
                </DialogFooter>
            </DialogContent>
        </Dialog>
    );
}
