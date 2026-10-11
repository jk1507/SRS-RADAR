import React, { useEffect, useState } from 'react';
import { Cpu, ShieldCheck, Save, Check, Loader2 } from 'lucide-react';
import { api } from '../api/client';
import { useAsync } from '../api/hooks';

export const SettingsView: React.FC = () => {
  const org = useAsync(() => api.getOrgSettings(), []);
  const [lintMode, setLintMode] = useState('strict');
  const [strictVague, setStrictVague] = useState(true);
  const [retention, setRetention] = useState('standard');
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!org.data) return;
    const s = org.data.settings || {};
    setLintMode(s.lint_mode || org.data.organization?.settings?.lint_mode || 'strict');
    setStrictVague(s.strict_vague_flagging !== false);
    setRetention(s.retention_mode || 'standard');
  }, [org.data]);

  const handleSave = async () => {
    setSaving(true);
    setError(null);
    try {
      await api.updateOrgSettings({
        settings: {
          lint_mode: lintMode,
          strict_vague_flagging: strictVague,
          retention_mode: retention,
        },
      });
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
      org.reload();
    } catch (err) {
      setError((err as Error).message || 'Save failed');
    } finally {
      setSaving(false);
    }
  };

  if (org.loading) {
    return (
      <div className="flex items-center justify-center py-20 text-on-surface-variant">
        <Loader2 className="w-6 h-6 animate-spin mr-2" /> Loading settings…
      </div>
    );
  }

  return (
    <div className="px-4 sm:px-6 py-6 max-w-4xl mx-auto w-full flex flex-col gap-6 animate-in fade-in duration-300">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-surface-container-high">
        <div className="flex flex-col gap-1">
          <h1 className="font-headline-lg text-2xl sm:text-3xl text-on-surface font-semibold tracking-tight">System & Engine Settings</h1>
          <p className="font-body-md text-body-md text-on-surface-variant">Configure verification AI models, linting strictness, and retention policy</p>
        </div>
        <button
          onClick={handleSave}
          disabled={saving}
          className="px-4 py-2 rounded-lg bg-primary text-on-primary font-label-md text-label-md font-semibold flex items-center gap-2 hover:opacity-90 transition-opacity shadow-md self-start sm:self-auto disabled:opacity-50"
        >
          {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : saved ? <Check className="w-4 h-4" /> : <Save className="w-4 h-4" />}
          <span>{saving ? 'Saving…' : saved ? 'Saved!' : 'Save Settings'}</span>
        </button>
      </div>

      {error && (
        <div className="p-3 rounded-lg bg-error-container/30 border border-error/40">
          <span className="font-body-sm text-body-sm text-error">{error}</span>
        </div>
      )}

      <div className="flex flex-col gap-6">
        {/* Engine Profile */}
        <div className="p-6 rounded-2xl bg-surface-container-low border border-surface-container-high flex flex-col gap-4">
          <h2 className="font-headline-sm text-headline-sm font-semibold text-on-surface flex items-center gap-2">
            <Cpu className="w-5 h-5 text-primary" /> Verification Engine
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div 
              onClick={() => setLintMode('strict')}
              className={`p-4 rounded-xl border cursor-pointer transition-all ${lintMode === 'strict' ? 'border-primary bg-primary-container/20' : 'border-surface-container-high bg-surface-container'}`}
            >
              <span className="font-label-md text-label-md font-semibold text-on-surface">AI + Rules (Recommended)</span>
              <p className="font-body-sm text-body-sm text-on-surface-variant mt-1">LLM semantic analysis grounded by INCOSE rule engine with automated testable rewrite generation.</p>
            </div>
            <div 
              onClick={() => setLintMode('deterministic')}
              className={`p-4 rounded-xl border cursor-pointer transition-all ${lintMode === 'deterministic' ? 'border-primary bg-primary-container/20' : 'border-surface-container-high bg-surface-container'}`}
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
              <span className="font-label-md text-label-md font-semibold text-on-surface">Strict Vague Word Flagging</span>
              <span className="font-body-sm text-body-sm text-on-surface-variant">Flag subjective adjectives like 'fast', 'easy', 'user-friendly', and 'seamless'.</span>
            </div>
            <input
              type="checkbox"
              checked={strictVague}
              onChange={(e) => setStrictVague(e.target.checked)}
              className="w-5 h-5 accent-primary rounded cursor-pointer"
            />
          </div>
          <div className="flex items-center justify-between p-4 rounded-xl bg-surface-container border border-surface-container-high">
            <div className="flex flex-col">
              <span className="font-label-md text-label-md font-semibold text-on-surface">Zero-Retention Mode</span>
              <span className="font-body-sm text-body-sm text-on-surface-variant">Delete uploaded source documents immediately after analysis.</span>
            </div>
            <input
              type="checkbox"
              checked={retention === 'zero_retention'}
              onChange={(e) => setRetention(e.target.checked ? 'zero_retention' : 'standard')}
              className="w-5 h-5 accent-primary rounded cursor-pointer"
            />
          </div>
        </div>

        {/* Engine info */}
        {org.data?.platform && (
          <div className="p-6 rounded-2xl bg-surface-container-low border border-surface-container-high flex flex-col gap-2">
            <h2 className="font-headline-sm text-headline-sm font-semibold text-on-surface">Platform</h2>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mt-2">
              {Object.entries(org.data.platform as Record<string, string>).map(([k, v]) => (
                <div key={k} className="flex flex-col">
                  <span className="font-code-sm text-code-sm text-outline uppercase">{k.replace(/_/g, ' ')}</span>
                  <span className="font-body-sm text-body-sm text-on-surface font-medium">{String(v)}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
