import { useEffect, useState } from 'react'
import { verifyPayment } from '../api'

export default function PaymentCallback() {
  const [message, setMessage] = useState('Verifying payment...')

  useEffect(() => {
    const params = new URLSearchParams(window.location.search)
    const txnRef = params.get('txn_ref')
    if (!txnRef) {
      setMessage('Missing transaction reference.')
      return
    }
    verifyPayment(txnRef)
      .then((data) => {
        if (data.status === 'SUCCESS') {
          setMessage('Payment confirmed. Appointment booked. Connecting to doctor...')
          // Redirect to consultation after a short delay
          setTimeout(() => {
            window.location.href = `/consultation?appointment_id=${data.appointment_id || ''}`
          }, 2000)
        } else {
          const provider = data.provider_response?.message || JSON.stringify(data.provider_response || {})
          setMessage(`Payment not confirmed (status=${data.status}). Provider reply: ${provider}`)
        }
      })
      .catch((error) => {
        console.error('Verify payment failed', error)
        setMessage('Verification failed (network or provider). Check console and Interswitch logs.')
      })
  }, [])

  return (
    <div className="card callback-card">
      <h2>Payment status</h2>
      <p>{message}</p>
      <a href="/">Return to home</a>
    </div>
  )
}
