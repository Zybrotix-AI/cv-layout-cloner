import { useState } from 'react';
import { getDownloadUrl } from '../lib/api';

/**
 * Download buttons for .docx and .pdf output files.
 *
 * @param {Object} props
 * @param {string} props.docxUrl - Download path for .docx
 * @param {string} props.pdfUrl - Download path for .pdf
 * @param {string|null} props.docxNote - Optional note about docx quality
 * @param {number} props.processingTime - Processing time in seconds
 * @param {string[]} props.sectionsFound - List of content sections found
 */
export default function DownloadButtons({
  docxUrl,
  pdfUrl,
  docxNote,
  processingTime,
  sectionsFound = [],
}) {
  const [downloadingPdf, setDownloadingPdf] = useState(false);
  const [downloadingDocx, setDownloadingDocx] = useState(false);

  const handleDownload = async (url, filename, setStatus) => {
    setStatus(true);
    try {
      const fullUrl = getDownloadUrl(url);
      const response = await fetch(fullUrl, {
        headers: { 'ngrok-skip-browser-warning': '69420' }
      });
      if (!response.ok) throw new Error('Download failed');
      const blob = await response.blob();
      const blobUrl = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.style.display = 'none';
      a.href = blobUrl;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(blobUrl);
      document.body.removeChild(a);
    } catch (err) {
      console.error('Blob download failed, falling back to direct navigation:', err);
      // Fallback
      window.open(getDownloadUrl(url), '_blank');
    } finally {
      setStatus(false);
    }
  };

  return (
    <div className="glass-card p-5 animate-slide-up" style={{ animationDelay: '0.1s' }}>
      {/* Download buttons */}
      <div className="flex gap-3 mb-4">
        <button
          onClick={() => handleDownload(pdfUrl, 'Converted_CV.pdf', setDownloadingPdf)}
          disabled={downloadingPdf}
          className="btn-primary flex-1 text-center justify-center disabled:opacity-75 disabled:cursor-wait"
        >
          <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
            <polyline points="7 10 12 15 17 10" />
            <line x1="12" y1="15" x2="12" y2="3" />
          </svg>
          {downloadingPdf ? 'Downloading...' : 'Download PDF'}
        </button>

        <button
          onClick={() => handleDownload(docxUrl, 'Converted_CV.docx', setDownloadingDocx)}
          disabled={downloadingDocx}
          className="btn-secondary flex-1 text-center justify-center disabled:opacity-75 disabled:cursor-wait"
        >
          <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
            <polyline points="7 10 12 15 17 10" />
            <line x1="12" y1="15" x2="12" y2="3" />
          </svg>
          {downloadingDocx ? 'Downloading...' : 'Download DOCX'}
        </button>
      </div>

      {/* DOCX quality note */}
      {docxNote && (
        <div className="flex items-start gap-2 p-3 rounded-xl bg-amber-500/[0.06] border border-amber-500/[0.12] mb-4">
          <svg className="w-4 h-4 text-amber-400 mt-0.5 shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="12" cy="12" r="10" />
            <line x1="12" y1="8" x2="12" y2="12" />
            <line x1="12" y1="16" x2="12.01" y2="16" />
          </svg>
          <p className="text-xs text-amber-400/80">{docxNote}</p>
        </div>
      )}

      {/* Metadata */}
      <div className="flex items-center justify-between text-xs text-white/30 pt-3 border-t border-white/[0.06]">
        <div className="flex items-center gap-1.5">
          <svg className="w-3 h-3" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="12" cy="12" r="10" />
            <polyline points="12 6 12 12 16 14" />
          </svg>
          <span>Processed in {processingTime}s</span>
        </div>

        {sectionsFound.length > 0 && (
          <span>{sectionsFound.length} sections mapped</span>
        )}
      </div>

      {/* Sections found */}
      {sectionsFound.length > 0 && (
        <div className="flex flex-wrap gap-1.5 mt-3">
          {sectionsFound.map((section, i) => (
            <span
              key={i}
              className="px-2 py-0.5 text-[10px] rounded-md bg-white/[0.04] text-white/30 border border-white/[0.06]"
            >
              {section}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}
