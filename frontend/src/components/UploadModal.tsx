import React, { useState } from 'react';
import { Upload, FileText, CheckCircle2, X, Cpu, ShieldCheck, Loader2 } from 'lucide-react';
import { api } from '../api/client';
import { useActiveProject } from '../api/hooks';

interface UploadModalProps {
  isOpen: boolean;
  onClose: () => void;
  onStartScan: () => void;
}

export const UploadModal: React.FC<UploadModalProps> = ({ isOpen, onClose, onStartScan }) => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [preset, setPreset] = useState<'incose' | 'ieee' | 'agile'>('incose');
  const [isDragging, setIsDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const { active, reload } = useActiveProject();

  if (!isOpen) return null;

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      setSelectedFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setSelectedFile(e.target.files[0]);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedFile || uploading) return;
    setUploading(true);
    setError(null);
    setProgress(0);
    try {
      await api.uploadDocument(selectedFile, {
        // Upload into the active project when one exists; else a new project
        // is created server-side from the filename.
        projectId: active?.id,
        onProgress: setProgress,
      });
      reload();
      onStartScan();
      onClose();
    } catch (err) {
      setError((err as Error).message || 'Upload failed');
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-md animate-in fade-in duration-200">
      <div className="fixed inset-0" onClick={onClose} />

      <div className="relative w-full max-w-xl bg-surface-container-low border border-surface-container-high rounded-2xl shadow-2xl overflow-hidden z-10 flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-surface-container-high bg-surface-container-lowest">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-primary-container/20 border border-primary/30 flex items-center justify-center text-primary">
              <Upload className="w-5 h-5" />
            </div>
            <div className="flex flex-col">
              <h2 className="font-headline-md text-headline-md font-semibold text-on-surface">Upload Specification</h2>
              <span className="font-code-sm text-code-sm text-outline">
                {active ? `Target project: ${active.name}` : 'A new project will be created'}
              </span>
            </div>
          </div>
          <button 
            onClick={onClose} 
            className="p-1.5 rounded-lg text-outline hover:text-on-surface hover:bg-surface-container transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 flex flex-col gap-6">
          {/* Drop Zone */}
          <div
            onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
            onDragLeave={() => setIsDragging(false)}
            onDrop={handleDrop}
            className={`
              border-2 border-dashed rounded-xl p-8 flex flex-col items-center justify-center text-center transition-all cursor-pointer relative
              ${isDragging ? 'border-primary bg-primary/5' : 'border-surface-container-high bg-surface-container-lowest hover:border-outline'}
              ${selectedFile ? 'border-tertiary bg-tertiary/5' : ''}
            `}
          >
            <input
              type="file"
              accept=".pdf,.docx,.txt,.md"
              onChange={handleFileChange}
              disabled={uploading}
              className="absolute inset-0 opacity-0 cursor-pointer"
            />

            {selectedFile ? (
              <div className="flex flex-col items-center gap-2">
                <CheckCircle2 className="w-10 h-10 text-tertiary" />
                <span className="font-body-md text-body-md font-semibold text-on-surface">{selectedFile.name}</span>
                <span className="font-code-sm text-code-sm text-outline">
                  {(selectedFile.size / 1024 / 1024).toFixed(2)} MB • Ready for analysis
                </span>
              </div>
            ) : (
              <div className="flex flex-col items-center gap-2">
                <Upload className="w-10 h-10 text-outline mb-1" />
                <span className="font-body-md text-body-md font-medium text-on-surface">
                  Drag and drop your SRS document here, or <span className="text-primary font-semibold underline">browse</span>
                </span>
                <span className="font-code-sm text-code-sm text-outline">Supports PDF, DOCX, Markdown</span>
              </div>
            )}
          </div>

          {/* Upload progress */}
          {uploading && (
            <div className="flex items-center gap-3">
              <Loader2 className="w-4 h-4 text-primary animate-spin" />
              <div className="flex-1 h-2 rounded-full bg-surface-container-highest overflow-hidden">
                <div className="h-full bg-primary transition-all" style={{ width: `${progress}%` }} />
              </div>
              <span className="font-code-sm text-code-sm text-on-surface-variant">{progress}%</span>
            </div>
          )}

          {error && (
            <div className="p-3 rounded-lg bg-error-container/30 border border-error/40">
              <span className="font-body-sm text-body-sm text-error">{error}</span>
            </div>
          )}

          {/* Engine Preset Selector */}
          <div className="flex flex-col gap-2">
            <span className="font-label-caps text-label-caps uppercase text-outline tracking-wider">Verification Engine Rule Set</span>
            <div className="grid grid-cols-3 gap-3">
              <button
                type="button"
                onClick={() => setPreset('incose')}
                disabled={uploading}
                className={`
                  p-3 rounded-xl border flex flex-col items-start gap-1 transition-all text-left
                  ${preset === 'incose' ? 'border-primary bg-primary-container/20 text-on-surface' : 'border-surface-container-high bg-surface-container hover:bg-surface-container-high text-on-surface-variant'}
                `}
              >
                <ShieldCheck className={`w-4 h-4 ${preset === 'incose' ? 'text-primary' : 'text-outline'}`} />
                <span className="font-label-md text-label-md font-semibold">Strict INCOSE</span>
                <span className="font-code-sm text-code-sm text-outline">ISO 29148 Standard</span>
              </button>

              <button
                type="button"
                onClick={() => setPreset('ieee')}
                disabled={uploading}
                className={`
                  p-3 rounded-xl border flex flex-col items-start gap-1 transition-all text-left
                  ${preset === 'ieee' ? 'border-primary bg-primary-container/20 text-on-surface' : 'border-surface-container-high bg-surface-container hover:bg-surface-container-high text-on-surface-variant'}
                `}
              >
                <Cpu className={`w-4 h-4 ${preset === 'ieee' ? 'text-primary' : 'text-outline'}`} />
                <span className="font-label-md text-label-md font-semibold">IEEE 830</span>
                <span className="font-code-sm text-code-sm text-outline">Classic Standard</span>
              </button>

              <button
                type="button"
                onClick={() => setPreset('agile')}
                disabled={uploading}
                className={`
                  p-3 rounded-xl border flex flex-col items-start gap-1 transition-all text-left
                  ${preset === 'agile' ? 'border-primary bg-primary-container/20 text-on-surface' : 'border-surface-container-high bg-surface-container hover:bg-surface-container-high text-on-surface-variant'}
                `}
              >
                <FileText className={`w-4 h-4 ${preset === 'agile' ? 'text-primary' : 'text-outline'}`} />
                <span className="font-label-md text-label-md font-semibold">Agile Stories</span>
                <span className="font-code-sm text-code-sm text-outline">Gherkin Syntax</span>
              </button>
            </div>
          </div>

          {/* Buttons */}
          <div className="flex items-center justify-end gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              disabled={uploading}
              className="px-4 py-2 rounded-lg bg-surface-container hover:bg-surface-container-high text-on-surface-variant font-label-md text-label-md transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={!selectedFile || uploading}
              className="px-5 py-2 rounded-lg bg-primary text-on-primary font-label-md text-label-md font-semibold hover:opacity-90 transition-opacity shadow-md flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {uploading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Upload className="w-4 h-4" />}
              <span>{uploading ? `Uploading ${progress}%` : 'Launch Ingestion Scan'}</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
