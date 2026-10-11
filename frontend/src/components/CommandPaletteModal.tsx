import React, { useEffect, useRef, useState } from 'react';
import { Search, FileText, Bug, FolderKanban, ArrowRight, X } from 'lucide-react';
import { ActiveTab } from '../types';
import { api } from '../api/client';
import { useActiveProject, useAsync } from '../api/hooks';

interface CommandPaletteModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSelectTab: (tab: ActiveTab) => void;
  onSelectReq: (reqId: string) => void;
  onSelectIssue: (issueId: string) => void;
}

interface SearchHit {
  scope: string;
  id: string;
  code?: string;
  title: string;
  subtitle?: string;
  score: number;
  project_id?: string;
}

export const CommandPaletteModal: React.FC<CommandPaletteModalProps> = ({
  isOpen,
  onClose,
  onSelectTab,
  onSelectReq,
  onSelectIssue,
}) => {
  const [query, setQuery] = useState('');
  const [hits, setHits] = useState<SearchHit[]>([]);
  const [searching, setSearching] = useState(false);
  const seq = useRef(0);
  const { activeId } = useActiveProject();

  // Debounced server-side search (300 ms)
  useEffect(() => {
    if (!isOpen || query.trim().length < 2) {
      setHits([]);
      return;
    }
    const id = ++seq.current;
    setSearching(true);
    const t = setTimeout(() => {
      api
        .search(query.trim())
        .then((res) => {
          if (seq.current === id) setHits(res as SearchHit[]);
        })
        .catch(() => {
          if (seq.current === id) setHits([]);
        })
        .finally(() => {
          if (seq.current === id) setSearching(false);
        });
    }, 300);
    return () => clearTimeout(t);
  }, [query, isOpen]);

  if (!isOpen) return null;

  const reqHits = hits.filter((h) => h.scope === 'requirements');
  const issueHits = hits.filter((h) => h.scope === 'issues');
  const projectHits = hits.filter((h) => h.scope === 'projects');

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center pt-20 px-4 bg-black/70 backdrop-blur-md animate-in fade-in duration-200">
      <div 
        className="fixed inset-0" 
        onClick={onClose} 
      />
      
      <div className="relative w-full max-w-2xl bg-surface-container-low border border-surface-container-high rounded-2xl shadow-2xl overflow-hidden z-10 flex flex-col">
        {/* Search Input Bar */}
        <div className="flex items-center px-4 py-3 border-b border-surface-container-high bg-surface-container-lowest">
          <Search className="w-5 h-5 text-outline mr-3 shrink-0" />
          <input
            type="text"
            autoFocus
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search requirements, issues, projects across all SRS..."
            className="w-full bg-transparent text-on-surface placeholder-outline font-body-md text-body-md focus:outline-none"
          />
          <button 
            onClick={onClose}
            className="p-1 rounded-lg text-outline hover:text-on-surface hover:bg-surface-container transition-colors ml-2"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Results List */}
        <div className="max-h-96 overflow-y-auto p-3 flex flex-col gap-3">
          {/* Section 1: Navigation Actions */}
          <div>
            <span className="font-label-caps text-label-caps text-outline uppercase px-2 tracking-wider">Quick Navigation</span>
            <div className="mt-1 flex flex-col gap-1">
              <button
                onClick={() => { onSelectTab('dashboard'); onClose(); }}
                className="flex items-center justify-between p-2.5 rounded-lg hover:bg-surface-container text-on-surface transition-colors w-full text-left"
              >
                <div className="flex items-center gap-3">
                  <FolderKanban className="w-4 h-4 text-primary" />
                  <span className="font-body-sm text-body-sm font-medium">Go to Executive Dashboard</span>
                </div>
                <ArrowRight className="w-4 h-4 text-outline" />
              </button>
              <button
                onClick={() => { onSelectTab('srs-progress'); onClose(); }}
                className="flex items-center justify-between p-2.5 rounded-lg hover:bg-surface-container text-on-surface transition-colors w-full text-left"
              >
                <div className="flex items-center gap-3">
                  <FileText className="w-4 h-4 text-tertiary" />
                  <span className="font-body-sm text-body-sm font-medium">View Live SRS Analysis Pipeline</span>
                </div>
                <ArrowRight className="w-4 h-4 text-outline" />
              </button>
            </div>
          </div>

          {searching && (
            <span className="font-body-sm text-body-sm text-outline px-2">Searching…</span>
          )}

          {/* Section 2: Projects */}
          {projectHits.length > 0 && (
            <div>
              <span className="font-label-caps text-label-caps text-outline uppercase px-2 tracking-wider">Projects ({projectHits.length})</span>
              <div className="mt-1 flex flex-col gap-1">
                {projectHits.map((h) => (
                  <button
                    key={h.id}
                    onClick={() => { onSelectTab('projects'); onClose(); }}
                    className="flex items-center justify-between p-2.5 rounded-lg hover:bg-surface-container text-on-surface transition-colors w-full text-left"
                  >
                    <div className="flex items-center gap-3 min-w-0">
                      <FolderKanban className="w-4 h-4 text-primary shrink-0" />
                      <span className="font-body-sm text-body-sm text-on-surface truncate">{h.title}</span>
                    </div>
                    {h.subtitle && (
                      <span className="font-code-sm text-code-sm px-2 py-0.5 rounded bg-surface-container text-outline shrink-0 ml-2">{h.subtitle}</span>
                    )}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Section 3: Requirements */}
          {reqHits.length > 0 && (
            <div>
              <span className="font-label-caps text-label-caps text-outline uppercase px-2 tracking-wider">Requirements ({reqHits.length})</span>
              <div className="mt-1 flex flex-col gap-1">
                {reqHits.map((h) => (
                  <button
                    key={h.id}
                    onClick={() => {
                      if (h.project_id && h.project_id !== activeId) {
                        localStorage.setItem('rr_active_project_id', h.project_id);
                      }
                      onSelectReq(h.id);
                      onClose();
                    }}
                    className="flex items-center justify-between p-2.5 rounded-lg hover:bg-surface-container text-on-surface transition-colors w-full text-left"
                  >
                    <div className="flex items-center gap-3 min-w-0">
                      <span className="font-code-sm text-code-sm px-2 py-0.5 rounded bg-surface-container-highest text-primary font-bold shrink-0">{h.code || h.id.slice(0, 8)}</span>
                      <span className="font-body-sm text-body-sm text-on-surface truncate">{h.title}</span>
                    </div>
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Section 4: Issues */}
          {issueHits.length > 0 && (
            <div>
              <span className="font-label-caps text-label-caps text-outline uppercase px-2 tracking-wider">Issues & Conflicts ({issueHits.length})</span>
              <div className="mt-1 flex flex-col gap-1">
                {issueHits.map((h) => (
                  <button
                    key={h.id}
                    onClick={() => {
                      if (h.project_id && h.project_id !== activeId) {
                        localStorage.setItem('rr_active_project_id', h.project_id);
                      }
                      onSelectIssue(h.id);
                      onClose();
                    }}
                    className="flex items-center justify-between p-2.5 rounded-lg hover:bg-surface-container text-on-surface transition-colors w-full text-left"
                  >
                    <div className="flex items-center gap-3 min-w-0">
                      <Bug className="w-4 h-4 text-error shrink-0" />
                      <span className="font-body-sm text-body-sm text-on-surface truncate">{h.title}</span>
                    </div>
                    {h.subtitle && (
                      <span className="font-code-sm text-code-sm px-2 py-0.5 rounded bg-error-container text-error font-medium shrink-0 ml-2">{h.subtitle}</span>
                    )}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Empty state */}
          {query.trim().length >= 2 && !searching && hits.length === 0 && (
            <span className="font-body-sm text-body-sm text-outline px-2 py-4 text-center">
              No results for “{query}”
            </span>
          )}
        </div>

        {/* Modal Footer */}
        <div className="px-4 py-2 bg-surface-container-lowest border-t border-surface-container-high flex items-center justify-between font-code-sm text-code-sm text-outline">
          <span>Press ESC to close</span>
          <span>Requirement Radar Intelligence Engine</span>
        </div>
      </div>
    </div>
  );
};
