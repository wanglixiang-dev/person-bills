import { expect, test } from '@playwright/test'

test('complete bill account workflow', async ({ page }) => {
  const email = `e2e-${Date.now()}@example.com`
  page.on('dialog', (dialog) => dialog.accept())

  await page.goto('/')
  await expect(page.getByRole('heading', { name: '个人记账本' })).toBeVisible()

  await page.getByLabel('邮箱').fill(email)
  await page.getByRole('button', { name: '获取' }).click()
  await expect(page.getByPlaceholder('6 位验证码')).toHaveValue('246810')
  await page.getByRole('button', { name: '注册并进入' }).click()

  await expect(page.getByText(email)).toBeVisible()
  await expect(page.getByRole('heading', { name: '分类支出占比' })).toBeVisible()
  await expect(page.getByRole('combobox')).toContainText('餐饮')

  await page.getByRole('button', { name: '新增账单' }).click()
  await page.getByPlaceholder('0.00').fill('25.50')
  await page.getByPlaceholder('选填，例如：午餐').fill('演示咖啡')
  await page.getByRole('button', { name: '保存' }).click()

  await expect(page.getByText('演示咖啡')).toBeVisible()
  await expect(page.getByText('1. 餐饮')).toBeVisible()
  await expect(page.getByRole('heading', { name: '近6个月趋势' })).toBeVisible()

  await page.getByRole('button', { name: '收入' }).click()
  await expect(page.getByText('这个月份还没有账单')).toBeVisible()
  await page.getByRole('button', { name: '支出' }).click()
  await expect(page.getByText('演示咖啡')).toBeVisible()

  await page.getByRole('button', { name: '分类管理' }).click()
  await expect(page.getByRole('heading', { name: '分类管理' })).toBeVisible()
  await page.getByPlaceholder('例如：设计设备').fill('健身')
  await page.getByRole('button', { name: '添加分类' }).click()
  await expect(page.getByRole('button', { name: '健身' })).toBeVisible()
  await page.getByRole('button', { name: '健身' }).click()
  await page.getByPlaceholder('例如：设计设备').fill('运动')
  await page.getByRole('button', { name: '保存分类' }).click()
  await expect(page.getByRole('button', { name: '运动' })).toBeVisible()
  await page.getByRole('button', { name: '停用分类' }).click()
  await expect(page.getByText('运动（已停用）')).toBeVisible()

  await page.getByRole('button', { name: '返回首页' }).click()
  await page.getByRole('button', { name: '新增账单' }).click()
  await expect(page.getByRole('button', { name: '运动' })).toHaveCount(0)
  await page.getByRole('button', { name: '关闭' }).click()

  await page.getByRole('button', { name: '删除账单' }).click()
  await expect(page.getByText('这个月份还没有账单')).toBeVisible()

  await page.getByRole('button', { name: '退出登录' }).click()
  await expect(page.getByRole('button', { name: '注册并进入' })).toBeVisible()
})
