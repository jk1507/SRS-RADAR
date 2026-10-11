import React from 'react';
import { ActiveTab } from '../types';
import { mockProjects } from '../data/mockData';
import { FolderKanban, FileText, CheckCircle2, AlertTriangle, ArrowRight, Plus } from 'lucide-react';

interface ProjectsViewProps {
  onNavigate: (tab: ActiveTab) => void;
  onOpenUpload: () => void;
}

export const ProjectsView: React.FC<ProjectsViewProps> = ({ onNavigate, onOpenUpload }) => {
  return (
    <div className="px-4 sm:px-6 py-6 max-w-7xl mx-auto w-full flex flex-col gap-6 animate-in fade-in duration-300">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-surface-container-high">
        <div className="flex flex-col gap-1">
          <h1 className="font-headline-lg text-2xl sm:text-3xl text-on-surface font-semibold tracking-tight">Active Specification Projects</h1>
          <p className="font-body-md text-body-md text-on-surface-variant">Manage and run automated audits across your system architecture specs</p>
        </div>
        <button
          onClick={onOpenUpload}
          className="px-4 py-2 rounded-lg bg-primary text-on-primary font-label-md text-label-md font-semibold flex items-center gap-2 hover:opacity-90 transition-opacity shadow-md self-start sm:self-auto"
        >
          <Plus className="w-4 h-4" />
          <span>Ingest New SRS Document</span>
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {mockProjects.map((proj) => (
          <div
            key={proj.id}
            onClick={() => onNavigate(proj.id === 'proj-01' ? 'srs-progress' : 'requirements')}
            className="p-6 rounded-2xl bg-surface-container-low border border-surface-container-high hover:border-primary/50 transition-all cursor-pointer flex flex-col justify-between gap-6 group hover:shadow-xl"
          >
            <div className="flex flex-col gap-3">
              <div className="flex items-center justify-between">
                <div className="w-10 h-10 rounded-xl bg-primary-container/20 border border-primary/30 flex items-center justify-center text-primary group-hover:scale-110 transition-transform">
                  <FolderKanban className="w-5 h-5" />
                </div>
                <span className={`font-code-sm text-code-sm px-2.5 py-0.5 rounded-full font-semibold ${proj.status === 'Completed' ? 'bg-tertiary-container/20 text-tertiary' : 'bg-primary-container/20 text-primary animate-pulse'}`}>
                  {proj.status}
                </span>
              </div>

              <div className="flex flex-col gap-1 mt-1">
                <h2 className="font-headline-md text-headline-md text-on-surface font-semibold group-hover:text-primary transition-colors">{proj.name}</h2>
                <span className="font-code-sm text-code-sm text-outline">{proj.fileName} ({proj.version})</span>
              </div>

              <span className="font-body-sm text-body-sm text-on-surface-variant bg-surface-container px-2.5 py-1 rounded-lg border border-surface-container-high inline-block self-start">
                Domain: {proj.domain}
              </span>
            </div>

            <div className="flex items-center justify-between border-t border-surface-container-high pt-4">
              <div className="flex flex-col">
                <span className="font-label-caps text-label-caps text-outline uppercase">Quality Index</span>
                <span className="font-code-md text-code-md font-bold text-tertiary">{proj.qualityScore}/100</span>
              </div>
              <div className="flex flex-col">
                <span className="font-label-caps text-label-caps text-outline uppercase">Issues</span>
                <span className="font-code-md text-code-md font-bold text-error">{proj.openIssuesCount}</span>
              </div>
              <ArrowRight className="w-5 h-5 text-outline group-hover:text-primary group-hover:translate-x-1 transition-all" />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
