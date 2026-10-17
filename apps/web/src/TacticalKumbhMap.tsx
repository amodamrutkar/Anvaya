import { useState, useEffect, useRef } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { Radio, Maximize2, RefreshCw, ZoomIn, ZoomOut } from 'lucide-react';

interface DroneSector {
  id: string;
  unit: string;
  sectorName: string;
  targetName: string;
  lat: number;
  lng: number;
  footfall: string;
  density: string;
  densityLevel: 'HIGH' | 'CRITICAL' | 'MODERATE';
  radius: number;
  terrain: string;
  bandwidth: string;
  alertType: string;
}

const DRONE_SECTORS: DroneSector[] = [
  {
    id: 'sec-4',
    unit: 'UNIT-D2',
    sectorName: 'SECTOR 4 RAMKUND',
    targetName: 'TARGET LOCATED: RAMKUND GHAT',
    lat: 19.9975,
    lng: 73.7898,
    footfall: '142,500',
    density: 'HIGH (8.4/m²)',
    densityLevel: 'HIGH',
    radius: 450,
    terrain: 'URBAN RIVERFRONT',
    bandwidth: '42 MBPS',
    alertType: 'CRIMINAL ANOMALY PINPOINTED'
  },
  {
    id: 'sec-3',
    unit: 'UNIT-D1',
    sectorName: 'SECTOR 3 PANCHAVATI',
    targetName: 'TARGET LOCATED: KALA RAM MANDIR',
    lat: 20.0050,
    lng: 73.7950,
    footfall: '118,000',
    density: 'HIGH (7.8/m²)',
    densityLevel: 'HIGH',
    radius: 400,
    terrain: 'TEMPLE CONCOURSE',
    bandwidth: '48 MBPS',
    alertType: 'SUSPICIOUS RECCE DETECTED'
  },
  {
    id: 'sec-5',
    unit: 'UNIT-D3',
    sectorName: 'SECTOR 5 TAPOVAN',
    targetName: 'PERIMETER HOLD: SANGAM SADHU CAMP',
    lat: 19.9880,
    lng: 73.8050,
    footfall: '95,000',
    density: 'CRITICAL (9.2/m²)',
    densityLevel: 'CRITICAL',
    radius: 500,
    terrain: 'ENCAMPMENT GROUND',
    bandwidth: '36 MBPS',
    alertType: 'HIGH CONGESTION BOTTLENECK'
  },
  {
    id: 'sec-2',
    unit: 'UNIT-D4',
    sectorName: 'SECTOR 2 SOMESHWAR',
    targetName: 'CHECKPOINT: SOMESHWAR UPSTREAM',
    lat: 19.9980,
    lng: 73.7380,
    footfall: '68,000',
    density: 'MODERATE (4.1/m²)',
    densityLevel: 'MODERATE',
    radius: 350,
    terrain: 'UPSTREAM WATERFRONT',
    bandwidth: '54 MBPS',
    alertType: 'CLEAR PERIMETER'
  }
];

export function TacticalKumbhMap({
  onNavigateKumbh,
  theme = 'light',
  style
}: {
  onNavigateKumbh?: () => void;
  theme?: 'dark' | 'light';
  style?: React.CSSProperties;
}) {
  const [currentSectorIndex, setCurrentSectorIndex] = useState<number>(0);
  const sector = DRONE_SECTORS[currentSectorIndex];

  const mapContainerRef = useRef<HTMLDivElement | null>(null);
  const mapInstanceRef = useRef<L.Map | null>(null);
  const markerRef = useRef<L.Marker | null>(null);
  const circleRef = useRef<L.Circle | null>(null);
  const tileLayerRef = useRef<L.TileLayer | null>(null);

  const handleNextSector = () => {
    setCurrentSectorIndex((prev) => (prev + 1) % DRONE_SECTORS.length);
  };

  const handleZoomIn = () => {
    mapInstanceRef.current?.zoomIn();
  };

  const handleZoomOut = () => {
    mapInstanceRef.current?.zoomOut();
  };

  // Helper to build custom tactical icon HTML
  const createMarkerIcon = (targetLabel: string) => {
    return L.divIcon({
      className: 'tactical-marker-container',
      html: `
        <div style="position: relative; display: flex; flex-direction: column; align-items: center; transform: translate(-50%, -50%); cursor: pointer;">
          <!-- Pulsing Outer Beacon Rings -->
          <div style="position: absolute; width: 48px; height: 48px; border-radius: 50%; background: rgba(220, 38, 38, 0.28); animation: pulseRing 1.8s infinite ease-out;"></div>
          <div style="position: absolute; width: 32px; height: 32px; border-radius: 50%; background: rgba(220, 38, 38, 0.45); animation: pulseRing 1.8s infinite ease-out 0.4s;"></div>
          
          <!-- Central Alert Badge Icon -->
          <div style="width: 26px; height: 26px; border-radius: 50%; background: #dc2626; border: 2.5px solid #ffffff; box-shadow: 0 0 12px rgba(220, 38, 38, 0.9); display: flex; align-items: center; justify-content: center; color: #ffffff; font-weight: 900; font-size: 13px; font-family: monospace; z-index: 10;">
            !
          </div>

          <!-- Callout Target Badge -->
          <div style="margin-top: 8px; background: rgba(255, 255, 255, 0.98); color: #991b1b; padding: 4px 12px; border-radius: 4px; font-size: 11px; font-weight: 800; font-family: 'JetBrains Mono', monospace; letter-spacing: 0.05em; border: 1.5px solid #dc2626; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3); white-space: nowrap; z-index: 10;">
            ${targetLabel}
          </div>
        </div>
      `,
      iconSize: [26, 26],
      iconAnchor: [13, 13]
    });
  };

  // Initialize Leaflet Map once
  useEffect(() => {
    if (!mapContainerRef.current || mapInstanceRef.current) return;

    const initialMap = L.map(mapContainerRef.current, {
      center: [sector.lat, sector.lng],
      zoom: 14.5,
      zoomControl: false,
      attributionControl: true
    });

    // Choose tile layer based on theme (Google Maps for light mode, Dark OSM for dark mode)
    const isDark = theme === 'dark';
    const tileUrl = isDark
      ? 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png'
      : 'https://mt{s}.google.com/vt/lyrs=m&x={x}&y={y}&z={z}';
    const subdomains = isDark ? ['a', 'b', 'c'] : ['0', '1', '2', '3'];
    const attribution = isDark
      ? '&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noreferrer">OpenStreetMap</a> contributors'
      : '&copy; Google Maps';

    const tileLayer = L.tileLayer(tileUrl, {
      subdomains,
      maxZoom: 20,
      attribution,
      className: isDark ? 'tactical-dark-tiles' : ''
    }).addTo(initialMap);

    tileLayerRef.current = tileLayer;

    // Geofence Circle Boundary
    const geofenceCircle = L.circle([sector.lat, sector.lng], {
      radius: sector.radius,
      color: sector.densityLevel === 'CRITICAL' ? '#dc2626' : (isDark ? '#fbbf24' : '#2563eb'),
      fillColor: sector.densityLevel === 'CRITICAL' ? '#ef4444' : (isDark ? '#fbbf24' : '#3b82f6'),
      fillOpacity: 0.12,
      weight: 2,
      dashArray: '6, 6'
    }).addTo(initialMap);
    circleRef.current = geofenceCircle;

    // Tactical Target Marker
    const marker = L.marker([sector.lat, sector.lng], {
      icon: createMarkerIcon(sector.targetName)
    }).addTo(initialMap);
    markerRef.current = marker;

    mapInstanceRef.current = initialMap;

    // Invalidate map size after short tick so tiles layout properly in flex containers
    const timer = setTimeout(() => {
      initialMap.invalidateSize();
    }, 150);

    return () => {
      clearTimeout(timer);
      initialMap.remove();
      mapInstanceRef.current = null;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Update sector position, marker icon, and circle when sector changes
  useEffect(() => {
    const map = mapInstanceRef.current;
    if (!map) return;

    // Smooth tactical pan to new sector
    map.flyTo([sector.lat, sector.lng], 14.5, {
      duration: 1.2
    });

    if (markerRef.current) {
      markerRef.current.setLatLng([sector.lat, sector.lng]);
      markerRef.current.setIcon(createMarkerIcon(sector.targetName));
    }

    if (circleRef.current) {
      const isDark = theme === 'dark';
      circleRef.current.setLatLng([sector.lat, sector.lng]);
      circleRef.current.setRadius(sector.radius);
      circleRef.current.setStyle({
        color: sector.densityLevel === 'CRITICAL' ? '#dc2626' : (isDark ? '#fbbf24' : '#2563eb'),
        fillColor: sector.densityLevel === 'CRITICAL' ? '#ef4444' : (isDark ? '#fbbf24' : '#3b82f6')
      });
    }
  }, [sector, theme]);

  // Seamlessly swap tile layer when theme changes
  useEffect(() => {
    const map = mapInstanceRef.current;
    if (!map) return;

    if (tileLayerRef.current) {
      map.removeLayer(tileLayerRef.current);
    }

    const isDark = theme === 'dark';
    const tileUrl = isDark
      ? 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png'
      : 'https://mt{s}.google.com/vt/lyrs=m&x={x}&y={y}&z={z}';
    const subdomains = isDark ? ['a', 'b', 'c'] : ['0', '1', '2', '3'];
    const attribution = isDark
      ? '&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noreferrer">OpenStreetMap</a> contributors'
      : '&copy; Google Maps';

    const newTileLayer = L.tileLayer(tileUrl, {
      subdomains,
      maxZoom: 20,
      attribution,
      className: isDark ? 'tactical-dark-tiles' : ''
    }).addTo(map);

    tileLayerRef.current = newTileLayer;
    map.invalidateSize();
  }, [theme]);

  return (
    <div
      className="gov-card"
      style={{
        padding: '0',
        overflow: 'hidden',
        border: '1px solid var(--border-medium)',
        borderRadius: 'var(--radius-md)',
        display: 'flex',
        flexDirection: 'column',
        height: '100%',
        ...style
      }}
    >
      {/* 1. Header Bar */}
      <div style={{
        padding: '10px 16px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        background: theme === 'light' ? '#f8fafc' : 'rgba(13, 21, 39, 0.9)',
        borderBottom: '1px solid var(--border-subtle)',
        flexWrap: 'wrap',
        gap: '8px'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <div style={{
            width: '28px',
            height: '28px',
            borderRadius: 'var(--radius-xs)',
            background: 'rgba(217, 119, 6, 0.15)',
            border: '1px solid rgba(217, 119, 6, 0.35)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}>
            <Radio size={16} color="var(--accent-gold)" />
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <span style={{ fontSize: '0.8rem', fontWeight: 800, letterSpacing: '0.04em', color: 'var(--text-primary)', fontFamily: 'var(--font-mono)' }}>
                TACTICAL SITREP // NASHIK KUMBH
              </span>
              <span style={{
                display: 'inline-block',
                width: '7px',
                height: '7px',
                borderRadius: '50%',
                background: '#16a34a',
                boxShadow: '0 0 8px #16a34a'
              }} />
            </div>
            <div style={{ fontSize: '0.66rem', color: 'var(--text-muted)' }}>
              Real-time surveillance & crowd geofence telemetry • Nashik Police Command Link
            </div>
          </div>
        </div>

        {/* Sector Badge */}
        <div style={{
          padding: '4px 10px',
          background: theme === 'light' ? '#fffbeb' : 'rgba(217, 119, 6, 0.15)',
          border: `1.5px solid ${theme === 'light' ? '#fde68a' : 'rgba(217, 119, 6, 0.4)'}`,
          borderRadius: 'var(--radius-xs)',
          fontSize: '0.74rem',
          fontWeight: 800,
          color: theme === 'light' ? '#92400e' : 'var(--accent-gold-light)',
          fontFamily: 'var(--font-mono)',
          letterSpacing: '0.05em'
        }}>
          {sector.sectorName}
        </div>
      </div>

      {/* 2. Interactive Leaflet Map Container with Overlays */}
      <div style={{ position: 'relative', flex: 1, minHeight: '300px', width: '100%', background: '#e5e7eb' }}>
        {/* Real Leaflet DOM container */}
        <div
          ref={mapContainerRef}
          style={{
            height: '100%',
            width: '100%',
            zIndex: 1
          }}
        />

        {/* Top-Left Tactical HUD Overlay */}
        <div style={{
          position: 'absolute',
          top: '8px',
          left: '8px',
          zIndex: 1000,
          background: 'rgba(255, 255, 255, 0.95)',
          border: '1px solid #cbd5e1',
          borderRadius: '4px',
          padding: '3px 8px',
          display: 'flex',
          alignItems: 'center',
          gap: '6px',
          boxShadow: '0 2px 6px rgba(0, 0, 0, 0.12)',
          fontFamily: 'var(--font-mono)',
          fontSize: '0.65rem',
          fontWeight: 800,
          color: '#0f172a'
        }}>
          <span style={{ width: '7px', height: '7px', borderRadius: '50%', background: '#16a34a', display: 'inline-block' }} />
          <span>DRONE_FEED_ACTIVE // {sector.unit}</span>
        </div>

        {/* Top-Right Coordinates HUD Overlay & Custom Zoom Controls */}
        <div style={{
          position: 'absolute',
          top: '8px',
          right: '8px',
          zIndex: 1000,
          display: 'flex',
          alignItems: 'center',
          gap: '6px'
        }}>
          <div style={{
            background: 'rgba(255, 255, 255, 0.95)',
            border: '1px solid #cbd5e1',
            borderRadius: '4px',
            padding: '3px 8px',
            boxShadow: '0 2px 6px rgba(0, 0, 0, 0.12)',
            fontFamily: 'var(--font-mono)',
            fontSize: '0.65rem',
            fontWeight: 800,
            color: '#1e3a8a'
          }}>
            {sector.lat.toFixed(4)}° N // {sector.lng.toFixed(4)}° E
          </div>

          {/* Clean Custom Tactical Zoom Controls */}
          <div style={{ display: 'flex', flexDirection: 'column', background: 'rgba(255, 255, 255, 0.95)', border: '1px solid #cbd5e1', borderRadius: '4px', boxShadow: '0 2px 6px rgba(0, 0, 0, 0.12)' }}>
            <button
              onClick={handleZoomIn}
              title="Zoom In"
              style={{ padding: '3px 5px', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#1e293b', borderBottom: '1px solid #e2e8f0' }}
            >
              <ZoomIn size={12} />
            </button>
            <button
              onClick={handleZoomOut}
              title="Zoom Out"
              style={{ padding: '3px 5px', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#1e293b' }}
            >
              <ZoomOut size={12} />
            </button>
          </div>
        </div>

        {/* Bottom Floating Tactical Metrics Grid */}
        <div style={{
          position: 'absolute',
          bottom: '8px',
          left: '8px',
          right: '8px',
          zIndex: 1000,
          display: 'grid',
          gridTemplateColumns: 'repeat(3, 1fr)',
          gap: '6px',
          pointerEvents: 'none'
        }}>
          {/* Stat 1: Est. Footfall */}
          <div style={{
            background: 'rgba(255, 255, 255, 0.96)',
            border: '1px solid #cbd5e1',
            borderRadius: '4px',
            padding: '4px 8px',
            boxShadow: '0 2px 6px rgba(0, 0, 0, 0.1)',
            pointerEvents: 'auto'
          }}>
            <div style={{ fontSize: '0.55rem', color: '#64748b', fontWeight: 800, letterSpacing: '0.04em', fontFamily: 'var(--font-mono)' }}>
              EST. FOOTFALL
            </div>
            <div style={{ fontSize: '0.8rem', fontWeight: 800, color: '#0f172a', fontFamily: 'var(--font-mono)', marginTop: '1px' }}>
              {sector.footfall}
            </div>
          </div>

          {/* Stat 2: Density Index */}
          <div style={{
            background: 'rgba(255, 255, 255, 0.96)',
            border: '1px solid #cbd5e1',
            borderRadius: '4px',
            padding: '4px 8px',
            boxShadow: '0 2px 6px rgba(0, 0, 0, 0.1)',
            pointerEvents: 'auto'
          }}>
            <div style={{ fontSize: '0.55rem', color: '#64748b', fontWeight: 800, letterSpacing: '0.04em', fontFamily: 'var(--font-mono)' }}>
              DENSITY INDEX
            </div>
            <div style={{
              fontSize: '0.78rem',
              fontWeight: 800,
              color: sector.densityLevel === 'CRITICAL' ? '#dc2626' : '#d97706',
              fontFamily: 'var(--font-mono)',
              marginTop: '1px'
            }}>
              {sector.density}
            </div>
          </div>

          {/* Stat 3: Geofence Lock */}
          <div style={{
            background: 'rgba(255, 255, 255, 0.96)',
            border: '1px solid #cbd5e1',
            borderRadius: '4px',
            padding: '4px 8px',
            boxShadow: '0 2px 6px rgba(0, 0, 0, 0.1)',
            pointerEvents: 'auto'
          }}>
            <div style={{ fontSize: '0.55rem', color: '#64748b', fontWeight: 800, letterSpacing: '0.04em', fontFamily: 'var(--font-mono)' }}>
              GEOFENCE LOCK
            </div>
            <div style={{ fontSize: '0.78rem', fontWeight: 800, color: '#16a34a', fontFamily: 'var(--font-mono)', marginTop: '1px' }}>
              {sector.radius}m RADIUS
            </div>
          </div>
        </div>
      </div>

      {/* 3. Tactical Command Footer Bar */}
      <div style={{
        padding: '8px 12px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        background: theme === 'light' ? '#ffffff' : 'var(--bg-secondary)',
        borderTop: '1px solid var(--border-subtle)',
        flexWrap: 'wrap',
        gap: '8px'
      }}>
        <div style={{ fontSize: '0.68rem', color: 'var(--text-secondary)', fontFamily: 'var(--font-mono)', fontWeight: 600 }}>
          <span>TERRAIN: <strong>{sector.terrain}</strong></span>
          <span style={{ margin: '0 6px', opacity: 0.4 }}>//</span>
          <span>BANDWIDTH: <strong>{sector.bandwidth}</strong></span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          {/* Switch Drone Feed Button */}
          <button
            onClick={handleNextSector}
            className="scenario-chip"
            style={{
              padding: '4px 10px',
              fontFamily: 'var(--font-mono)',
              fontSize: '0.68rem',
              fontWeight: 700
            }}
            title="Cycle across active Kumbh drone surveillance sectors"
          >
            <RefreshCw size={12} />
            <span>[ Switch Drone Feed ]</span>
          </button>

          {/* Fullscreen / Open Operations Button */}
          {onNavigateKumbh && (
            <button
              onClick={onNavigateKumbh}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '5px',
                padding: '4px 10px',
                borderRadius: 'var(--radius-xs)',
                background: theme === 'light' ? '#eff6ff' : 'rgba(37, 99, 235, 0.15)',
                border: `1.5px solid ${theme === 'light' ? '#2563eb' : 'rgba(59, 130, 246, 0.4)'}`,
                color: theme === 'light' ? '#1e3a8a' : '#93c5fd',
                fontSize: '0.68rem',
                fontWeight: 700,
                fontFamily: 'var(--font-mono)',
                cursor: 'pointer',
                transition: 'all 0.15s ease'
              }}
              title="Launch Full Kumbh Operations Surveillance Grid"
            >
              <Maximize2 size={12} />
              <span>[ Fullscreen Tactical Map ]</span>
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
