import { useCallback, useState } from 'react';

const ACCEPTED_TYPES = {
  'application/pdf': ['.pdf'],
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
  'image/png': ['.png'],
  'image/jpeg': ['.jpg', '.jpeg'],
};

const ACCEPTED_EXTENSIONS = ['.docx', '.pdf', '.png', '.jpg', '.jpeg'];

/**
 * Drag-and-drop file upload zone.
 *
 * @param {Object} props
 * @param {'content' | 'sample'} props.type - Which CV this zone is for
 * @param {File|null} props.file - Currently selected file
 * @param {function} props.onFileSelect - Callback when file is selected
 * @param {boolean} props.disabled - Whether the zone is disabled
 */
export default function UploadZone({ type, file, onFileSelect, disabled = false }) {
  const [isDragging, setIsDragging] = useState(false);

  const isContent = type === 'content';
  const label = isContent ? 'Your CV' : 'Template CV';
  const sublabel = isContent ? 'Content Source' : 'Design Source';
  const description = isContent
    ? 'Upload the CV with your information'
    : 'Upload the CV whose layout you want to clone';
  const icon = isContent ? ContentIcon : TemplateIcon;

  const handleDragOver = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    if (!disabled) setIsDragging(true);
  }, [disabled]);

  const handleDragLeave = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
    if (disabled) return;

    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile && isValidFile(droppedFile)) {
      onFileSelect(droppedFile);
    }
  }, [disabled, onFileSelect]);

  const handleClick = useCallback(() => {
    if (disabled) return;
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = ACCEPTED_EXTENSIONS.join(',');
    input.onchange = (e) => {
      const selectedFile = e.target.files[0];
      if (selectedFile && isValidFile(selectedFile)) {
        onFileSelect(selectedFile);
      }
    };
    input.click();
  }, [disabled, onFileSelect]);

  const handleRemove = useCallback((e) => {
    e.stopPropagation();
    onFileSelect(null);
  }, [onFileSelect]);

  const zoneClasses = [
    'upload-zone min-h-[220px]',
    isDragging ? 'upload-zone-active' : '',
    file ? 'upload-zone-filled' : '',
    disabled ? 'opacity-50 cursor-not-allowed' : '',
  ].filter(Boolean).join(' ');

  return (
    <div
      className={zoneClasses}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      onClick={handleClick}
    >
      {file ? (
        <FilePreview file={file} sublabel={sublabel} onRemove={handleRemove} />
      ) : (
        <EmptyState
          Icon={icon}
          label={label}
          sublabel={sublabel}
          description={description}
          isDragging={isDragging}
        />
      )}
    </div>
  );
}

function EmptyState({ Icon, label, sublabel, description, isDragging }) {
  return (
    <>
      <div className={`mb-4 p-4 rounded-2xl transition-all duration-300 ${
        isDragging
          ? 'bg-brand-500/20 scale-110'
          : 'bg-white/[0.04]'
      }`}>
        <Icon className="w-8 h-8 text-white/40" />
      </div>

      <div className="text-center">
        <p className="text-sm font-semibold text-white/70 mb-0.5">{label}</p>
        <p className="text-xs text-brand-400/70 font-medium mb-2">{sublabel}</p>
        <p className="text-xs text-white/30 max-w-[200px]">{description}</p>
      </div>

      <div className="mt-4 flex items-center gap-2 text-xs text-white/25">
        <span>.docx</span>
        <span className="w-1 h-1 rounded-full bg-white/20" />
        <span>.pdf</span>
        <span className="w-1 h-1 rounded-full bg-white/20" />
        <span>.png / .jpg</span>
      </div>
    </>
  );
}

function FilePreview({ file, sublabel, onRemove }) {
  const ext = file.name.split('.').pop()?.toUpperCase() || '?';
  const sizeKB = Math.round(file.size / 1024);
  const sizeLabel = sizeKB > 1024
    ? `${(sizeKB / 1024).toFixed(1)} MB`
    : `${sizeKB} KB`;

  const extColors = {
    DOCX: 'from-blue-500 to-blue-600',
    PDF: 'from-red-500 to-red-600',
    PNG: 'from-emerald-500 to-emerald-600',
    JPG: 'from-amber-500 to-amber-600',
    JPEG: 'from-amber-500 to-amber-600',
  };

  return (
    <div className="flex flex-col items-center gap-3 animate-fade-in">
      <div className="relative">
        <div className={`w-14 h-14 rounded-xl bg-gradient-to-br ${extColors[ext] || 'from-gray-500 to-gray-600'} flex items-center justify-center shadow-lg`}>
          <span className="text-white text-xs font-bold">{ext}</span>
        </div>
        <div className="absolute -top-1 -right-1 w-5 h-5 rounded-full bg-emerald-500 flex items-center justify-center">
          <svg className="w-3 h-3 text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
            <polyline points="20 6 9 17 4 12" />
          </svg>
        </div>
      </div>

      <div className="text-center">
        <p className="text-xs text-brand-400/70 font-medium mb-1">{sublabel}</p>
        <p className="text-sm font-medium text-white/80 truncate max-w-[200px]">{file.name}</p>
        <p className="text-xs text-white/30 mt-0.5">{sizeLabel}</p>
      </div>

      <button
        onClick={onRemove}
        className="text-xs text-white/30 hover:text-red-400 transition-colors duration-200 flex items-center gap-1"
      >
        <svg className="w-3 h-3" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <line x1="18" y1="6" x2="6" y2="18" />
          <line x1="6" y1="6" x2="18" y2="18" />
        </svg>
        Remove
      </button>
    </div>
  );
}

function isValidFile(file) {
  const ext = '.' + file.name.split('.').pop()?.toLowerCase();
  return ACCEPTED_EXTENSIONS.includes(ext);
}

function ContentIcon({ className }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
      <polyline points="14 2 14 8 20 8" />
      <line x1="16" y1="13" x2="8" y2="13" />
      <line x1="16" y1="17" x2="8" y2="17" />
      <polyline points="10 9 9 9 8 9" />
    </svg>
  );
}

function TemplateIcon({ className }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <rect x="3" y="3" width="18" height="18" rx="2" />
      <line x1="3" y1="9" x2="21" y2="9" />
      <line x1="9" y1="21" x2="9" y2="9" />
    </svg>
  );
}
