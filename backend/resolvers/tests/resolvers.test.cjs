const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

function load(name) {
  const source = fs.readFileSync(path.join(__dirname, '..', `Query.${name}.js`), 'utf8')
    .replace(/import .*?;\n/, '').replaceAll('export function', 'function');
  const util = {
    dynamodb: { toMapValues: values => Object.fromEntries(
      Object.entries(values).map(([key, value]) => [key, { S: value }])) },
    appendError: (message, type) => { throw new Error(`${type}: ${message}`); },
  };
  return new Function('util', `${source}\nreturn { request, response };`)(util);
}

for (const name of ['getItems', 'getAccounts', 'getTransactions']) {
  test(`${name} uses the authenticated subject, including when username differs`, () => {
    const resolver = load(name);
    const context = { identity: { sub: 'subject', username: 'other-user' },
      arguments: { id: 'item', limit: 10, cursor: 'next' } };
    const result = resolver.request(context);
    const values = result.query.expressionValues;
    assert.ok(JSON.stringify(values).includes('USER#subject#'));
    assert.ok(!JSON.stringify(values).includes('other-user'));
    if (name !== 'getAccounts') {
      assert.equal(result.limit, 10);
      assert.equal(result.nextToken, 'next');
    }
  });
  test(`${name} propagates datasource errors`, () => {
    assert.throws(() => load(name).response({ error: { message: 'denied', type: 'Unauthorized' } }), /denied/);
  });
}

test('getItems returns item IDs and pagination', () => {
  assert.deepEqual(load('getItems').response({ identity: { sub: 'subject', username: 'different' },
    result: { items: [{ sk: 'USER#subject#ITEM#item', institution_id: 'bank', institution_name: 'Bank' }], nextToken: 'next' } }),
    { items: [{ item_id: 'item', institution_id: 'bank', institution_name: 'Bank' }], cursor: 'next' });
});
test('getAccounts returns account IDs', () => {
  assert.deepEqual(load('getAccounts').response({ result: { items: [{ sk: 'ACCOUNT#account' }] } }),
    [{ sk: 'ACCOUNT#account', account_id: 'account' }]);
});
test('getTransactions preserves transactions and cursor', () => {
  assert.deepEqual(load('getTransactions').response({ result: { items: [{ transaction_id: 'txn' }], nextToken: 'next' } }),
    { transactions: [{ transaction_id: 'txn' }], cursor: 'next' });
});
