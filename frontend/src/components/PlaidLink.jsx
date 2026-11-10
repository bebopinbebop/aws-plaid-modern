import { useEffect } from 'react';
import { usePlaidLink } from 'react-plaid-link';

export default function PlaidLink({ token, onSuccess, onExit }) {
  const { open, ready, error } = usePlaidLink({
    token,
    receivedRedirectUri: new URLSearchParams(window.location.search).has('oauth_state_id')
      ? window.location.href : undefined,
    onSuccess,
    onExit,
  });

  useEffect(() => {
    if (token && ready) {
      open();
    }
  }, [token, ready, open]);

  useEffect(() => {
    if (error) onExit(error);
  }, [error, onExit]);

  return <div />;
}
