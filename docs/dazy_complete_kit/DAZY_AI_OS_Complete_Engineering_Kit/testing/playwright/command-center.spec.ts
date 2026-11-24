import { test, expect } from '@playwright/test';

// Replace accessible names and routes with the real audited DAZY UI.
test('Command Center exposes key operating areas and truthful states', async ({ page }) => {
  await page.goto('/');
  await expect(page.getByRole('heading', { name: /command center/i })).toBeVisible();
  await expect(page.getByText(/repo radar/i).first()).toBeVisible();
  await expect(page.getByText(/workers/i).first()).toBeVisible();
  await expect(page.getByText(/integrations/i).first()).toBeVisible();

  // Any unconfigured demo/test provider must not be represented as connected.
  await expect(page.getByText(/demo data/i)).toHaveCount(0); // remove/change if explicit demo mode is enabled
});
