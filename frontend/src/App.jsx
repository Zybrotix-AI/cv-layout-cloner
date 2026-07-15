import Header from './components/Header';
import UploadZone from './components/UploadZone';
import ProcessingStatus from './components/ProcessingStatus';
import PreviewPanel from './components/PreviewPanel';
import FidelityBadge from './components/FidelityBadge';
import DownloadButtons from './components/DownloadButtons';
import { useConversion } from './hooks/useConversion';

export default function App() {
  const {
    contentFile,
    sampleFile,
    status,
    progress,
    stepLabel,
    eta,
    result,
    error,
    canConvert,
    setContentFile,
    setSampleFile,
    startConversion,
    reset,
  } = useConversion();

  const isProcessing = status === 'uploading' || status === 'processing';
  const isDone = status === 'done' && result;

  return (
    <div className="min-h-screen bg-grid relative">
      {/* Background glow */}
      <div className="bg-glow" />

      {/* Header */}
      <Header />

      {/* Main content */}
      <main className="relative z-10 px-6 pb-16">
        <div className="max-w-7xl mx-auto">

          {/* Hero section */}
          <div className="text-center mt-8 mb-12 animate-fade-in">
            <h2 className="font-display text-4xl sm:text-5xl font-bold tracking-tight mb-4">
              <span className="text-white">Clone any CV </span>
              <span className="gradient-text">layout instantly</span>
            </h2>
            <p className="text-lg text-white/40 max-w-xl mx-auto leading-relaxed">
              Upload your CV and a template — we'll re-render your content
              in the template's exact design. Same fonts, colors, spacing.
              Only the words change.
            </p>
          </div>

          {/* Two-column layout */}
          <div className="grid lg:grid-cols-2 gap-8">

            {/* Left Column — Upload & Controls */}
            <div className="space-y-6">

              {/* Upload zones */}
              <div className="grid sm:grid-cols-2 gap-4">
                <UploadZone
                  type="content"
                  file={contentFile}
                  onFileSelect={setContentFile}
                  disabled={isProcessing}
                />
                <UploadZone
                  type="sample"
                  file={sampleFile}
                  onFileSelect={setSampleFile}
                  disabled={isProcessing}
                />
              </div>

              {/* Conversion button */}
              <div className="flex gap-3">
                <button
                  onClick={startConversion}
                  disabled={!canConvert}
                  className="btn-primary flex-1"
                >
                  {isProcessing ? (
                    <>
                      <svg className="w-4 h-4 animate-spin" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <path d="M21 12a9 9 0 1 1-6.219-8.56" />
                      </svg>
                      Processing...
                    </>
                  ) : (
                    <>
                      <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <path d="M4 12v8a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-8" />
                        <polyline points="16 6 12 2 8 6" />
                        <line x1="12" y1="2" x2="12" y2="15" />
                      </svg>
                      Clone Layout
                    </>
                  )}
                </button>

                {(contentFile || sampleFile || isDone) && (
                  <button
                    onClick={reset}
                    disabled={isProcessing}
                    className="btn-secondary"
                    title="Start over"
                  >
                    <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <polyline points="1 4 1 10 7 10" />
                      <path d="M3.51 15a9 9 0 1 0 2.13-9.36L1 10" />
                    </svg>
                  </button>
                )}
              </div>

              {/* Processing status */}
              <ProcessingStatus status={status} progress={progress} stepLabel={stepLabel} eta={eta} error={error} />

              {/* Results — Fidelity badge & downloads */}
              {isDone && (
                <div className="space-y-4">
                  <FidelityBadge
                    tier={result.fidelity_tier}
                    label={result.tier_label}
                  />
                  <DownloadButtons
                    docxUrl={result.docx_download_url}
                    pdfUrl={result.pdf_download_url}
                    docxNote={result.docx_note}
                    processingTime={result.processing_time_seconds}
                    sectionsFound={result.content_sections_found}
                  />
                </div>
              )}
            </div>

            {/* Right Column — Preview */}
            <div>
              {isDone ? (
                <PreviewPanel previewUrl={result.preview_image_url} />
              ) : (
                <div className="glass-card flex items-center justify-center min-h-[500px]">
                  <div className="text-center px-8">
                    {isProcessing ? (
                      <>
                        <div className="w-16 h-16 mx-auto mb-6 rounded-2xl bg-brand-500/10 flex items-center justify-center animate-pulse-glow">
                          <svg className="w-7 h-7 text-brand-400 animate-spin" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                            <path d="M21 12a9 9 0 1 1-6.219-8.56" />
                          </svg>
                        </div>
                        <p className="text-sm text-white/40">Generating preview...</p>
                      </>
                    ) : (
                      <>
                        {/* Skeleton Document Layout */}
                        <div className="w-full max-w-[280px] mx-auto bg-white/[0.02] rounded-xl border border-white/10 p-6 flex flex-col gap-4 shadow-2xl relative overflow-hidden">
                          {/* Shimmer effect */}
                          <div className="absolute inset-0 -translate-x-full animate-[shimmer_2s_infinite] bg-gradient-to-r from-transparent via-white/5 to-transparent z-10" />
                          
                          {/* Header block */}
                          <div className="flex gap-4 items-center border-b border-white/5 pb-4">
                            <div className="w-12 h-12 rounded-full bg-white/5" />
                            <div className="space-y-2 flex-1">
                              <div className="h-4 bg-white/10 rounded-md w-3/4" />
                              <div className="h-3 bg-white/5 rounded-md w-1/2" />
                            </div>
                          </div>
                          
                          {/* Content blocks */}
                          <div className="space-y-3 pt-2">
                            <div className="h-3 bg-white/5 rounded-md w-full" />
                            <div className="h-3 bg-white/5 rounded-md w-5/6" />
                            <div className="h-3 bg-white/5 rounded-md w-4/6" />
                          </div>
                          
                          <div className="space-y-3 pt-2">
                            <div className="h-3 bg-white/10 rounded-md w-1/3 mb-2" />
                            <div className="h-3 bg-white/5 rounded-md w-full" />
                            <div className="h-3 bg-white/5 rounded-md w-11/12" />
                          </div>
                        </div>
                        
                        <div className="mt-8 text-center">
                          <p className="text-sm font-medium text-white/40 mb-1">Preview will appear here</p>
                          <p className="text-xs text-white/20">Upload both CVs and click "Clone Layout"</p>
                        </div>
                      </>
                    )}
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* How it works section */}
          <div className="mt-20 animate-fade-in" style={{ animationDelay: '0.3s' }}>
            <h3 className="text-center text-lg font-display font-semibold text-white/60 mb-8">
              How it works
            </h3>
            <div className="grid sm:grid-cols-3 gap-6">
              <StepCard
                number="1"
                title="Upload"
                description="Drop your CV (content) and a template CV (design) into the upload zones"
              />
              <StepCard
                number="2"
                title="Analyze & Map"
                description="AI extracts your content and maps it to the template's layout structure"
              />
              <StepCard
                number="3"
                title="Download"
                description="Get your content perfectly re-rendered in the template's exact design"
              />
            </div>
          </div>

        </div>
      </main>
    </div>
  );
}

function StepCard({ number, title, description }) {
  return (
    <div className="glass-card-hover p-6 text-center">
      <div className="w-10 h-10 mx-auto mb-4 rounded-xl bg-gradient-to-br from-brand-500/20 to-purple-500/20 border border-brand-500/20 flex items-center justify-center">
        <span className="text-sm font-bold gradient-text">{number}</span>
      </div>
      <h4 className="text-sm font-semibold text-white/80 mb-2">{title}</h4>
      <p className="text-xs text-white/35 leading-relaxed">{description}</p>
    </div>
  );
}
