import { test, expect } from '@playwright/test';

// Adapt selectors and routes to the audited DAZY application.
// Use a dedicated test account, never a production user's session.
test.describe('DAZY canonical identity', () => {
  test('shows profile display name from authenticated profile, not a hard-coded demo name', async ({ page }) => {
    await page.goto('/');
    await expect(page.getByText('Tarik', { exact: false }).first()).toBeVisible();
    await expect(page.getByText('John Doe', { exact: false })).toHaveCount(0);
    await expect(page.getByText('Alex', { exact: true })).toHaveCount(0);
  });

  test('profile name persists after reload', async ({ page }) => {
    await page.goto('/');
    await expect(page.getByText('Tarik', { exact: false }).first()).toBeVisible();
    await page.reload();
    await expect(page.getByText('Tarik', { exact: false }).first()).toBeVisible();
  });
});
