import { getDownloadUrl } from '../lib/api';

/**
 * Preview panel showing the conversion result.
 *
 * @param {Object} props
 * @param {string} props.previewUrl - URL to the preview image
 */
export default function PreviewPanel({ previewUrl }) {
  const fullUrl = getDownloadUrl(previewUrl);

  return (
    <div className="glass-card overflow-hidden animate-slide-up">
      {/* Preview header */}
      <div className="px-5 py-3 border-b border-white/[0.06] flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-emerald-400" />
          <span className="text-xs font-medium text-white/50">Preview</span>
        </div>
        <span className="text-xs text-white/25">First page</span>
      </div>

      {/* Preview image */}
      <div className="p-4 flex items-center justify-center bg-white/[0.01] min-h-[400px]">
        <div className="relative rounded-lg overflow-hidden shadow-2xl shadow-black/30 border border-white/[0.08] max-w-full">
          <img
            src={fullUrl}
            alt="Conversion preview — first page of the generated CV"
            className="max-h-[600px] w-auto object-contain"
            loading="lazy"
          />
          {/* Subtle overlay for depth */}
          <div className="absolute inset-0 pointer-events-none ring-1 ring-inset ring-white/[0.05] rounded-lg" />
        </div>
      </div>
    </div>
  );
}
