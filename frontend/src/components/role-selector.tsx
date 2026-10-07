"use client";

import { useState, useRef, useEffect } from "react";
import { Target, Briefcase } from "lucide-react";

interface RoleSelectorProps {
  currentRole: string;
  targetRole: string;
}

export function RoleSelector({ currentRole, targetRole }: RoleSelectorProps) {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  return (
    <div className="relative" ref={dropdownRef}>
      <button 
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 rounded-full border border-rw-border px-4 py-2 text-sm transition-colors hover:border-rw-green hover:bg-rw-green/5"
      >
        <span className="h-2 w-2 rounded-full bg-rw-green" />
        <span className="font-medium text-rw-ink">{currentRole}</span>
        <svg
          width="12"
          height="12"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          className={`text-rw-ink-muted transition-transform duration-200 ${isOpen ? "rotate-90" : ""}`}
        >
          <polyline points="9 18 15 12 9 6" />
        </svg>
      </button>

      {isOpen && (
        <div className="absolute right-0 top-full mt-2 w-56 rounded-xl border border-rw-border bg-rw-surface-alt p-2 shadow-xl animate-in fade-in slide-in-from-top-2">
          <div className="mb-2 px-2 py-1 text-xs font-semibold text-rw-ink-muted uppercase tracking-wider">
            Your Roles
          </div>
          
          <div className="flex flex-col gap-1">
            <div className="flex items-center gap-3 rounded-lg px-3 py-2 bg-rw-surface">
              <Briefcase size={16} className="text-rw-ink-secondary" />
              <div className="flex flex-col">
                <span className="text-[10px] uppercase text-rw-ink-muted font-bold leading-none mb-1">Current</span>
                <span className="text-sm font-medium text-rw-ink leading-none">{currentRole}</span>
              </div>
            </div>

            <div className="flex items-center gap-3 rounded-lg px-3 py-2 bg-rw-green/10 border border-rw-green/20">
              <Target size={16} className="text-rw-green" />
              <div className="flex flex-col">
                <span className="text-[10px] uppercase text-rw-green font-bold leading-none mb-1">Target</span>
                <span className="text-sm font-medium text-rw-ink leading-none">{targetRole}</span>
              </div>
            </div>
          </div>
          
          <div className="mt-2 pt-2 border-t border-rw-border">
            <a href="/onboarding?force=true" className="block w-full rounded-md px-3 py-2 text-left text-sm text-rw-ink-secondary hover:bg-rw-surface hover:text-rw-ink transition-colors">
              Update Roles...
            </a>
          </div>
        </div>
      )}
    </div>
  );
}
