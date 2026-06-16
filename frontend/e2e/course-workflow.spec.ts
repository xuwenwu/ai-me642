import { expect, test } from '@playwright/test';
import { login, logout, sampleFile, seedPilotCourse, selectOptionContaining } from './helpers';

test.describe.configure({ mode: 'serial' });

test('student submits a validated LAMMPS package and instructor grades it', async ({ page, request, baseURL }) => {
  const seed = await seedPilotCourse(request, baseURL!);
  const submissionTitle = `${seed.assignment.title} package`;

  await login(page, seed.student.email, seed.student.password);
  await expect(page).toHaveURL(/\/dashboard$/);
  await expect(page.getByRole('heading', { name: 'Dashboard' })).toBeVisible();
  await expect(page.getByText(seed.assignment.title)).toBeVisible();
  await expect(page.getByText('Create a submission package and upload the required evidence.').first()).toBeVisible();

  await page.getByRole('link', { name: 'Prompt Logs' }).click();
  await page.getByLabel('Template').selectOption({ label: 'LAMMPS debugging check' });
  await page.getByLabel('Assignment').selectOption({ label: seed.assignment.title });
  await page.getByLabel('Prompt text').fill('Help inspect this E2E NVE LAMMPS log for energy drift and warnings.');
  await page.getByLabel('AI output summary').fill('Suggested checking log health, thermo trends, warnings, and energy drift.');
  await page.getByLabel('Accepted parts').fill('Used validation checklist structure.');
  await page.getByLabel('Rejected parts').fill('Rejected any unsupported scientific conclusion.');
  await page.getByLabel('Manual edits').fill('Adapted advice to the uploaded sample files.');
  await page.getByLabel('Validation performed').fill('Ran platform validation and reviewed plots.');
  await page.getByLabel('Remaining concerns').fill('Pressure interpretation still requires context.');
  await page.getByRole('button', { name: 'Save prompt log' }).click();
  await expect(page.getByText('Prompt log saved')).toBeVisible();

  await page.getByRole('link', { name: 'Submission' }).click();
  await page.getByLabel('Assignment').selectOption({ label: seed.assignment.title });
  await expect(page.getByText('nve_energy_conservation')).toBeVisible();
  await page.getByRole('button', { name: 'Create submission' }).click();
  await expect(page.getByRole('status').filter({ hasText: /Created submission #\d+/ })).toBeVisible();
  await expect(page.getByTestId('student-submission-select')).toContainText(submissionTitle);

  const uploads = [
    ['lammps_input', 'sample_input.in'],
    ['lammps_log', 'sample_good_nve.log'],
    ['slurm_script', 'sample_slurm.sbatch'],
    ['python_analysis', 'sample_analysis.py'],
    ['ovito_script', 'sample_ovito.py'],
    ['lammps_log', 'sample_warning.log'],
  ] as const;
  for (const [fileType, filename] of uploads) {
    await page.getByLabel('File type').selectOption(fileType);
    await page.getByTestId('artifact-upload-input').setInputFiles(sampleFile(filename));
    await page.getByRole('button', { name: 'Upload' }).click();
    await expect(page.getByText(filename)).toBeVisible();
  }

  await page.getByRole('button', { name: 'Run validation' }).click();
  await expect(page.locator('.success').filter({ hasText: 'Validation completed with status: warning' })).toBeVisible();
  await expect(page.getByRole('heading', { name: 'Thermo Plots' })).toBeVisible();
  await expect(page.getByRole('heading', { name: 'Interpretation Cues' })).toBeVisible();
  await expect(page.getByText('Energy conservation').first()).toBeVisible();
  await expect(page.getByText('AI disclosure').first()).toBeVisible();

  await page.locator('section').filter({ hasText: 'Student Interpretation' }).locator('textarea').fill(
    'The E2E sample has acceptable energy-drift evidence, but warnings and pressure behavior need instructor review before strong scientific claims.',
  );
  await page.getByRole('button', { name: 'Save interpretation' }).click();
  await expect(page.getByText('Interpretation saved')).toBeVisible();
  await page.getByRole('button', { name: 'Submit assignment' }).click();
  await expect(page.getByText('Assignment submitted')).toBeVisible();
  await expect(page.getByRole('button', { name: 'Submitted' })).toBeDisabled();

  await logout(page);
  await login(page, seed.instructor.email, seed.instructor.password);
  await expect(page).toHaveURL(/\/instructor$/);
  await expect(page.getByRole('heading', { name: 'Instructor Overview' })).toBeVisible();

  await page.getByRole('link', { name: 'Open review queue' }).click();
  await expect(page.getByRole('heading', { name: 'Instructor Review' })).toBeVisible();
  await selectOptionContaining(page, 'instructor-submission-select', submissionTitle);
  await expect(page.locator('section').filter({ hasText: 'Submission Evidence' }).getByText(submissionTitle, { exact: true })).toBeVisible();
  await expect(page.getByRole('heading', { name: 'Thermo Plots' })).toBeVisible();

  const scoreInputs = page.locator('section').filter({ hasText: 'Rubric Grade' }).getByRole('spinbutton');
  const scores = ['19', '19', '24', '19', '14'];
  for (let index = 0; index < scores.length; index += 1) {
    await scoreInputs.nth(index).fill(scores[index]);
  }
  await page.getByLabel('Late penalty').fill('0');
  await page.getByLabel('Overall feedback').fill('E2E grade saved after reviewing validation plots and interpretation.');
  await page.getByRole('button', { name: 'Save grade' }).click();
  await expect(page.getByText('Grade saved. Final score')).toBeVisible();

  await page.getByRole('link', { name: 'Gradebook dashboard' }).click();
  await expect(page.getByRole('heading', { name: 'Gradebook' })).toBeVisible();
  await expect(page.getByText(seed.student.email)).toBeVisible();
  const assignmentOperations = page.locator('section').filter({ hasText: 'Assignment Operations' });
  const gradedAssignmentRow = assignmentOperations.getByRole('row').filter({ hasText: seed.assignment.title });
  await expect(gradedAssignmentRow).toBeVisible();
  await expect(gradedAssignmentRow).toContainText('1 warning, 0 failed');
  await expect(gradedAssignmentRow).toContainText('95.0');
});
