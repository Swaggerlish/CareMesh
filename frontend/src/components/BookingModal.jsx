import { useState } from 'react'
import { createAppointment } from '../api'

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

  const onChange = (key, value) => setForm((prev) => ({ ...prev, [key]: value }))

  async function onSubmit(e) {
    e.preventDefault()
    if (isOfflineMode) {
      setStatus('Offline demo mode: booking is view-only right now. Switch back online to create an appointment and continue to payment.')
      return
    }
    setStatus('Creating appointment...')
    try {
      const payment = await createAppointment({ ...form, hospital_id: hospital.id })
      setStatus('Appointment created. Opening payment...')
      startPayment(payment)
    } catch (error) {
      setStatus('Could not create appointment.')
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
          <input placeholder="Full name" value={form.patient_name} onChange={(e) => onChange('patient_name', e.target.value)} required />
          <input placeholder="Email" type="email" value={form.patient_email} onChange={(e) => onChange('patient_email', e.target.value)} required />
          <input placeholder="Phone number" value={form.patient_phone} onChange={(e) => onChange('patient_phone', e.target.value)} required />
          <input placeholder="Appointment date and time" type="datetime-local" value={form.scheduled_for} onChange={(e) => onChange('scheduled_for', e.target.value)} required />
          <textarea placeholder="Reason for visit" value={form.reason} onChange={(e) => onChange('reason', e.target.value)} required />
          <button type="submit">{isOfflineMode ? 'Offline demo only' : 'Create booking and pay'}</button>
        </form>
        {status && <p className="muted">{status}</p>}
      </div>
    </div>
  )
}
