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

  const xhr = new XMLHttpRequest();
  
  return new Promise((resolve, reject) => {
    xhr.upload.addEventListener('progress', (e) => {
      if (e.lengthComputable && onProgress) {
        const percent = Math.round((e.loaded / e.total) * 50); // Upload is 0-50%
        onProgress(percent);
      }
    });

    xhr.addEventListener('load', () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        try {
          const response = JSON.parse(xhr.responseText);
          onProgress?.(100);
          resolve(response);
        } catch (e) {
          reject(new Error('Invalid response from server'));
        }
      } else {
        try {
          const error = JSON.parse(xhr.responseText);
          reject(new Error(error.detail || error.error || `Server error: ${xhr.status}`));
        } catch {
          reject(new Error(`Server error: ${xhr.status}`));
        }
      }
    });

    xhr.addEventListener('error', () => {
      reject(new Error('Network error — is the backend running?'));
    });

    xhr.addEventListener('timeout', () => {
      reject(new Error('Request timed out — the conversion may take up to 2 minutes'));
    });

    xhr.open('POST', `${API_BASE}/convert`);
    xhr.setRequestHeader('ngrok-skip-browser-warning', '69420');
    xhr.timeout = 180000; // 3 minute timeout
    xhr.send(formData);

    // Simulate processing progress after upload completes
    let processingInterval;
    xhr.upload.addEventListener('loadend', () => {
      let progress = 50;
      processingInterval = setInterval(() => {
        if (progress < 90) {
          progress += Math.random() * 5;
          onProgress?.(Math.min(90, Math.round(progress)));
        }
      }, 1000);
    });

    const originalLoad = xhr.onload;
    xhr.addEventListener('loadend', () => {
      clearInterval(processingInterval);
    });
  });
}

/**
 * Get the full download URL for a file.
 * @param {string} path - Relative download path from the API response
 * @returns {string} Full URL
 */
export function getDownloadUrl(path) {
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
