import React, { useState } from 'react';
import { ActiveTab } from '../types';
import { Settings, Cpu, ShieldCheck, Database, Save, Check } from 'lucide-react';

interface SettingsViewProps {
  onNavigate: (tab: ActiveTab) => void;
}

export const SettingsView: React.FC<SettingsViewProps> = () => {
  const [engineMode, setEngineMode] = useState('specsentinel');
  const [incoseStrict, setIncoseStrict] = useState(true);
  const [saved, setSaved] = useState(false);

  const handleSave = () => {
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  return (
    <div className="px-4 sm:px-6 py-6 max-w-4xl mx-auto w-full flex flex-col gap-6 animate-in fade-in duration-300">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-surface-container-high">
        <div className="flex flex-col gap-1">
          <h1 className="font-headline-lg text-2xl sm:text-3xl text-on-surface font-semibold tracking-tight">System & Engine Settings</h1>
          <p className="font-body-md text-body-md text-on-surface-variant">Configure verification AI models, linting strictness, and airgap privacy rings</p>
        </div>
        <button
          onClick={handleSave}
          className="px-4 py-2 rounded-lg bg-primary text-on-primary font-label-md text-label-md font-semibold flex items-center gap-2 hover:opacity-90 transition-opacity shadow-md self-start sm:self-auto"
        >
          {saved ? <Check className="w-4 h-4" /> : <Save className="w-4 h-4" />}
          <span>{saved ? 'Saved!' : 'Save Settings'}</span>
        </button>
      </div>

      <div className="flex flex-col gap-6">
        {/* Engine Profile */}
        <div className="p-6 rounded-2xl bg-surface-container-low border border-surface-container-high flex flex-col gap-4">
          <h2 className="font-headline-sm text-headline-sm font-semibold text-on-surface flex items-center gap-2">
            <Cpu className="w-5 h-5 text-primary" /> Target Verification Engine
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div 
              onClick={() => setEngineMode('specsentinel')}
              className={`p-4 rounded-xl border cursor-pointer transition-all ${engineMode === 'specsentinel' ? 'border-primary bg-primary-container/20' : 'border-surface-container-high bg-surface-container'}`}
            >
              <span className="font-label-md text-label-md font-semibold text-on-surface">SpecSentinel AI v2.4 (Recommended)</span>
              <p className="font-body-sm text-body-sm text-on-surface-variant mt-1">Deep semantic neural parser with INCOSE rule engine and automated testable rewrite generation.</p>
            </div>
            <div 
              onClick={() => setEngineMode('rule-only')}
              className={`p-4 rounded-xl border cursor-pointer transition-all ${engineMode === 'rule-only' ? 'border-primary bg-primary-container/20' : 'border-surface-container-high bg-surface-container'}`}
            >
              <span className="font-label-md text-label-md font-semibold text-on-surface">Deterministic Rule Linter</span>
              <p className="font-body-sm text-body-sm text-on-surface-variant mt-1">Fast regex-based INCOSE and IEEE keyword validator without external LLM calls.</p>
            </div>
          </div>
        </div>

        {/* INCOSE Rule strictness */}
        <div className="p-6 rounded-2xl bg-surface-container-low border border-surface-container-high flex flex-col gap-4">
          <h2 className="font-headline-sm text-headline-sm font-semibold text-on-surface flex items-center gap-2">
            <ShieldCheck className="w-5 h-5 text-tertiary" /> ISO/IEC/IEEE 29148 Standard Rules
          </h2>
          <div className="flex items-center justify-between p-4 rounded-xl bg-surface-container border border-surface-container-high">
            <div className="flex flex-col">
              <span className="font-label-md text-label-md font-semibold text-on-surface">Strict INCOSE Vague Word Flagging</span>
              <span className="font-body-sm text-body-sm text-on-surface-variant">Flag subjective adjectives like 'fast', 'easy', 'user-friendly', and 'seamless'.</span>
            </div>
            <input
              type="checkbox"
              checked={incoseStrict}
              onChange={(e) => setIncoseStrict(e.target.checked)}
              className="w-5 h-5 accent-primary rounded cursor-pointer"
            />
          </div>
        </div>
      </div>
    </div>
  );
};
