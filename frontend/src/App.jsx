import { useEffect, useMemo, useState } from 'react'
import { fetchHospitals, fetchLgas, fetchPlanningSnapshot, fetchStates } from './api'
import BookingModal from './components/BookingModal'
import ChatBox from './components/ChatBox'
import ConsultationPage from './components/ConsultationPage'
import HealthcarePlanningPanel from './components/HealthcarePlanningPanel'
import HospitalCard from './components/HospitalCard'
import PaymentCallback from './components/PaymentCallback'
import PaymentPayload from './components/PaymentPayload'

const scriptUrl = import.meta.env.VITE_INTERSWITCH_SCRIPT_URL
const CACHE_PREFIX = 'caremesh-cache'

function readCache(key, fallback = null) {
  try {
    const raw = window.localStorage.getItem(`${CACHE_PREFIX}:${key}`)
    return raw ? JSON.parse(raw) : fallback
  } catch {
    return fallback
  }
}

function writeCache(key, value) {
  try {
    window.localStorage.setItem(`${CACHE_PREFIX}:${key}`, JSON.stringify(value))
  } catch {
    // Ignore storage failures in demo mode.
  }
}

export default function App() {
  const [state, setState] = useState('')
  const [lga, setLga] = useState('')
  const [query, setQuery] = useState('')
  const [hospitals, setHospitals] = useState([])
  const [selectedHospital, setSelectedHospital] = useState(null)
  const [bootstrapLoading, setBootstrapLoading] = useState(false)
  const [searchLoading, setSearchLoading] = useState(false)
  const [stateOptions, setStateOptions] = useState([])
  const [lgaOptions, setLgaOptions] = useState([])
  const [hospitalOptions, setHospitalOptions] = useState([])
  const [selectedHospitalId, setSelectedHospitalId] = useState('')
  const [isOfflineMode, setIsOfflineMode] = useState(() => readCache('offline-mode', false))
  const [networkOnline, setNetworkOnline] = useState(() => window.navigator.onLine)
  const [planning, setPlanning] = useState(null)
  const [planningLoading, setPlanningLoading] = useState(false)
  const [planningError, setPlanningError] = useState('')
  const offlineActive = isOfflineMode || !networkOnline

  const isCallbackPage = useMemo(() => window.location.pathname.includes('/payment/callback'), [])
  const isPayloadPage = useMemo(() => window.location.pathname.includes('/payment/payload'), [])
  const isConsultationPage = useMemo(() => window.location.pathname.includes('/consultation'), [])

  useEffect(() => {
    const script = document.createElement('script')
    script.src = scriptUrl
    script.async = true
    document.body.appendChild(script)
    return () => {
      document.body.removeChild(script)
    }
  }, [])

  useEffect(() => {
    function handleOnline() {
      setNetworkOnline(true)
    }

    function handleOffline() {
      setNetworkOnline(false)
    }

    window.addEventListener('online', handleOnline)
    window.addEventListener('offline', handleOffline)
    return () => {
      window.removeEventListener('online', handleOnline)
      window.removeEventListener('offline', handleOffline)
    }
  }, [])

  useEffect(() => {
    writeCache('offline-mode', isOfflineMode)
  }, [isOfflineMode])

  useEffect(() => {
    async function loadAll() {
      setBootstrapLoading(true)
      try {
        const states = offlineActive
          ? readCache('states:Nigeria', [])
          : await fetchStates('Nigeria')
        if (!offlineActive) {
          writeCache('states:Nigeria', states)
        }
        setStateOptions(states)
        const initialState = states.includes('Lagos') ? 'Lagos' : states[0] || ''
        setState(initialState)
      } catch (error) {
        console.error('Failed to load hospitals for state list:', error)
        const cachedStates = readCache('states:Nigeria', [])
        setStateOptions(cachedStates)
        setState((current) => current || (cachedStates.includes('Lagos') ? 'Lagos' : cachedStates[0] || ''))
      } finally {
        setBootstrapLoading(false)
      }
    }

    loadAll()
  }, [offlineActive])

  useEffect(() => {
    if (!state) {
      setLgaOptions([])
      setLga('')
      setHospitalOptions([])
      setHospitals([])
      setSelectedHospitalId('')
      return
    }
    let cancelled = false

    async function loadLgas() {
      setBootstrapLoading(true)
      try {
        const cacheKey = `lgas:Nigeria:${state}`
        const lgas = offlineActive
          ? readCache(cacheKey, [])
          : await fetchLgas({ country: 'Nigeria', state })
        if (!offlineActive) {
          writeCache(cacheKey, lgas)
        }
        if (cancelled) return
        setLgaOptions(lgas)
        const initialLga = lgas.includes('Ikeja') ? 'Ikeja' : lgas[0] || ''
        setLga((currentLga) => (lgas.includes(currentLga) ? currentLga : initialLga))
        setSelectedHospitalId('')
      } catch (error) {
        console.error('Failed to load LGAs:', error)
        if (!cancelled) {
          const cachedLgas = readCache(`lgas:Nigeria:${state}`, [])
          setLgaOptions(cachedLgas)
          setLga((current) => (cachedLgas.includes(current) ? current : cachedLgas[0] || ''))
        }
      } finally {
        if (!cancelled) {
          setBootstrapLoading(false)
        }
      }
    }

    loadLgas()

    return () => {
      cancelled = true
    }
  }, [state, offlineActive])

  useEffect(() => {
    if (!state || !lga) {
      setHospitalOptions([])
      setHospitals([])
      setSelectedHospitalId('')
      return
    }
    let cancelled = false

    async function loadHospitalsForLga() {
      setBootstrapLoading(true)
      try {
        const cacheKey = `hospitals:Nigeria:${state}:${lga}`
        const filtered = offlineActive
          ? readCache(cacheKey, [])
          : await fetchHospitals({ country: 'Nigeria', state, lga })
        if (!offlineActive) {
          writeCache(cacheKey, filtered)
        }
        if (cancelled) return
        setHospitalOptions(filtered)
        setSelectedHospitalId((currentId) => (
          filtered.some((hospital) => String(hospital.id) === String(currentId)) ? currentId : ''
        ))
      } catch (error) {
        console.error('Failed to load hospitals for dropdown:', error)
        if (!cancelled) {
          setHospitalOptions(readCache(`hospitals:Nigeria:${state}:${lga}`, []))
          setSelectedHospitalId('')
        }
      } finally {
        if (!cancelled) {
          setBootstrapLoading(false)
        }
      }
    }

    loadHospitalsForLga()

    return () => {
      cancelled = true
    }
  }, [state, lga, offlineActive])

  useEffect(() => {
    if (!state || !lga) {
      setPlanning(null)
      setPlanningError('')
      setPlanningLoading(false)
      return
    }

    let cancelled = false

    async function loadPlanning() {
      setPlanningLoading(true)
      setPlanningError('')
      try {
        const cacheKey = `planning:Nigeria:${state}:${lga}`
        const data = offlineActive
          ? readCache(cacheKey, null)
          : await fetchPlanningSnapshot({ country: 'Nigeria', state, lga })
        if (!offlineActive && data) {
          writeCache(cacheKey, data)
        }
        if (!cancelled) {
          setPlanning(data)
          if (!data && offlineActive) {
            setPlanningError('Offline mode needs a previously loaded planning snapshot for this location.')
          }
        }
      } catch (error) {
        console.error('Failed to load planning snapshot:', error)
        if (!cancelled) {
          const cachedPlanning = readCache(`planning:Nigeria:${state}:${lga}`, null)
          setPlanning(cachedPlanning)
          setPlanningError(
            cachedPlanning
              ? 'Showing cached planning snapshot because live analytics are unavailable.'
              : 'Planning analytics could not be loaded right now.'
          )
        }
      } finally {
        if (!cancelled) {
          setPlanningLoading(false)
        }
      }
    }

    loadPlanning()

    return () => {
      cancelled = true
    }
  }, [state, lga, offlineActive])

  async function runSearch() {
    setSearchLoading(true)
    try {
      const cacheKey = `hospitals:Nigeria:${state}:${lga}`
      const data = offlineActive
        ? readCache(cacheKey, [])
        : await fetchHospitals({ country: 'Nigeria', state, lga, q: query })
      if (!offlineActive) {
        writeCache(cacheKey, data)
      }
      const filtered = selectedHospitalId
        ? data.filter((hospital) => String(hospital.id) === String(selectedHospitalId))
        : data
      const normalizedQuery = query.trim().toLowerCase()
      const queryFiltered = normalizedQuery
        ? filtered.filter((hospital) =>
            [hospital.name, hospital.specialties, hospital.services, hospital.capabilities]
              .filter(Boolean)
              .join(' ')
              .toLowerCase()
              .includes(normalizedQuery)
          )
        : filtered
      setHospitals(queryFiltered)
    } catch (error) {
      console.error('Failed to search hospitals:', error)
      setHospitals([])
    } finally {
      setSearchLoading(false)
    }
  }

  if (isPayloadPage) {
    return <PaymentPayload />
  }

  if (isCallbackPage) {
    return <PaymentCallback />
  }

  if (isConsultationPage) {
    return <ConsultationPage />
  }

  return (
    <div className="page-shell">
      <header className="hero">
        <div>
          <h1>CareMesh</h1>
          <p>Nigeria healthcare navigation, booking, payments, and hosted AI assistance.</p>
        </div>
        <div className="hero-badge">Built for Enyata-Interswitch Buildathon</div>
        <div className="hero-controls">
        <div className="mode-toggle">
          <label>
            <input type="checkbox" checked={isOfflineMode} onChange={(e) => setIsOfflineMode(e.target.checked)} />
            Connection Mode ({offlineActive ? 'Offline' : 'Online'})
          </label>
        </div>
        </div>
      </header>

      {offlineActive && (
        <section className="card offline-banner">
          <strong>Offline mode is active.</strong> Hospital search and planning use cached data. Chat uses offline demo replies, and live booking or payment actions are disabled.
        </section>
      )}

      <section className="search-panel card">
        <div className="search-grid">
          <select value={state} onChange={(e) => setState(e.target.value)}>
            <option value="">Select State</option>
            {stateOptions.map((s) => (
              <option key={s} value={s}>{s}</option>
            ))}
          </select>
          <select value={lga} onChange={(e) => setLga(e.target.value)}>
            <option value="">Select Local Government Area</option>
            {lgaOptions.map((l) => (
              <option key={l} value={l}>{l}</option>
            ))}
          </select>
          <select value={selectedHospitalId} onChange={(e) => setSelectedHospitalId(e.target.value)}>
            <option value="">Select Hospital (Optional)</option>
            {hospitalOptions.map((hospital) => (
              <option key={hospital.id} value={hospital.id}>{hospital.name}</option>
            ))}
          </select>
          <button onClick={runSearch} disabled={bootstrapLoading || searchLoading || !state || !lga}>
            {searchLoading ? 'Searching...' : bootstrapLoading ? 'Loading hospitals...' : 'Search hospitals'}
          </button>
        </div>
      </section>

      <HealthcarePlanningPanel
        hospitals={hospitalOptions}
        highlightedHospitalId={selectedHospital?.id}
        onBook={setSelectedHospital}
        planning={planning}
        planningLoading={planningLoading}
        planningError={planningError}
      />

      <section className="layout-grid">
        <div>
          <h2>Hospitals</h2>
          <div className="stack">
            {hospitals.map((hospital) => (
              <HospitalCard key={hospital.id} hospital={hospital} onBook={setSelectedHospital} />
            ))}
            {!hospitals.length && !searchLoading && <p className="muted">No hospitals found.</p>}
          </div>
        </div>

        <ChatBox state={state} lga={lga} hospitals={hospitalOptions} isOfflineMode={offlineActive} />
      </section>

      {selectedHospital && <BookingModal hospital={selectedHospital} onClose={() => setSelectedHospital(null)} isTestMode={false} isOfflineMode={offlineActive} />}
    </div>
  )
}
