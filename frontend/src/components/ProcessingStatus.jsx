/**
 * Processing status indicator with progress bar and animated states.
 *
 * @param {Object} props
 * @param {'idle'|'uploading'|'processing'|'done'|'error'} props.status
 * @param {number} props.progress - 0-100
 * @param {string|null} props.error - Error message
 */
export default function ProcessingStatus({ status, progress, stepLabel, eta, error }) {
  if (status === 'idle') return null;

  const statusConfig = {
    uploading: {
      label: 'Uploading files...',
      sublabel: 'Sending your CVs to the server',
      icon: UploadIcon,
      color: 'text-brand-400',
    },
    processing: {
      label: 'Processing...',
      sublabel: 'Analyzing layouts and mapping content',
      icon: ProcessIcon,
      color: 'text-purple-400',
    },
    done: {
      label: 'Conversion complete!',
      sublabel: 'Your CV has been re-rendered',
      icon: DoneIcon,
      color: 'text-emerald-400',
    },
    error: {
      label: 'Conversion failed',
      sublabel: error || 'An unexpected error occurred',
      icon: ErrorIcon,
      color: 'text-red-400',
    },
  };

  const config = statusConfig[status];
  if (!config) return null;

  const Icon = config.icon;

  return (
    <div className="glass-card p-5 animate-slide-up">
      <div className="flex items-center gap-4">
        {/* Animated icon */}
        <div className={`p-2.5 rounded-xl ${
          status === 'error' ? 'bg-red-500/10' :
          status === 'done' ? 'bg-emerald-500/10' :
          'bg-brand-500/10'
        }`}>
          <Icon className={`w-5 h-5 ${config.color} ${
            status === 'processing' ? 'animate-spin' :
            status === 'uploading' ? 'animate-pulse' :
            ''
          }`} />
        </div>

        {/* Labels */}
        <div className="flex-1 min-w-0">
          <p className={`text-sm font-semibold ${config.color}`}>
            {config.label}
          </p>
          <p className="text-xs text-white/40 mt-0.5 truncate">
            {config.sublabel}
          </p>
        </div>

        {/* Progress percentage */}
        {(status === 'started' || status === 'uploading' || status === 'processing') && (
          <span className="text-sm font-mono text-white/50">
            {Math.round(progress)}%
          </span>
        )}
      </div>

      {/* Progress bar */}
      {(status === 'started' || status === 'uploading' || status === 'processing') && (
        <div className="progress-bar mt-4">
          <div
            className="progress-bar-fill transition-all duration-500 ease-out"
            style={{ width: `${progress}%` }}
          />
        </div>
      )}

      {/* Dynamic Processing Step */}
      {(status === 'started' || status === 'uploading' || status === 'processing') && (
        <div className="mt-5 flex items-center justify-between border-t border-white/5 pt-4">
          <div className="flex items-center gap-3">
            <div className="w-4 h-4 rounded-full border-2 border-brand-400 border-t-transparent animate-spin" />
            <span className="text-sm text-white/70">
              {stepLabel || 'Working...'}
            </span>
          </div>
          
          {eta !== null && eta > 0 && (
            <div className="text-xs font-mono text-white/40 bg-white/5 px-2 py-1 rounded">
              ~{eta}s remaining
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function StepIndicator({ label, done, active }) {
  return (
    <div className="flex items-center gap-2.5">
      {done ? (
        <div className="w-4 h-4 rounded-full bg-emerald-500/20 flex items-center justify-center">
          <svg className="w-2.5 h-2.5 text-emerald-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
            <polyline points="20 6 9 17 4 12" />
          </svg>
        </div>
      ) : active ? (
        <div className="w-4 h-4 rounded-full border-2 border-brand-400 border-t-transparent animate-spin" />
      ) : (
        <div className="w-4 h-4 rounded-full border border-white/10" />
      )}
      <span className={`text-xs ${done ? 'text-emerald-400/70' : active ? 'text-white/60' : 'text-white/25'}`}>
        {label}
      </span>
    </div>
  );
}

function UploadIcon({ className }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <polyline points="16 16 12 12 8 16" />
      <line x1="12" y1="12" x2="12" y2="21" />
      <path d="M20.39 18.39A5 5 0 0 0 18 9h-1.26A8 8 0 1 0 3 16.3" />
    </svg>
  );
}

function ProcessIcon({ className }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M21 12a9 9 0 1 1-6.219-8.56" />
    </svg>
  );
}

function DoneIcon({ className }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
      <polyline points="22 4 12 14.01 9 11.01" />
    </svg>
  );
}

function ErrorIcon({ className }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="10" />
      <line x1="15" y1="9" x2="9" y2="15" />
      <line x1="9" y1="9" x2="15" y2="15" />
    </svg>
  );
}
