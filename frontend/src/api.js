const rawApiBaseUrl = (import.meta.env.VITE_API_BASE_URL || '').trim();
const normalizedApiBaseUrl = rawApiBaseUrl.replace(/\/+$/, '').replace(/\/api$/, '');

function buildApiUrl(path) {
  const normalizedPath = path.startsWith('/') ? path : `/${path}`;
  return `${normalizedApiBaseUrl}/api${normalizedPath}`;
}

export async function fetchStates(country = 'Nigeria') {
  const query = new URLSearchParams();
  if (country) query.set('country', country);
  const response = await fetch(`${buildApiUrl('/hospitals/states')}?${query.toString()}`);
  if (!response.ok) throw new Error('Failed to load states');
  return response.json();
}

export async function fetchLgas(params = {}) {
  const query = new URLSearchParams();
  if (params.country) query.set('country', params.country);
  if (params.state) query.set('state', params.state);
  const response = await fetch(`${buildApiUrl('/hospitals/lgas')}?${query.toString()}`);
  if (!response.ok) throw new Error('Failed to load LGAs');
  return response.json();
}

export async function fetchHospitals(params = {}) {
  const query = new URLSearchParams();
  if (params.country) query.set('country', params.country);
  if (params.state) query.set('state', params.state);
  if (params.lga) query.set('lga', params.lga);
  if (params.q) query.set('q', params.q);
  const response = await fetch(`${buildApiUrl('/hospitals')}?${query.toString()}`);
  if (!response.ok) throw new Error('Failed to load hospitals');
  return response.json();
}

export async function fetchPlanningSnapshot(params = {}) {
  const query = new URLSearchParams();
  if (params.country) query.set('country', params.country);
  if (params.state) query.set('state', params.state);
  if (params.lga) query.set('lga', params.lga);
  const response = await fetch(`${buildApiUrl('/hospitals/planning/deserts')}?${query.toString()}`);
  if (!response.ok) throw new Error('Failed to load planning snapshot');
  return response.json();
}

export async function createAppointment(payload) {
  const response = await fetch(buildApiUrl('/appointments'), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!response.ok) throw new Error('Failed to create appointment');
  return response.json();
}

export async function verifyPayment(txnRef) {
  const response = await fetch(buildApiUrl(`/payments/verify/${txnRef}`));
  if (!response.ok) throw new Error('Failed to verify payment');
  return response.json();
}

export async function fetchAppointment(appointmentId) {
  const response = await fetch(buildApiUrl(`/appointments/${appointmentId}`));
  if (!response.ok) throw new Error('Failed to load appointment');
  return response.json();
}

export async function simulatePayment(txnRef, result = 'success') {
  const response = await fetch(
    `${buildApiUrl(`/payments/simulate/${txnRef}`)}?result=${encodeURIComponent(result)}`,
    { method: 'POST' }
  );
  if (!response.ok) throw new Error('Failed to simulate payment');
  return response.json();
}

export async function sendChat(message, state, lga) {
  const response = await fetch(buildApiUrl('/chat'), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      message,
      hospital_state: state,
      hospital_lga: lga,
    }),
  });
  if (!response.ok) throw new Error('Chat failed');
  return response.json();
}
