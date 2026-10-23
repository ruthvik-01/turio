// Execute the actual proxy/client modules with synthetic fetches; no network or account writes.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const Module = require('node:module');
const babel = require('../frontend/node_modules/next/dist/compiled/babel/core');
const { NextRequest } = require('../frontend/node_modules/next/server.js');
function load(relative) {
  const filename = path.resolve(__dirname, relative);
  const code = babel.transformSync(fs.readFileSync(filename, 'utf8'), { filename, configFile: false, babelrc: false,
    presets: [require('../frontend/node_modules/next/dist/compiled/babel/preset-typescript')],
    plugins: [require('../frontend/node_modules/next/dist/compiled/babel/plugin-transform-modules-commonjs')] }).code;
  const result = new Module(filename, module);
  result.filename = filename; result.paths = Module._nodeModulePaths(path.dirname(filename));
  result._compile(code, filename);
  return result.exports;
}
const proxy = load('../frontend/app/api/[...path]/route.ts');
const client = load('../frontend/lib/api.ts');
const fetchBefore = global.fetch, timeoutBefore = AbortSignal.timeout;
const budgets = [];
AbortSignal.timeout = milliseconds => { budgets.push(milliseconds); return timeoutBefore(milliseconds); };
(async () => {
  try {
    for (const failure of [false, true]) {
      let calls = 0;
      global.fetch = async () => {
        calls += 1;
        if (calls === 1) return Response.json({ data: null, error: { code: 'EXPIRED', message: 'Fixture' } }, { status: 401 });
        if (calls === 2) return Response.json({ data: { token: { access_token: 'fixture-new-access', refresh_token: 'fixture-new-refresh', expires_in: 900 } } });
        if (failure) throw new DOMException('Fixture upstream timeout', 'TimeoutError');
        return Response.json({ data: { fixture: true }, error: null });
      };
      const request = new NextRequest('http://127.0.0.1:13000/api/profiles/me', { headers: { cookie: `turio_access=fixture-old; turio_refresh=fixture-${failure}` } });
      const response = await proxy.GET(request, { params: Promise.resolve({ path: ['profiles', 'me'] }) });
      assert.equal(calls, 3);
      assert.equal(response.status, failure ? 503 : 200);
      assert.match(response.headers.get('set-cookie'), /fixture-new-access/);
      assert.match(response.headers.get('set-cookie'), /fixture-new-refresh/);
    }
    global.fetch = async () => Response.json({ data: { fixture: true }, error: null });
    await client.api('/profiles/me');
    assert.equal(budgets.at(-1), 60000);
    assert.ok(budgets.at(-1) > 3 * 15000, 'Client must allow initial read, refresh and retry');
    global.fetch = async () => { throw new DOMException('Fixture timeout', 'TimeoutError'); };
    await assert.rejects(client.api('/profiles/me'), error => error.code === 'REQUEST_TIMEOUT');
    console.log('PASS: bounded reads, aggregate authentication budget, refreshed cookies retained after failed retry, timeout message');
  } finally { global.fetch = fetchBefore; AbortSignal.timeout = timeoutBefore; }
})().catch(error => { console.error(error); process.exitCode = 1; });
