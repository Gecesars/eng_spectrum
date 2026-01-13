import { useEffect, useRef, useState } from 'react';
import maplibregl from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';
import { useParams } from 'react-router-dom';

export default function NetworkMap() {
    const { networkId } = useParams();
    const mapContainer = useRef<HTMLDivElement>(null);
    const map = useRef<maplibregl.Map | null>(null);
    const [lng] = useState(-47.9292);
    const [lat] = useState(-15.7801);
    const [zoom] = useState(4);

    useEffect(() => {
        if (map.current || !mapContainer.current) return;

        // Custom Tile URL
        const tileUrl = `${window.location.origin}/api/v4/tiles/ibge/{z}/{x}/{y}.pbf`;

        map.current = new maplibregl.Map({
            container: mapContainer.current,
            style: {
                version: 8,
                sources: {
                    'osm': {
                        'type': 'raster',
                        'tiles': [
                            'https://a.tile.openstreetmap.org/{z}/{x}/{y}.png',
                            'https://b.tile.openstreetmap.org/{z}/{x}/{y}.png',
                            'https://c.tile.openstreetmap.org/{z}/{x}/{y}.png'
                        ],
                        'tileSize': 256,
                        'attribution': '&copy; OpenStreetMap Contributors'
                    },
                    'ibge-vector': {
                        'type': 'vector',
                        'tiles': [tileUrl],
                        'minzoom': 0,
                        'maxzoom': 14
                    }
                },
                layers: [
                    {
                        'id': 'osm-layer',
                        'type': 'raster',
                        'source': 'osm',
                        'minzoom': 0,
                        'maxzoom': 22
                    },
                    {
                        'id': 'stations-circle',
                        'type': 'circle',
                        'source': 'ibge-vector',
                        'source-layer': 'stations',
                        'paint': {
                            'circle-radius': 6,
                            'circle-color': '#e11d48',
                            'circle-stroke-width': 1,
                            'circle-stroke-color': '#fff'
                        }
                    }
                ]
            },
            center: [lng, lat],
            zoom: zoom
        });

        // Add controls
        map.current.addControl(new maplibregl.NavigationControl(), 'top-right');
        map.current.addControl(new maplibregl.FullscreenControl(), 'top-right');
        map.current.addControl(new maplibregl.ScaleControl(), 'bottom-right');

        // Cleanup
        return () => {
            map.current?.remove();
            map.current = null;
        };

    }, [lng, lat, zoom, networkId]); // Re-init if basic params change, though usually just once

    return (
        <div className="h-full w-full relative bg-zinc-950">
            <div ref={mapContainer} className="absolute inset-0" />

            <div className="absolute top-4 left-4 bg-zinc-900/90 p-4 rounded-lg border border-zinc-800 backdrop-blur pointer-events-none">
                <h3 className="text-sm font-semibold text-white mb-1">Layer Control</h3>
                <div className="flex items-center gap-2">
                    <div className="w-3 h-3 rounded-full bg-red-600 border border-white"></div>
                    <span className="text-xs text-zinc-400">Stations (MVT)</span>
                </div>
            </div>
        </div>
    );
}
