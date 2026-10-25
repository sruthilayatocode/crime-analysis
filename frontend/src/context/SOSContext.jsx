import React, { createContext, useContext, useState, useEffect, useRef, useCallback } from 'react';
import { useAuth } from './AuthContext';
import { sosService, playAlertBeep } from '../services/sosService';
import {
  requestNotificationPermission,
  triggerSOSNotification,
  listenToForegroundMessages,
  sosContactsStore,
} from '../services/firebase';

const SOSContext = createContext(null);

export function SOSProvider({ children }) {
  const { user } = useAuth();

  // Initialize immediately from persistent store so reload NEVER loses contacts
  const [contacts, setContacts] = useState(() => sosContactsStore.getStoredContacts());
  const [loadingContacts, setLoadingContacts] = useState(false);
  const [onboardingRequired, setOnboardingRequired] = useState(false);
  const [notificationPermissionGranted, setNotificationPermissionGranted] = useState(false);

  // SOS Trigger & 5s Countdown State
  const [isCountingDown, setIsCountingDown] = useState(false);
  const [countdown, setCountdown] = useState(5);
  const [activeSosEvent, setActiveSosEvent] = useState(null);
  const [isLiveTracking, setIsLiveTracking] = useState(false);
  const [sosStatusMessage, setSosStatusMessage] = useState('');
  const [triggering, setTriggering] = useState(false);

  // Red Zone Inactivity State Machine
  const [redZoneState, setRedZoneState] = useState('SAFE'); // 'SAFE' | 'IN_RED' | 'WARNING' | 'AUTO_ALERT_SENT'
  const [isWarningActive, setIsWarningActive] = useState(false);
  const [warningCountdown, setWarningCountdown] = useState(60);
  const [currentZone, setCurrentZone] = useState('green');
  const [simulatorOpen, setSimulatorOpen] = useState(false);

  // Interaction & Heartbeat tracking
  const hasInteractedRef = useRef(false);
  const lastLocationRef = useRef(null);
  const countdownTimerRef = useRef(null);
  const trackingIntervalRef = useRef(null);
  const heartbeatIntervalRef = useRef(null);
  const warningTimerRef = useRef(null);

  // Attach global interaction listeners (touch, click, scroll, keydown)
  useEffect(() => {
    const markInteraction = () => {
      hasInteractedRef.current = true;
    };

    window.addEventListener('touchstart', markInteraction, { passive: true });
    window.addEventListener('click', markInteraction, { passive: true });
    window.addEventListener('scroll', markInteraction, { passive: true });
    window.addEventListener('keydown', markInteraction, { passive: true });

    return () => {
      window.removeEventListener('touchstart', markInteraction);
      window.removeEventListener('click', markInteraction);
      window.removeEventListener('scroll', markInteraction);
      window.removeEventListener('keydown', markInteraction);
    };
  }, []);

  // Request Firebase / Browser Push Notification permission & listen to FCM events
  const requestPushPermission = useCallback(async () => {
    try {
      const res = await requestNotificationPermission();
      if (res && res.granted) {
        setNotificationPermissionGranted(true);
      }
      return res;
    } catch {
      return { granted: false };
    }
  }, []);

  useEffect(() => {
    requestPushPermission();

    // Listen to incoming Firebase Cloud Messaging push events
    let unsubscribe = () => {};
    listenToForegroundMessages((payload) => {
      console.log('[SOSContext] Foreground SOS message:', payload);
    }).then((unsub) => {
      if (typeof unsub === 'function') unsubscribe = unsub;
    });

    return () => {
      unsubscribe();
    };
  }, [requestPushPermission]);

  // Keep persistent storage updated whenever contacts change
  useEffect(() => {
    if (contacts && contacts.length > 0) {
      sosContactsStore.persistContacts(contacts);
    }
  }, [contacts]);

  // Load contacts and check onboarding whenever user changes
  const refreshContacts = useCallback(async () => {
    const cached = sosContactsStore.getStoredContacts();
    if (cached && cached.length > 0) {
      setContacts(cached);
      setOnboardingRequired(false);
    }

    if (!user) {
      // User is logging in or guest: Keep persistent contacts so reload never loses them!
      return;
    }

    setLoadingContacts(true);
    try {
      const data = await sosService.getOnboardingStatus();
      if (data && data.contacts && data.contacts.length > 0) {
        setContacts(data.contacts);
        sosContactsStore.persistContacts(data.contacts);
        setOnboardingRequired(false);
      } else if (cached && cached.length > 0) {
        // If database was empty for this user, automatically restore cached contacts to backend!
        try {
          await sosService.bulkSaveContacts(cached);
          setContacts(cached);
          setOnboardingRequired(false);
        } catch {
          setContacts(cached);
          setOnboardingRequired(false);
        }
      } else {
        setContacts([]);
        setOnboardingRequired(true);
      }
    } catch (err) {
      // If network fails or session expired, NEVER wipe cached contacts!
      if (cached && cached.length > 0) {
        setContacts(cached);
        setOnboardingRequired(false);
      }
    } finally {
      setLoadingContacts(false);
    }
  }, [user]);

  // Check for active SOS event underway on server
  const checkActiveEvent = useCallback(async () => {
    if (!user) return;
    try {
      const res = await sosService.getActiveSOSEvent();
      if (res.active && res.event) {
        setActiveSosEvent(res.event);
        setIsLiveTracking(true);
      } else {
        setActiveSosEvent(null);
        setIsLiveTracking(false);
      }
    } catch (err) {
      console.error('[SOSContext] Error checking active SOS:', err);
    }
  }, [user]);

  useEffect(() => {
    refreshContacts();
    checkActiveEvent();
  }, [refreshContacts, checkActiveEvent]);

  // Helper to obtain current GPS location
  const getCurrentLocation = () => {
    return new Promise((resolve) => {
      if (!navigator.geolocation) {
        resolve({ latitude: 12.9165, longitude: 79.1325, accuracy: 50, zone: currentZone });
        return;
      }
      navigator.geolocation.getCurrentPosition(
        (pos) => {
          resolve({
            latitude: pos.coords.latitude,
            longitude: pos.coords.longitude,
            accuracy: pos.coords.accuracy,
            zone: currentZone,
          });
        },
        () => {
          resolve({ latitude: 12.9165, longitude: 79.1325, accuracy: 100, zone: currentZone });
        },
        { enableHighAccuracy: true, timeout: 6000, maximumAge: 10000 }
      );
    });
  };

  // Heartbeat loop every 30 seconds
  const sendHeartbeatPing = useCallback(async () => {
    if (!user) return;
    if (localStorage.getItem('crimesense_setting_location_access') === 'false') {
      // Location access is turned off by user
      setRedZoneState('SAFE');
      setIsWarningActive(false);
      return;
    }

    try {
      const loc = await getCurrentLocation();
      const hadInteraction = hasInteractedRef.current;
      hasInteractedRef.current = false; // reset interaction flag

      const res = await sosService.sendHeartbeat({
        latitude: loc.latitude,
        longitude: loc.longitude,
        accuracy: loc.accuracy,
        zone: loc.zone || currentZone,
        has_interaction: hadInteraction,
      });

      setRedZoneState(res.state || 'SAFE');
      setCurrentZone(res.zone || 'green');

      if (res.warning_active && !isWarningActive) {
        triggerWarningPrompt(res.seconds_remaining || 60);
      } else if (!res.warning_active && isWarningActive) {
        setIsWarningActive(false);
      }

      if (res.state === 'AUTO_ALERT_SENT') {
        checkActiveEvent();
      }
    } catch {
      // Ignore background sync errors
    }
  }, [user, currentZone, isWarningActive, checkActiveEvent]);

  useEffect(() => {
    if (user) {
      sendHeartbeatPing();
      heartbeatIntervalRef.current = setInterval(sendHeartbeatPing, 30000); // 30s heartbeat
    }
    return () => {
      if (heartbeatIntervalRef.current) clearInterval(heartbeatIntervalRef.current);
    };
  }, [user, sendHeartbeatPing]);

  // Trigger the 60-second "Are you safe?" prompt
  const triggerWarningPrompt = (remainingSeconds = 60) => {
    setIsWarningActive(true);
    setWarningCountdown(remainingSeconds);
    playAlertBeep(600, 0.3);

    // Trigger Web Notification
    if ('Notification' in window && Notification.permission === 'granted') {
      try {
        new Notification('CrimeSense Safety Check', {
          body: 'You have been stationary in a high-risk RED zone. Are you safe? Please check in within 60s.',
          icon: '/favicon.ico',
          tag: 'red-zone-warning',
          requireInteraction: true,
        });
      } catch {}
    }
  };

  // Warning countdown timer effect
  useEffect(() => {
    if (isWarningActive) {
      warningTimerRef.current = setInterval(() => {
        setWarningCountdown((prev) => {
          if (prev <= 1) {
            clearInterval(warningTimerRef.current);
            setIsWarningActive(false);
            checkActiveEvent();
            return 0;
          }
          if (prev % 10 === 0 || prev <= 5) {
            playAlertBeep(750, 0.15);
          }
          return prev - 1;
        });
      }, 1000);
    } else {
      if (warningTimerRef.current) clearInterval(warningTimerRef.current);
    }
    return () => {
      if (warningTimerRef.current) clearInterval(warningTimerRef.current);
    };
  }, [isWarningActive, checkActiveEvent]);

  // User Safety Check-in ("I'm Safe" tap)
  const confirmSafetyCheckin = async () => {
    setIsWarningActive(false);
    if (warningTimerRef.current) clearInterval(warningTimerRef.current);
    try {
      await sosService.safetyCheckin();
      setRedZoneState('IN_RED');
    } catch (err) {
      console.error('Check-in error:', err);
    }
  };

  // Manual SOS Trigger execution
  const executeSOSTrigger = async () => {
    setTriggering(true);
    setIsCountingDown(false);
    setSosStatusMessage('Capturing coordinates & dispatching emergency alerts...');

    try {
      const loc = await getCurrentLocation();
      const res = await sosService.triggerSOS({
        latitude: loc.latitude,
        longitude: loc.longitude,
        accuracy: loc.accuracy,
        zone: loc.zone || 'red',
        type: 'manual',
      });

      if (res.success && res.event) {
        setActiveSosEvent(res.event);
        setIsLiveTracking(true);
        setSosStatusMessage('Emergency SOS active! Contacts notified via SMS & Push.');

        // Dispatch Firebase / Native Push Notification
        triggerSOSNotification({
          title: '🚨 CRIMESENSE SOS DISTRESS ALERT DISPATCHED',
          body: `Emergency distress alert active at (${loc.latitude.toFixed(4)}, ${loc.longitude.toFixed(4)}). Live location broadcasted to ${contacts.length} emergency contact(s)!`,
          urgent: true,
          data: {
            latitude: String(loc.latitude),
            longitude: String(loc.longitude),
            zone: loc.zone || 'red',
          },
        });
      }
    } catch (err) {
      console.error('[SOSContext] Failed to trigger SOS:', err);
      setSosStatusMessage(`Failed to trigger SOS: ${err.message}`);
    } finally {
      setTriggering(false);
    }
  };

  // Start 5-second countdown for SOS button
  const startSOSCountdown = () => {
    if (activeSosEvent) return;
    if (contacts.length === 0) {
      setOnboardingRequired(true);
      return;
    }
    setCountdown(5);
    setIsCountingDown(true);
    playAlertBeep(880, 0.2);
  };

  const cancelCountdown = () => {
    setIsCountingDown(false);
    setCountdown(5);
    if (countdownTimerRef.current) {
      clearInterval(countdownTimerRef.current);
      countdownTimerRef.current = null;
    }
  };

  useEffect(() => {
    if (isCountingDown) {
      countdownTimerRef.current = setInterval(() => {
        setCountdown((prev) => {
          if (prev <= 1) {
            clearInterval(countdownTimerRef.current);
            countdownTimerRef.current = null;
            executeSOSTrigger();
            return 0;
          }
          playAlertBeep(700 + (6 - prev) * 60, 0.12);
          return prev - 1;
        });
      }, 1000);
    } else {
      if (countdownTimerRef.current) {
        clearInterval(countdownTimerRef.current);
        countdownTimerRef.current = null;
      }
    }
    return () => {
      if (countdownTimerRef.current) clearInterval(countdownTimerRef.current);
    };
  }, [isCountingDown]);

  // Live tracking loop when SOS is active
  useEffect(() => {
    if (activeSosEvent && isLiveTracking) {
      trackingIntervalRef.current = setInterval(async () => {
        try {
          const loc = await getCurrentLocation();
          await sosService.updateLiveSOSLocation(activeSosEvent.id, loc);
        } catch {}
      }, 20000);
    } else {
      if (trackingIntervalRef.current) {
        clearInterval(trackingIntervalRef.current);
        trackingIntervalRef.current = null;
      }
    }
    return () => {
      if (trackingIntervalRef.current) clearInterval(trackingIntervalRef.current);
    };
  }, [activeSosEvent, isLiveTracking]);

  // Resolve active SOS ("I'm Safe")
  const resolveSOS = async () => {
    if (!activeSosEvent) return;
    try {
      await sosService.resolveSOSEvent(activeSosEvent.id);
      setActiveSosEvent(null);
      setIsLiveTracking(false);
      setSosStatusMessage('Distress alert resolved. Contacts received all-clear notice.');
    } catch (err) {
      console.error('[SOSContext] Error resolving SOS:', err);
      alert(`Could not resolve SOS: ${err.message}`);
    }
  };

  const extendLiveLocationSharing = async () => {
    if (!activeSosEvent) return;
    try {
      await sosService.extendLiveTracking(activeSosEvent.id);
      setIsLiveTracking(true);
      alert('Live location tracking extended for 1 hour.');
    } catch (err) {
      alert(`Failed to extend tracking: ${err.message}`);
    }
  };

  const value = {
    contacts,
    loadingContacts,
    onboardingRequired,
    setOnboardingRequired,
    refreshContacts,
    // SOS trigger & countdown
    isCountingDown,
    countdown,
    triggering,
    startSOSCountdown,
    cancelCountdown,
    executeSOSTriggerNow: executeSOSTrigger,
    // Active SOS event
    activeSosEvent,
    isLiveTracking,
    sosStatusMessage,
    resolveSOS,
    extendLiveLocationSharing,
    // Red Zone Inactivity & Heartbeat
    redZoneState,
    setRedZoneState,
    currentZone,
    setCurrentZone,
    isWarningActive,
    warningCountdown,
    confirmSafetyCheckin,
    triggerWarningPrompt,
    sendHeartbeatPing,
    // Dev Simulator
    simulatorOpen,
    setSimulatorOpen,
    // Push & Firebase Notifications
    requestPushPermission,
    notificationPermissionGranted,
  };

  return <SOSContext.Provider value={value}>{children}</SOSContext.Provider>;
}

export function useSOS() {
  const context = useContext(SOSContext);
  if (!context) {
    throw new Error('useSOS must be used within an SOSProvider');
  }
  return context;
}
