import React, { useState } from 'react';
import { Upload, FileText, CheckCircle2, X, Cpu, ShieldCheck } from 'lucide-react';
import { api } from '../api/client';

interface UploadModalProps {
  isOpen: boolean;
  onClose: () => void;
  onStartScan: () => void;
}

export const UploadModal: React.FC<UploadModalProps> = ({ isOpen, onClose, onStartScan }) => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [preset, setPreset] = useState<'incose' | 'ieee' | 'agile'>('incose');
  const [isDragging, setIsDragging] = useState(false);

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
    if (selectedFile) {
      try {
        await api.uploadDocument(selectedFile);
      } catch (err) {
        console.warn('API upload failed, triggering scan:', err);
      }
    }
    onStartScan();
    onClose();
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
              <h2 className="font-headline-md text-headline-md font-semibold text-on-surface">Quick Upload Specification</h2>
              <span className="font-code-sm text-code-sm text-outline">Ingest SRS, PDF, DOCX, or Markdown files</span>
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
              accept=".pdf,.docx,.txt,.md,.json"
              onChange={handleFileChange}
              className="absolute inset-0 opacity-0 cursor-pointer"
            />

            {selectedFile ? (
              <div className="flex flex-col items-center gap-2">
                <CheckCircle2 className="w-10 h-10 text-tertiary" />
                <span className="font-body-md text-body-md font-semibold text-on-surface">{selectedFile.name}</span>
                <span className="font-code-sm text-code-sm text-outline">{(selectedFile.size / 1024 / 1024).toFixed(2)} MB • Ready for analysis</span>
              </div>
            ) : (
              <div className="flex flex-col items-center gap-2">
                <Upload className="w-10 h-10 text-outline mb-1" />
                <span className="font-body-md text-body-md font-medium text-on-surface">
                  Drag and drop your SRS document here, or <span className="text-primary font-semibold underline">browse</span>
                </span>
                <span className="font-code-sm text-code-sm text-outline">Supports PDF, DOCX, Markdown up to 50MB</span>
              </div>
            )}
          </div>

          {/* Engine Preset Selector */}
          <div className="flex flex-col gap-2">
            <span className="font-label-caps text-label-caps uppercase text-outline tracking-wider">Verification Engine Rule Set</span>
            <div className="grid grid-cols-3 gap-3">
              <button
                type="button"
                onClick={() => setPreset('incose')}
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
              className="px-4 py-2 rounded-lg bg-surface-container hover:bg-surface-container-high text-on-surface-variant font-label-md text-label-md transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-5 py-2 rounded-lg bg-primary text-on-primary font-label-md text-label-md font-semibold hover:opacity-90 transition-opacity shadow-md flex items-center gap-2"
            >
              <Upload className="w-4 h-4" />
              <span>Launch Ingestion Scan</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
