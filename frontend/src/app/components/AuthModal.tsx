import { useState } from 'react';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from './ui/dialog';
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
        const response = await login({ username, password });
        TokenManager.setToken(response.access_token);
        onSuccess();
      } else {
        await register({ username, password });
        // After registration, automatically login
        const response = await login({ username, password });
        TokenManager.setToken(response.access_token);
        onSuccess();
      }
    } catch (err: any) {
      setError(err.message || 'Authentication failed');
    } finally {
      setIsLoading(false);
    }
  };

  const toggleMode = () => {
    setMode(mode === 'login' ? 'register' : 'login');
    setError('');
  };

  return (
    <Dialog open={isOpen} onOpenChange={() => {}}>
      <DialogContent className="sm:max-w-md" hideCloseButton>
        <DialogHeader>
          <div className="flex items-center justify-center mb-4">
            <div className="size-16 rounded-full bg-gradient-to-br from-amber-500 to-orange-600 flex items-center justify-center">
              <Scale className="size-9 text-white" />
            </div>
          </div>
          <DialogTitle className="text-center text-2xl">
            {mode === 'login' ? 'Welcome to LegalGPT' : 'Create Account'}
          </DialogTitle>
          <DialogDescription className="text-center">
            {mode === 'login'
              ? 'Sign in to access your legal research assistant'
              : 'Register to start your legal research journey'}
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="username">Username</Label>
            <Input
              id="username"
              type="text"
              placeholder="Enter your username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
              disabled={isLoading}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="password">Password</Label>
            <Input
              id="password"
              type="password"
              placeholder="Enter your password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              disabled={isLoading}
            />
          </div>

          {error && (
            <div className="text-sm text-red-600 bg-red-50 p-3 rounded-md">
              {error}
            </div>
          )}

          <Button
            type="submit"
            className="w-full bg-gradient-to-r from-amber-500 to-orange-600 hover:from-amber-600 hover:to-orange-700"
            disabled={isLoading}
          >
            {isLoading ? 'Please wait...' : mode === 'login' ? 'Sign In' : 'Register'}
          </Button>

          <div className="text-center text-sm">
            <button
              type="button"
              onClick={toggleMode}
              className="text-amber-600 hover:text-amber-700 hover:underline"
              disabled={isLoading}
            >
              {mode === 'login'
                ? "Don't have an account? Register"
                : 'Already have an account? Sign in'}
            </button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}
