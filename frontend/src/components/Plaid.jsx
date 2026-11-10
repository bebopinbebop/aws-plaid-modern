import { useState } from 'react';
import { get, post } from 'aws-amplify/api';
import { ConsoleLogger } from 'aws-amplify/utils';
import { Button, Flex, Alert } from '@aws-amplify/ui-react';
import PlaidLink from './PlaidLink';

const logger = new ConsoleLogger("Plaid");

const apiName = "plaidapi";

export default function Plaid({ getItems }) {
  const [connecting, setConnecting] = useState(false);
  const [error, setError] = useState(null);
  const [token, setToken] = useState(() =>
    new URLSearchParams(window.location.search).has('oauth_state_id')
      ? sessionStorage.getItem('plaid_link_token') : null);

  const handleGetToken = async () => {
    setConnecting(true);
    setError(null);
    setToken(null);
    try {
      const { body } = await get({
        apiName,
        path: '/v1/tokens'
      }).response;
      const data = await body.json();

      sessionStorage.setItem('plaid_link_token', data.link_token);
      setToken(data.link_token);
    } catch (err) {
      logger.error('unable to create link token');
      setError('Unable to start Plaid Link. Please try again.');
      setConnecting(false);
    }
  };

  const handleSuccess = async (public_token, metadata) => {
    try {
      const { body } = await post({
        apiName,
        path: '/v1/tokens',
        options: {
          body: {
            public_token,
            metadata
          },
        },
      }).response;
      const data = await body.text(); // returns an 202 response code with an empty body
      logger.debug('POST /v1/tokens response:', data);
      getItems();
      setConnecting(false);
    } catch (err) {
      logger.error('unable to exchange public token');
      setError('Unable to link this institution. It may already be linked.');
    } finally {
      setConnecting(false);
      setToken(null);
      sessionStorage.removeItem('plaid_link_token');
      if (window.location.search.includes('oauth_state_id')) {
        window.history.replaceState({}, '', window.location.pathname);
      }
    }
  };

  return (
    <Flex direction="column">
      {error && <Alert variation="error">{error}</Alert>}
      <Button
        variation="primary"
        isLoading={connecting}
        onClick={handleGetToken}
      >
        CONNECT WITH PLAID
      </Button>
      {token ? (
        <PlaidLink
          token={token}
          onSuccess={handleSuccess}
          onExit={(linkError) => {
            if (linkError) setError('Plaid Link could not complete. Please try again.');
            setConnecting(false); setToken(null);
            sessionStorage.removeItem('plaid_link_token');
            window.history.replaceState({}, '', window.location.pathname);
          }}
        />
      ) : null}
    </Flex>
  );
}
