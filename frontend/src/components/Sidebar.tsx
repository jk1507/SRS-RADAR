import React from 'react';
import { ActiveTab } from '../types';
import { 
  LayoutDashboard, 
  FolderKanban, 
  FileText, 
  Bug, 
  GitFork, 
  BarChart3, 
  Settings, 
  Radar, 
  X,
  Play
} from 'lucide-react';

interface SidebarProps {
  activeTab: ActiveTab;
  setActiveTab: (tab: ActiveTab) => void;
  isOpen: boolean;
  onClose: () => void;
  openIssuesCount: number;
}

export const Sidebar: React.FC<SidebarProps> = ({
  activeTab,
  setActiveTab,
  isOpen,
  onClose,
  openIssuesCount,
}) => {
  const navItems = [
    { id: 'dashboard' as ActiveTab, label: 'Dashboard', icon: LayoutDashboard },
    { id: 'projects' as ActiveTab, label: 'Projects', icon: FolderKanban },
    { id: 'srs-progress' as ActiveTab, label: 'SRS Analysis', icon: Play, badge: 'LIVE', badgeColor: 'bg-tertiary-container text-tertiary font-semibold' },
    { id: 'requirements' as ActiveTab, label: 'Requirements', icon: FileText },
    { id: 'issues' as ActiveTab, label: 'Issues', icon: Bug, badge: String(openIssuesCount), badgeColor: 'bg-error-container text-error font-medium' },
    { id: 'traceability' as ActiveTab, label: 'Traceability', icon: GitFork, badge: '82%', badgeColor: 'bg-surface-container text-tertiary font-medium' },
    { id: 'reports' as ActiveTab, label: 'Reports', icon: BarChart3 },
    { id: 'settings' as ActiveTab, label: 'Settings', icon: Settings },
  ];

  return (
    <>
      {/* Mobile backdrop */}
      {isOpen && (
        <div 
          className="fixed inset-0 bg-black/60 z-40 lg:hidden backdrop-blur-sm"
          onClick={onClose}
        />
      )}

      <aside className={`
        fixed top-0 left-0 h-full w-64 bg-surface-container-lowest z-50 flex flex-col justify-between py-4 shadow-[0_1px_8px_rgba(0,0,0,0.4)] transition-transform duration-300 ease-in-out
        ${isOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
      `}>
        <div className="flex flex-col">
          {/* Logo & Header */}
          <div className="h-14 px-5 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-primary-container/20 border border-primary/30 flex items-center justify-center text-primary shadow-sm">
                <Radar className="w-5 h-5 animate-pulse-subtle" />
              </div>
              <div className="flex flex-col leading-none">
                <span className="font-label-caps text-label-caps tracking-wider text-primary font-bold uppercase">Requirement Radar</span>
                <span className="font-code-sm text-code-sm text-outline mt-0.5">v2.4.0-audit</span>
              </div>
            </div>
            <button 
              className="lg:hidden text-outline hover:text-on-surface p-1 rounded"
              onClick={onClose}
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Engine Status Badge */}
          <div className="px-5 py-2">
            <div className="bg-surface-container-low border border-surface-container-high px-3 py-2 rounded flex items-center justify-between">
              <div className="flex flex-col">
                <span className="font-label-caps text-label-caps uppercase text-outline">Target Engine</span>
                <span className="font-label-md text-label-md text-on-surface font-semibold">SpecSentinel AI</span>
              </div>
              <span className="w-2 h-2 rounded-full bg-tertiary animate-pulse" />
            </div>
          </div>

          {/* Navigation Links */}
          <nav className="mt-4 flex flex-col gap-1 px-3">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = activeTab === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => {
                    setActiveTab(item.id);
                    onClose();
                  }}
                  className={`
                    flex items-center justify-between px-3 py-2 rounded-lg text-left transition-all
                    ${isActive 
                      ? 'bg-surface-container-high text-on-surface font-semibold shadow-sm border-l-2 border-primary' 
                      : 'text-on-surface-variant hover:bg-surface-container hover:text-on-surface'
                    }
                  `}
                >
                  <div className="flex items-center gap-3">
                    <Icon className={`w-4 h-4 ${isActive ? 'text-primary' : 'text-outline'}`} />
                    <span className="font-label-md text-label-md">{item.label}</span>
                  </div>
                  {item.badge && (
                    <span className={`font-code-sm text-code-sm px-1.5 py-0.5 rounded ${item.badgeColor}`}>
                      {item.badge}
                    </span>
                  )}
                </button>
              );
            })}
          </nav>
        </div>

        {/* Footer Guard Card */}
        <div className="px-4 flex flex-col gap-2">
          <div className="p-3 bg-surface-container-low border border-surface-container-high rounded-xl flex items-center justify-between">
            <div className="flex flex-col">
              <span className="font-code-sm text-code-sm text-outline">Radar Sweep</span>
              <span className="font-label-md text-label-md text-tertiary font-semibold flex items-center gap-1">
                <span className="w-1.5 h-1.5 rounded-full bg-tertiary animate-ping" />
                Active Guard
              </span>
            </div>
            <Radar className="w-5 h-5 text-tertiary" />
          </div>
        </div>
      </aside>
    </>
  );
};
