/**
 * API client for communicating with the CV Layout Cloner backend.
 */

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:2222/api';

/**
 * Upload two CVs for conversion.
 * @param {File} contentCV - User's CV with content
 * @param {File} sampleCV - Template CV with desired layout
 * @param {function} onProgress - Progress callback (0-100)
 * @returns {Promise<Object>} Conversion result
 */
export async function convertCV(contentCV, sampleCV, onProgress) {
  const formData = new FormData();
  formData.append('content_cv', contentCV);
  formData.append('sample_cv', sampleCV);

  // 1. Start the job
  const startResponse = await fetch(`${API_BASE}/convert`, {
    method: 'POST',
    headers: { 'ngrok-skip-browser-warning': '69420' },
    body: formData,
  });

  if (!startResponse.ok) {
    let errorMsg = 'Failed to start conversion';
    try {
      const errorData = await startResponse.json();
      errorMsg = errorData.detail || errorData.error || errorMsg;
    } catch (e) {}
    throw new Error(errorMsg);
  }

  const { job_id } = await startResponse.json();

  // 2. Poll for status
  return new Promise((resolve, reject) => {
    const pollInterval = setInterval(async () => {
      try {
        const statusResponse = await fetch(`${API_BASE}/status/${job_id}`, {
          headers: { 'ngrok-skip-browser-warning': '69420' },
        });

        if (!statusResponse.ok) {
          throw new Error('Failed to fetch status');
        }

        const statusData = await statusResponse.json();

        // Trigger progress callback with full status object
        if (onProgress) {
          onProgress(statusData);
        }

        if (statusData.status === 'done') {
          clearInterval(pollInterval);
          resolve(statusData.result);
        } else if (statusData.status === 'error') {
          clearInterval(pollInterval);
          reject(new Error(statusData.error || 'Conversion failed during processing'));
        }
      } catch (err) {
        // Don't kill the polling on a single network blip, just log it.
        // If it persists, maybe add a retry counter.
        console.warn('Status polling error:', err);
      }
    }, 1000); // Poll every 1 second
  });
}

/**
 * Get the full download URL for a file.
 * @param {string} path - Relative download path from the API response
 * @returns {string} Full URL
 */
export function getDownloadUrl(path) {
  if (!path) return '';
  if (path.startsWith('http')) return path;
  let base = import.meta.env.VITE_API_URL || 'http://localhost:2222';
  if (base.endsWith('/api')) {
      base = base.slice(0, -4);
  }
  return `${base}${path}`;
}

/**
 * Check backend health.
 * @returns {Promise<Object>} Health status
 */
export async function checkHealth() {
  const response = await fetch(`${API_BASE}/health`, {
    headers: { 'ngrok-skip-browser-warning': '69420' }
  });
  if (!response.ok) throw new Error('Backend health check failed');
  return response.json();
}
