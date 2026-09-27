async function request(path, options = {}) {
  const response = await fetch(`/api${path}`, {
    ...options,
    headers: {
      ...(options.body ? { 'Content-Type': 'application/json' } : {}),
      ...options.headers,
    },
  });
  const result = await response.json();
  if (!response.ok) {
    throw new Error(result.error?.message || `Request failed (${response.status})`);
  }
  return result;
}

export const api = {
  health: () => request('/health'),
  login: (credentials) => request('/auth/login', { method: 'POST', body: JSON.stringify(credentials) }),
  listPatients: () => request('/patients'),
  createPatient: (patient) => request('/patients', { method: 'POST', body: JSON.stringify(patient) }),
  listAppointments: () => request('/appointments'),
  createAppointment: (appointment) => request('/appointments', { method: 'POST', body: JSON.stringify(appointment) }),
  getMedicalRecords: (patientId) => request(`/medical-records/${encodeURIComponent(patientId)}`),
  listBilling: () => request('/billing'),
  listReports: () => request('/reports'),
};