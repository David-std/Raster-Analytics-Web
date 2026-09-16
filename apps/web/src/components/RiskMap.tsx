import { CircleMarker, MapContainer, Popup, TileLayer } from "react-leaflet";

import type { RiskMapItem } from "../types";

interface RiskMapProps {
  items: RiskMapItem[];
  selectedId: string | null;
  onSelect: (item: RiskMapItem) => void;
}

function markerColor(value: number | null): string {
  if (value === null) return "#64748b";
  if (value < 0.33) return "#0f766e";
  if (value < 0.66) return "#d97706";
  return "#b91c1c";
}

function markerRadius(value: number | null): number {
  if (value === null) return 10;
  return 9 + value * 11;
}

export function RiskMap({ items, selectedId, onSelect }: RiskMapProps) {
  return (
    <MapContainer
      center={[-12.06, -77.04]}
      zoom={11}
      scrollWheelZoom
      className="risk-map"
    >
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />

      {items.map((item) => {
        const isSelected = item.spatial_unit_id === selectedId;
        const center: [number, number] = [item.latitude, item.longitude];
        const color = markerColor(item.value);

        return (
          <CircleMarker
            key={`${item.spatial_unit_id}-${item.period_id}`}
            center={center}
            radius={markerRadius(item.value) + (isSelected ? 3 : 0)}
            pathOptions={{
              color,
              fillColor: color,
              fillOpacity: isSelected ? 0.9 : 0.68,
              weight: isSelected ? 4 : 2,
            }}
            eventHandlers={{ click: () => onSelect(item) }}
          >
            <Popup>
              <strong>{item.name}</strong>
              <br />
              Score: {item.value?.toFixed(4) ?? "No value"}
            </Popup>
          </CircleMarker>
        );
      })}
    </MapContainer>
  );
}
