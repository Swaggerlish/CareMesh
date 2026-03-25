import { useEffect, useState } from 'react'
import { simulatePayment, verifyPayment } from '../api'

export default function PaymentPayload() {
  const [message, setMessage] = useState('Prepare payment payload...')
  const [txnRef, setTxnRef] = useState('')
  const [payload, setPayload] = useState(null)

  useEffect(() => {
    const params = new URLSearchParams(window.location.search)
    const t = params.get('txn_ref')
    const amount = params.get('amount')
    const merchant_code = params.get('merchant_code')
    const pay_item_id = params.get('pay_item_id')

    if (!t) {
      setMessage('Missing txn_ref query parameter')
      return
    }

    setTxnRef(t)
    setPayload({
      txn_ref: t,
      amount: amount || 'unknown',
      merchant_code: merchant_code || 'default',
      pay_item_id: pay_item_id || 'default',
    })
  }, [])

  const submitResult = async (result) => {
    setMessage(`Simulating ${result}...`)
    try {
      const data = await simulatePayment(txnRef, result)
      setMessage(`Simulation complete: ${data.status}. Now verifying...`)
      const verified = await verifyPayment(txnRef)
      setMessage(`Final status: ${verified.status}. Appointment: ${verified.appointment_status}`)
    } catch (error) {
      console.error('Simulation failed', error)
      setMessage('Simulation/verification failed. Check console for error details.')
    }
  }

  return (
    <div className="page-shell">
      <header className="hero">
        <h1>Interswitch test payload checker</h1>
        <p>Use this page to verify the details and simulate a payment result.</p>
      </header>
      {payload ? (
        <div className="card">
          <h2>Payload</h2>
          <pre>{JSON.stringify(payload, null, 2)}</pre>
          <div style={{ display: 'flex', gap: '12px' }}>
            <button onClick={() => submitResult('success')}>Simulate success</button>
            <button onClick={() => submitResult('failed')}>Simulate failure</button>
          </div>
          <p>{message}</p>
          <a href="/">Home</a>
        </div>
      ) : (
        <div className="card">
          <p>{message}</p>
        </div>
      )}
    </div>
  )
}
