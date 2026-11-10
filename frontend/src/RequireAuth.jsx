import { useLocation, Navigate } from 'react-router-dom';
import { useAuthenticator, Loader } from '@aws-amplify/ui-react';

export default function RequireAuth({ children }) {
  const location = useLocation();
  const { route, authStatus } = useAuthenticator((context) => [context.route, context.authStatus]);

  if (authStatus === 'configuring') return <Loader />;

  if (route !== 'authenticated') {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return children;
}
