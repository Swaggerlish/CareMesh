import { useState } from 'react'
import HospitalCoverageMap from './HospitalCoverageMap'

const tabs = [
  { id: 'coverage', label: 'Coverage Map' },
  { id: 'facilities', label: 'Facilities' },
  { id: 'deserts', label: 'Medical Deserts' },
  { id: 'inventory', label: 'Inventory' },
]

function severityClass(severity) {
  if (severity === 'CRITICAL GAP') return 'desert-card critical'
  if (severity === 'SERVICE GAP') return 'desert-card medium'
  return 'desert-card watch'
}

export default function HealthcarePlanningPanel({
  hospitals,
  highlightedHospitalId,
  onBook,
  planning,
  planningLoading,
  planningError,
}) {
  const [activeTab, setActiveTab] = useState('coverage')
  const [expandedAnalysisKey, setExpandedAnalysisKey] = useState('')
  const medicalDeserts = planning?.medical_deserts || []
  const facilitySummary = planning?.facilities_summary || []
  const inventorySignals = planning?.inventory_signals || []

  return (
    <section className="planning-panel card">
      <div className="planning-tabs" role="tablist" aria-label="Healthcare planning views">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            type="button"
            className={activeTab === tab.id ? 'planning-tab active' : 'planning-tab'}
            onClick={() => setActiveTab(tab.id)}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {activeTab === 'coverage' && (
        <HospitalCoverageMap
          hospitals={hospitals}
          highlightedHospitalId={highlightedHospitalId}
          onBook={onBook}
          embedded
        />
      )}

      {activeTab === 'facilities' && (
        <div className="planning-view">
          <div className="planning-copy">
            <h2>Facilities Snapshot</h2>
            <p className="muted">
              Quick view of where mapped hospital capacity is concentrated across Nigerian states.
            </p>
          </div>
          <div className="facility-grid">
            {facilitySummary.map((item) => (
              <article key={item.state} className="facility-card">
                <h3>{item.state}</h3>
                <p>{item.count} hospitals listed</p>
                <p>{item.mapped} with coordinates</p>
                <div className="service-tags">
                  {item.specialties.map((specialty) => (
                    <span key={specialty} className="service-tag">{specialty}</span>
                  ))}
                </div>
              </article>
            ))}
          </div>
        </div>
      )}

      {activeTab === 'deserts' && (
        <div className="planning-view">
          <div className="planning-copy">
            <h2>Medical Deserts Detected</h2>
            <p className="muted">
              Areas with critical healthcare gaps based on hospital scarcity, missing core services, and nearest-care distance.
            </p>
            <p className="planning-note">{planning?.note || 'Loading planning methodology...'}</p>
          </div>
          {planningLoading && <p className="muted">Updating planning snapshot...</p>}
          {planningError && <p className="muted">{planningError}</p>}
          <div className="desert-list">
            {medicalDeserts.slice(0, 6).map((desert) => (
              <article key={`${desert.state}-${desert.lga}`} className={severityClass(desert.severity)}>
                {(() => {
                  const analysisKey = `${desert.state}-${desert.lga}`
                  const isExpanded = expandedAnalysisKey === analysisKey
                  const localHospitals = hospitals.filter(
                    (hospital) => hospital.state === desert.state && hospital.lga === desert.lga
                  )

                  return (
                    <>
                <div className="desert-header">
                  <div>
                    <h3>{desert.lga}</h3>
                    <p>{desert.state}</p>
                  </div>
                  <span className="severity-pill">{desert.severity}</span>
                </div>
                <div className="desert-metrics">
                  <div className="desert-metric">
                    <span>Affected</span>
                    <strong>{(desert.population || 0).toLocaleString()}</strong>
                  </div>
                  <div className="desert-metric">
                    <span>Nearest Care</span>
                    <strong>{desert.nearest_care_km} km</strong>
                  </div>
                  <div className="desert-metric">
                    <span>Road Travel Time</span>
                    <strong>{desert.estimated_travel_time_minutes} min</strong>
                  </div>
                  <div className="desert-metric">
                    <span>Doctor Capacity</span>
                    <strong>{desert.doctor_capacity}</strong>
                  </div>
                </div>
                <div className="desert-services">
                  <span>Missing Services:</span>
                  <div className="service-tags">
                    {desert.missing_services.slice(0, 5).map((service) => (
                      <span key={service} className="service-tag">{service}</span>
                    ))}
                  </div>
                </div>
                <div className="desert-actions">
                  <button
                    type="button"
                    className="secondary-ghost"
                    onClick={() => setExpandedAnalysisKey(isExpanded ? '' : analysisKey)}
                  >
                    {isExpanded ? 'Hide Analysis' : 'View Analysis'}
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      const facility = hospitals.find(
                        (hospital) =>
                          hospital.state === desert.state && hospital.lga === desert.lga
                      )
                      if (facility) onBook(facility)
                    }}
                  >
                    Allocate Resources
                  </button>
                </div>
                {isExpanded && (
                  <div className="desert-analysis">
                    <div className="desert-analysis-header">
                      <h4>Analysis for {desert.lga}, {desert.state}</h4>
                      <span className="analysis-score">Priority Score {desert.score}</span>
                    </div>
                    <div className="desert-analysis-grid">
                      <div className="analysis-card">
                        <span>Facilities in LGA</span>
                        <strong>{desert.facilities_in_lga}</strong>
                        <p>{desert.mapped_hospitals} mapped with coordinates in the current registry dataset.</p>
                      </div>
                      <div className="analysis-card">
                        <span>Capacity Snapshot</span>
                        <strong>{desert.bed_capacity} beds</strong>
                        <p>{desert.doctor_capacity} doctors and {desert.nurse_capacity} nurses currently inferred.</p>
                      </div>
                      <div className="analysis-card">
                        <span>Access Pressure</span>
                        <strong>{desert.estimated_travel_time_minutes} min</strong>
                        <p>Estimated travel time to nearest care is {desert.nearest_care_km} km.</p>
                      </div>
                      <div className="analysis-card">
                        <span>Response Need</span>
                        <strong>{desert.missing_services.length} service gaps</strong>
                        <p>{desert.missing_services.join(', ') || 'No missing core services recorded.'}</p>
                      </div>
                    </div>
                    <div className="desert-analysis-note">
                      <p><strong>Population source:</strong> {desert.population_source}</p>
                      <p><strong>Recommendation:</strong> {desert.recommendation}</p>
                      <p><strong>Local hospitals in this LGA:</strong> {localHospitals.length ? localHospitals.map((hospital) => hospital.name).slice(0, 4).join(', ') : 'No mapped hospitals currently available in the selected LGA list.'}</p>
                    </div>
                  </div>
                )}
                <p className="desert-footnote">
                  Population source: {desert.population_source}. Recommendation: {desert.recommendation}
                </p>
                    </>
                  )
                })()}
              </article>
            ))}
            {!medicalDeserts.length && (
              <p className="muted">No priority medical desert candidates were detected from the current dataset.</p>
            )}
          </div>
        </div>
      )}

      {activeTab === 'inventory' && (
        <div className="planning-view">
          <div className="planning-copy">
            <h2>Priority Inventory Signals</h2>
            <p className="muted">
              Resource categories that appear most often in underserved areas and may need government intervention first.
            </p>
          </div>
          <div className="inventory-grid">
            {inventorySignals.map((item) => (
              <article key={item.service} className="inventory-card">
                <h3>{item.service}</h3>
                <p>{item.desert_count} underserved areas flagged</p>
                <strong>{item.affected_population.toLocaleString()} residents impacted</strong>
              </article>
            ))}
          </div>
        </div>
      )}
    </section>
  )
}
