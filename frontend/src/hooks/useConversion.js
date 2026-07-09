import { useState, useCallback, useRef } from 'react';
import { convertCV } from '../lib/api';

/**
 * Hook for managing the CV conversion workflow.
 * Handles file uploads, API communication, progress tracking, and results.
 */
export function useConversion() {
  const [contentFile, setContentFile] = useState(null);
  const [sampleFile, setSampleFile] = useState(null);
  const [status, setStatus] = useState('idle'); // idle | uploading | processing | done | error
  const [progress, setProgress] = useState(0);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const abortRef = useRef(null);

  const canConvert = contentFile && sampleFile && status !== 'uploading' && status !== 'processing';

  const startConversion = useCallback(async () => {
    if (!contentFile || !sampleFile) return;

    setStatus('uploading');
    setProgress(0);
    setError(null);
    setResult(null);

    try {
      const response = await convertCV(
        contentFile,
        sampleFile,
        (pct) => {
          setProgress(pct);
          if (pct > 50 && status !== 'processing') {
            setStatus('processing');
          }
        }
      );

      setResult(response);
      setStatus('done');
      setProgress(100);
    } catch (err) {
      setError(err.message || 'Conversion failed');
      setStatus('error');
    }
  }, [contentFile, sampleFile]);

  const reset = useCallback(() => {
    setContentFile(null);
    setSampleFile(null);
    setStatus('idle');
    setProgress(0);
    setResult(null);
    setError(null);
  }, []);

  const clearResult = useCallback(() => {
    setStatus('idle');
    setProgress(0);
    setResult(null);
    setError(null);
  }, []);

  return {
    // State
    contentFile,
    sampleFile,
    status,
    progress,
    result,
    error,
    canConvert,

    // Actions
    setContentFile,
    setSampleFile,
    startConversion,
    reset,
    clearResult,
  };
}
