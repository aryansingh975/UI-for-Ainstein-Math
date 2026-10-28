// Ainstein API Client for FastAPI Backend
const API_BASE = '';

export const AVAILABLE_CHAPTERS = [
  {
    id: 'proportional-reasoning',
    title: 'Proportional Reasoning',
    grade: 8,
    description: 'Grade 8 · 14 problems',
    problems: [
      { id: 'g08-hegp107-ex001', title: 'Proportional Ratios: 3:4 and 72:96', uuid: 'g08-hegp107-ex001' },
      { id: 'g08-hegp107-ex002-lemonade', title: 'Lemonade Stand Sugar Ratios', uuid: 'g08-hegp107-ex002' },
      { id: 'g08-hegp107-ex002-ratio', title: 'Proportional Ratios: 6:8 and 72:96', uuid: 'g08-hegp107-ex002-ratio' },
      { id: 'g08-hegp107-ex003', title: 'Compound Wall Strength', uuid: 'g08-hegp107-ex003' },
      { id: 'g08-hegp107-ex004', title: 'Teacher-to-Student Ratio Comparison', uuid: 'g08-hegp107-ex004' },
      { id: 'g08-hegp107-ex005', title: 'Blackboard Width-Height Ratio', uuid: 'g08-hegp107-ex005' },
      { id: 'g08-hegp107-ex006', title: 'Age Ratios: Neelima and Her Mother', uuid: 'g08-hegp107-ex006' },
      { id: 'g08-hegp107-ex007', title: 'Ratio Fill-ins: 14:21', uuid: 'g08-hegp107-ex007' },
      { id: 'g08-hegp107-ex008', title: 'Rice for 80 Students', uuid: 'g08-hegp107-ex008' },
      { id: 'g08-hegp107-ex009', title: 'Car Travels 90 km in 150 minutes', uuid: 'g08-hegp107-ex009' },
      { id: 'g08-hegp107-ex010', title: 'Tea Cost Comparison: Himachal vs Meghalaya', uuid: 'g08-hegp107-ex010' },
      { id: 'g08-hegp107-ex011', title: 'Profit Sharing: Prashanti and Bhuvan', uuid: 'g08-hegp107-ex011' },
      { id: 'g08-hegp107-ex012', title: 'Sand and Cement Ratio Adjustment', uuid: 'g08-hegp107-ex012' },
      { id: 'g08-hegp107-p176-q1', title: 'Figure it Out p.176 Q1', uuid: 'g08-hegp107-p176-q1' },
      { id: 'g08-hegp107-p176-q2', title: 'Figure it Out p.176 Q2', uuid: 'g08-hegp107-p176-q2' },
      { id: 'g08-hegp107-p176-q3', title: 'Figure it Out p.176 Q3', uuid: 'g08-hegp107-p176-q3' }
    ]
  },
  {
    id: 'squares-and-cubes',
    title: 'Squares and Cubes',
    grade: 8,
    description: 'Grade 8 · 3 problems',
    problems: [
      { id: 'g08-hegp101-sqrt-324', title: 'Square Root of 324', uuid: 'g08-hegp101-sqrt-324' },
      { id: 'g08-hegp101-cbrt-3375', title: 'Cube Root of 3375', uuid: 'g08-hegp101-cbrt-3375' },
      { id: 'g08-hegp101-ex-p10-q6', title: 'Smallest Number for Perfect Square', uuid: 'g08-hegp101-ex-p10-q6' }
    ]
  },
  {
    id: 'power-play',
    title: 'Power Play',
    grade: 8,
    description: 'Grade 8 · 3 problems',
    problems: [
      { id: 'g08-hegp102-ex-p11-q1', title: 'Simplify 2⁻⁴ × 2⁷', uuid: 'g08-hegp102-ex-p11-q1' },
      { id: 'g08-hegp102-ex-p26-q5v', title: 'Simplify m⁵n¹²/(mn)⁹', uuid: 'g08-hegp102-ex-p26-q5v' },
      { id: 'g08-hegp102-ex-p26-q1', title: 'Units Digit of 2²²⁴ ÷ 4³²', uuid: 'g08-hegp102-ex-p26-q1' }
    ]
  },
  {
    id: 'inverse-proportion',
    title: 'Inverse Proportion',
    grade: 8,
    description: 'Grade 8 · 3 problems',
    problems: [
      { id: 'g08-hegp203-ex003', title: 'Workers and Road Laying', uuid: 'g08-hegp203-ex003' },
      { id: 'g08-hegp203-ex005', title: 'School Provisions Problem', uuid: 'g08-hegp203-ex005' },
      { id: 'g08-hegp203-ex006', title: 'Ram and Shyam Working Together', uuid: 'g08-hegp203-ex006' }
    ]
  },
  {
    id: 'percentages',
    title: 'Percentages',
    grade: 8,
    description: 'Grade 8 · 3 problems',
    problems: [
      { id: 'g08-hegp201-ex-p19-q1', title: 'Geometry Box Profit and Loss', uuid: 'g08-hegp201-ex-p19-q1' },
      { id: 'g08-hegp201-ex010', title: 'TV Depreciation Problem', uuid: 'g08-hegp201-ex010' },
      { id: 'g08-hegp201-ex-p22-q1', title: 'Simple vs Compound Interest', uuid: 'g08-hegp201-ex-p22-q1' }
    ]
  },
  {
    id: 'algebra-play',
    title: 'Algebra Play',
    grade: 8,
    description: 'Grade 8 · 3 problems',
    problems: [
      { id: 'g08-hegp206-grid-eq', title: 'Grid Intersection Points', uuid: 'g08-hegp206-grid-eq' },
      { id: 'g08-hegp206-age-q7', title: 'Mother and Daughter Age Problem', uuid: 'g08-hegp206-age-q7' },
      { id: 'g08-hegp206-heads-legs', title: 'Horses and Hens Problem', uuid: 'g08-hegp206-heads-legs' }
    ]
  },
  {
    id: 'linear-equation',
    title: 'Linear Equation',
    grade: 10,
    description: 'Grade 10 · Latest problem',
    problems: [
      { id: 'g10-quad-ex001', title: 'Quadratic Equation: x² - 5x + 6 = 0', uuid: 'g10-quad-ex001' }
    ]
  }
];

export async function fetchAllProblems() {
  const res = await fetch(`${API_BASE}/api/v1/problems`);
  if (!res.ok) throw new Error('Failed to fetch problems catalogue');
  return res.json();
}

export async function startTutorSession(problemId) {
  const res = await fetch(`${API_BASE}/api/v1/sessions/start`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ problem_id: problemId })
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Could not start problem session');
  }
  return res.json();
}

export async function submitTutorStep(sessionId, studentInput) {
  const res = await fetch(`${API_BASE}/api/v1/sessions/${sessionId}/step`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ student_input: studentInput })
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Step evaluation failed.');
  }
  return res.json();
}

export async function resetTutorSession(sessionId) {
  const res = await fetch(`${API_BASE}/api/v1/sessions/${sessionId}/reset`, {
    method: 'POST'
  });
  if (!res.ok) throw new Error('Failed to reset session');
  return res.json();
}

export async function classifyJevMethod(problemId, studentWork) {
  const res = await fetch(`${API_BASE}/api/jev/method`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ problemId, studentWork })
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.message || 'Jev could not classify this response.');
  }
  return res.json();
}

