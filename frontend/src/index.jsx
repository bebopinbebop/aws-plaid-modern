import { createRoot } from 'react-dom/client';
import { Amplify } from 'aws-amplify';
import { fetchAuthSession } from 'aws-amplify/auth';
import App from './App';
import { createConfig } from './config.mjs';
import '@aws-amplify/ui-react/styles.css';
import '@fontsource/inter/latin-400.css';
import './index.css';

const root = createRoot(document.getElementById('root'));
async function headers() {
  const accessToken = (await fetchAuthSession()).tokens?.accessToken?.toString();
  return accessToken ? { Authorization: `Bearer ${accessToken}` } : {};
}
try {
  Amplify.configure(createConfig(import.meta.env), { API: { REST: { headers } } });
  root.render(<App />);
} catch (error) {
  root.render(<main role="alert"><h1>Application configuration required</h1><p>{error.message}</p></main>);
}
