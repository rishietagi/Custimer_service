import React, { useState, useEffect, useRef } from 'react';
import { api } from '../services/api';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Phone, PhoneOff, Mic, MicOff, Volume2, VolumeX, Play, RotateCcw, 
  Loader2, AlertCircle, Calendar, ShieldCheck, MapPin, Sparkles, CheckCircle2
} from 'lucide-react';

interface CallCenterProps {
  user: any;
  onRefreshDashboard: () => void;
}

const STATES_META: Record<string, { label: string; progress: number }> = {
  "HOME_MENU": { label: "IVR Greeting", progress: 10 },
  "PRODUCT_CATEGORY": { label: "Appliance Category", progress: 25 },
  "PRODUCT_MODEL": { label: "Model Number", progress: 40 },
  "PRODUCT_PURCHASE_DATE": { label: "Purchase Date", progress: 50 },
  "PRODUCT_WARRANTY": { label: "Warranty Check", progress: 60 },
  "PRODUCT_SERIAL": { label: "Serial Number", progress: 70 },
  "PRODUCT_INSTALL_DATE": { label: "Installation Date", progress: 75 },
  "ISSUE_COLLECTION": { label: "Describe Issue", progress: 80 },
  "ISSUE_EXPLANATION": { label: "Issue Details", progress: 85 },
  "CONFIRM_DETAILS_BEFORE_BOOKING": { label: "Review Details", progress: 90 },
  "SERVICE_ADDRESS": { label: "Service Address", progress: 95 },
  "SERVICE_SCHEDULE": { label: "Date & Time Selection", progress: 98 },
  "BOOKING_CONFIRMATION": { label: "Booking Completed", progress: 100 },
  "TICKET_SUBMITTED": { label: "Ticket Registered", progress: 100 }
};

export const CallCenter: React.FC<CallCenterProps> = ({ user, onRefreshDashboard }) => {
  const [callSession, setCallSession] = useState<any>(null);
  const [callActive, setCallActive] = useState(false);
  const [connecting, setConnecting] = useState(false);
  const [callDuration, setCallDuration] = useState(0);
  const [isMuted, setIsMuted] = useState(false);
  const [volume, setVolume] = useState(0.8);
  const [continuousListening, setContinuousListening] = useState(true);
  const [silenceTimeout, setSilenceTimeout] = useState(3); // default 3 seconds
  
  const [voiceStatus, setVoiceStatus] = useState<'idle' | 'listening' | 'transcribing' | 'thinking' | 'speaking'>('idle');
  const [liveTranscript, setLiveTranscript] = useState('');
  const [transcriptHistory, setTranscriptHistory] = useState<any[]>([]);
  const [ttsWarning, setTtsWarning] = useState('');
  const [errorMsg, setErrorMsg] = useState('');

  // Post-call summary & booking states
  const [finalSummary, setFinalSummary] = useState<string | null>(null);
  const [bookingSummary, setBookingSummary] = useState<any | null>(null);

  // Refs for audio and speech recording
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const audioPlayerRef = useRef<HTMLAudioElement | null>(null);
  const timerIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const silenceTimerRef = useRef<NodeJS.Timeout | null>(null);
  const recognitionRef = useRef<any>(null);
  const speechLimitTimerRef = useRef<NodeJS.Timeout | null>(null);
  const lastResultIndexRef = useRef(0);
  const finalTranscriptRef = useRef('');

  // Web Speech API
  const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
  const isSpeechSupported = !!SpeechRecognition;

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      endCallCleanup();
    };
  }, []);

  // Update audio volume when adjusted
  useEffect(() => {
    if (audioPlayerRef.current) {
      audioPlayerRef.current.volume = isMuted ? 0 : volume;
    }
  }, [volume, isMuted]);

  // Duration Timer Effect
  useEffect(() => {
    if (callActive) {
      timerIntervalRef.current = setInterval(() => {
        setCallDuration(prev => prev + 1);
      }, 1000);
    } else {
      if (timerIntervalRef.current) {
        clearInterval(timerIntervalRef.current);
      }
    }
    return () => {
      if (timerIntervalRef.current) clearInterval(timerIntervalRef.current);
    };
  }, [callActive]);

  const formatDuration = (secs: number) => {
    const m = Math.floor(secs / 60).toString().padStart(2, '0');
    const s = (secs % 60).toString().padStart(2, '0');
    return `${m}:${s}`;
  };

  // State Refs to prevent stale closure capturing in callbacks
  const callActiveRef = useRef(callActive);
  const voiceStatusRef = useRef(voiceStatus);
  const continuousListeningRef = useRef(continuousListening);
  const silenceTimeoutRef = useRef(silenceTimeout);
  const callSessionRef = useRef(callSession);
  const transcriptHistoryRef = useRef(transcriptHistory);

  useEffect(() => {
    callActiveRef.current = callActive;
  }, [callActive]);

  useEffect(() => {
    voiceStatusRef.current = voiceStatus;
  }, [voiceStatus]);

  useEffect(() => {
    continuousListeningRef.current = continuousListening;
  }, [continuousListening]);

  useEffect(() => {
    silenceTimeoutRef.current = silenceTimeout;
  }, [silenceTimeout]);

  useEffect(() => {
    callSessionRef.current = callSession;
  }, [callSession]);

  useEffect(() => {
    transcriptHistoryRef.current = transcriptHistory;
  }, [transcriptHistory]);

  const speakTextFallback = (text: string) => {
    if (isMuted) return;
    stopAudioPlayback();
    setTtsWarning('');
    try {
      const cleanText = text
        .replace(/<[^>]*>/g, '') 
        .replace(/\*\*/g, '')    
        .replace(/###/g, '')     
        .trim();

      if (typeof window !== 'undefined' && window.speechSynthesis) {
        const utterance = new SpeechSynthesisUtterance(cleanText);
        utterance.lang = 'en-US';
        utterance.volume = volume;

        utterance.onstart = () => {
          setVoiceStatus('speaking');
        };

        utterance.onend = () => {
          setVoiceStatus('idle');
          if (callActiveRef.current) {
            startListeningForUserSpeech();
          }
        };

        utterance.onerror = (e) => {
          console.error("SpeechSynthesis error", e);
          setVoiceStatus('idle');
        };

        window.speechSynthesis.cancel();
        window.speechSynthesis.speak(utterance);
      }
    } catch (err) {
      console.error("Browser fallback speech failed", err);
      setVoiceStatus('idle');
    }
  };

  const playAudioResponse = (audioBase64: string, textFallback?: string) => {
    if (isMuted) return;
    stopAudioPlayback();
    setTtsWarning('');

    try {
      const audioUrl = `data:audio/wav;base64,${audioBase64}`;
      const audio = new Audio(audioUrl);
      audioPlayerRef.current = audio;
      audio.volume = volume;
      setVoiceStatus('speaking');

      audio.onended = () => {
        setVoiceStatus('idle');
        audioPlayerRef.current = null;
        if (callActiveRef.current) {
          startListeningForUserSpeech();
        }
      };

      audio.onerror = () => {
        console.warn("TTS Audio element failed, running browser fallback SpeechSynthesis");
        if (textFallback) {
          speakTextFallback(textFallback);
        } else {
          setVoiceStatus('idle');
        }
      };

      audio.play().catch((err) => {
        console.warn("Blocked playback or device error", err);
        if (textFallback) {
          speakTextFallback(textFallback);
        } else {
          setVoiceStatus('idle');
        }
      });
    } catch (err) {
      console.error("Audio playback instantiation failed", err);
      if (textFallback) {
        speakTextFallback(textFallback);
      } else {
        setVoiceStatus('idle');
      }
    }
  };

  const stopAudioPlayback = () => {
    if (audioPlayerRef.current) {
      audioPlayerRef.current.pause();
      audioPlayerRef.current = null;
    }
    if (typeof window !== 'undefined' && window.speechSynthesis) {
      window.speechSynthesis.cancel();
    }
    setVoiceStatus('idle');
  };

  const replayLastResponse = () => {
    const currentSession = callSessionRef.current;
    const currentHistory = transcriptHistoryRef.current;
    if (!currentSession || !currentHistory.length) return;
    const assistantMsgs = currentHistory.filter(m => m.role === 'assistant');
    if (assistantMsgs.length > 0) {
      const lastMsg = assistantMsgs[assistantMsgs.length - 1];
      if (currentSession.audio) {
        playAudioResponse(currentSession.audio, lastMsg.content);
      } else {
        speakTextFallback(lastMsg.content);
      }
    }
  };

  // Start Voice Listening (Browser Microphones)
  const startListeningForUserSpeech = async () => {
    if (!callActiveRef.current) return;
    stopAudioPlayback();
    setErrorMsg('');
    setLiveTranscript('');
    setVoiceStatus('listening');
    audioChunksRef.current = [];
    finalTranscriptRef.current = '';

    try {
      // 1. Initialize Web Audio MediaRecorder
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      let options = {};
      if (MediaRecorder.isTypeSupported('audio/webm')) {
        options = { mimeType: 'audio/webm' };
      }
      const mediaRecorder = new MediaRecorder(stream, options);
      mediaRecorderRef.current = mediaRecorder;

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        stream.getTracks().forEach(track => track.stop());
        if (callActiveRef.current) {
          await submitUserVoice(audioBlob);
        }
      };

      // 2. Initialize Web Speech Recognition for Live Text & Silence Detection
      if (isSpeechSupported) {
        const recognition = new SpeechRecognition();
        recognition.continuous = true;
        recognition.interimResults = true;
        recognition.lang = 'en-US';

        recognition.onresult = (event: any) => {
          let interimTranscript = '';
          for (let i = event.resultIndex; i < event.results.length; ++i) {
            if (event.results[i].isFinal) {
              finalTranscriptRef.current += event.results[i][0].transcript;
            } else {
              interimTranscript += event.results[i][0].transcript;
            }
          }
          const currentText = finalTranscriptRef.current + interimTranscript;
          setLiveTranscript(currentText);
          
          // Set a hard 5-second speaking limit from the moment they start talking
          if (currentText.trim() && !speechLimitTimerRef.current) {
            speechLimitTimerRef.current = setTimeout(() => {
              triggerVoiceSubmit();
            }, 5000);
          }

          // Clear standard silence timer if speaking limit is active to prevent early trigger on pause
          if (silenceTimerRef.current) {
            clearTimeout(silenceTimerRef.current);
            silenceTimerRef.current = null;
          }
        };

        recognition.onend = () => {
          // Restart recognition if listening was active and user didn't trigger submit
          if (voiceStatusRef.current === 'listening' && callActiveRef.current) {
            try {
              recognition.start();
            } catch (e) {}
          }
        };

        recognitionRef.current = recognition;
        recognition.start();
      }

      mediaRecorder.start();

      // Trigger automatic silence timeout if in continuous listening mode
      if (continuousListeningRef.current) {
        resetSilenceTimer();
      }
    } catch (err) {
      console.error("Microphone access failed", err);
      setVoiceStatus('idle');
      setErrorMsg('Microphone access denied or unsupported. Please check your browser audio settings.');
    }
  };

  const resetSilenceTimer = () => {
    if (silenceTimerRef.current) {
      clearTimeout(silenceTimerRef.current);
    }
    if (continuousListeningRef.current && callActiveRef.current) {
      if (isSpeechSupported) {
        // Absolute safety timeout of 12 seconds of absolute silence before auto submitting
        silenceTimerRef.current = setTimeout(() => {
          triggerVoiceSubmit();
        }, 12000);
      } else {
        // Fallback for non-supported browsers
        silenceTimerRef.current = setTimeout(() => {
          triggerVoiceSubmit();
        }, 5000);
      }
    }
  };

  const stopListening = () => {
    if (silenceTimerRef.current) {
      clearTimeout(silenceTimerRef.current);
      silenceTimerRef.current = null;
    }
    if (speechLimitTimerRef.current) {
      clearTimeout(speechLimitTimerRef.current);
      speechLimitTimerRef.current = null;
    }
    if (recognitionRef.current) {
      recognitionRef.current.onend = null;
      recognitionRef.current.stop();
      recognitionRef.current = null;
    }
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop();
    }
  };

  const triggerVoiceSubmit = () => {
    stopListening();
  };

  const submitUserVoice = async (audioBlob: Blob) => {
    const currentSession = callSessionRef.current;
    if (!currentSession) return;
    setVoiceStatus('transcribing');
    setErrorMsg('');

    try {
      const res = await api.calls.sendVoice(currentSession.call_id, audioBlob);
      setVoiceStatus('thinking');

      setCallSession(res);
      setTranscriptHistory(res.transcript || []);
      
      const isBookingDone = res.chat_data?.appointment_id;
      if (isBookingDone) {
        setBookingSummary(res.chat_data);
      }

      const finalStates = ["BOOKING_CONFIRMATION", "TICKET_SUBMITTED", "ORDER_CALLBACK_CONFIRM", "ORDER_ESCALATE_CONFIRM"];
      if (finalStates.includes(res.current_state)) {
        // Complete the call automatically since flow is done
        handleEndCall(res.call_id);
        onRefreshDashboard();
        return;
      }

      // Play audio response or voice fallback
      if (res.audio) {
        playAudioResponse(res.audio, res.latest_message);
      } else if (res.latest_message) {
        speakTextFallback(res.latest_message);
      } else {
        setVoiceStatus('idle');
      }

    } catch (err: any) {
      console.error("Voice response submit failed", err);
      setErrorMsg(err.response?.data?.detail || 'Transcription / response generation failed.');
      setVoiceStatus('idle');
      // Let user retry or manually end call
    }
  };

  // Start Call Function
  const handleStartCall = async () => {
    setConnecting(true);
    setErrorMsg('');
    setFinalSummary(null);
    setBookingSummary(null);
    setTranscriptHistory([]);
    setCallDuration(0);

    try {
      const session = await api.calls.start(user.user_id);
      setCallSession(session);
      setCallActive(true);
      setTranscriptHistory(session.transcript || []);

      // Voice greeting
      if (session.audio) {
        playAudioResponse(session.audio, session.latest_message);
      } else {
        speakTextFallback(session.latest_message);
      }
    } catch (err) {
      console.error("Failed to start voice call", err);
      setErrorMsg("Failed to connect with Appliance Call Center. Check Groq API configuration.");
    } finally {
      setConnecting(false);
    }
  };

  // End Call Function
  const handleEndCall = async (callIdToStop?: string) => {
    const currentSession = callSessionRef.current;
    const id = callIdToStop || currentSession?.call_id;
    if (!id) return;
    
    stopListening();
    stopAudioPlayback();
    setCallActive(false);
    setConnecting(true);

    try {
      const finalSess = await api.calls.end(id);
      setCallSession(finalSess);
      setFinalSummary(finalSess.summary);
      setTranscriptHistory(finalSess.transcript || []);
      
      // If we finished booking, give user a quick spoken confirmation
      if (finalSess.appointment_id) {
        speakTextFallback("Your appointment has been successfully scheduled.");
      }
    } catch (err) {
      console.error("Failed to terminate call session", err);
      setErrorMsg("Call ended, but database log summary could not be saved.");
    } finally {
      setConnecting(false);
    }
  };

  const endCallCleanup = () => {
    stopListening();
    stopAudioPlayback();
    if (timerIntervalRef.current) clearInterval(timerIntervalRef.current);
    if (silenceTimerRef.current) clearTimeout(silenceTimerRef.current);
  };

  const currentState = callSession?.current_state || "HOME_MENU";
  const stateMeta = STATES_META[currentState] || { label: "Voice Support", progress: 50 };

  return (
    <div className="space-y-6">
      {/* Visual Header Banner */}
      <div className="bg-gradient-to-r from-slate-900 to-indigo-950 rounded-2xl p-6 md:p-8 text-white relative overflow-hidden shadow-premium">
        <div className="absolute right-0 bottom-0 top-0 w-1/3 opacity-10 pointer-events-none">
          <svg className="w-full h-full" viewBox="0 0 100 100" preserveAspectRatio="none">
            <path d="M0,100 C30,40 70,60 100,0 L100,100 Z" fill="currentColor"></path>
          </svg>
        </div>
        <div className="relative z-10 space-y-2 max-w-2xl">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-brand-red/20 border border-brand-red/30 text-brand-red text-xs font-semibold uppercase tracking-wider">
            <Phone className="w-3.5 h-3.5" />
            Voice Support System
          </div>
          <h2 className="text-2xl md:text-3xl font-extrabold tracking-tight">Call Center Agent Simulation</h2>
          <p className="text-slate-300 text-sm md:text-base leading-relaxed">
            Experience appliance support through a voice-first connection. Guide our support engineer to file cases, schedule home repair technician visits, or track shipments using natural spoken conversation.
          </p>
        </div>
      </div>

      {errorMsg && (
        <div className="bg-red-50 text-brand-red text-sm p-4 rounded-xl border border-red-200 flex items-center gap-3 animate-shake">
          <AlertCircle className="w-5 h-5 shrink-0" />
          <span>{errorMsg}</span>
        </div>
      )}

      {/* Main Grid Dashboard */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Left Column: Call Connection & Audio Widgets */}
        <div className="lg:col-span-1 space-y-6">
          <div className="bg-white rounded-2xl border border-gray-200 shadow-sm overflow-hidden flex flex-col justify-between h-[450px]">
            {/* Header Connection State */}
            <div className="p-4 border-b border-gray-100 flex items-center justify-between bg-gray-50/50">
              <div className="flex items-center gap-2">
                <div className={`w-2.5 h-2.5 rounded-full ${callActive ? 'bg-green-500 animate-pulse' : 'bg-gray-400'}`}></div>
                <span className="text-xs font-bold text-gray-500 uppercase tracking-wider">
                  {callActive ? 'Active Call' : connecting ? 'Connecting...' : 'Call Offline'}
                </span>
              </div>
              {callActive && (
                <span className="text-sm font-bold font-mono text-gray-700 bg-gray-100 px-2.5 py-1 rounded-md">
                  {formatDuration(callDuration)}
                </span>
              )}
            </div>

            {/* Core Waveform & Animation Visualizer */}
            <div className="flex-1 flex flex-col items-center justify-center p-6 relative">
              <AnimatePresence mode="wait">
                {callActive ? (
                  <motion.div 
                    key="call-active"
                    initial={{ opacity: 0, scale: 0.9 }}
                    animate={{ opacity: 1, scale: 1 }}
                    exit={{ opacity: 0, scale: 0.9 }}
                    className="flex flex-col items-center justify-center space-y-6 w-full"
                  >
                    {/* Animated SVG Waveform Reacting to Voice status */}
                    <div className="w-48 h-20 flex items-center justify-center gap-1.5 px-4">
                      {Array.from({ length: 14 }).map((_, idx) => {
                        let duration = 0.8 + (idx % 3) * 0.2;
                        let heightArr = [10, 40, 20, 60, 15, 80, 25, 75];
                        let targetHeight = heightArr[idx % heightArr.length];
                        
                        if (voiceStatus === 'idle') targetHeight = 4;
                        if (voiceStatus === 'listening') targetHeight = targetHeight * 0.5;
                        if (voiceStatus === 'transcribing') targetHeight = 6;
                        if (voiceStatus === 'thinking') targetHeight = 12;

                        return (
                          <motion.div
                            key={idx}
                            className={`w-1.5 rounded-full ${
                              voiceStatus === 'speaking' 
                                ? 'bg-brand-red' 
                                : voiceStatus === 'listening' 
                                ? 'bg-indigo-500' 
                                : 'bg-gray-300'
                            }`}
                            animate={{
                              height: [4, targetHeight, 4]
                            }}
                            transition={{
                              repeat: Infinity,
                              duration: voiceStatus === 'thinking' ? 1.5 : duration,
                              ease: "easeInOut"
                            }}
                            style={{ minHeight: '4px' }}
                          />
                        );
                      })}
                    </div>

                    {/* Spoken UI State Label */}
                    <div className="text-center space-y-1">
                      <span className="text-xs font-semibold text-gray-400 uppercase tracking-widest block">
                        {voiceStatus === 'listening' 
                          ? 'Listening to you' 
                          : voiceStatus === 'transcribing'
                          ? 'Transcribing audio'
                          : voiceStatus === 'thinking'
                          ? 'Processing request'
                          : voiceStatus === 'speaking'
                          ? 'Assistant is speaking'
                          : 'Connected'}
                      </span>
                      <p className="text-lg font-bold text-gray-800 capitalize animate-pulse">
                        {voiceStatus === 'idle' ? 'Ready to Speak' : `${voiceStatus}...`}
                      </p>
                    </div>
                  </motion.div>
                ) : (
                  <motion.div 
                    key="call-offline"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className="text-center space-y-4 max-w-[200px]"
                  >
                    <div className="w-20 h-20 bg-gray-100 rounded-full flex items-center justify-center mx-auto text-gray-400 border border-gray-200 shadow-inner">
                      <Phone className="w-8 h-8" />
                    </div>
                    <div className="space-y-1">
                      <h4 className="text-sm font-bold text-gray-800">No Call Connected</h4>
                      <p className="text-xs text-gray-500">Initiate a call to connect to appliance repair services.</p>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>

            {/* Bottom Call Buttons */}
            <div className="p-6 border-t border-gray-100 bg-gray-50/50">
              {callActive ? (
                <button
                  onClick={() => handleEndCall()}
                  disabled={connecting}
                  className="w-full flex items-center justify-center gap-2 py-3.5 bg-brand-red text-white font-bold rounded-xl shadow-premium hover:bg-brand-redHover transition-all duration-150 active:scale-[0.98] disabled:opacity-50"
                >
                  {connecting ? (
                    <Loader2 className="w-5 h-5 animate-spin" />
                  ) : (
                    <PhoneOff className="w-5 h-5" />
                  )}
                  End Call
                </button>
              ) : (
                <button
                  onClick={handleStartCall}
                  disabled={connecting}
                  className="w-full flex items-center justify-center gap-2 py-3.5 bg-green-600 text-white font-bold rounded-xl shadow-premium hover:bg-green-700 transition-all duration-150 active:scale-[0.98] disabled:opacity-50"
                >
                  {connecting ? (
                    <Loader2 className="w-5 h-5 animate-spin" />
                  ) : (
                    <Phone className="w-5 h-5" />
                  )}
                  Start Call
                </button>
              )}
            </div>
          </div>

          {/* Audio & Mic Settings Panel */}
          <div className="bg-white rounded-2xl border border-gray-200 p-5 shadow-sm space-y-4">
            <h3 className="text-xs font-extrabold uppercase tracking-wider text-gray-400">Audio Controls</h3>
            
            {/* Audio Settings Rows */}
            <div className="space-y-3">
              {/* Mute button & Replay */}
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setIsMuted(!isMuted)}
                  disabled={!callActive}
                  className={`flex-1 flex items-center justify-center gap-2 py-2 px-3 border rounded-lg text-sm font-semibold transition-all ${
                    isMuted 
                      ? 'bg-red-50 border-red-200 text-brand-red hover:bg-red-100' 
                      : 'bg-white border-gray-200 text-gray-700 hover:bg-gray-50'
                  } disabled:opacity-40`}
                >
                  {isMuted ? <MicOff className="w-4 h-4" /> : <Mic className="w-4 h-4" />}
                  {isMuted ? 'Unmute' : 'Mute Mic'}
                </button>
                <button
                  onClick={replayLastResponse}
                  disabled={!callActive || voiceStatus === 'speaking'}
                  className="flex-1 flex items-center justify-center gap-2 py-2 px-3 bg-white border border-gray-200 text-gray-700 rounded-lg text-sm font-semibold hover:bg-gray-50 transition-all disabled:opacity-40"
                >
                  <Play className="w-4 h-4" />
                  Replay Voice
                </button>
              </div>

              {/* Volume Slider */}
              <div className="space-y-1">
                <div className="flex items-center justify-between text-xs font-semibold text-gray-500">
                  <span>Speaker Volume</span>
                  <span>{Math.round(volume * 100)}%</span>
                </div>
                <div className="flex items-center gap-2">
                  <VolumeX className="w-4 h-4 text-gray-400" />
                  <input
                    type="range"
                    min="0"
                    max="1"
                    step="0.05"
                    value={volume}
                    onChange={(e) => setVolume(parseFloat(e.target.value))}
                    className="flex-1 h-1.5 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-indigo-600"
                  />
                  <Volume2 className="w-4 h-4 text-gray-400" />
                </div>
              </div>
            </div>

            <hr className="border-gray-100" />

            {/* Continuous / Silence Timeout Configuration */}
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h4 className="text-xs font-bold text-gray-700">Continuous Voice Detection</h4>
                  <p className="text-[10px] text-gray-400">Auto submit after silence</p>
                </div>
                <button
                  onClick={() => setContinuousListening(!continuousListening)}
                  className={`w-11 h-6 rounded-full p-1 transition-colors duration-200 ease-in-out focus:outline-none ${
                    continuousListening ? 'bg-indigo-600' : 'bg-gray-200'
                  }`}
                >
                  <div
                    className={`bg-white w-4 h-4 rounded-full shadow-md transform duration-200 ease-in-out ${
                      continuousListening ? 'translate-x-5' : 'translate-x-0'
                    }`}
                  />
                </button>
              </div>

              {continuousListening && (
                <div className="space-y-1">
                  <div className="flex items-center justify-between text-xs font-semibold text-gray-500">
                    <span>Silence Timeout</span>
                    <span>{silenceTimeout}s</span>
                  </div>
                  <input
                    type="range"
                    min="1.5"
                    max="5"
                    step="0.5"
                    value={silenceTimeout}
                    onChange={(e) => setSilenceTimeout(parseFloat(e.target.value))}
                    className="w-full h-1.5 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-indigo-600"
                  />
                </div>
              )}

              {!isSpeechSupported && (
                <div className="text-[10px] text-amber-600 bg-amber-50 p-2 rounded border border-amber-100 flex gap-1.5 items-start">
                  <AlertCircle className="w-3.5 h-3.5 shrink-0" />
                  <span>Real-time voice parsing not supported in this browser. Running push-to-talk instead.</span>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Middle and Right Column Combined: Transcription & Workflow */}
        <div className="lg:col-span-2 space-y-6">
          {/* Active Call Workflow Stepper Tracker */}
          {callActive && (
            <div className="bg-white rounded-2xl border border-gray-200 p-5 shadow-sm space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-indigo-600 uppercase bg-indigo-50 px-2.5 py-1 rounded-md">
                  Active Workflow
                </span>
                <span className="text-sm font-bold text-gray-800">
                  {stateMeta.label}
                </span>
              </div>
              
              {/* Progress Slider */}
              <div className="relative pt-1">
                <div className="overflow-hidden h-2 text-xs flex rounded bg-gray-100">
                  <div 
                    style={{ width: `${stateMeta.progress}%` }} 
                    className="shadow-none flex flex-col text-center whitespace-nowrap text-white justify-center bg-indigo-600 transition-all duration-300"
                  ></div>
                </div>
                <div className="flex justify-between text-[10px] text-gray-400 font-semibold mt-1">
                  <span>Welcome / IVR</span>
                  <span>Category & Model</span>
                  <span>Warranty Check</span>
                  <span>Scheduling</span>
                  <span>Done</span>
                </div>
              </div>
            </div>
          )}

          {/* Transcript History & Live Transcription Panel */}
          <div className="bg-white rounded-2xl border border-gray-200 shadow-sm flex flex-col h-[520px]">
            {/* Panel Title */}
            <div className="p-4 border-b border-gray-100 flex items-center justify-between">
              <h3 className="text-sm font-extrabold uppercase tracking-wider text-gray-700">Live Transcript</h3>
              {callActive && voiceStatus === 'listening' && (
                <span className="text-xs text-indigo-600 font-semibold animate-pulse flex items-center gap-1.5">
                  <Mic className="w-3.5 h-3.5" />
                  Mic Active
                </span>
              )}
            </div>

            {/* Scrollable Conversation Stream */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-slate-50/50">
              {transcriptHistory.length === 0 ? (
                <div className="h-full flex flex-col items-center justify-center text-gray-400 text-xs text-center space-y-2 select-none">
                  <Phone className="w-8 h-8 opacity-40" />
                  <p>When the call begins, the dialogue stream will print here.</p>
                </div>
              ) : (
                transcriptHistory.map((msg, index) => {
                  const isUser = msg.role === 'user';
                  return (
                    <div 
                      key={index} 
                      className={`flex ${isUser ? 'justify-end' : 'justify-start'} animate-fade-in`}
                    >
                      <div 
                        className={`max-w-[85%] rounded-2xl px-4 py-3 text-sm shadow-sm ${
                          isUser 
                            ? 'bg-indigo-600 text-white rounded-tr-none' 
                            : 'bg-white border border-gray-100 text-gray-800 rounded-tl-none'
                        }`}
                      >
                        <p className="leading-relaxed whitespace-pre-wrap">{msg.content}</p>
                        <span className={`text-[10px] mt-1 block text-right font-medium ${isUser ? 'text-indigo-200' : 'text-gray-400'}`}>
                          {isUser ? 'You' : 'Assistant'}
                        </span>
                      </div>
                    </div>
                  );
                })
              )}
              
              {/* Interim / Live speech recognition overlay */}
              {callActive && liveTranscript && (
                <div className="flex justify-end animate-fade-in">
                  <div className="max-w-[85%] bg-indigo-50 border border-indigo-100 text-indigo-700 rounded-2xl rounded-tr-none px-4 py-3 text-sm italic shadow-inner">
                    <p className="leading-relaxed">{liveTranscript}</p>
                    <span className="text-[10px] mt-1 block text-right font-bold text-indigo-400 animate-pulse">
                      Speaking...
                    </span>
                  </div>
                </div>
              )}
            </div>

            {/* Push-to-Talk active button overlay */}
            {callActive && !continuousListening && (
              <div className="p-4 border-t border-gray-100 bg-white flex justify-center">
                <button
                  onMouseDown={startListeningForUserSpeech}
                  onMouseUp={triggerVoiceSubmit}
                  onTouchStart={startListeningForUserSpeech}
                  onTouchEnd={triggerVoiceSubmit}
                  className={`flex items-center gap-2 px-6 py-3 rounded-xl font-bold transition-all shadow-md active:scale-95 ${
                    voiceStatus === 'listening' 
                      ? 'bg-brand-red text-white' 
                      : 'bg-indigo-600 text-white hover:bg-indigo-700'
                  }`}
                >
                  <Mic className="w-5 h-5" />
                  {voiceStatus === 'listening' ? 'Release to Send' : 'Hold to Speak (Push-to-Talk)'}
                </button>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Structured Call Summary & Booking sheets at the end */}
      <AnimatePresence>
        {!callActive && (finalSummary || bookingSummary) && (
          <motion.div 
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            className="grid grid-cols-1 md:grid-cols-2 gap-6"
          >
            {/* Call Summary Sheet */}
            {finalSummary && (
              <div className="bg-white rounded-2xl border border-gray-200 p-6 shadow-premium relative overflow-hidden">
                <div className="absolute right-0 top-0 w-24 h-24 bg-indigo-50 rounded-bl-full flex items-center justify-end p-4 text-indigo-400 opacity-20 pointer-events-none">
                  <CheckCircle2 className="w-12 h-12" />
                </div>
                <div className="space-y-4">
                  <div className="flex items-center gap-2">
                    <span className="w-1.5 h-6 bg-indigo-600 rounded-full"></span>
                    <h3 className="text-lg font-bold text-gray-800">Call Summary Details</h3>
                  </div>
                  
                  {/* Parse Key Value Summary content */}
                  <div className="bg-slate-50 border border-gray-100 rounded-xl p-4 font-mono text-xs text-gray-700 leading-relaxed whitespace-pre-line space-y-1">
                    {finalSummary}
                  </div>
                </div>
              </div>
            )}

            {/* Appointment Booking Sheet */}
            {bookingSummary && (
              <div className="bg-white rounded-2xl border border-gray-200 p-6 shadow-premium relative overflow-hidden">
                <div className="absolute right-0 top-0 w-24 h-24 bg-green-50 rounded-bl-full flex items-center justify-end p-4 text-green-400 opacity-20 pointer-events-none">
                  <Calendar className="w-12 h-12" />
                </div>
                <div className="space-y-4">
                  <div className="flex items-center gap-2">
                    <span className="w-1.5 h-6 bg-green-500 rounded-full"></span>
                    <h3 className="text-lg font-bold text-gray-800">Booking Confirmation</h3>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <div className="bg-gray-50 p-3.5 rounded-xl border border-gray-100">
                      <p className="text-[10px] uppercase tracking-wider font-extrabold text-gray-400">Appointment ID</p>
                      <p className="text-sm font-bold text-gray-800 mt-0.5">{bookingSummary.appointment_id}</p>
                    </div>
                    <div className="bg-gray-50 p-3.5 rounded-xl border border-gray-100">
                      <p className="text-[10px] uppercase tracking-wider font-extrabold text-gray-400">Product</p>
                      <p className="text-sm font-bold text-gray-800 mt-0.5">{bookingSummary.category} ({bookingSummary.model_number})</p>
                    </div>
                    <div className="bg-gray-50 p-3.5 rounded-xl border border-gray-100">
                      <p className="text-[10px] uppercase tracking-wider font-extrabold text-gray-400">Technician</p>
                      <p className="text-sm font-bold text-gray-800 mt-0.5">{bookingSummary.technician_name || 'Certified Tech'}</p>
                    </div>
                    <div className="bg-gray-50 p-3.5 rounded-xl border border-gray-100">
                      <p className="text-[10px] uppercase tracking-wider font-extrabold text-gray-400">Date & Slot</p>
                      <p className="text-sm font-bold text-gray-800 mt-0.5">{bookingSummary.preferred_date} | {bookingSummary.preferred_time_slot}</p>
                    </div>
                    <div className="bg-gray-50 p-3.5 rounded-xl border border-gray-100 sm:col-span-2">
                      <div className="flex items-start gap-1.5">
                        <MapPin className="w-4 h-4 text-gray-400 shrink-0 mt-0.5" />
                        <div>
                          <p className="text-[10px] uppercase tracking-wider font-extrabold text-gray-400">Service Address</p>
                          <p className="text-xs font-semibold text-gray-700 mt-0.5">
                            {bookingSummary.service_address}, {bookingSummary.service_city} - {bookingSummary.service_pincode}
                          </p>
                        </div>
                      </div>
                    </div>
                  </div>

                  <div className="bg-green-50 border border-green-200 text-green-700 text-xs px-4 py-3 rounded-xl flex items-center gap-2">
                    <ShieldCheck className="w-5 h-5 shrink-0" />
                    <span>Your technician appointment was logged successfully. You can track or reschedule this anytime under the appointments planner.</span>
                  </div>
                </div>
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};
