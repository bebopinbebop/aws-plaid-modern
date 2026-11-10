export function createConfig(env) {
  const required = ['VITE_BACKEND_URL', 'VITE_COGNITO_USERPOOL_ID',
    'VITE_COGNITO_CLIENT_ID', 'VITE_GRAPHQL_URL', 'VITE_REGION'];
  const missing = required.filter(key => !env[key]);
  if (missing.length) {
    throw new Error(`Missing frontend configuration: ${missing.join(', ')}. See frontend/.env.example.`);
  }
  return {
    Auth: {
      Cognito: {
        userPoolId: env.VITE_COGNITO_USERPOOL_ID,
        userPoolClientId: env.VITE_COGNITO_CLIENT_ID,
        loginWith: { email: true },
        signUpVerificationMethod: 'code',
        mfa: { status: 'on', totpEnabled: true },
        passwordFormat: {
          minLength: 8, requireLowercase: true, requireUppercase: true,
          requireNumbers: true, requireSpecialCharacters: true,
        },
      },
    },
    API: {
      GraphQL: {
        endpoint: env.VITE_GRAPHQL_URL,
        region: env.VITE_REGION,
        defaultAuthMode: 'userPool',
      },
      REST: {
        plaidapi: { endpoint: env.VITE_BACKEND_URL, region: env.VITE_REGION },
      },
    },
  };
}
