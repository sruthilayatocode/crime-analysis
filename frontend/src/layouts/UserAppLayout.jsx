import React from 'react';
import { Outlet } from 'react-router-dom';
import UserBottomNav from '../components/user/UserBottomNav';
import FloatingSOSButton from '../components/user/FloatingSOSButton';
import SOSOnboardingModal from '../components/user/SOSOnboardingModal';
import SOSCountdownModal from '../components/user/SOSCountdownModal';
import ActiveSOSOverlay from '../components/user/ActiveSOSOverlay';
import RedZoneWarningModal from '../components/user/RedZoneWarningModal';
import RedZoneSimulatorModal from '../components/user/RedZoneSimulatorModal';
import { SOSProvider } from '../context/SOSContext';

/**
 * UserAppLayout: Strictly mobile-first container (375px-430px centered).
 * Encapsulates the entire SOS safety lifecycle, mandatory onboarding,
 * 5s cancel countdown, Red Zone inactivity 60s warning, and live emergency overlays.
 */
export default function UserAppLayout() {
  return (
    <SOSProvider>
      <div className="min-h-screen bg-slate-900 flex justify-center items-stretch antialiased selection:bg-red-600 selection:text-white">
        <div className="w-full max-w-[430px] min-h-screen bg-slate-50 text-slate-900 flex flex-col relative shadow-2xl overflow-x-hidden border-x border-slate-200/80">
          {/* Main page content area */}
          <main className="flex-1 flex flex-col pb-16 relative">
            <Outlet />
          </main>

          {/* Floating always-visible Red SOS Button with 2s hold */}
          <FloatingSOSButton />

          {/* Bottom Tab Navigation */}
          <UserBottomNav />

          {/* Mandatory Onboarding Modal for SOS Contacts */}
          <SOSOnboardingModal />

          {/* 5-Second Cancel Countdown Modal */}
          <SOSCountdownModal />

          {/* 60-Second Red Zone Inactivity 'Are you safe?' Modal */}
          <RedZoneWarningModal />

          {/* Dev-Mode Simulator Controls */}
          <RedZoneSimulatorModal />

          {/* Active SOS Distress Screen with 'I'm Safe' & 112 Call */}
          <ActiveSOSOverlay />
        </div>
      </div>
    </SOSProvider>
  );
}

