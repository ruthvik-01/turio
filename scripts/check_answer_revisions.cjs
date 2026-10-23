// Exercise the real client save boundary with synthetic HTTP responses.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const Module = require('node:module');
const babel = require('../frontend/node_modules/next/dist/compiled/babel/core');
const filename = path.resolve(__dirname, '../frontend/lib/api.ts');
const code = babel.transformSync(fs.readFileSync(filename, 'utf8'), { filename, configFile: false, babelrc: false,
  presets: [require('../frontend/node_modules/next/dist/compiled/babel/preset-typescript')],
  plugins: [require('../frontend/node_modules/next/dist/compiled/babel/plugin-transform-modules-commonjs')] }).code;
const loaded = new Module(filename, module);
loaded.filename = filename;
loaded.paths = Module._nodeModulePaths(path.dirname(filename));
loaded._compile(code, filename);
const { saveApplicationAnswers } = loaded.exports;
const app = { id: 'fixture', revision: 1, status: 'needs_input', fields: [
  { id: 'field', field_key: 'question', label: 'Question', input_type: 'text', options: [], required: true,
    normalized_intent: 'custom', value: null, value_source: 'missing', user_confirmed: false }] };
const answers = [{ field_id: 'field', value: 'User edit', user_confirmed: true, save_for_reuse: false }];
const fetchBefore = global.fetch;
function envelope(data) { return Response.json({ data, error: null }); }
function stale() { return Response.json({ data: null, error: { code: 'STALE_REVISION', message: 'Stale' } }, { status: 409 }); }
(async () => {
  try {
    let calls = [];
    global.fetch = async (url, options) => { calls.push({ url, options }); return envelope({ ...app, revision: 2 }); };
    assert.equal((await saveApplicationAnswers(app, answers)).revision, 2);
    assert.equal(JSON.parse(calls[0].options.body).expected_revision, 1);
    const latest = { ...app, revision: 3 };
    calls = [];
    global.fetch = async (url, options) => {
      calls.push({ url, options });
      if (calls.length === 1) return stale();
      if (calls.length === 2) return envelope(latest);
      return envelope({ ...latest, revision: 4 });
    };
    assert.equal((await saveApplicationAnswers(app, answers)).revision, 4);
    assert.equal(calls.length, 3);
    assert.equal(JSON.parse(calls[2].options.body).expected_revision, 3);
    assert.notEqual(new Headers(calls[0].options.headers).get('Idempotency-Key'), new Headers(calls[2].options.headers).get('Idempotency-Key'));
    for (const changed of [
      { ...latest, fields: [{ ...app.fields[0], value: 'Other editor' }] },
      { ...latest, fields: [{ ...app.fields[0], input_type: 'checkbox' }] },
      { ...latest, fields: [{ ...app.fields[0], value_source: 'jev_profile' }] },
      { ...latest, fields: [{ ...app.fields[0], help_text: 'Salary in INR per month' }] },
      { ...latest, status: 'submitting' },
      { ...latest, fields: [] },
    ]) {
      calls = [];
      global.fetch = async (url, options) => { calls.push({ url, options }); return calls.length === 1 ? stale() : envelope(changed); };
      await assert.rejects(saveApplicationAnswers(app, answers), error => error.code === 'STALE_REVISION');
      assert.equal(calls.length, 2, 'Conflicting values, mappings or states must not be overwritten');
    }
    calls = [];
    global.fetch = async (url, options) => { calls.push({ url, options }); return calls.length === 2 ? envelope(latest) : stale(); };
    await assert.rejects(saveApplicationAnswers(app, answers), error => error.code === 'STALE_REVISION');
    assert.equal(calls.length, 3, 'At most one revision retry');
    global.fetch = async () => { throw new Error('Network lost'); };
    await assert.rejects(saveApplicationAnswers(app, answers), /Network lost/);
    console.log('PASS: revision payload, safe retry, conflicting edit/schema/AI/state protection, retry limit, network failure');
  } finally { global.fetch = fetchBefore; }
})().catch(error => { console.error(error); process.exitCode = 1; });
