import React, { useState } from 'react';
import { Search, FileText, Bug, FolderKanban, ArrowRight, X } from 'lucide-react';
import { mockRequirements, mockIssues } from '../data/mockData';
import { ActiveTab } from '../types';

interface CommandPaletteModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSelectTab: (tab: ActiveTab) => void;
  onSelectReq: (reqId: string) => void;
  onSelectIssue: (issueId: string) => void;
}

export const CommandPaletteModal: React.FC<CommandPaletteModalProps> = ({
  isOpen,
  onClose,
  onSelectTab,
  onSelectReq,
  onSelectIssue,
}) => {
  const [query, setQuery] = useState('');

  if (!isOpen) return null;

  const filteredReqs = mockRequirements.filter(
    (r) =>
      r.id.toLowerCase().includes(query.toLowerCase()) ||
      r.originalText.toLowerCase().includes(query.toLowerCase()) ||
      r.title.toLowerCase().includes(query.toLowerCase())
  );

  const filteredIssues = mockIssues.filter(
    (i) =>
      i.id.toLowerCase().includes(query.toLowerCase()) ||
      i.title.toLowerCase().includes(query.toLowerCase()) ||
      i.summary.toLowerCase().includes(query.toLowerCase())
  );

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
            placeholder="Type a command or search requirements, issues, specs (e.g. REQ-024)..."
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

          {/* Section 2: Requirements */}
          <div>
            <span className="font-label-caps text-label-caps text-outline uppercase px-2 tracking-wider">Requirements ({filteredReqs.length})</span>
            <div className="mt-1 flex flex-col gap-1">
              {filteredReqs.map((req) => (
                <button
                  key={req.id}
                  onClick={() => {
                    onSelectReq(req.id);
                    onClose();
                  }}
                  className="flex items-center justify-between p-2.5 rounded-lg hover:bg-surface-container text-on-surface transition-colors w-full text-left"
                >
                  <div className="flex items-center gap-3 min-w-0">
                    <span className="font-code-sm text-code-sm px-2 py-0.5 rounded bg-surface-container-highest text-primary font-bold shrink-0">{req.id}</span>
                    <span className="font-body-sm text-body-sm text-on-surface truncate">{req.originalText}</span>
                  </div>
                  <span className="font-code-sm text-code-sm px-2 py-0.5 rounded bg-surface-container text-outline shrink-0 ml-2">{req.category}</span>
                </button>
              ))}
            </div>
          </div>

          {/* Section 3: Issues */}
          <div>
            <span className="font-label-caps text-label-caps text-outline uppercase px-2 tracking-wider">Issues & Conflicts ({filteredIssues.length})</span>
            <div className="mt-1 flex flex-col gap-1">
              {filteredIssues.map((issue) => (
                <button
                  key={issue.id}
                  onClick={() => {
                    onSelectIssue(issue.id);
                    onClose();
                  }}
                  className="flex items-center justify-between p-2.5 rounded-lg hover:bg-surface-container text-on-surface transition-colors w-full text-left"
                >
                  <div className="flex items-center gap-3 min-w-0">
                    <Bug className="w-4 h-4 text-error shrink-0" />
                    <span className="font-body-sm text-body-sm text-on-surface truncate">{issue.title}</span>
                  </div>
                  <span className="font-code-sm text-code-sm px-2 py-0.5 rounded bg-error-container text-error font-medium shrink-0 ml-2">{issue.severity}</span>
                </button>
              ))}
            </div>
          </div>
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
