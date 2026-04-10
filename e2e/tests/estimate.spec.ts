import { test, expect } from "@playwright/test"

test.describe("見積もり生成フロー", () => {
  test("LP → 見積もり入力ページに遷移できる", async ({ page }) => {
    await page.goto("/")
    await expect(page).toHaveTitle(/EstiMate/)
    await page.getByRole("link", { name: /無料で見積もりを作る/ }).first().click()
    await expect(page).toHaveURL(/\/auth|\/estimate\/new/)
  })

  test("未ログインで /estimate/new にアクセスすると /auth にリダイレクト", async ({ page }) => {
    await page.goto("/estimate/new")
    await expect(page).toHaveURL(/auth/)
  })
})
