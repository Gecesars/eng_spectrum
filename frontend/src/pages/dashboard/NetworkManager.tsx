import { useParams, Routes, Route, Navigate } from 'react-router-dom';
import NetworkObjects from './network/NetworkObjects';
import NetworkMap from './network/NetworkMap';
import NetworkCalculations from './network/NetworkCalculations';

export default function NetworkManager() {
    const { networkId } = useParams();

    return (
        <Routes>
            <Route index element={<Navigate to="objects" replace />} />
            <Route path="objects" element={<NetworkObjects />} />
            <Route path="map" element={<NetworkMap />} />
            <Route path="calculations" element={<NetworkCalculations />} />
            <Route path="reports" element={<div className="p-6">Reports ({networkId}) (Coming Soon)</div>} />
        </Routes>
    );
}
