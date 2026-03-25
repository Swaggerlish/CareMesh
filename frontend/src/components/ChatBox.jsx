import { useState } from 'react'
import { sendChat } from '../api'

function buildOfflineReply(message, state, lga, hospitals) {
  const normalized = message.toLowerCase()
  const hospitalNames = hospitals.slice(0, 3).map((hospital) => hospital.name)

  if (normalized.includes('nearest') || normalized.includes('hospital')) {
    if (hospitalNames.length) {
      return `Offline demo mode: for ${lga || 'this area'}, you can start with ${hospitalNames.join(', ')}. Switch back online for live AI recommendations and booking.`
    }
    return `Offline demo mode: I do not have cached hospitals for ${lga || state || 'this location'} yet. Switch online once to load and cache them.`
  }

  if (normalized.includes('emergency') || normalized.includes('bleeding') || normalized.includes('breathing')) {
    return 'Offline demo mode: for emergencies like severe bleeding, chest pain, seizures, stroke signs, or trouble breathing, seek urgent medical care immediately.'
  }

  return `Offline demo mode: I can still guide a demo for ${lga || state || 'your selected location'}, but live AI responses need online mode. Try asking for nearby hospitals or urgent care guidance.`
}

export default function ChatBox({ state, lga, hospitals = [], isOfflineMode = false }) {
  const [messages, setMessages] = useState([
    { role: 'assistant', content: 'Hi, I am CareMesh AI. Ask about hospitals, bookings, or simple symptom guidance.' },
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [assistantStatus, setAssistantStatus] = useState('Hosted Hugging Face model')

  async function submit(e) {
    e.preventDefault()
    if (!input.trim()) return
    const userMessage = input.trim()
    setMessages((prev) => [...prev, { role: 'user', content: userMessage }])
    setInput('')
    setLoading(true)
    try {
      if (isOfflineMode) {
        const offlineReply = buildOfflineReply(userMessage, state, lga, hospitals)
        setAssistantStatus('Offline demo assistant')
        setMessages((prev) => [...prev, { role: 'assistant', content: offlineReply }])
        return
      }
      const response = await sendChat(userMessage, state || undefined, lga || undefined)
      if (response.model === 'fallback-assistant') {
        setAssistantStatus('Selected HF model is not supported by your enabled provider')
      } else if (response.reply.includes('switched to fallback model')) {
        setAssistantStatus(`Using fallback Hugging Face model: ${response.model}`)
      } else {
        setAssistantStatus(`Using model: ${response.model}`)
      }
      setMessages((prev) => [...prev, { role: 'assistant', content: response.reply }])
    } catch {
      setAssistantStatus('AI assistant is unavailable right now')
      setMessages((prev) => [...prev, { role: 'assistant', content: 'AI assistant is unavailable right now.' }])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="card chat-card">
      <div className="card-header">
        <h3>CareMesh AI</h3>
        <span className="badge">{assistantStatus}</span>
      </div>
      <div className="chat-stream">
        {messages.map((msg, index) => (
          <div key={index} className={`bubble ${msg.role}`}>
            {msg.content}
          </div>
        ))}
      </div>
      <form onSubmit={submit} className="chat-form">
        <input value={input} onChange={(e) => setInput(e.target.value)} placeholder={isOfflineMode ? 'Ask for cached hospitals or offline guidance' : 'Ask for nearby hospitals or symptom guidance'} />
        <button type="submit" disabled={loading}>{loading ? 'Sending...' : 'Send'}</button>
      </form>
    </div>
  )
}
