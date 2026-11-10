import { test } from 'node:test';
import assert from 'node:assert/strict';
import { createConfig } from '../src/config.mjs';
const env = {
  VITE_BACKEND_URL: 'https://api.example.com', VITE_GRAPHQL_URL: 'https://graphql.example.com/graphql',
  VITE_COGNITO_USERPOOL_ID: 'us-east-1_pool', VITE_COGNITO_CLIENT_ID: 'client', VITE_REGION: 'us-east-1',
};
test('reports missing stack outputs before initializing Amplify', () => {
  assert.throws(() => createConfig({}), /VITE_COGNITO_USERPOOL_ID/);
});
test('configures existing Cognito and authenticated AppSync', () => {
  const config = createConfig(env);
  assert.equal(config.Auth.Cognito.userPoolId, env.VITE_COGNITO_USERPOOL_ID);
  assert.equal(config.Auth.Cognito.mfa.totpEnabled, true);
  assert.equal(config.API.GraphQL.defaultAuthMode, 'userPool');
  assert.equal(config.API.REST.plaidapi.endpoint, env.VITE_BACKEND_URL);
});
test('does not propagate unrelated environment secrets', () => {
  assert.ok(!JSON.stringify(createConfig({ ...env, PLAID_SECRET: 'do-not-copy' })).includes('do-not-copy'));
});
