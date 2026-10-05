import { useState } from 'react';
import { login, register, TokenManager } from '../services/api';
import { Scale } from 'lucide-react';

interface AuthModalProps {
  isOpen: boolean;
  onSuccess: () => void;
}

export function AuthModal({ isOpen, onSuccess }: AuthModalProps) {
  const [mode, setMode] = useState<'login' | 'register'>('login');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);
    try {
      if (mode === 'login') {
        const res = await login({ username, password });
        TokenManager.setToken(res.access_token);
        onSuccess();
      } else {
        await register({ username, password });
        const res = await login({ username, password });
        TokenManager.setToken(res.access_token);
        onSuccess();
      }
    } catch (err: any) {
      setError(err.message || 'Authentication failed');
    } finally {
      setIsLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="auth-overlay">
      <div className="auth-card">
        {/* Logo */}
        <div className="auth-logo-wrap">
          <div className="auth-logo">
            <Scale size={28} color="rgba(30,15,5,0.90)" strokeWidth={2.2} />
          </div>
        </div>

        <h2 className="auth-title">
          {mode === 'login' ? 'Welcome to LegalGPT' : 'Create Account'}
        </h2>
        <p className="auth-sub">
          {mode === 'login'
            ? 'Sign in to your legal research assistant'
            : 'Start your legal research journey'}
        </p>

        <form onSubmit={handleSubmit} className="auth-form">
          <div className="form-field">
            <label className="form-label" htmlFor="auth-username">USERNAME</label>
            <input
              id="auth-username"
              type="text"
              className="form-input"
              placeholder="Enter your username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
              disabled={isLoading}
              autoComplete="username"
            />
          </div>

          <div className="form-field">
            <label className="form-label" htmlFor="auth-password">PASSWORD</label>
            <input
              id="auth-password"
              type="password"
              className="form-input"
              placeholder="Enter your password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              disabled={isLoading}
              autoComplete="current-password"
            />
          </div>

          {error && <div className="auth-error">{error}</div>}

          <button
            type="submit"
            className="auth-submit-btn"
            disabled={isLoading || !username || !password}
          >
            {isLoading ? 'Please wait…' : mode === 'login' ? 'Sign In' : 'Register'}
          </button>
        </form>

        <div className="auth-switch">
          <button
            type="button"
            className="auth-switch-btn"
            onClick={() => { setMode(m => m === 'login' ? 'register' : 'login'); setError(''); }}
            disabled={isLoading}
          >
            {mode === 'login'
              ? "Don't have an account? Register"
              : 'Already have an account? Sign in'}
          </button>
        </div>
      </div>
    </div>
  );
}
