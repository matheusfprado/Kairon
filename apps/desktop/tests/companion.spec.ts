import { expect, test } from "@playwright/test";

test.beforeEach(async ({ page }) => {
  await page.routeWebSocket("ws://127.0.0.1:8765/ws?voice=true", (socket) => {
    socket.send(JSON.stringify({ type: "state_changed", state: "listening_for_wake_word" }));
  });
  await page.goto("http://127.0.0.1:1420");
});

test("starts listening automatically without text controls or response bubbles", async ({ page }) => {
  await expect(page.getByRole("status")).toHaveText("Estou ouvindo");
  await expect(page.locator("input, textarea, form, .tamagotchi__bubble")).toHaveCount(0);
  await expect(page.getByText("Fale naturalmente. Estou ouvindo.")).toBeVisible();
});

test("transparent compact companion can be dragged and moved by keyboard", async ({ page }) => {
  await page.setViewportSize({ width: 1000, height: 800 });
  expect(await page.locator("html").evaluate((element) => getComputedStyle(element).backgroundColor)).toBe("rgba(0, 0, 0, 0)");
  await expect(page.locator(".tamagotchi__body")).toHaveCSS("width", "148px");
  const handle = page.getByRole("button", { name: "Arrastar Kairon", exact: false });
  const box = await handle.boundingBox();
  if (!box) throw new Error("Missing drag handle");
  await page.mouse.move(box.x + 15, box.y + 15);
  await page.mouse.down();
  await page.mouse.move(box.x + 115, box.y + 95);
  await page.mouse.up();
  await expect(page.locator("main")).toHaveCSS("transform", "matrix(1, 0, 0, 1, 100, 80)");
  await handle.focus();
  await page.keyboard.press("ArrowRight");
  await expect(page.locator("main")).toHaveCSS("transform", "matrix(1, 0, 0, 1, 120, 80)");
});

for (const viewport of [{ width: 320, height: 560 }, { width: 280, height: 480 }, { width: 667, height: 375 }]) {
  test(`layout fits ${viewport.width}x${viewport.height}`, async ({ page }) => {
    await page.setViewportSize(viewport);
    await page.emulateMedia({ reducedMotion: "reduce" });
    const handle = await page.getByRole("button", { name: "Arrastar Kairon", exact: false }).boundingBox();
    expect(handle).not.toBeNull();
    expect(handle!.y + handle!.height).toBeLessThanOrEqual(viewport.height);
    expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBe(viewport.width);
    if (viewport.width === 320) {
      expect(await page.locator<HTMLImageElement>(".tamagotchi__body img").evaluate(async (image) => {
        await image.decode();
        const canvas = document.createElement("canvas");
        canvas.width = image.naturalWidth;
        canvas.height = image.naturalHeight;
        const context = canvas.getContext("2d")!;
        context.drawImage(image, 0, 0);
        return context.getImageData(0, 0, 1, 1).data[3];
      })).toBe(0);
    }
  });
}
