const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

const modulePath = path.join(__dirname, "../frontend/lib/theme.ts");
assert.ok(fs.existsSync(modulePath), "Theme preference helper is missing");
const { resolveTheme, applyTheme, THEME_BOOTSTRAP } = require(modulePath);
let checks = 0;
for (const saved of [null, undefined, "invalid", {}, 1]) {
  assert.equal(resolveTheme(saved, false), "light");
  assert.equal(resolveTheme(saved, true), "dark");
  checks += 2;
}
for (const saved of ["light", "dark"]) {
  assert.equal(resolveTheme(saved, false), saved);
  assert.equal(resolveTheme(saved, true), saved);
  const document = { documentElement: { dataset: {} } };
  vm.runInNewContext(THEME_BOOTSTRAP, { document, localStorage: { getItem: () => saved } });
  assert.equal(document.documentElement.dataset.theme, saved);
  checks += 3;
}
for (const getItem of [() => "invalid", () => null, () => { throw Error("blocked"); }]) {
  const document = { documentElement: { dataset: {} } };
  vm.runInNewContext(THEME_BOOTSTRAP, { document, localStorage: { getItem } });
  assert.equal(document.documentElement.dataset.theme, undefined);
  checks++;
}
global.document = { documentElement: { dataset: {} } };
global.localStorage = { setItem() { throw Error("blocked"); } };
applyTheme("dark");
assert.equal(global.document.documentElement.dataset.theme, "dark");
checks++;
let written;
global.localStorage = { setItem(key, value) { written = [key, value]; } };
applyTheme("light");
assert.equal(global.document.documentElement.dataset.theme, "light");
assert.deepEqual(written, ["turio-theme", "light"]);
checks += 2;
const configPath = path.join(__dirname, "../frontend/next.config.ts");
assert.ok(fs.existsSync(configPath), "Isolated frontend build configuration is missing");
const { execFileSync } = require("node:child_process");
for (const [flag, expected] of [["", ".next"], ["1", ".next/atmos"], ["0", ".next"]]) {
  const actual = execFileSync(process.execPath,
    ["-e", `console.log(require(${JSON.stringify(configPath)}).default.distDir)`],
    { env: { ...process.env, TURIO_UI_VERIFY: flag }, encoding: "utf-8" }).trim();
  assert.equal(actual, expected);
  checks++;
}
console.log(`Theme checks: ${checks} passed`);
