import React, { useState } from 'react';
import { ActiveTab } from './types';
import { Sidebar } from './components/Sidebar';
import { Header } from './components/Header';
import { CommandPaletteModal } from './components/CommandPaletteModal';
import { UploadModal } from './components/UploadModal';
import { DashboardView } from './views/DashboardView';
import { SrsProgressView } from './views/SrsProgressView';
import { RequirementsMatrixView } from './views/RequirementsMatrixView';
import { IssuesConflictResolverView } from './views/IssuesConflictResolverView';
import { ProjectsView } from './views/ProjectsView';
import { TraceabilityView } from './views/TraceabilityView';
import { ReportsView } from './views/ReportsView';
import { SettingsView } from './views/SettingsView';
import { useAsync } from './api/hooks';
import { api } from './api/client';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<ActiveTab>('dashboard');
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [isCommandPaletteOpen, setIsCommandPaletteOpen] = useState(false);
  const [isUploadModalOpen, setIsUploadModalOpen] = useState(false);
  const [selectedReqId, setSelectedReqId] = useState<string>('');
  const [selectedIssueId, setSelectedIssueId] = useState<string>('');

  // Real open-issue count across all projects (sidebar badge)
  const issueCounts = useAsync(() => api.getIssueCounts(), []);
  const openIssuesCount = issueCounts.data?.open ?? 0;

  // Handle keyboard shortcut ⌘K or Ctrl+K for search command palette
  React.useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        setIsCommandPaletteOpen((prev) => !prev);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  return (
    <div className="min-h-screen bg-background font-body-md text-on-surface antialiased flex flex-col">
      {/* Sidebar Navigation Pane */}
      <Sidebar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        isOpen={isMobileMenuOpen}
        onClose={() => setIsMobileMenuOpen(false)}
        openIssuesCount={openIssuesCount}
      />

      {/* Header Top Bar */}
      <Header
        activeTab={activeTab}
        onOpenMobileMenu={() => setIsMobileMenuOpen(true)}
        onOpenCommandPalette={() => setIsCommandPaletteOpen(true)}
        onOpenUploadModal={() => setIsUploadModalOpen(true)}
      />

      {/* Main Responsive Content Area */}
      <main className="w-full pt-14 lg:pl-64 min-h-screen bg-background flex-1 flex flex-col">
        {activeTab === 'dashboard' && (
          <DashboardView
            onNavigate={(tab) => setActiveTab(tab)}
            onOpenUpload={() => setIsUploadModalOpen(true)}
          />
        )}

        {activeTab === 'srs-progress' && (
          <SrsProgressView onNavigate={(tab) => setActiveTab(tab)} />
        )}

        {activeTab === 'requirements' && (
          <RequirementsMatrixView
            onNavigate={(tab) => setActiveTab(tab)}
            selectedReqId={selectedReqId}
            onSelectReq={(id) => setSelectedReqId(id)}
          />
        )}

        {activeTab === 'issues' && (
          <IssuesConflictResolverView
            onNavigate={(tab) => setActiveTab(tab)}
            selectedIssueId={selectedIssueId}
          />
        )}

        {activeTab === 'projects' && (
          <ProjectsView
            onNavigate={(tab) => setActiveTab(tab)}
            onOpenUpload={() => setIsUploadModalOpen(true)}
          />
        )}

        {activeTab === 'traceability' && (
          <TraceabilityView onNavigate={(tab) => setActiveTab(tab)} />
        )}

        {activeTab === 'reports' && (
          <ReportsView onNavigate={(tab) => setActiveTab(tab)} />
        )}

        {activeTab === 'settings' && <SettingsView />}
      </main>

      {/* Global Command Palette Modal (⌘K) */}
      <CommandPaletteModal
        isOpen={isCommandPaletteOpen}
        onClose={() => setIsCommandPaletteOpen(false)}
        onSelectTab={(tab) => setActiveTab(tab)}
        onSelectReq={(id) => {
          setSelectedReqId(id);
          setActiveTab('requirements');
        }}
        onSelectIssue={(id) => {
          setSelectedIssueId(id);
          setActiveTab('issues');
        }}
      />

      {/* SRS Upload Modal */}
      <UploadModal
        isOpen={isUploadModalOpen}
        onClose={() => setIsUploadModalOpen(false)}
        onStartScan={() => setActiveTab('srs-progress')}
      />
    </div>
  );
};

export default App;
