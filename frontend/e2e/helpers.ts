import { APIRequestContext, expect, Page } from '@playwright/test';
import path from 'node:path';

export type E2ESeed = {
  marker: string;
  instructor: { email: string; password: string; token: string };
  student: { email: string; password: string; fullName: string };
  assignment: { id: number; title: string };
};

const instructorCandidates = [
  {
    email: process.env.E2E_INSTRUCTOR_EMAIL || '',
    password: process.env.E2E_INSTRUCTOR_PASSWORD || '',
  },
  { email: 'instructor-docker@example.edu', password: 'temporary-pass-123' },
  { email: 'instructor@example.edu', password: 'password123' },
].filter((item) => item.email && item.password);

export const sampleFile = (name: string) => path.resolve(__dirname, '..', '..', 'sample_data', name);

async function apiLogin(request: APIRequestContext, baseURL: string, email: string, password: string) {
  const response = await request.post(`${baseURL}/api/auth/login`, {
    data: { email, password },
  });
  if (!response.ok()) return null;
  return response.json() as Promise<{ access_token: string; user: { email: string; role: string } }>;
}

export async function seedPilotCourse(request: APIRequestContext, baseURL: string): Promise<E2ESeed> {
  let instructor: E2ESeed['instructor'] | null = null;
  for (const candidate of instructorCandidates) {
    const login = await apiLogin(request, baseURL, candidate.email, candidate.password);
    if (login?.access_token) {
      instructor = { ...candidate, token: login.access_token };
      break;
    }
  }
  if (!instructor) {
    throw new Error('No configured E2E instructor account could log in.');
  }

  const marker = `e2e-${Date.now()}`;
  const student = {
    email: `${marker}@example.edu`,
    password: 'e2e-pass-123',
    fullName: `E2E Student ${marker}`,
  };
  const headers = { Authorization: `Bearer ${instructor.token}` };

  const studentResponse = await request.post(`${baseURL}/api/instructor/roster/students`, {
    headers,
    data: {
      full_name: student.fullName,
      email: student.email,
      section: 'E2E Section',
      password: student.password,
      is_active: true,
      must_change_password: false,
    },
  });
  expect(studentResponse.ok()).toBeTruthy();

  const title = `E2E NVE Validation ${marker}`;
  const assignmentResponse = await request.post(`${baseURL}/api/instructor/assignments`, {
    headers,
    data: {
      title,
      description: 'Automated browser smoke assignment for LAMMPS validation.',
      assignment_type: 'lab',
      due_date: '2026-12-15',
      total_points: 100,
      status: 'published',
      validation_profile: 'nve_energy_conservation',
      required_file_types: ['lammps_input', 'lammps_log'],
      optional_file_types: ['readme', 'prompt_log', 'python_analysis', 'ovito_script', 'slurm_script'],
      validation_settings: { energy_drift_warning_threshold: 0.05 },
      interpretation_prompts: [
        'Explain the total-energy drift evidence.',
        'Identify warnings or pressure caveats.',
      ],
    },
  });
  expect(assignmentResponse.ok()).toBeTruthy();
  const assignment = await assignmentResponse.json();

  return {
    marker,
    instructor,
    student,
    assignment: { id: assignment.id, title },
  };
}

export async function login(page: Page, email: string, password: string) {
  await page.goto('/login');
  await page.getByLabel('Email').fill(email);
  await page.getByLabel('Password').fill(password);
  await page.getByRole('button', { name: 'Sign in' }).click();
}

export async function logout(page: Page) {
  await page.getByRole('button', { name: 'Logout' }).click();
  await expect(page.getByRole('heading', { name: 'AI-ME642 Studio' })).toBeVisible();
}

export async function selectOptionContaining(page: Page, testId: string, text: string) {
  const control = page.getByTestId(testId);
  await expect(control).toContainText(text);
  const value = await control.evaluate((select, expected) => {
    const options = Array.from((select as HTMLSelectElement).options);
    const match = options.find((option) => option.textContent?.includes(expected));
    return match?.value || '';
  }, text);
  expect(value, `No ${testId} option contained ${text}`).not.toBe('');
  await page.getByTestId(testId).selectOption(value);
}
