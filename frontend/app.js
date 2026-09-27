const departmentData = [
  { department: 'Cardiology', visits: 18, occupancy: '82%', status: 'Healthy', tone: 'healthy' },
  { department: 'Pediatrics', visits: 12, occupancy: '65%', status: 'Stable', tone: 'primary' },
  { department: 'Emergency', visits: 24, occupancy: '94%', status: 'Busy', tone: 'busy' },
];

const patientData = [
  { name: 'Aisha Rahman', doctor: 'Dr. Patel', lastVisit: '2026-09-26', status: 'Active', tone: 'healthy' },
  { name: 'Daniel Brooks', doctor: 'Dr. Singh', lastVisit: '2026-09-25', status: 'Follow-up', tone: 'warning' },
  { name: 'Noor Hassan', doctor: 'Dr. Carter', lastVisit: '2026-09-24', status: 'Critical', tone: 'busy' },
];

const appointmentData = [
  { patient: 'Leah Gomez', doctor: 'Dr. Patel', time: '09:30 AM', status: 'Confirmed', tone: 'healthy' },
  { patient: 'Sam Ali', doctor: 'Dr. Singh', time: '11:00 AM', status: 'Pending', tone: 'warning' },
  { patient: 'Nadia Saleh', doctor: 'Dr. Carter', time: '01:15 PM', status: 'Checked in', tone: 'primary' },
];

const stats = [
  { label: 'Patients today', value: 142, meta: '+12% vs yesterday' },
  { label: 'Appointments', value: 38, meta: '6 pending review' },
  { label: 'Bed occupancy', value: '86%', meta: '2 beds available' },
  { label: 'Lab results', value: 26, meta: '8 urgent' },
];

const statsGrid = document.getElementById('statsGrid');
const deptTable = document.getElementById('deptTable');
const patientTable = document.getElementById('patientTable');
const appointmentTable = document.getElementById('appointmentTable');

function renderStatus(status, tone) {
  const labelMap = {
    Healthy: 'healthy',
    Stable: 'primary',
    Busy: 'busy',
    Active: 'healthy',
    'Follow-up': 'warning',
    Critical: 'busy',
    Confirmed: 'healthy',
    Pending: 'warning',
    'Checked in': 'primary',
  };

  const safeTone = labelMap[status] || tone || 'primary';
  return `<span class="status-pill status-${safeTone}">${status}</span>`;
}

function renderStats() {
  statsGrid.innerHTML = stats
    .map(
      (stat) => `
        <article class="stat-card">
          <div class="stat-label">${stat.label}</div>
          <div class="stat-value">${stat.value}</div>
          <div class="stat-meta">${stat.meta}</div>
        </article>
      `
    )
    .join('');
}

function renderDepartments() {
  deptTable.innerHTML = departmentData
    .map(
      (row) => `
        <tr>
          <td>${row.department}</td>
          <td>${row.visits}</td>
          <td>${row.occupancy}</td>
          <td>${renderStatus(row.status, row.tone)}</td>
        </tr>
      `
    )
    .join('');
}

function renderPatients() {
  patientTable.innerHTML = patientData
    .map(
      (row) => `
        <tr>
          <td>${row.name}</td>
          <td>${row.doctor}</td>
          <td>${row.lastVisit}</td>
          <td>${renderStatus(row.status, row.tone)}</td>
        </tr>
      `
    )
    .join('');
}

function renderAppointments() {
  appointmentTable.innerHTML = appointmentData
    .map(
      (row) => `
        <tr>
          <td>${row.patient}</td>
          <td>${row.doctor}</td>
          <td>${row.time}</td>
          <td>${renderStatus(row.status, row.tone)}</td>
        </tr>
      `
    )
    .join('');
}

renderStats();
renderDepartments();
renderPatients();
renderAppointments();
