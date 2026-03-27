import { useState } from 'react'
import { createAppointment } from '../api'

function formatDateTimeLocal(date) {
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  const hours = String(date.getHours()).padStart(2, '0')
  const minutes = String(date.getMinutes()).padStart(2, '0')

  return `${year}-${month}-${day}T${hours}:${minutes}`
}

function validateBookingForm(form) {
  const errors = {}
  const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

  if (!form.patient_name.trim()) {
    errors.patient_name = 'Enter the patient name.'
  }

  if (!form.patient_email.trim()) {
    errors.patient_email = 'Enter an email address.'
  } else if (!emailPattern.test(form.patient_email.trim())) {
    errors.patient_email = 'Enter a valid email address.'
  }

  if (!form.patient_phone.trim()) {
    errors.patient_phone = 'Enter a phone number.'
  }

  if (!form.scheduled_for) {
    errors.scheduled_for = 'Choose an appointment date and time.'
  } else {
    const scheduledDate = new Date(form.scheduled_for)
    if (Number.isNaN(scheduledDate.getTime())) {
      errors.scheduled_for = 'Enter a valid appointment date and time.'
    } else if (scheduledDate <= new Date()) {
      errors.scheduled_for = 'Appointment date and time must be in the future.'
    }
  }

  if (!form.reason.trim()) {
    errors.reason = 'Enter the reason for visit.'
  }

  return errors
}

function mapApiErrors(error) {
  const details = error?.payload?.detail
  if (!Array.isArray(details)) return {}

  return details.reduce((fieldErrors, detail) => {
    const field = detail?.loc?.[detail.loc.length - 1]
    if (field && typeof detail?.msg === 'string') {
      fieldErrors[field] = detail.msg
    }
    return fieldErrors
  }, {})
}

export default function BookingModal({ hospital, onClose, isTestMode = true, isOfflineMode = false }) {
  const [form, setForm] = useState({
    patient_name: '',
    patient_email: '',
    patient_phone: '',
    reason: '',
    scheduled_for: '',
    amount_kobo: 500000,
  })
  const [status, setStatus] = useState('')
  const [errors, setErrors] = useState({})

  const onChange = (key, value) => {
    setForm((prev) => ({ ...prev, [key]: value }))
    setErrors((prev) => {
      if (!prev[key]) return prev
      return { ...prev, [key]: '' }
    })
    setStatus('')
  }

  async function onSubmit(e) {
    e.preventDefault()
    if (isOfflineMode) {
      setStatus('Offline demo mode: booking is view-only right now. Switch back online to create an appointment and continue to payment.')
      return
    }

    const nextErrors = validateBookingForm(form)
    if (Object.keys(nextErrors).length > 0) {
      setErrors(nextErrors)
      setStatus('Please correct the highlighted fields and try again.')
      return
    }

    setErrors({})
    setStatus('Creating appointment...')
    try {
      const payment = await createAppointment({ ...form, hospital_id: hospital.id })
      setStatus('Appointment created. Opening payment...')
      startPayment(payment)
    } catch (error) {
      const apiErrors = mapApiErrors(error)
      if (Object.keys(apiErrors).length > 0) {
        setErrors(apiErrors)
        setStatus('Please correct the highlighted fields and try again.')
        return
      }

      setStatus('Could not create appointment. Please review your details and try again.')
    }
  }

  function startPayment(payment) {
    const merchant_code = payment.merchant_code || 'MX-TEST'
    const pay_item_id = payment.pay_item_id || '101'

    if (isTestMode) {
      setStatus('Test mode: Showing payload simulator.')
      const query = new URLSearchParams({
        txn_ref: payment.txn_ref,
        amount: payment.amount,
        merchant_code,
        pay_item_id,
      }).toString()
      window.location.href = `/payment/payload?${query}`
      return
    }

    if (!window.webpayCheckout) {
      setStatus('Interswitch web checkout not available in this browser. Showing payload test page.')
      const query = new URLSearchParams({
        txn_ref: payment.txn_ref,
        amount: payment.amount,
        merchant_code,
        pay_item_id,
      }).toString()
      window.location.href = `/payment/payload?${query}`
      return
    }

    window.webpayCheckout({
      merchant_code,
      pay_item_id,
      txn_ref: payment.txn_ref,
      site_redirect_url: payment.redirect_url,
      amount: payment.amount,
      currency: 566,
      cust_email: form.patient_email,
      cust_name: form.patient_name,
      mode: payment.mode || 'TEST',
      onComplete: function () {
        window.location.href = `/payment/callback?txn_ref=${payment.txn_ref}`
      },
      onFailure: function (err) {
        console.error('Webpay checkout failed', err)
        setStatus('Payment gateway checkout failed. Please try again or use test credentials.')
      },
    })
  }

  return (
    <div className="modal-backdrop">
      <div className="modal card">
        <div className="card-header">
          <h3>Book at {hospital.name}</h3>
          <button onClick={onClose}>Close</button>
        </div>
        <form onSubmit={onSubmit} className="form-grid">
          <div className="form-field">
            <input
              className={errors.patient_name ? 'input-error' : ''}
              placeholder="Full name"
              value={form.patient_name}
              onChange={(e) => onChange('patient_name', e.target.value)}
              aria-invalid={Boolean(errors.patient_name)}
              required
            />
            {errors.patient_name && <p className="field-error">{errors.patient_name}</p>}
          </div>
          <div className="form-field">
            <input
              className={errors.patient_email ? 'input-error' : ''}
              placeholder="Email"
              type="email"
              value={form.patient_email}
              onChange={(e) => onChange('patient_email', e.target.value)}
              aria-invalid={Boolean(errors.patient_email)}
              required
            />
            {errors.patient_email && <p className="field-error">{errors.patient_email}</p>}
          </div>
          <div className="form-field">
            <input
              className={errors.patient_phone ? 'input-error' : ''}
              placeholder="Phone number"
              value={form.patient_phone}
              onChange={(e) => onChange('patient_phone', e.target.value)}
              aria-invalid={Boolean(errors.patient_phone)}
              required
            />
            {errors.patient_phone && <p className="field-error">{errors.patient_phone}</p>}
          </div>
          <div className="form-field">
            <input
              className={errors.scheduled_for ? 'input-error' : ''}
              placeholder="Appointment date and time"
              type="datetime-local"
              value={form.scheduled_for}
              min={formatDateTimeLocal(new Date())}
              onChange={(e) => onChange('scheduled_for', e.target.value)}
              aria-invalid={Boolean(errors.scheduled_for)}
              required
            />
            {errors.scheduled_for && <p className="field-error">{errors.scheduled_for}</p>}
          </div>
          <div className="form-field">
            <textarea
              className={errors.reason ? 'input-error' : ''}
              placeholder="Reason for visit"
              value={form.reason}
              onChange={(e) => onChange('reason', e.target.value)}
              aria-invalid={Boolean(errors.reason)}
              required
            />
            {errors.reason && <p className="field-error">{errors.reason}</p>}
          </div>
          <button type="submit">{isOfflineMode ? 'Offline demo only' : 'Create booking and pay'}</button>
        </form>
        {status && <p className="muted">{status}</p>}
      </div>
    </div>
  )
}
