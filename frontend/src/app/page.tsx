'use client';

import { motion } from 'framer-motion';
import { useState, useCallback } from 'react';
import { Upload, Folder, FileCode, ArrowRight, Loader2 } from 'lucide-react';

export default function HomePage() {
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);

    const files = e.dataTransfer.files;
    if (files.length > 0) {
      handleUpload(files[0]);
    }
  }, []);

  const handleUpload = async (file: File) => {
    setIsUploading(true);

    // Simulate progress
    for (let i = 0; i <= 100; i += 10) {
      await new Promise(r => setTimeout(r, 200));
      setUploadProgress(i);
    }

    // TODO: Actually upload to backend
    setTimeout(() => {
      setIsUploading(false);
      window.location.href = '/chat';
    }, 500);
  };

  return (
    <div className="flex-1 flex flex-col items-center justify-center p-8">
      {/* Hero Section */}
      <motion.div
        initial={{ opacity: 0, y: 30 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
        className="text-center mb-12"
      >
        <motion.div
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          transition={{ delay: 0.2, type: 'spring', stiffness: 200 }}
          className="w-24 h-24 mx-auto mb-6 rounded-2xl bg-gradient-to-br from-sky-400 to-violet-500 flex items-center justify-center shadow-lg shadow-sky-500/30"
        >
          <span className="text-5xl">🕷️</span>
        </motion.div>

        <h1 className="text-4xl font-bold bg-gradient-to-r from-sky-400 to-violet-400 bg-clip-text text-transparent mb-4">
          CodeCritic AI
        </h1>
        <p className="text-slate-400 text-lg max-w-md">
          AI-powered codebase assistant. Upload your project and start exploring.
        </p>
      </motion.div>

      {/* Upload Zone */}
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ delay: 0.3, duration: 0.5 }}
        onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={handleDrop}
        className={`
          w-full max-w-2xl p-12 rounded-2xl border-2 border-dashed 
          transition-all duration-300 cursor-pointer
          ${isDragging
            ? 'border-sky-400 bg-sky-500/10 scale-105'
            : 'border-slate-600 hover:border-sky-500/50 hover:bg-slate-800/30'
          }
        `}
      >
        {isUploading ? (
          <div className="text-center">
            <Loader2 className="w-12 h-12 mx-auto mb-4 text-sky-400 animate-spin" />
            <p className="text-slate-300 mb-4">Processing codebase...</p>
            <div className="w-full bg-slate-700 rounded-full h-2">
              <motion.div
                className="bg-gradient-to-r from-sky-400 to-violet-500 h-2 rounded-full"
                initial={{ width: 0 }}
                animate={{ width: `${uploadProgress}%` }}
                transition={{ duration: 0.3 }}
              />
            </div>
            <p className="text-sm text-slate-500 mt-2">{uploadProgress}%</p>
          </div>
        ) : (
          <div className="text-center">
            <motion.div
              animate={{ y: isDragging ? -10 : 0 }}
              className="mb-6"
            >
              <Upload className="w-16 h-16 mx-auto text-slate-500" />
            </motion.div>
            <p className="text-xl text-slate-300 mb-2">
              Drop your project here
            </p>
            <p className="text-slate-500 mb-6">
              or click to select a ZIP file
            </p>

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
              <Folder className="w-5 h-5" />
              Browse Files
            </label>
          </div>
        )}
      </motion.div>

      {/* Features */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.5 }}
        className="mt-12 flex gap-6"
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
