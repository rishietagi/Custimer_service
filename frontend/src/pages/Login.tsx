import React, { useState } from 'react';
import { api } from '../services/api';
import { Shield, Key, UserPlus, AlertCircle, Sparkles } from 'lucide-react';

interface LoginProps {
  onLoginSuccess: (user: any) => void;
}

export const Login: React.FC<LoginProps> = ({ onLoginSuccess }) => {
  const [activeTab, setActiveTab] = useState<'signin' | 'register'>('signin');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [errorMsg, setErrorMsg] = useState('');
  const [successMsg, setSuccessMsg] = useState('');
  const [submitting, setSubmitting] = useState(false);

  // Registration Form State
  const [regUsername, setRegUsername] = useState('');
  const [regPassword, setRegPassword] = useState('');
  const [regFullName, setRegFullName] = useState('');
  const [regEmail, setRegEmail] = useState('');
  const [regPhone, setRegPhone] = useState('');
  const [regAddress, setRegAddress] = useState('');
  const [regCity, setRegCity] = useState('');
  const [regPincode, setRegPincode] = useState('');

  const handleLoginSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!username || !password) {
      setErrorMsg('Please fill in all fields.');
      return;
    }
    setSubmitting(true);
    setErrorMsg('');
    try {
      const user = await api.auth.login(username, password);
      onLoginSuccess(user);
    } catch (err: any) {
      setErrorMsg(err.response?.data?.detail || 'Invalid username or password. Try customer1 / password123');
    } finally {
      setSubmitting(false);
    }
  };

  const handleRegisterSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!regUsername || !regPassword || !regFullName || !regEmail || !regPhone) {
      setErrorMsg('Please fill in all required fields marked with *.');
      return;
    }
    setSubmitting(true);
    setErrorMsg('');
    setSuccessMsg('');
    try {
      await api.auth.register({
        username: regUsername,
        password: regPassword,
        full_name: regFullName,
        email: regEmail,
        phone: regPhone,
        address: regAddress || null,
        city: regCity || null,
        pincode: regPincode || null,
      });
      setSuccessMsg('Account created successfully! You can now sign in.');
      setActiveTab('signin');
      setUsername(regUsername);
      setPassword(regPassword);
      // Reset
      setRegUsername('');
      setRegPassword('');
      setRegFullName('');
      setRegEmail('');
      setRegPhone('');
      setRegAddress('');
      setRegCity('');
      setRegPincode('');
    } catch (err: any) {
      setErrorMsg(err.response?.data?.detail || 'Failed to create account.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
      <div className="w-full max-w-md bg-white rounded-2xl border border-gray-100 shadow-xl overflow-hidden">
        {/* Brand Header */}
        <div className="bg-brand-red p-8 flex flex-col items-center justify-center text-white relative">
          <div className="absolute top-4 right-4 bg-white/10 px-2 py-0.5 rounded text-[9px] uppercase tracking-wider font-semibold">
            v1.0.0
          </div>
          <div className="w-12 h-12 bg-white/10 rounded-full flex items-center justify-center mb-3">
            <Sparkles className="w-6 h-6 text-white" />
          </div>
          <h2 className="text-xl font-bold tracking-tight">SmartCare Customer Portal</h2>
          <p className="text-xs text-red-100 mt-1">Guided Customer Support & Repairs</p>
        </div>

        {/* Tabs Control */}
        <div className="flex border-b border-gray-100">
          <button
            onClick={() => { setActiveTab('signin'); setErrorMsg(''); }}
            className={`w-1/2 py-4 text-sm font-semibold flex items-center justify-center gap-2 border-b-2 transition-all ${
              activeTab === 'signin' 
                ? 'border-brand-red text-brand-red' 
                : 'border-transparent text-gray-400 hover:text-gray-600'
            }`}
          >
            <Key className="w-4 h-4" />
            Sign In
          </button>
          <button
            onClick={() => { setActiveTab('register'); setErrorMsg(''); }}
            className={`w-1/2 py-4 text-sm font-semibold flex items-center justify-center gap-2 border-b-2 transition-all ${
              activeTab === 'register' 
                ? 'border-brand-red text-brand-red' 
                : 'border-transparent text-gray-400 hover:text-gray-600'
            }`}
          >
            <UserPlus className="w-4 h-4" />
            Create Account
          </button>
        </div>

        {/* Tab Content */}
        <div className="p-6">
          {errorMsg && (
            <div className="bg-red-50 text-brand-red text-xs p-3 rounded-lg border border-red-200 flex items-center gap-2 mb-4">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{errorMsg}</span>
            </div>
          )}

          {successMsg && (
            <div className="bg-emerald-50 text-emerald-700 text-xs p-3 rounded-lg border border-emerald-200 flex items-center gap-2 mb-4">
              <Shield className="w-4 h-4 shrink-0" />
              <span>{successMsg}</span>
            </div>
          )}

          {activeTab === 'signin' ? (
            <form onSubmit={handleLoginSubmit} className="space-y-4">
              <div className="space-y-1">
                <label className="text-xs font-semibold text-gray-600">Username</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. customer1"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  className="w-full bg-gray-50 border border-gray-200 rounded-lg p-2.5 text-sm focus:bg-white focus:outline-none focus:ring-2 focus:ring-brand-red focus:border-transparent transition-all"
                />
              </div>

              <div className="space-y-1">
                <label className="text-xs font-semibold text-gray-600">Password</label>
                <input
                  type="password"
                  required
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full bg-gray-50 border border-gray-200 rounded-lg p-2.5 text-sm focus:bg-white focus:outline-none focus:ring-2 focus:ring-brand-red focus:border-transparent transition-all"
                />
              </div>

              <button
                type="submit"
                disabled={submitting}
                className="w-full btn-premium py-3 text-sm mt-2"
              >
                {submitting ? 'Signing in...' : 'Sign In'}
              </button>

              <div className="mt-6 p-4 rounded-xl bg-gray-50 border border-gray-100 space-y-2 text-xs text-gray-500">
                <p className="font-semibold text-gray-700 flex items-center gap-1.5">
                  <Shield className="w-3.5 h-3.5 text-brand-red" /> Demo Accounts Included:
                </p>
                <ul className="list-disc pl-4 space-y-1">
                  <li>Username: <code className="font-mono text-gray-700 font-bold">customer1</code> | Pass: <code className="font-mono text-gray-700">password123</code></li>
                  <li>Username: <code className="font-mono text-gray-700 font-bold">customer2</code> | Pass: <code className="font-mono text-gray-700">password123</code></li>
                </ul>
              </div>
            </form>
          ) : (
            <form onSubmit={handleRegisterSubmit} className="space-y-4 max-h-[480px] overflow-y-auto pr-1">
              <p className="text-[10px] text-gray-400 font-semibold uppercase tracking-wider mb-2">Basic Information</p>
              
              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1">
                  <label className="text-xs font-semibold text-gray-600">Username *</label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. johndoe12"
                    value={regUsername}
                    onChange={(e) => setRegUsername(e.target.value)}
                    className="w-full bg-gray-50 border border-gray-200 rounded-lg p-2.5 text-sm focus:bg-white focus:outline-none focus:ring-2 focus:ring-brand-red focus:border-transparent transition-all"
                  />
                </div>
                <div className="space-y-1">
                  <label className="text-xs font-semibold text-gray-600">Password *</label>
                  <input
                    type="password"
                    required
                    placeholder="Min 6 chars"
                    value={regPassword}
                    onChange={(e) => setRegPassword(e.target.value)}
                    className="w-full bg-gray-50 border border-gray-200 rounded-lg p-2.5 text-sm focus:bg-white focus:outline-none focus:ring-2 focus:ring-brand-red focus:border-transparent transition-all"
                  />
                </div>
              </div>

              <div className="space-y-1">
                <label className="text-xs font-semibold text-gray-600">Full Name *</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. John Doe"
                  value={regFullName}
                  onChange={(e) => setRegFullName(e.target.value)}
                  className="w-full bg-gray-50 border border-gray-200 rounded-lg p-2.5 text-sm focus:bg-white focus:outline-none focus:ring-2 focus:ring-brand-red focus:border-transparent transition-all"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1">
                  <label className="text-xs font-semibold text-gray-600">Email Address *</label>
                  <input
                    type="email"
                    required
                    placeholder="john@example.com"
                    value={regEmail}
                    onChange={(e) => setRegEmail(e.target.value)}
                    className="w-full bg-gray-50 border border-gray-200 rounded-lg p-2.5 text-sm focus:bg-white focus:outline-none focus:ring-2 focus:ring-brand-red focus:border-transparent transition-all"
                  />
                </div>
                <div className="space-y-1">
                  <label className="text-xs font-semibold text-gray-600">Phone Number *</label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. 5550199283"
                    value={regPhone}
                    onChange={(e) => setRegPhone(e.target.value)}
                    className="w-full bg-gray-50 border border-gray-200 rounded-lg p-2.5 text-sm focus:bg-white focus:outline-none focus:ring-2 focus:ring-brand-red focus:border-transparent transition-all"
                  />
                </div>
              </div>

              <div className="h-[1px] bg-gray-100 my-4" />
              <p className="text-[10px] text-gray-400 font-semibold uppercase tracking-wider mb-2">Service Site Address (Optional)</p>

              <div className="space-y-1">
                <label className="text-xs font-semibold text-gray-600">Street Address</label>
                <input
                  type="text"
                  placeholder="e.g. 123 Maple St"
                  value={regAddress}
                  onChange={(e) => setRegAddress(e.target.value)}
                  className="w-full bg-gray-50 border border-gray-200 rounded-lg p-2.5 text-sm focus:bg-white focus:outline-none focus:ring-2 focus:ring-brand-red focus:border-transparent transition-all"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1">
                  <label className="text-xs font-semibold text-gray-600">City</label>
                  <input
                    type="text"
                    placeholder="e.g. Chicago"
                    value={regCity}
                    onChange={(e) => setRegCity(e.target.value)}
                    className="w-full bg-gray-50 border border-gray-200 rounded-lg p-2.5 text-sm focus:bg-white focus:outline-none focus:ring-2 focus:ring-brand-red focus:border-transparent transition-all"
                  />
                </div>
                <div className="space-y-1">
                  <label className="text-xs font-semibold text-gray-600">Pincode</label>
                  <input
                    type="text"
                    placeholder="e.g. 60601"
                    value={regPincode}
                    onChange={(e) => setRegPincode(e.target.value)}
                    className="w-full bg-gray-50 border border-gray-200 rounded-lg p-2.5 text-sm focus:bg-white focus:outline-none focus:ring-2 focus:ring-brand-red focus:border-transparent transition-all"
                  />
                </div>
              </div>

              <button
                type="submit"
                disabled={submitting}
                className="w-full btn-premium py-3 text-sm mt-4"
              >
                {submitting ? 'Creating account...' : 'Register Account'}
              </button>
            </form>
          )}
        </div>
      </div>
    </div>
  );
};
