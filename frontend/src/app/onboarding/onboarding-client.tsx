"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Sparkles, ArrowRight, Loader2, GraduationCap, Code2, Rocket, Crown, Star, Briefcase, CalendarClock, ChevronRight } from "lucide-react";
import { completeOnboarding } from "../actions/onboarding";

type Step = 1 | 2 | 3;

export function OnboardingClient() {
  const router = useRouter();
  const [step, setStep] = useState<Step>(1);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const [currentRole, setCurrentRole] = useState("");
  const [targetRole, setTargetRole] = useState("");
  const [timeline, setTimeline] = useState("");

  const handleNext = async () => {
    if (step === 1 && !currentRole) return;
    if (step === 2 && !targetRole) return;

    if (step < 3) {
      setStep((s) => (s + 1) as Step);
    } else {
      if (!timeline) return;
      setIsSubmitting(true);
      try {
        await completeOnboarding({ currentRole, targetRole, timeline });
        router.push("/roles");
      } catch (e) {
        console.error("Failed to onboard", e);
        setIsSubmitting(false);
      }
    }
  };

  const steps = [
    { id: 1, title: "Current Role", subtitle: "Where are you starting?" },
    { id: 2, title: "Target Role", subtitle: "Where are you going?" },
    { id: 3, title: "Timeline", subtitle: "When is the interview?" }
  ];

  return (
    <div className="relative bg-rw-surface border border-rw-border rounded-3xl shadow-xl overflow-hidden transition-all duration-500 min-h-[600px] flex flex-col">
      {/* Premium subtle gradient background */}
      <div className="absolute inset-0 bg-gradient-to-br from-rw-green/5 to-transparent pointer-events-none" />
      
      {/* Top Header / Progress */}
      <div className="relative z-10 px-8 py-6 border-b border-rw-border bg-rw-surface/80 backdrop-blur-xl flex items-center justify-between">
        <div className="flex gap-2 items-center">
          {steps.map((s) => (
            <div key={s.id} className="flex items-center gap-2">
              <div className={`flex items-center justify-center w-8 h-8 rounded-full text-sm font-semibold transition-all duration-300 ${step === s.id ? "bg-rw-ink text-white shadow-md scale-110" : step > s.id ? "bg-rw-green text-white" : "bg-rw-surface-alt text-rw-ink-muted border border-rw-border"}`}>
                {step > s.id ? "✓" : s.id}
              </div>
              {s.id !== 3 && <ChevronRight className={`w-4 h-4 ${step > s.id ? "text-rw-green" : "text-rw-border"}`} />}
            </div>
          ))}
        </div>
        <div className="text-right hidden sm:block">
          <p className="text-sm font-medium text-rw-ink">{steps[step - 1].title}</p>
          <p className="text-xs text-rw-ink-muted">{steps[step - 1].subtitle}</p>
        </div>
      </div>

      {/* Main Content Area */}
      <div className="relative z-10 flex-1 p-8 md:p-12 flex flex-col">
        {step === 1 && (
          <div className="animate-in fade-in slide-in-from-right-8 duration-500 flex-1">
            <h1 className="font-serif tracking-tight text-4xl text-rw-ink mb-3">Define your baseline</h1>
            <p className="text-rw-ink-secondary mb-10 text-lg">Select your current role so we can calibrate the learning curve.</p>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {[
                { id: "student", label: "Student / New Grad", icon: GraduationCap },
                { id: "sde_1", label: "Junior (SDE I)", icon: Code2 },
                { id: "sde_2", label: "Mid-Level (SDE II)", icon: Briefcase },
                { id: "sde_3", label: "Senior (SDE III)", icon: Star },
                { id: "staff", label: "Staff / Principal", icon: Crown },
              ].map((role) => {
                const Icon = role.icon;
                const isSelected = currentRole === role.id;
                return (
                  <button
                    key={role.id}
                    onClick={() => setCurrentRole(role.id)}
                    className={`group relative w-full flex items-center gap-4 p-5 rounded-2xl border text-left transition-all duration-300 overflow-hidden ${
                      isSelected
                        ? "border-rw-green bg-rw-green/5 ring-1 ring-rw-green shadow-sm"
                        : "border-rw-border bg-rw-surface hover:border-rw-ink-secondary hover:shadow-sm"
                    }`}
                  >
                    {isSelected && <div className="absolute inset-0 bg-gradient-to-r from-rw-green/10 to-transparent opacity-50" />}
                    <div className={`relative p-3 rounded-xl transition-colors ${isSelected ? "bg-rw-green text-white" : "bg-rw-surface-alt text-rw-ink-secondary group-hover:text-rw-ink"}`}>
                      <Icon size={22} strokeWidth={isSelected ? 2.5 : 2} />
                    </div>
                    <span className={`relative text-lg font-medium transition-colors ${isSelected ? "text-rw-green" : "text-rw-ink"}`}>
                      {role.label}
                    </span>
                  </button>
                );
              })}
            </div>
          </div>
        )}

        {step === 2 && (
          <div className="animate-in fade-in slide-in-from-right-8 duration-500 flex-1">
            <h1 className="font-serif tracking-tight text-4xl text-rw-ink mb-3">Set your target</h1>
            <p className="text-rw-ink-secondary mb-10 text-lg">We'll filter out the noise and focus on what matters for this level.</p>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {[
                { id: "sde_2", label: "Mid-Level (SDE II)", icon: Briefcase },
                { id: "sde_3", label: "Senior (SDE III)", icon: Star },
                { id: "staff", label: "Staff", icon: Rocket },
                { id: "principal", label: "Principal+", icon: Crown },
              ].map((role) => {
                const Icon = role.icon;
                const isSelected = targetRole === role.id;
                return (
                  <button
                    key={role.id}
                    onClick={() => setTargetRole(role.id)}
                    className={`group relative w-full flex items-center gap-4 p-5 rounded-2xl border text-left transition-all duration-300 overflow-hidden ${
                      isSelected
                        ? "border-rw-green bg-rw-green/5 ring-1 ring-rw-green shadow-sm"
                        : "border-rw-border bg-rw-surface hover:border-rw-ink-secondary hover:shadow-sm"
                    }`}
                  >
                    {isSelected && <div className="absolute inset-0 bg-gradient-to-r from-rw-green/10 to-transparent opacity-50" />}
                    <div className={`relative p-3 rounded-xl transition-colors ${isSelected ? "bg-rw-green text-white" : "bg-rw-surface-alt text-rw-ink-secondary group-hover:text-rw-ink"}`}>
                      <Icon size={22} strokeWidth={isSelected ? 2.5 : 2} />
                    </div>
                    <span className={`relative text-lg font-medium transition-colors ${isSelected ? "text-rw-green" : "text-rw-ink"}`}>
                      {role.label}
                    </span>
                  </button>
                );
              })}
            </div>
          </div>
        )}

        {step === 3 && (
          <div className="animate-in fade-in slide-in-from-right-8 duration-500 flex-1">
            <h1 className="font-serif tracking-tight text-4xl text-rw-ink mb-3">Pacing & Timeline</h1>
            <p className="text-rw-ink-secondary mb-10 text-lg">Tell us your timeline so we can optimize your study cadence.</p>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {[
                { id: "2_weeks", label: "Next 2 weeks", desc: "Intense review", icon: "🔥" },
                { id: "1_month", label: "Next month", desc: "Steady pacing", icon: "🚀" },
                { id: "3_months", label: "3+ months out", desc: "Deep mastery", icon: "🧠" },
                { id: "browsing", label: "Just browsing", desc: "No pressure", icon: "👀" },
              ].map((t) => {
                const isSelected = timeline === t.id;
                return (
                  <button
                    key={t.id}
                    onClick={() => setTimeline(t.id)}
                    className={`group relative flex flex-col items-start p-6 rounded-2xl border text-left transition-all duration-300 overflow-hidden ${
                      isSelected
                        ? "border-rw-green bg-rw-green/5 ring-1 ring-rw-green shadow-sm scale-[1.02]"
                        : "border-rw-border bg-rw-surface hover:border-rw-ink-secondary hover:shadow-sm"
                    }`}
                  >
                    {isSelected && <div className="absolute inset-0 bg-gradient-to-br from-rw-green/10 to-transparent opacity-50" />}
                    <span className="relative text-3xl mb-3">{t.icon}</span>
                    <span className={`relative text-lg font-medium mb-1 transition-colors ${isSelected ? "text-rw-green" : "text-rw-ink"}`}>
                      {t.label}
                    </span>
                    <span className={`relative text-sm transition-colors ${isSelected ? "text-rw-green/80" : "text-rw-ink-muted group-hover:text-rw-ink-secondary"}`}>
                      {t.desc}
                    </span>
                  </button>
                );
              })}
            </div>
          </div>
        )}

        {/* Footer Navigation */}
        <div className="mt-auto pt-10 flex items-center justify-between border-t border-rw-border/50">
          <button
            onClick={() => setStep(Math.max(1, step - 1) as Step)}
            className={`px-5 py-2.5 rounded-xl text-rw-ink-secondary hover:text-rw-ink hover:bg-rw-surface-alt transition-all font-medium ${step === 1 ? 'invisible' : 'visible'}`}
          >
            Back
          </button>

          <button
            onClick={handleNext}
            disabled={
              (step === 1 && !currentRole) ||
              (step === 2 && !targetRole) ||
              (step === 3 && (!timeline || isSubmitting))
            }
            className="group relative flex items-center gap-2 bg-rw-ink text-white px-8 py-3.5 rounded-xl font-bold shadow-lg hover:shadow-xl hover:-translate-y-0.5 disabled:opacity-50 disabled:hover:translate-y-0 disabled:cursor-not-allowed transition-all overflow-hidden"
          >
            {/* Shimmer effect */}
            <div className="absolute inset-0 -translate-x-full bg-gradient-to-r from-transparent via-white/20 to-transparent group-hover:animate-[shimmer_1.5s_infinite]" />
            
            <span className="relative flex items-center gap-2">
              {isSubmitting ? (
                <>
                  <Loader2 size={20} className="animate-spin" />
                  Finalizing...
                </>
              ) : (
                <>
                  {step === 3 ? "Complete Setup" : "Continue"}
                  {step === 3 ? (
                    <Sparkles size={20} className="text-rw-green group-hover:scale-110 transition-transform" />
                  ) : (
                    <ArrowRight size={20} className="group-hover:translate-x-1 transition-transform" />
                  )}
                </>
              )}
            </span>
          </button>
        </div>
      </div>
    </div>
  );
}
