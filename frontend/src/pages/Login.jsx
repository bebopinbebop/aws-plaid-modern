import { Authenticator } from '@aws-amplify/ui-react';
import { useAuthenticator, View } from '@aws-amplify/ui-react';
import { useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';

export default function Login() {
  const { route } = useAuthenticator((context) => [context.route]);
  const location = useLocation();
  const navigate = useNavigate();
  const origin = location.state?.from;
  const from = origin ? `${origin.pathname}${origin.search || ''}` : '/';

  const components = {
    SignUp: {
      Footer() {
        return (
          <View textAlign="center">
            <strong>Password Policy</strong>:
            <ul>
              <li>Minimum of 8 characters</li>
              <li>At least one lowercase character</li>
              <li>At least one uppercase character</li>
              <li>At least one number character</li>
              <li>At least one symbol character</li>
            </ul>
          </View>
        );
      }
    }
  }

  useEffect(() => {
    if (route === 'authenticated') {
      navigate(from, { replace: true });
    }
  }, [route, navigate, from]);

  return (
    <View className="auth-wrapper">
      <Authenticator components={components}/>
    </View>
  );
}
