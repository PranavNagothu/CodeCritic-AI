'use client';

import { motion } from 'framer-motion';
import { useState, useCallback } from 'react';
import { Upload, Folder, Github, ArrowRight, Loader2, CheckCircle, AlertCircle } from 'lucide-react';
import { useRouter } from 'next/navigation';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

type SourceMode = 'zip' | 'github';
type Status = 'idle' | 'uploading' | 'success' | 'error';

export default function HomePage() {
  const router = useRouter();
  const [mode, setMode] = useState<SourceMode>('github');
  const [isDragging, setIsDragging] = useState(false);
  const [status, setStatus] = useState<Status>('idle');
  const [progress, setProgress] = useState(0);
  const [githubUrl, setGithubUrl] = useState('');
  const [errorMsg, setErrorMsg] = useState('');

  const handleGithubSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!githubUrl.trim()) return;
    setStatus('uploading');
    setProgress(0);
    setErrorMsg('');

    // Fake progress ticks while waiting for API
    const interval = setInterval(() => setProgress(p => Math.min(p + 5, 85)), 400);

    try {
      const res = await fetch(`${API_BASE}/api/index`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ source: githubUrl.trim(), provider: 'gemini', use_agent: true }),
      });
      if (!res.ok) throw new Error(await res.text());
      clearInterval(interval);
      setProgress(100);
      setStatus('success');
      setTimeout(() => router.push('/chat'), 800);
    } catch (err: any) {
      clearInterval(interval);
      setStatus('error');
      setErrorMsg(err.message || 'Failed to index repository');
    }
  };

  const handleUpload = useCallback(async (file: File) => {
    if (!file.name.endsWith('.zip')) {
      setErrorMsg('Please upload a .zip file');
      setStatus('error');
      return;
    }
    setStatus('uploading');
    setProgress(0);
    setErrorMsg('');

    const interval = setInterval(() => setProgress(p => Math.min(p + 5, 85)), 400);

    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('provider', 'gemini');
      const res = await fetch(`${API_BASE}/api/index`, { method: 'POST', body: formData });
      if (!res.ok) throw new Error(await res.text());
      clearInterval(interval);
      setProgress(100);
      setStatus('success');
      setTimeout(() => router.push('/chat'), 800);
    } catch (err: any) {
      clearInterval(interval);
      setStatus('error');
      setErrorMsg(err.message || 'Upload failed');
    }
  }, [router]);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const files = e.dataTransfer.files;
    if (files.length > 0) handleUpload(files[0]);
  }, [handleUpload]);

  return (
    <div className="flex-1 flex flex-col items-center justify-center p-8">
      {/* Hero */}
      <motion.div
        initial={{ opacity: 0, y: 30 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
        className="text-center mb-10"
      >
        <motion.div
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          transition={{ delay: 0.2, type: 'spring', stiffness: 200 }}
          className="w-24 h-24 mx-auto mb-6 rounded-2xl bg-gradient-to-br from-sky-400 to-violet-500 flex items-center justify-center shadow-lg shadow-sky-500/30"
        >
          <span className="text-5xl">🧠</span>
        </motion.div>

        <h1 className="text-4xl font-bold bg-gradient-to-r from-sky-400 to-violet-400 bg-clip-text text-transparent mb-4">
          CodeCritic AI
        </h1>
        <p className="text-slate-400 text-lg max-w-md">
          AI-powered codebase analysis. Connect a GitHub repo or upload a ZIP to get started.
        </p>
      </motion.div>

      {/* Mode Toggle */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.3 }}
        className="flex gap-2 mb-6 bg-slate-900/60 border border-white/10 rounded-xl p-1"
      >
        {(['github', 'zip'] as const).map((m) => (
          <button
            key={m}
            onClick={() => { setMode(m); setStatus('idle'); setErrorMsg(''); }}
            className={`flex items-center gap-2 px-5 py-2 rounded-lg text-sm font-medium transition-all duration-200 ${
              mode === m
                ? 'bg-gradient-to-r from-sky-500 to-violet-500 text-white shadow'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            {m === 'github' ? <Github className="w-4 h-4" /> : <Upload className="w-4 h-4" />}
            {m === 'github' ? 'GitHub URL' : 'Upload ZIP'}
          </button>
        ))}
      </motion.div>

      {/* Input Area */}
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ delay: 0.35, duration: 0.5 }}
        className="w-full max-w-2xl"
      >
        {status === 'uploading' ? (
          <div className="bg-slate-900/60 backdrop-blur-xl border border-white/10 rounded-2xl p-10 text-center">
            <Loader2 className="w-12 h-12 mx-auto mb-4 text-sky-400 animate-spin" />
            <p className="text-slate-300 mb-4">Indexing codebase with AI...</p>
            <div className="w-full bg-slate-700 rounded-full h-2">
              <motion.div
                className="bg-gradient-to-r from-sky-400 to-violet-500 h-2 rounded-full"
                animate={{ width: `${progress}%` }}
                transition={{ duration: 0.3 }}
              />
            </div>
            <p className="text-sm text-slate-500 mt-2">{progress}%</p>
          </div>
        ) : status === 'success' ? (
          <div className="bg-slate-900/60 backdrop-blur-xl border border-emerald-500/30 rounded-2xl p-10 text-center">
            <CheckCircle className="w-12 h-12 mx-auto mb-4 text-emerald-400" />
            <p className="text-slate-200 font-semibold">Indexed successfully! Redirecting...</p>
          </div>
        ) : mode === 'github' ? (
          <form onSubmit={handleGithubSubmit} className="flex flex-col gap-3">
            <div className="flex gap-3">
              <input
                type="text"
                value={githubUrl}
                onChange={(e) => setGithubUrl(e.target.value)}
                placeholder="https://github.com/owner/repo"
                className="flex-1 bg-slate-900/60 backdrop-blur-xl border border-white/10 rounded-xl px-5 py-4 text-slate-200 placeholder:text-slate-500 outline-none focus:border-sky-500/50 transition-colors"
              />
              <motion.button
                whileHover={{ scale: 1.03 }}
                whileTap={{ scale: 0.97 }}
                type="submit"
                disabled={!githubUrl.trim()}
                className="flex items-center gap-2 px-6 py-4 bg-gradient-to-r from-sky-500 to-violet-500 rounded-xl font-semibold disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Analyze <ArrowRight className="w-4 h-4" />
              </motion.button>
            </div>
            {status === 'error' && (
              <div className="flex items-center gap-2 text-red-400 text-sm px-1">
                <AlertCircle className="w-4 h-4" /> {errorMsg}
              </div>
            )}
          </form>
        ) : (
          <div
            onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
            onDragLeave={() => setIsDragging(false)}
            onDrop={handleDrop}
            className={`p-12 rounded-2xl border-2 border-dashed transition-all duration-300 cursor-pointer text-center ${
              isDragging
                ? 'border-sky-400 bg-sky-500/10 scale-105'
                : 'border-slate-600 hover:border-sky-500/50 hover:bg-slate-800/30'
            }`}
          >
            <motion.div animate={{ y: isDragging ? -10 : 0 }} className="mb-6">
              <Upload className="w-16 h-16 mx-auto text-slate-500" />
            </motion.div>
            <p className="text-xl text-slate-300 mb-2">Drop your ZIP here</p>
            <p className="text-slate-500 mb-6">or click to browse</p>
            <input
              type="file"
              accept=".zip"
              onChange={(e) => e.target.files?.[0] && handleUpload(e.target.files[0])}
              className="hidden"
              id="file-input"
            />
            <label
              htmlFor="file-input"
              className="inline-flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-sky-500 to-violet-500 rounded-xl font-semibold hover:opacity-90 transition-opacity cursor-pointer"
            >
              <Folder className="w-5 h-5" /> Browse Files
            </label>
            {status === 'error' && (
              <p className="mt-4 text-red-400 text-sm flex items-center justify-center gap-1">
                <AlertCircle className="w-4 h-4" /> {errorMsg}
              </p>
            )}
          </div>
        )}
      </motion.div>

      {/* Features */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.5 }}
        className="mt-10 flex gap-6"
      >
        {[
          { icon: '💬', label: 'Chat' },
          { icon: '🔍', label: 'Search' },
          { icon: '🔧', label: 'Refactor' },
          { icon: '✨', label: 'Generate' },
        ].map((feature, i) => (
          <motion.div
            key={feature.label}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.6 + i * 0.1 }}
            className="bg-slate-900/60 backdrop-blur-xl border border-white/10 rounded-2xl p-6 text-center min-w-[100px]"
          >
            <span className="text-2xl mb-2 block">{feature.icon}</span>
            <span className="text-sm text-slate-400">{feature.label}</span>
          </motion.div>
        ))}
      </motion.div>
    </div>
  );
}
