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
import { Upload, FileUp, Loader2 } from 'lucide-react';

interface ImportStationsModalProps {
    isOpen: boolean;
    onClose: () => void;
    networkId: string;
    onSuccess: () => void;
}

export default function ImportStationsModal({ isOpen, onClose, networkId, onSuccess }: ImportStationsModalProps) {
    const [file, setFile] = useState<File | null>(null);
    const [isLoading, setIsLoading] = useState(false);

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files[0]) {
            setFile(e.target.files[0]);
        }
    };

    const handleImport = async () => {
        if (!file) return;

        setIsLoading(true);
        const formData = new FormData();
        formData.append('file', file);
        formData.append('network_id', networkId);

        try {
            await api.post(`/v4/networks/${networkId}/import`, formData, {
                headers: { 'Content-Type': 'multipart/form-data' }
            });
            onSuccess();
            onClose();
        } catch (error) {
            console.error("Import failed", error);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <Dialog open={isOpen} onOpenChange={onClose}>
            <DialogContent className="bg-zinc-900 border-zinc-800 text-zinc-100 sm:max-w-md">
                <DialogHeader>
                    <DialogTitle>Import Stations (Anatel)</DialogTitle>
                    <DialogDescription className="text-zinc-400">
                        Upload an XML file (Plano Básico) to import stations into this network.
                    </DialogDescription>
                </DialogHeader>

                <div className="grid gap-4 py-4">
                    <div className="flex items-center justify-center w-full">
                        <Label
                            htmlFor="dropzone-file"
                            className="flex flex-col items-center justify-center w-full h-32 border-2 border-zinc-700 border-dashed rounded-lg cursor-pointer bg-zinc-800/50 hover:bg-zinc-800 transition-colors"
                        >
                            <div className="flex flex-col items-center justify-center pt-5 pb-6">
                                <Upload className="w-8 h-8 mb-3 text-zinc-400" />
                                <p className="mb-2 text-sm text-zinc-400">
                                    <span className="font-semibold">Click to upload</span> or drag and drop
                                </p>
                                <p className="text-xs text-zinc-500">XML (MAX. 50MB)</p>
                            </div>
                            <Input
                                id="dropzone-file"
                                type="file"
                                accept=".xml"
                                className="hidden"
                                onChange={handleFileChange}
                            />
                        </Label>
                    </div>
                    {file && (
                        <div className="flex items-center gap-2 text-sm text-green-400 bg-green-900/20 p-2 rounded">
                            <FileUp size={16} />
                            {file.name}
                        </div>
                    )}
                </div>

                <DialogFooter>
                    <Button variant="ghost" onClick={onClose} disabled={isLoading}>
                        Cancel
                    </Button>
                    <Button onClick={handleImport} disabled={!file || isLoading} className="bg-blue-600 hover:bg-blue-500">
                        {isLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                        Import
                    </Button>
                </DialogFooter>
            </DialogContent>
        </Dialog>
    );
}
