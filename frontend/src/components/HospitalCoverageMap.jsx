import { useEffect, useMemo } from 'react'
import {
  MapContainer,
  Marker,
  Popup,
  TileLayer,
  useMap,
} from 'react-leaflet'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import markerIcon2x from 'leaflet/dist/images/marker-icon-2x.png'
import markerIcon from 'leaflet/dist/images/marker-icon.png'
import markerShadow from 'leaflet/dist/images/marker-shadow.png'

const nigeriaCenter = [9.082, 8.6753]
const nigeriaZoom = 6

L.Icon.Default.mergeOptions({
  iconRetinaUrl: markerIcon2x,
  iconUrl: markerIcon,
  shadowUrl: markerShadow,
})

function MapBounds({ hospitals }) {
  const map = useMap()

  useEffect(() => {
    if (!hospitals.length) return

    const bounds = L.latLngBounds(
      hospitals.map((hospital) => [hospital.latitude, hospital.longitude])
    )
    map.fitBounds(bounds, { padding: [32, 32], maxZoom: 12 })
  }, [hospitals, map])

  return null
}

function formatFacilities(hospital) {
  if (hospital.facilities?.length) {
    return hospital.facilities.join(', ')
  }
  return [hospital.services, hospital.capabilities].filter(Boolean).join(', ')
}

export default function HospitalCoverageMap({
  hospitals,
  highlightedHospitalId,
  onBook,
  embedded = false,
}) {
  const hospitalsWithCoordinates = useMemo(
    () =>
      hospitals.filter(
        (hospital) =>
          typeof hospital.latitude === 'number' &&
          typeof hospital.longitude === 'number'
      ),
    [hospitals]
  )

  if (!hospitalsWithCoordinates.length) {
    return (
      <section className={embedded ? 'map-section map-section-embedded' : 'map-section card'}>
        <div className="map-copy">
          <span className="map-eyebrow">Healthcare Coverage Map</span>
          <h2>Hospital locations will appear here</h2>
          <p className="muted">
            This view needs hospitals with latitude and longitude. Once coordinates
            are available, we can plot every facility on the Nigeria map.
          </p>
        </div>
      </section>
    )
  }

  return (
    <section className={embedded ? 'map-section map-section-embedded' : 'map-section card'}>
      <div className="map-header">
        <div className="map-copy">
          <span className="map-eyebrow">Healthcare Coverage Map</span>
          <h2>Find hospitals across Nigeria</h2>
          <p>
            Explore mapped hospitals, inspect specialties, and jump straight into
            booking from the map.
          </p>
        </div>
        <div className="map-stats">
          <div className="map-stat">
            <strong>{hospitalsWithCoordinates.length}</strong>
            <span>Mapped hospitals</span>
          </div>
        </div>
      </div>

      <div className="map-canvas">
        <MapContainer
          center={nigeriaCenter}
          zoom={nigeriaZoom}
          scrollWheelZoom
          className="leaflet-map"
        >
          <TileLayer
            attribution='&copy; OpenStreetMap contributors'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
          <MapBounds hospitals={hospitalsWithCoordinates} />
          {hospitalsWithCoordinates.map((hospital) => (
            <Marker
              key={hospital.id}
              position={[hospital.latitude, hospital.longitude]}
            >
              <Popup>
                <div className="map-popup">
                  <h3>{hospital.name}</h3>
                  <p>{hospital.lga}, {hospital.state}</p>
                  <p>{hospital.address}</p>
                  <p>
                    <strong>Specialties:</strong> {hospital.specialties}
                  </p>
                  <p>
                    <strong>Facilities:</strong> {formatFacilities(hospital)}
                  </p>
                  <button
                    type="button"
                    className={
                      highlightedHospitalId === hospital.id
                        ? 'map-popup-button active'
                        : 'map-popup-button'
                    }
                    onClick={() => onBook(hospital)}
                  >
                    {highlightedHospitalId === hospital.id ? 'Booking Open' : 'Book appointment'}
                  </button>
                </div>
              </Popup>
            </Marker>
          ))}
        </MapContainer>
      </div>
    </section>
  )
}
