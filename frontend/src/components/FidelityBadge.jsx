/**
 * Fidelity tier badge.
 * Shows which quality tier the conversion result belongs to.
 *
 * @param {Object} props
 * @param {1|2|3} props.tier - Fidelity tier number
 * @param {string} props.label - Human-readable tier label
 */
export default function FidelityBadge({ tier, label }) {
  const config = {
    1: {
      className: 'badge-tier1',
      icon: ExactIcon,
      description: 'Sample was .docx — formatting preserved by construction',
    },
    2: {
      className: 'badge-tier2',
      icon: NearExactIcon,
      description: 'Sample was text-based PDF — text replaced at original coordinates',
    },
    3: {
      className: 'badge-tier3',
      icon: BestEffortIcon,
      description: 'Sample was image/scanned — layout reconstructed from visual analysis',
    },
  };

  const { className, icon: Icon, description } = config[tier] || config[3];

  return (
    <div className="animate-fade-in">
      <div className={`${className} mb-2`}>
        <Icon className="w-3.5 h-3.5" />
        <span>{label}</span>
      </div>
      <p className="text-xs text-white/30 pl-1">{description}</p>
    </div>
  );
}

function ExactIcon({ className }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
      <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
      <polyline points="22 4 12 14.01 9 11.01" />
    </svg>
  );
}

function NearExactIcon({ className }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="10" />
      <polyline points="12 6 12 12 16 14" />
    </svg>
  );
}

function BestEffortIcon({ className }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="10" />
      <line x1="12" y1="8" x2="12" y2="12" />
      <line x1="12" y1="16" x2="12.01" y2="16" />
    </svg>
  );
}
