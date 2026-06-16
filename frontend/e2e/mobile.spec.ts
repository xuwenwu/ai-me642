import { expect, test } from '@playwright/test';
import { login, seedPilotCourse } from './helpers';

test('mobile student and instructor core pages render without blocking controls', async ({ page, request, baseURL }) => {
  const seed = await seedPilotCourse(request, baseURL!);

  await login(page, seed.student.email, seed.student.password);
  await expect(page).toHaveURL(/\/dashboard$/);
  await expect(page.getByRole('heading', { name: 'Dashboard' })).toBeVisible();
  await expect(page.getByText(seed.assignment.title)).toBeVisible();
  await page.getByRole('link', { name: 'Submission', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Submission Workflow' })).toBeVisible();
  await expect(page.getByRole('button', { name: 'Create submission' })).toBeDisabled();

  await page.getByRole('button', { name: 'Logout' }).click();
  await login(page, seed.instructor.email, seed.instructor.password);
  await expect(page).toHaveURL(/\/instructor$/);
  await expect(page.getByRole('heading', { name: 'Instructor Overview' })).toBeVisible();
  await page.getByRole('link', { name: 'Course setup' }).click();
  await expect(page.getByRole('heading', { name: 'Course Setup' })).toBeVisible();
  await expect(page.getByRole('heading', { name: 'AI Policy' })).toBeVisible();
  await expect(page.getByRole('button', { name: 'Test course assistant' })).toBeVisible();
});
