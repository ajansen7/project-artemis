import { useState } from 'react';
import { supabase } from '../lib/supabase';

interface LoginPageProps {
  onLoginSuccess: () => void;
}

export function LoginPage({ onLoginSuccess }: LoginPageProps) {
  const [tab, setTab] = useState<'signin' | 'signup'>('signin');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [passwordConfirm, setPasswordConfirm] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [useMagicLink, setUseMagicLink] = useState(false);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccess(null);
    setLoading(true);

    try {
      if (useMagicLink) {
        const { error: err } = await supabase.auth.signInWithOtp({ email });
        if (err) throw err;
        setError(null);
        alert('Check your email for the magic link');
      } else {
        const { error: err } = await supabase.auth.signInWithPassword({
          email,
          password,
        });
        if (err) throw err;
        onLoginSuccess();
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Sign-in failed');
    } finally {
      setLoading(false);
    }
  };

  const handleSignup = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccess(null);

    if (password !== passwordConfirm) {
      setError('Passwords do not match');
      return;
    }

    if (password.length < 6) {
      setError('Password must be at least 6 characters');
      return;
    }

    setLoading(true);

    try {
      const { error: err } = await supabase.auth.signUp({
        email,
        password,
      });
      if (err) throw err;
      setSuccess('Account created! Check your email to verify.');
      setEmail('');
      setPassword('');
      setPasswordConfirm('');
      // Switch back to signin tab after a moment
      setTimeout(() => setTab('signin'), 2000);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Sign-up failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      minHeight: '100vh',
      background: '#f5f5f5',
    }}>
      <div style={{
        background: 'white',
        padding: '40px',
        borderRadius: '8px',
        boxShadow: '0 2px 10px rgba(0, 0, 0, 0.1)',
        width: '100%',
        maxWidth: '400px',
      }}>
        <h1 style={{ marginBottom: '30px', textAlign: 'center' }}>
          Artemis
        </h1>

        {/* Tab buttons */}
        <div style={{
          display: 'flex',
          gap: '10px',
          marginBottom: '30px',
          borderBottom: '1px solid #ddd',
        }}>
          <button
            onClick={() => setTab('signin')}
            style={{
              flex: 1,
              padding: '10px',
              border: 'none',
              background: 'transparent',
              color: tab === 'signin' ? '#2E7EBF' : '#999',
              borderBottom: tab === 'signin' ? '2px solid #2E7EBF' : 'none',
              fontSize: '14px',
              fontWeight: tab === 'signin' ? '600' : '400',
              cursor: 'pointer',
              marginBottom: '-1px',
            }}
          >
            Sign In
          </button>
          <button
            onClick={() => setTab('signup')}
            style={{
              flex: 1,
              padding: '10px',
              border: 'none',
              background: 'transparent',
              color: tab === 'signup' ? '#2E7EBF' : '#999',
              borderBottom: tab === 'signup' ? '2px solid #2E7EBF' : 'none',
              fontSize: '14px',
              fontWeight: tab === 'signup' ? '600' : '400',
              cursor: 'pointer',
              marginBottom: '-1px',
            }}
          >
            Create Account
          </button>
        </div>

        <form onSubmit={tab === 'signin' ? handleLogin : handleSignup}>
          <div style={{ marginBottom: '15px' }}>
            <label style={{ display: 'block', marginBottom: '5px' }}>
              Email
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="your@email.com"
              required
              style={{
                width: '100%',
                padding: '10px',
                border: '1px solid #ddd',
                borderRadius: '4px',
                fontSize: '14px',
                boxSizing: 'border-box',
              }}
            />
          </div>

          {tab === 'signin' && !useMagicLink && (
            <div style={{ marginBottom: '15px' }}>
              <label style={{ display: 'block', marginBottom: '5px' }}>
                Password
              </label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                required
                style={{
                  width: '100%',
                  padding: '10px',
                  border: '1px solid #ddd',
                  borderRadius: '4px',
                  fontSize: '14px',
                  boxSizing: 'border-box',
                }}
              />
            </div>
          )}

          {tab === 'signup' && (
            <>
              <div style={{ marginBottom: '15px' }}>
                <label style={{ display: 'block', marginBottom: '5px' }}>
                  Password
                </label>
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  required
                  style={{
                    width: '100%',
                    padding: '10px',
                    border: '1px solid #ddd',
                    borderRadius: '4px',
                    fontSize: '14px',
                    boxSizing: 'border-box',
                  }}
                />
              </div>
              <div style={{ marginBottom: '15px' }}>
                <label style={{ display: 'block', marginBottom: '5px' }}>
                  Confirm Password
                </label>
                <input
                  type="password"
                  value={passwordConfirm}
                  onChange={(e) => setPasswordConfirm(e.target.value)}
                  placeholder="••••••••"
                  required
                  style={{
                    width: '100%',
                    padding: '10px',
                    border: '1px solid #ddd',
                    borderRadius: '4px',
                    fontSize: '14px',
                    boxSizing: 'border-box',
                  }}
                />
              </div>
            </>
          )}

          {error && (
            <div style={{
              color: '#d32f2f',
              fontSize: '14px',
              marginBottom: '15px',
              padding: '10px',
              background: '#ffebee',
              borderRadius: '4px',
            }}>
              {error}
            </div>
          )}

          {success && (
            <div style={{
              color: '#2e7d32',
              fontSize: '14px',
              marginBottom: '15px',
              padding: '10px',
              background: '#f1f8f4',
              borderRadius: '4px',
            }}>
              {success}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            style={{
              width: '100%',
              padding: '10px',
              background: '#2E7EBF',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              fontSize: '14px',
              fontWeight: '500',
              cursor: loading ? 'not-allowed' : 'pointer',
              opacity: loading ? 0.6 : 1,
            }}
          >
            {tab === 'signin' && (loading ? 'Signing in...' : 'Sign in')}
            {tab === 'signup' && (loading ? 'Creating account...' : 'Create account')}
          </button>

          {tab === 'signin' && (
            <div style={{
              marginTop: '15px',
              textAlign: 'center',
            }}>
              <label style={{ fontSize: '14px', cursor: 'pointer' }}>
                <input
                  type="checkbox"
                  checked={useMagicLink}
                  onChange={(e) => setUseMagicLink(e.target.checked)}
                  style={{ marginRight: '5px' }}
                />
                Use magic link instead
              </label>
            </div>
          )}
        </form>
      </div>
    </div>
  );
}
