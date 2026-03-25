import { useEffect, useMemo, useState } from 'react'
import { fetchAppointment } from '../api'

const urgencyOptions = ['Routine', 'Priority', 'Urgent', 'Critical']
const doctorCountOptions = ['1 doctor', '2 doctors', '3 doctors', '4+ doctors']
const durationOptions = ['30 minutes', '45 minutes', '1 hour', '2 hours', 'Half day']

function splitOptions(value, fallback = []) {
  const options = value
    ?.split(',')
    .map((item) => item.trim())
    .filter(Boolean)

  return options?.length ? options : fallback
}

export default function ConsultationPage() {
  const [appointment, setAppointment] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [submitState, setSubmitState] = useState('')

  const appointmentId = useMemo(() => {
    const params = new URLSearchParams(window.location.search)
    return params.get('appointment_id')
  }, [])

  const [form, setForm] = useState({
    facilityName: '',
    region: '',
    specialty: '',
    urgency: 'Priority',
    doctorCount: '1 doctor',
    duration: '45 minutes',
    details: '',
    contactName: '',
    email: '',
  })

  useEffect(() => {
    if (!appointmentId) {
      setError('Missing appointment id.')
      setLoading(false)
      return
    }

    async function loadAppointment() {
      try {
        const data = await fetchAppointment(appointmentId)
        setAppointment(data)

        const specialtyOptions = splitOptions(data.hospital?.specialties, ['General Practice'])

        setForm((prev) => ({
          ...prev,
          facilityName: data.hospital?.name || '',
          region: data.hospital?.state || '',
          specialty: specialtyOptions[0] || '',
          details: data.reason || '',
          contactName: data.patient_name || '',
          email: data.patient_email || '',
        }))
      } catch (loadError) {
        console.error('Failed to load appointment', loadError)
        setError('Could not load the consultation details.')
      } finally {
        setLoading(false)
      }
    }

    loadAppointment()
  }, [appointmentId])

  const specialtyOptions = useMemo(
    () => splitOptions(appointment?.hospital?.specialties, ['General Practice', 'Emergency Care']),
    [appointment]
  )

  const regionOptions = useMemo(() => {
    const values = [
      appointment?.hospital?.state,
      appointment?.hospital?.lga && `${appointment.hospital.state} - ${appointment.hospital.lga}`,
      appointment?.hospital?.country,
    ].filter(Boolean)

    return Array.from(new Set(values))
  }, [appointment])

  function onChange(key, value) {
    setForm((prev) => ({ ...prev, [key]: value }))
  }

  function onSubmit(event) {
    event.preventDefault()
    setSubmitState('Doctor request submitted. The care team can now continue with patient triage and consultation setup.')
  }

  if (loading) {
    return (
      <div className="consultation-shell">
        <div className="consultation-panel card">
          <h2>Preparing doctor connection...</h2>
          <p className="muted">We’re loading the confirmed appointment and facility details.</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="consultation-shell">
        <div className="consultation-panel card">
          <h2>Consultation setup unavailable</h2>
          <p>{error}</p>
          <a href="/">Return to home</a>
        </div>
      </div>
    )
  }

  return (
    <div className="consultation-shell">
      <section className="consultation-panel card">
        <div className="consultation-header">
          <div>
            <span className="consultation-eyebrow">Patient to Doctor Connection</span>
            <h1>Connect patient to doctor</h1>
            <p>
              Payment is confirmed. Review the facility request and route this patient to the right doctor quickly.
            </p>
          </div>
          <div className="consultation-status">
            <span className="badge">Payment Confirmed</span>
            <span className="badge">Appointment #{appointment?.id}</span>
          </div>
        </div>

        <div className="consultation-layout">
          <form className="consultation-form" onSubmit={onSubmit}>
            <div className="consultation-section">
              <div className="section-title">
                <span className="section-icon">O</span>
                <h2>Facility Information</h2>
              </div>
              <div className="consultation-grid">
                <label>
                  <span>Facility Name</span>
                  <input value={form.facilityName} onChange={(e) => onChange('facilityName', e.target.value)} placeholder="e.g. General Hospital Ikeja" />
                </label>
                <label>
                  <span>Region</span>
                  <select value={form.region} onChange={(e) => onChange('region', e.target.value)}>
                    {regionOptions.map((option) => (
                      <option key={option} value={option}>{option}</option>
                    ))}
                  </select>
                </label>
              </div>
            </div>

            <div className="consultation-section">
              <div className="section-title">
                <span className="section-icon">+</span>
                <h2>Medical Need</h2>
              </div>
              <div className="consultation-grid">
                <label>
                  <span>Specialty Required</span>
                  <select value={form.specialty} onChange={(e) => onChange('specialty', e.target.value)}>
                    {specialtyOptions.map((option) => (
                      <option key={option} value={option}>{option}</option>
                    ))}
                  </select>
                </label>
                <label>
                  <span>Urgency Level</span>
                  <select value={form.urgency} onChange={(e) => onChange('urgency', e.target.value)}>
                    {urgencyOptions.map((option) => (
                      <option key={option} value={option}>{option}</option>
                    ))}
                  </select>
                </label>
                <label>
                  <span>Number of Doctors</span>
                  <select value={form.doctorCount} onChange={(e) => onChange('doctorCount', e.target.value)}>
                    {doctorCountOptions.map((option) => (
                      <option key={option} value={option}>{option}</option>
                    ))}
                  </select>
                </label>
                <label>
                  <span>Duration</span>
                  <select value={form.duration} onChange={(e) => onChange('duration', e.target.value)}>
                    {durationOptions.map((option) => (
                      <option key={option} value={option}>{option}</option>
                    ))}
                  </select>
                </label>
              </div>

              <label className="consultation-field consultation-field-wide">
                <span>Additional Details</span>
                <textarea
                  value={form.details}
                  onChange={(e) => onChange('details', e.target.value)}
                  placeholder="Describe the specific needs, patient volume, available equipment, accommodation for doctors, etc."
                />
              </label>
            </div>

            <div className="consultation-section">
              <div className="section-title">
                <span className="section-icon">=</span>
                <h2>Contact Information</h2>
              </div>
              <div className="consultation-grid">
                <label>
                  <span>Your Name</span>
                  <input value={form.contactName} onChange={(e) => onChange('contactName', e.target.value)} placeholder="Full name" />
                </label>
                <label>
                  <span>Email</span>
                  <input value={form.email} onChange={(e) => onChange('email', e.target.value)} placeholder="your@email.com" type="email" />
                </label>
              </div>
            </div>

            <div className="consultation-actions">
              <a className="secondary-action" href="/">Cancel</a>
              <button type="submit">Submit Request</button>
            </div>

            {submitState && <p className="consultation-success">{submitState}</p>}
          </form>

          <aside className="consultation-summary">
            <h3>Confirmed appointment</h3>
            <dl>
              <div>
                <dt>Patient</dt>
                <dd>{appointment?.patient_name}</dd>
              </div>
              <div>
                <dt>Hospital</dt>
                <dd>{appointment?.hospital?.name}</dd>
              </div>
              <div>
                <dt>Location</dt>
                <dd>{appointment?.hospital?.state}, {appointment?.hospital?.lga}</dd>
              </div>
              <div>
                <dt>Status</dt>
                <dd>{appointment?.status}</dd>
              </div>
              <div>
                <dt>Scheduled For</dt>
                <dd>{new Date(appointment?.scheduled_for).toLocaleString()}</dd>
              </div>
            </dl>

            <div className="summary-note">
              <strong>Reason for visit</strong>
              <p>{appointment?.reason}</p>
            </div>
          </aside>
        </div>
      </section>
    </div>
  )
}
