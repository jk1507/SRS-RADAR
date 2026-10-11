import React, { useState } from 'react';
import { ActiveTab } from '../types';
import { Search, Bell, HelpCircle, ChevronRight, Menu, Upload, Plus } from 'lucide-react';

interface HeaderProps {
  activeTab: ActiveTab;
  onOpenMobileMenu: () => void;
  onOpenCommandPalette: () => void;
  onOpenUploadModal: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  activeTab,
  onOpenMobileMenu,
  onOpenCommandPalette,
  onOpenUploadModal,
}) => {
  const [showNotifications, setShowNotifications] = useState(false);

  const getBreadcrumbTitle = (tab: ActiveTab) => {
    switch (tab) {
      case 'dashboard': return 'Dashboard Overview';
      case 'projects': return 'Project Specifications';
      case 'srs-progress': return 'SRS Analysis Progress';
      case 'requirements': return 'Requirements Matrix';
      case 'issues': return 'Issues & Conflict Resolver';
      case 'traceability': return 'Traceability Matrix';
      case 'reports': return 'Quality Audit Reports';
      case 'settings': return 'System Settings';
      default: return 'Requirements';
    }
  };

  return (
    <header className="fixed top-0 left-0 lg:left-64 right-0 h-14 bg-surface-container-lowest/90 backdrop-blur-md z-40 flex items-center justify-between px-4 sm:px-6 shadow-[0_1px_8px_rgba(0,0,0,0.3)] border-b border-surface-container-high/40">
      {/* Left: Mobile hamburger + Breadcrumbs */}
      <div className="flex items-center gap-3">
        <button
          onClick={onOpenMobileMenu}
          className="lg:hidden p-1.5 rounded-lg text-outline hover:text-on-surface hover:bg-surface-container transition-colors"
          aria-label="Toggle Navigation"
        >
          <Menu className="w-5 h-5" />
        </button>

        <nav className="flex items-center gap-2 text-on-surface-variant font-body-sm text-body-sm overflow-x-auto">
          <span className="hover:text-on-surface cursor-pointer transition-colors hidden sm:inline">Projects</span>
          <ChevronRight className="w-3.5 h-3.5 text-outline hidden sm:inline" />
          <span className="hover:text-on-surface cursor-pointer transition-colors truncate max-w-[120px] sm:max-w-none">Smart Hospital</span>
          <ChevronRight className="w-3.5 h-3.5 text-outline" />
          <span className="text-on-surface font-semibold truncate">{getBreadcrumbTitle(activeTab)}</span>
        </nav>
      </div>

      {/* Right: Search + Action Buttons + Profile */}
      <div className="flex items-center gap-2 sm:gap-4">
        {/* Search Command Trigger */}
        <div 
          onClick={onOpenCommandPalette}
          className="flex items-center bg-surface-container-low px-3 py-1.5 rounded-lg w-36 sm:w-64 md:w-72 justify-between cursor-pointer hover:bg-surface-container transition-colors border border-surface-container-high"
        >
          <div className="flex items-center gap-2 text-outline">
            <Search className="w-4 h-4 text-outline" />
            <span className="font-body-sm text-body-sm text-on-surface-variant truncate">Search specs (⌘K)...</span>
          </div>
          <kbd className="hidden sm:inline-block font-code-sm text-code-sm px-1.5 py-0.5 rounded bg-surface-container-highest text-on-surface-variant">⌘ K</kbd>
        </div>

        {/* Quick Upload Button (Desktop) */}
        <button
          onClick={onOpenUploadModal}
          className="hidden md:flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-primary-container/20 border border-primary/30 text-primary hover:bg-primary-container/30 transition-all text-label-md font-semibold"
        >
          <Upload className="w-4 h-4" />
          <span>Upload SRS</span>
        </button>

        {/* Notifications & Help */}
        <div className="relative">
          <button 
            onClick={() => setShowNotifications(!showNotifications)}
            className="relative p-1.5 rounded-lg hover:bg-surface-container text-on-surface-variant hover:text-on-surface transition-colors"
            title="Notifications"
          >
            <Bell className="w-5 h-5" />
            <span className="absolute top-1 right-1 w-4 h-4 bg-error text-on-error font-code-sm text-[10px] rounded-full flex items-center justify-center font-bold">3</span>
          </button>

          {/* Notifications Dropdown Popover */}
          {showNotifications && (
            <div className="absolute right-0 mt-2 w-80 bg-surface-container-low border border-surface-container-high rounded-xl shadow-2xl p-4 z-50">
              <div className="flex items-center justify-between pb-2 border-b border-surface-container-high mb-3">
                <span className="font-headline-sm text-headline-sm font-semibold text-on-surface">Notifications</span>
                <span className="font-code-sm text-code-sm text-tertiary">3 unread</span>
              </div>
              <div className="flex flex-col gap-2.5 max-h-64 overflow-y-auto">
                <div className="p-2.5 rounded-lg bg-surface-container hover:bg-surface-container-high transition-colors cursor-pointer">
                  <div className="flex items-center justify-between">
                    <span className="font-code-sm text-code-sm text-error font-semibold">Critical Conflict Detected</span>
                    <span className="font-code-sm text-code-sm text-outline">5m ago</span>
                  </div>
                  <p className="font-body-sm text-body-sm text-on-surface mt-1">REQ-031 conflicts with REQ-042 on session lock timers.</p>
                </div>
                <div className="p-2.5 rounded-lg bg-surface-container hover:bg-surface-container-high transition-colors cursor-pointer">
                  <div className="flex items-center justify-between">
                    <span className="font-code-sm text-code-sm text-tertiary font-semibold">Live Ingestion Complete</span>
                    <span className="font-code-sm text-code-sm text-outline">12m ago</span>
                  </div>
                  <p className="font-body-sm text-body-sm text-on-surface mt-1">Smart Hospital SRS v1.3 finished scanning 84 clauses.</p>
                </div>
                <div className="p-2.5 rounded-lg bg-surface-container hover:bg-surface-container-high transition-colors cursor-pointer">
                  <div className="flex items-center justify-between">
                    <span className="font-code-sm text-code-sm text-primary font-semibold">AI Rewrite Ready</span>
                    <span className="font-code-sm text-code-sm text-outline">1h ago</span>
                  </div>
                  <p className="font-body-sm text-body-sm text-on-surface mt-1">SpecSentinel generated INCOSE testable rewrite for REQ-024.</p>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* User Profile */}
        <div className="h-4 w-px bg-surface-container-high mx-1 hidden sm:block"></div>
        <div className="flex items-center gap-3 pl-1">
          <div className="relative flex items-center justify-center">
            <div className="w-8 h-8 rounded-full bg-primary/20 border border-primary/40 flex items-center justify-center text-primary font-bold font-code-sm text-sm">
              JA
            </div>
            <span className="absolute bottom-0 right-0 w-2.5 h-2.5 rounded-full bg-tertiary ring-2 ring-surface-container-lowest" />
          </div>
          <div className="hidden xl:flex flex-col leading-none">
            <span className="font-label-md text-label-md font-semibold text-on-surface">Jack</span>
            <span className="font-code-sm text-code-sm text-outline">Lead Architect</span>
          </div>
        </div>
      </div>
    </header>
  );
};
