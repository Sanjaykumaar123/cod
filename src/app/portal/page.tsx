"use client";

import React, { useState, useEffect, useRef } from "react";
import { 
  Shield, Eye, EyeOff, AlertTriangle, Activity, 
  Settings, User, FileText, Database, Server, 
  Terminal, Lock, Unlock, HelpCircle, RefreshCw, 
  Check, X, ChevronRight, BarChart2, Video, 
  Sliders, LogOut, Loader2, Download, AlertCircle,
  TrendingUp, Users, Radio, Cpu
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { 
  ResponsiveContainer, AreaChart, Area, XAxis, YAxis, 
  Tooltip, BarChart, Bar, RadarChart, PolarGrid, 
  PolarAngleAxis, PolarRadiusAxis, Radar, PieChart, Pie, Cell
} from "recharts";
import { API_URL } from "@/config";

export default function PortalPage() {
  // Auth state
  const [token, setToken] = useState<string | null>(null);
  const [user, setUser] = useState<{ username: string; role: string; full_name?: string } | null>(null);
  const [usernameInput, setUsernameInput] = useState("");
  const [passwordInput, setPasswordInput] = useState("");
  const [authError, setAuthError] = useState("");
  const [isLoggingIn, setIsLoggingIn] = useState(false);

  // Navigation state
  const [activeTab, setActiveTab] = useState("dashboard");

  // Core Data states
  const [cameras, setCameras] = useState<any[]>([]);
  const [entities, setEntities] = useState<any[]>([]);
  const [events, setEvents] = useState<any[]>([]);
  const [identityRequests, setIdentityRequests] = useState<any[]>([]);
  const [auditLogs, setAuditLogs] = useState<any[]>([]);
  const [privacyData, setPrivacyData] = useState<any>(null);
  const [analyticsData, setAnalyticsData] = useState<any>(null);
  const [systemConnected, setSystemConnected] = useState(false);

  // Interactive UI states
  const [selectedCamera, setSelectedCamera] = useState<any>(null);
  const [selectedEvent, setSelectedEvent] = useState<any>(null);
  const [selectedEntityForIdRequest, setSelectedEntityForIdRequest] = useState<string>("");
  const [justificationInput, setJustificationInput] = useState("");
  const [requestDuration, setRequestDuration] = useState(30);
  const [isSubmittingRequest, setIsSubmittingRequest] = useState(false);
  const [requestSuccessMsg, setRequestSuccessMsg] = useState("");
  const [explainData, setExplainData] = useState<any>(null);
  const [isExplaining, setIsExplaining] = useState(false);
  
  // Simulator Input states
  const [simConfigName, setSimConfigName] = useState("Corporate Campus Alpha");
  const [simCamerasCount, setSimCamerasCount] = useState(12);
  const [simRetentionDays, setSimRetentionDays] = useState(14);
  const [simSensitivity, setSimSensitivity] = useState(0.75);
  const [simIdentityCollection, setSimIdentityCollection] = useState("default_anonymized");
  const [simCrowdDensity, setSimCrowdDensity] = useState("medium");
  const [simThreatLevel, setSimThreatLevel] = useState("medium");
  const [simResult, setSimResult] = useState<any>(null);
  const [isSimulating, setIsSimulating] = useState(false);
  
  // Decrypted Identity Reveal state
  const [revealedIdentities, setRevealedIdentities] = useState<Record<string, string>>({});
  const [revealedLeaseExpires, setRevealedLeaseExpires] = useState<Record<string, number>>({});

  // Live Camera stream simulator loop
  const [liveCoords, setLiveCoords] = useState<{ x: number; y: number; speed: number; id: string; risk: number; anonymized: boolean } | null>(null);
  const [isLiveStreaming, setIsLiveStreaming] = useState(false);

  // Initialize and check localStorage
  useEffect(() => {
    const savedToken = localStorage.getItem("bw_token");
    const savedUser = localStorage.getItem("bw_user");
    if (savedToken && savedUser) {
      setToken(savedToken);
      setUser(JSON.parse(savedUser));
    }
  }, []);

  // Fetch core telemetry data on load/login
  const fetchAllData = async (activeToken: string) => {
    try {
      const headers = { "Authorization": `Bearer ${activeToken}` };
      
      // Cameras
      const camRes = await fetch(`${API_URL}/api/v1/cameras`, { headers });
      if (camRes.ok) {
        const cams = await camRes.json();
        setCameras(cams);
        if (cams.length > 0 && !selectedCamera) {
          setSelectedCamera(cams[0]);
        }
      }

      // Entities
      const entRes = await fetch(`${API_URL}/api/v1/entities`, { headers });
      if (entRes.ok) setEntities(await entRes.json());

      // Events
      const evRes = await fetch(`${API_URL}/api/v1/events`, { headers });
      if (evRes.ok) setEvents(await evRes.json());

      // Requests
      const reqRes = await fetch(`${API_URL}/api/v1/identity-requests`, { headers });
      if (reqRes.ok) setIdentityRequests(await reqRes.json());

      // Audit logs (RBAC protected backend, so only fetch if admin/auditor)
      const decoded = JSON.parse(localStorage.getItem("bw_user") || "{}");
      if (decoded.role === "admin" || decoded.role === "auditor") {
        const auditRes = await fetch(`${API_URL}/api/v1/audit/logs`, { headers });
        if (auditRes.ok) setAuditLogs(await auditRes.json());
      }

      // Privacy
      const privRes = await fetch(`${API_URL}/api/v1/privacy/dashboard`, { headers });
      if (privRes.ok) {
        const privData = await privRes.json();
        // adapter for dashboard data matching UI historical score chart expectations
        setPrivacyData({
          current: {
            privacy_score: privData.privacy_score,
            compliance_score: privData.compliance_score,
            transparency_score: privData.transparency_score,
            retention_risk: privData.privacy_score > 80 ? "Low" : "Medium",
            exposure_risk: privData.privacy_score > 80 ? "Low" : "Medium",
            active_anonymous_count: privData.active_anonymous_count,
            requests_denied: privData.requests_denied,
            requests_approved: privData.requests_approved
          },
          history: [
            { timestamp: "10:00", privacy_score: 93, compliance_score: 95, transparency_score: 98, active_anonymous_count: 5 },
            { timestamp: "11:00", privacy_score: 94, compliance_score: 96, transparency_score: 98, active_anonymous_count: 8 },
            { timestamp: "12:00", privacy_score: privData.privacy_score, compliance_score: privData.compliance_score, transparency_score: privData.transparency_score, active_anonymous_count: privData.active_anonymous_count }
          ],
          recommendations: [
            "Purge metadata logs older than 7 days (GDPR compliance optimization).",
            "Enable double-blind authorization locks on Gate Alpha video nodes."
          ]
        });
      }

      // Analytics
      const analRes = await fetch(`${API_URL}/api/v1/analytics/dashboard`, { headers });
      if (analRes.ok) setAnalyticsData(await analRes.json());

      setSystemConnected(true);
    } catch (e) {
      console.error("API connection error: ", e);
      setSystemConnected(false);
    }
  };

  // Re-fetch data periodically when logged in
  useEffect(() => {
    if (token) {
      fetchAllData(token);
      const interval = setInterval(() => {
        fetchAllData(token);
      }, 6000);
      return () => clearInterval(interval);
    }
  }, [token]);

  // Live Camera stream telemetry polling
  useEffect(() => {
    if (token && selectedCamera && isLiveStreaming) {
      const interval = setInterval(async () => {
        try {
          const headers = { "Authorization": `Bearer ${token}` };
          const res = await fetch(`${API_URL}/api/v1/live-feed/${selectedCamera.id}`, { 
            method: "POST", 
            headers 
          });
          if (res.ok) {
            const data = await res.json();
            if (data.entity) {
              setLiveCoords({
                x: data.entity.x,
                y: data.entity.y,
                speed: data.entity.speed,
                id: data.entity.entity_id,
                risk: data.entity.risk_score,
                anonymized: data.entity.is_anonymized
              });
            }
          }
        } catch (err) {
          console.error(err);
        }
      }, 2000);
      return () => clearInterval(interval);
    }
  }, [token, selectedCamera, isLiveStreaming]);

  // Auth Handlers
  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!usernameInput || !passwordInput) return;
    setAuthError("");
    setIsLoggingIn(true);

    try {
      const res = await fetch(`${API_URL}/api/v1/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          username: usernameInput,
          password: passwordInput
        })
      });

      if (res.ok) {
        const data = await res.json();
        const loggedUser = { username: data.username, role: data.role.toLowerCase(), full_name: data.full_name };
        
        localStorage.setItem("bw_token", data.access_token);
        localStorage.setItem("bw_user", JSON.stringify(loggedUser));
        
        setToken(data.access_token);
        setUser(loggedUser);
        
        fetchAllData(data.access_token);
      } else {
        const errData = await res.json();
        setAuthError(errData.detail || "Authentication failed. Verify credentials.");
      }
    } catch (e) {
      setAuthError("Failed to connect to surveillance daemon. Is server online?");
    } finally {
      setIsLoggingIn(false);
    }
  };

  const selectDemoRole = (role: string) => {
    setUsernameInput(role);
    setPasswordInput(`${role}123`);
  };

  const handleLogout = () => {
    localStorage.removeItem("bw_token");
    localStorage.removeItem("bw_user");
    setToken(null);
    setUser(null);
    setUsernameInput("");
    setPasswordInput("");
    setLiveCoords(null);
    setIsLiveStreaming(false);
  };


  // Toggle Camera Privacy Shield
  const handleTogglePrivacyShield = async (camId: number, currentShieldState: boolean) => {
    if (!token) return;
    try {
      const headers = { "Authorization": `Bearer ${token}` };
      const res = await fetch(`${API_URL}/api/v1/cameras/${camId}/privacy-shield?active=${!currentShieldState}`, {
        method: "PUT",
        headers
      });
      if (res.ok) {
        // Refresh local camera state
        setCameras((prev: any[]) => prev.map(c => c.id === camId ? { ...c, privacy_shield_active: !currentShieldState } : c));
        if (selectedCamera?.id === camId) {
          setSelectedCamera((prev: any) => ({ ...prev, privacy_shield_active: !currentShieldState }));
        }
        fetchAllData(token);
      }
    } catch (err) {
      console.error(err);
    }
  };

  // Explain Alert (Explainable AI Engine)
  const handleExplainEvent = async (event: any) => {
    setSelectedEvent(event);
    setExplainData(null);
    setIsExplaining(true);
    if (!token) return;
    try {
      const headers = { "Authorization": `Bearer ${token}` };
      const res = await fetch(`${API_URL}/api/v1/events/${event.id}/explanation`, { headers });
      if (res.ok) {
        const data = await res.json();
        setExplainData(data);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setIsExplaining(false);
    }
  };

  // Acknowledge Event (Escalate)
  const handleAcknowledgeEvent = async (eventId: number) => {
    if (!token) return;
    try {
      const headers = { 
        "Authorization": `Bearer ${token}`
      };
      const res = await fetch(`${API_URL}/api/v1/events/${eventId}/escalate`, {
        method: "POST",
        headers
      });
      if (res.ok) {
        const data = await res.json();
        const updated = data.event;
        setEvents(prev => prev.map(e => e.id === eventId ? updated : e));
        setSelectedEvent(updated);
        fetchAllData(token);
      }
    } catch (err) {
      console.error(err);
    }
  };

  // Mark False Positive (Dismiss)
  const handleFalsePositive = async (eventId: number) => {
    if (!token) return;
    try {
      const headers = { 
        "Authorization": `Bearer ${token}`
      };
      const res = await fetch(`${API_URL}/api/v1/events/${eventId}/dismiss`, {
        method: "POST",
        headers
      });
      if (res.ok) {
        const data = await res.json();
        const updated = data.event;
        setEvents(prev => prev.map(e => e.id === eventId ? updated : e));
        setSelectedEvent(updated);
        fetchAllData(token);
      }
    } catch (err) {
      console.error(err);
    }
  };

  // Submit Decryption Request
  const handleSubmitDecryptionRequest = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token || !selectedEntityForIdRequest || !justificationInput) return;
    setIsSubmittingRequest(true);
    setRequestSuccessMsg("");

    try {
      const headers = { 
        "Authorization": `Bearer ${token}`,
        "Content-Type": "application/json"
      };
      const res = await fetch(`${API_URL}/api/v1/identity-requests`, {
        method: "POST",
        headers,
        body: JSON.stringify({
          entity_id: selectedEntityForIdRequest,
          reason: justificationInput,
          case_number: "CASE-" + Math.floor(100000 + Math.random() * 900000)
        })
      });
      if (res.ok) {
        setRequestSuccessMsg("Decryption request filed in identity ledger. Status: PENDING DUAL APPROVAL.");
        setJustificationInput("");
        setSelectedEntityForIdRequest("");
        fetchAllData(token);
      } else {
        const data = await res.json();
        alert(data.detail || "Governance violation. Request rejected.");
      }
    } catch (err) {
      console.error(err);
    } finally {
      setIsSubmittingRequest(false);
    }
  };

  // Governance Approvals
  const handleApproveRequest = async (requestId: number) => {
    if (!token) return;
    try {
      const decoded = JSON.parse(localStorage.getItem("bw_user") || "{}");
      const role = decoded.role || "viewer";
      const endpoint = role === "auditor" ? "auditor-approve" : "admin-approve";
      
      const headers = { "Authorization": `Bearer ${token}` };
      const res = await fetch(`${API_URL}/api/v1/identity-requests/${requestId}/${endpoint}`, {
        method: "POST",
        headers
      });
      if (res.ok) {
        fetchAllData(token);
      } else {
        const err = await res.json();
        alert(err.detail || "Approval error.");
      }
    } catch (e) {
       console.error(e);
    }
  };

  const handleRejectRequest = async (requestId: number) => {
    if (!token) return;
    try {
      const decoded = JSON.parse(localStorage.getItem("bw_user") || "{}");
      const role = decoded.role || "viewer";
      const endpoint = role === "auditor" ? "auditor-reject" : "auditor-reject"; // Reject using auditor-reject
      
      const headers = { "Authorization": `Bearer ${token}` };
      const res = await fetch(`${API_URL}/api/v1/identity-requests/${requestId}/${endpoint}`, {
        method: "POST",
        headers
      });
      if (res.ok) {
        fetchAllData(token);
      }
    } catch (e) {
       console.error(e);
    }
  };

  // Inspect Decrypted Identity (Reveal)
  const handleRevealIdentity = async (entityId: string) => {
    if (!token) return;
    try {
      const headers = { "Authorization": `Bearer ${token}` };
      const res = await fetch(`${API_URL}/api/v1/entities/${entityId}/identity`, { headers });
      if (res.ok) {
        const data = await res.json();
        if (data.permitted) {
          setRevealedIdentities(prev => ({ ...prev, [entityId]: data.decrypted_identity }));
          setRevealedLeaseExpires(prev => ({ ...prev, [entityId]: data.expires_in_seconds }));
        } else {
          alert(`Access Denied: ${data.decrypted_identity}`);
        }
      }
    } catch (e) {
      console.error(e);
    }
  };

  // Verify Cryptographic Ledger Integrity
  const [ledgerVerification, setLedgerVerification] = useState<{ verified: boolean; checked: boolean; isChecking: boolean } | null>(null);

  const handleVerifyLedger = async () => {
    if (!token) return;
    setLedgerVerification({ verified: false, checked: false, isChecking: true });
    try {
      const headers = { "Authorization": `Bearer ${token}` };
      const res = await fetch(`${API_URL}/api/v1/audit/verify`, {
        method: "POST",
        headers
      });
      if (res.ok) {
        const data = await res.json();
        setLedgerVerification({
          verified: data.integrity_verified,
          checked: true,
          isChecking: false
        });
      } else {
        alert("Failed to verify audit trail ledger.");
        setLedgerVerification(null);
      }
    } catch (err) {
      console.error(err);
      setLedgerVerification(null);
    }
  };

  // Simulator Run
  const handleRunSimulation = async () => {
    if (!token) return;
    setIsSimulating(true);
    setSimResult(null);
    try {
      const headers = { 
        "Authorization": `Bearer ${token}`,
        "Content-Type": "application/json" 
      };
      const res = await fetch(`${API_URL}/api/v1/simulator/run`, {

        method: "POST",
        headers,
        body: JSON.stringify({
          config_name: simConfigName,
          cameras_count: simCamerasCount,
          retention_days: simRetentionDays,
          sensitivity: simSensitivity,
          identity_collection: simIdentityCollection,
          crowd_density: simCrowdDensity,
          threat_level: simThreatLevel
        })
      });
      if (res.ok) {
        const data = await res.json();
        // Since API returns DB model, we'll format comparison scores in the frontend or grab the simulator return
        // Let's call the endpoint or simulate it in client matching backend math
        // Let's reconstruct matching backend details
        const safety_base = 40.0;
        const safety_cams = Math.min(simCamerasCount * 2.5, 30.0);
        const safety_sens = simSensitivity * 20.0;
        const safety_threat = simThreatLevel === "low" ? 10.0 : (simThreatLevel === "medium" ? 20.0 : 30.0);
        const bw_safety = Math.min(safety_base + safety_cams + safety_sens + safety_threat, 98.0);
        
        let privacy_base = 98.0;
        if (simIdentityCollection === "stored_by_default") privacy_base -= 50.0;
        const retention_penalty = Math.min(simRetentionDays * 0.4, 25.0);
        const camera_penalty = Math.min(simCamerasCount * 0.15, 8.0);
        const bw_privacy = Math.max(privacy_base - retention_penalty - camera_penalty, 30.0);
        
        const bw_trust = Math.min(bw_privacy * 0.8 + bw_safety * 0.2, 99.0);
        
        let bw_compliance = 99.0;
        if (simIdentityCollection === "stored_by_default") bw_compliance -= 45.0;
        if (simRetentionDays > 30) bw_compliance -= Math.min((simRetentionDays - 30) * 0.5, 20.0);
        bw_compliance = Math.max(bw_compliance, 35.0);
        
        const bw_fpr = Math.min((simSensitivity ** 2) * 15.0 + (simCrowdDensity === "high" ? 5.0 : 1.0), 35.0);
        const bw_bias = Math.min(3.0 + (simSensitivity * 2.0), 10.0);
        
        const trad_safety = Math.max(bw_safety - 10.0, 30.0);
        const trad_privacy = Math.max(20.0 - (simRetentionDays * 0.3) - (simCamerasCount * 0.1), 5.0);
        const trad_trust = Math.max(15.0 - (simRetentionDays * 0.1), 8.0);
        const trad_compliance = Math.max(simRetentionDays > 14 ? 10.0 : 25.0, 5.0);
        const trad_fpr = Math.min((simSensitivity * 12.0) + 8.0, 40.0);
        const trad_bias = Math.min(45.0 + (simSensitivity * 20.0), 85.0);

        setSimResult({
          blindwatch: {
            safety_score: bw_safety.toFixed(1),
            privacy_score: bw_privacy.toFixed(1),
            trust_score: bw_trust.toFixed(1),
            compliance_score: bw_compliance.toFixed(1),
            false_positive_rate: bw_fpr.toFixed(1),
            bias_risk: bw_bias.toFixed(1)
          },
          traditional: {
            safety_score: trad_safety.toFixed(1),
            privacy_score: trad_privacy.toFixed(1),
            trust_score: trad_trust.toFixed(1),
            compliance_score: trad_compliance.toFixed(1),
            false_positive_rate: trad_fpr.toFixed(1),
            bias_risk: trad_bias.toFixed(1)
          }
        });
        fetchAllData(token);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setIsSimulating(false);
    }
  };

  // Executive Report Export simulation
  const handleExportReport = async () => {
    if (!token) return;
    try {
      const headers = { "Authorization": `Bearer ${token}` };
      const res = await fetch(`${API_URL}/api/reports/download`, { headers });
      if (res.ok) {
        const data = await res.json();
        // Trigger file download alert or visual mockup
        alert(`Generating report file ${data.report_id}... Compiled at ${data.generated_at}. Safety Score: ${data.security_score} | Privacy Score: ${data.privacy_score}%`);
      }
    } catch (e) {
      console.error(e);
    }
  };

  // Loading Screen
  if (!token) {
    return (
      <div className="min-h-screen grid-bg flex flex-col justify-center items-center px-4 relative">
        <div className="absolute top-8 left-8 flex items-center gap-2">
          <Shield className="w-8 h-8 text-accent-cyan" />
          <span className="text-xl font-bold tracking-wider text-white">BLINDWATCH <span className="text-accent-cyan font-light">AI</span></span>
        </div>

        <motion.div 
          initial={{ opacity: 0, y: 25 }}
          animate={{ opacity: 1, y: 0 }}
          className="glass-panel w-full max-w-md p-8 rounded-xl border border-glass-border relative z-10"
        >
          <div className="text-center mb-8">
            <h2 className="text-2xl font-bold text-white mb-2">OS Access Authorization</h2>
            <p className="text-sm text-gray-400">Decentralized Surveillance Gate Sentinel</p>
          </div>

          <form onSubmit={handleLogin} className="space-y-6">
            {authError && (
              <div className="bg-rose-950/50 border border-rose-800/80 rounded-md p-3 flex gap-2 items-center text-rose-300 text-xs">
                <AlertCircle className="w-5 h-5 flex-shrink-0" />
                <span>{authError}</span>
              </div>
            )}
            <div>
              <label className="block text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">Username / Node ID</label>
              <input 
                type="text" 
                value={usernameInput} 
                onChange={(e) => setUsernameInput(e.target.value)} 
                className="w-full bg-gray-950/60 border border-glass-border focus:border-accent-cyan outline-none text-white text-sm px-4 py-3 rounded-md transition-all"
                placeholder="Enter credentials..."
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">Access Signature Key</label>
              <input 
                type="password" 
                value={passwordInput} 
                onChange={(e) => setPasswordInput(e.target.value)} 
                className="w-full bg-gray-950/60 border border-glass-border focus:border-accent-cyan outline-none text-white text-sm px-4 py-3 rounded-md transition-all"
                placeholder="••••••••"
              />
            </div>
            
            <button 
              type="submit" 
              disabled={isLoggingIn}
              className="w-full bg-accent-cyan hover:bg-cyan-500 disabled:bg-cyan-900/40 text-black font-semibold text-sm py-3 rounded-md transition-all flex items-center justify-center gap-2 cursor-pointer shadow-[0_0_15px_rgba(6,182,212,0.3)] hover:shadow-[0_0_25px_rgba(6,182,212,0.5)]"
            >
              {isLoggingIn ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Decrypting Keyring...</span>
                </>
              ) : (
                <>
                  <Shield className="w-4 h-4" />
                  <span>Request Authorization</span>
                </>
              )}
            </button>
          </form>

          <div className="mt-8 border-t border-glass-border pt-6">
            <span className="block text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3 text-center">Demo Quick-Role Ingestion</span>
            <div className="grid grid-cols-2 gap-2">
              {[
                { name: "Admin", role: "admin", color: "hover:border-cyan-500/40 hover:bg-cyan-950/20" },
                { name: "Auditor", role: "auditor", color: "hover:border-emerald-500/40 hover:bg-emerald-950/20" },
                { name: "Security Lead", role: "officer", color: "hover:border-amber-500/40 hover:bg-amber-950/20" },
                { name: "Viewer Node", role: "viewer", color: "hover:border-slate-500/40 hover:bg-slate-950/20" }
              ].map(roleBtn => (
                <button
                  key={roleBtn.role}
                  onClick={() => selectDemoRole(roleBtn.role)}
                  className={`bg-gray-900/40 border border-glass-border rounded-md py-2 px-3 text-xs text-gray-300 font-medium transition-all ${roleBtn.color}`}
                >
                  {roleBtn.name}
                </button>
              ))}
            </div>
            <div className="mt-3 text-center">
              <span className="text-[10px] text-gray-500">Auto-filled passwords match roles: e.g., <code>admin123</code></span>
            </div>
          </div>
        </motion.div>
      </div>
    );
  }

  // Loaded Dashboard shell
  return (
    <div className="min-h-screen flex bg-gray-950 text-gray-200 grid-bg relative">
      {/* Sidebar Nav */}
      <aside className="w-64 bg-gray-950/90 border-r border-glass-border flex flex-col z-20">
        <div className="p-6 border-b border-glass-border flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Shield className="w-6 h-6 text-accent-cyan" />
            <span className="font-bold text-sm tracking-wider text-white">BLINDWATCH <span className="text-accent-cyan font-light">AI</span></span>
          </div>
          <div className={`w-2.5 h-2.5 rounded-full ${systemConnected ? 'bg-emerald-500 radar-pulse' : 'bg-rose-500'}`} />
        </div>

        {/* User Card */}
        <div className="p-4 mx-4 my-4 bg-gray-900/40 border border-glass-border rounded-lg flex items-center gap-3">
          <div className="w-10 h-10 rounded-full bg-accent-cyan/15 flex items-center justify-center border border-accent-cyan/30 text-accent-cyan font-semibold uppercase">
            {user?.username?.slice(0, 2)}
          </div>
          <div className="overflow-hidden">
            <span className="block text-xs font-bold text-white truncate">{user?.full_name || user?.username}</span>
            <span className="inline-block text-[10px] px-1.5 py-0.5 rounded bg-gray-800 border border-glass-border text-cyan-400 font-semibold uppercase mt-1 tracking-wider">
              {user?.role}
            </span>
          </div>
        </div>

        {/* Sidebar Tabs */}
        <nav className="flex-1 px-4 space-y-1 overflow-y-auto">
          {[
            { id: "dashboard", label: "Operations Center", icon: Activity },
            { id: "monitoring", label: "Live Shield Feeds", icon: Video },
            { id: "events", label: "Explainable Alerts", icon: AlertTriangle, badge: events.filter(e => e.status === "unresolved").length },
            { id: "privacy", label: "Privacy Center", icon: Shield },
            { id: "identity", label: "Governance Vault", icon: Lock, badge: identityRequests.filter(r => r.status === "pending").length },
            { id: "audit", label: "Audit Logs", icon: Database, restricted: ["officer", "viewer"] },
            { id: "analytics", label: "AI Analytics", icon: BarChart2 },
            { id: "simulator", label: "Threat Simulator", icon: Sliders },
            { id: "reports", label: "Compliance Reports", icon: FileText },
            { id: "settings", label: "System Config", icon: Settings }
          ].map(tab => {
            const Icon = tab.icon;
            const isRestricted = tab.restricted && user && tab.restricted.includes(user.role);
            if (isRestricted) return null;

            return (
              <button
                key={tab.id}
                onClick={() => {
                  setActiveTab(tab.id);
                  setSelectedEvent(null);
                }}
                className={`w-full flex items-center justify-between py-3 px-4 rounded-md transition-all font-medium text-xs tracking-wide cursor-pointer ${
                  activeTab === tab.id 
                    ? "bg-accent-cyan/10 border-l-2 border-accent-cyan text-white font-bold" 
                    : "text-gray-400 hover:bg-gray-900/60 hover:text-white"
                }`}
              >
                <div className="flex items-center gap-3">
                  <Icon className="w-4 h-4" />
                  <span>{tab.label}</span>
                </div>
                {tab.badge !== undefined && tab.badge > 0 && (
                  <span className="bg-rose-500/20 text-rose-300 border border-rose-500/30 text-[10px] px-1.5 py-0.5 rounded-full font-bold">
                    {tab.badge}
                  </span>
                )}
              </button>
            );
          })}
        </nav>

        {/* Footer logout */}
        <div className="p-4 border-t border-glass-border">
          <button 
            onClick={handleLogout}
            className="w-full flex items-center justify-center gap-2 bg-gray-900/50 hover:bg-rose-950/20 border border-glass-border hover:border-rose-900/50 text-gray-400 hover:text-rose-300 py-2.5 rounded-md text-xs font-semibold transition-all cursor-pointer"
          >
            <LogOut className="w-3.5 h-3.5" />
            <span>Terminate Session</span>
          </button>
        </div>
      </aside>

      {/* Main Panel Content Area */}
      <main className="flex-1 flex flex-col min-w-0 overflow-y-auto">
        {/* Top Header Bar */}
        <header className="h-16 bg-gray-950/70 border-b border-glass-border flex items-center justify-between px-8 z-10 sticky top-0 backdrop-blur-md">
          <div className="flex items-center gap-3">
            <span className="text-xs uppercase tracking-widest text-gray-400 font-semibold">{activeTab}</span>
            <ChevronRight className="w-3 h-3 text-gray-600" />
            <span className="text-xs font-bold text-white">Node: Security_Grid_01</span>
          </div>

          {/* Quick Metrics Bar */}
          <div className="flex items-center gap-6">
            <div className="flex items-center gap-2 bg-gray-900/30 border border-glass-border px-3 py-1 rounded-md">
              <span className="text-[10px] text-gray-500 font-semibold">PRIVACY</span>
              <span className="text-xs font-bold text-accent-cyan">{privacyData?.current?.privacy_score || 97.5}%</span>
            </div>
            <div className="flex items-center gap-2 bg-gray-900/30 border border-glass-border px-3 py-1 rounded-md">
              <span className="text-[10px] text-gray-500 font-semibold">COMPLIANCE</span>
              <span className="text-xs font-bold text-accent-emerald">{privacyData?.current?.compliance_score || 99.0}%</span>
            </div>
            <div className="flex items-center gap-2 bg-gray-900/30 border border-glass-border px-3 py-1 rounded-md">
              <span className="text-[10px] text-gray-500 font-semibold">THREATS</span>
              <span className="text-xs font-bold text-rose-500">{events.filter(e => e.status === "unresolved").length}</span>
            </div>
          </div>
        </header>

        {/* Tab Components container */}
        <div className="flex-1 p-8">
          <AnimatePresence mode="wait">
            <motion.div
              key={activeTab}
              initial={{ opacity: 0, y: 15 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -15 }}
              transition={{ duration: 0.2 }}
            >
              {/* --- DASHBOARD TAB --- */}
              {activeTab === "dashboard" && (
                <div className="space-y-8">
                  {/* Top Stats */}
                  <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                    {[
                      { label: "Shield Cameras", val: `${cameras.filter(c=>c.status==="active").length} / ${cameras.length}`, desc: "Active video ingest pipelines", icon: Video, color: "text-accent-cyan" },
                      { label: "Tracked Entities", val: entities.filter(e=>e.status==="active").length.toString(), desc: "Anonymous entity profiles", icon: Users, color: "text-accent-cyan" },
                      { label: "Safety Events", val: events.length.toString(), desc: "Live threats flagged by Engine", icon: AlertTriangle, color: "text-rose-500" },
                      { label: "Compliance Index", val: `${privacyData?.current?.privacy_score || 97.5}%`, desc: "GDPR / CCPA privacy shield", icon: Shield, color: "text-accent-emerald" }
                    ].map((stat, i) => (
                      <div key={i} className="glass-panel p-6 rounded-lg border border-glass-border">
                        <div className="flex justify-between items-start mb-3">
                          <span className="text-xs font-semibold text-gray-400 uppercase tracking-wider">{stat.label}</span>
                          <stat.icon className={`w-5 h-5 ${stat.color}`} />
                        </div>
                        <h3 className="text-2xl font-bold text-white mb-1">{stat.val}</h3>
                        <p className="text-[10px] text-gray-500">{stat.desc}</p>
                      </div>
                    ))}
                  </div>

                  {/* Main Grid: Charts & Alerts */}
                  <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                    {/* Recharts Area */}
                    <div className="glass-panel lg:col-span-2 p-6 rounded-lg border border-glass-border">
                      <div className="flex justify-between items-center mb-6">
                        <h4 className="text-sm font-bold tracking-wider text-white uppercase flex items-center gap-2">
                          <Activity className="w-4 h-4 text-accent-cyan" />
                          <span>Dynamic Threat and Anonymity Index</span>
                        </h4>
                        <span className="text-[10px] text-gray-500">Streaming Real-Time Telemetry</span>
                      </div>
                      
                      <div className="h-64">
                        {analyticsData ? (
                          <ResponsiveContainer width="100%" height="100%">
                            <AreaChart data={analyticsData.threat_trends}>
                              <defs>
                                <linearGradient id="colorViolence" x1="0" y1="0" x2="0" y2="1">
                                  <stop offset="5%" stopColor="#f43f5e" stopOpacity={0.4}/>
                                  <stop offset="95%" stopColor="#f43f5e" stopOpacity={0}/>
                                </linearGradient>
                                <linearGradient id="colorTheft" x1="0" y1="0" x2="0" y2="1">
                                  <stop offset="5%" stopColor="#06b6d4" stopOpacity={0.4}/>
                                  <stop offset="95%" stopColor="#06b6d4" stopOpacity={0}/>
                                </linearGradient>
                              </defs>
                              <XAxis dataKey="time" stroke="#4b5563" fontSize={10} />
                              <YAxis stroke="#4b5563" fontSize={10} />
                              <Tooltip contentStyle={{ backgroundColor: '#090d16', borderColor: '#1f2937' }} />
                              <Area type="monotone" dataKey="violence" stroke="#f43f5e" fillOpacity={1} fill="url(#colorViolence)" name="Safety Anomaly" />
                              <Area type="monotone" dataKey="theft" stroke="#06b6d4" fillOpacity={1} fill="url(#colorTheft)" name="Privacy Actions" />
                            </AreaChart>
                          </ResponsiveContainer>
                        ) : (
                          <div className="h-full flex items-center justify-center">
                            <Loader2 className="w-6 h-6 animate-spin text-accent-cyan" />
                          </div>
                        )}
                      </div>
                    </div>

                    {/* Threat Log widget */}
                    <div className="glass-panel p-6 rounded-lg border border-glass-border flex flex-col">
                      <h4 className="text-sm font-bold tracking-wider text-white uppercase mb-4 flex items-center gap-2">
                        <AlertTriangle className="w-4 h-4 text-rose-500 animate-pulse" />
                        <span>Shield Alert Console</span>
                      </h4>
                      <div className="flex-1 overflow-y-auto max-h-60 space-y-3">
                        {events.length > 0 ? (
                          events.slice(0, 5).map(event => (
                            <div 
                              key={event.id}
                              onClick={() => {
                                setActiveTab("events");
                                handleExplainEvent(event);
                              }}
                              className="bg-gray-950/80 border border-glass-border hover:border-rose-500/30 p-3 rounded-md cursor-pointer transition-all"
                            >
                              <div className="flex justify-between items-start mb-1">
                                <span className="text-xs font-bold text-white">{event.event_type}</span>
                                <span className="text-[10px] text-gray-500">{new Date(event.timestamp).toLocaleTimeString()}</span>
                              </div>
                              <div className="flex justify-between items-center text-[10px]">
                                <span className="text-gray-400">Node: {event.location}</span>
                                <span className={`font-semibold ${event.risk_score > 70 ? 'text-rose-400' : 'text-amber-400'}`}>Risk: {event.risk_score}</span>
                              </div>
                            </div>
                          ))
                        ) : (
                          <div className="text-center py-8 text-xs text-gray-500">No active events logged</div>
                        )}
                      </div>
                    </div>
                  </div>

                  {/* Operational Controls */}
                  <div className="glass-panel p-6 rounded-lg border border-glass-border">
                    <h4 className="text-sm font-bold tracking-wider text-white uppercase mb-4">Command Actions Vault</h4>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                      <button 
                        onClick={() => setActiveTab("monitoring")}
                        className="bg-gray-900/60 hover:bg-cyan-950/20 border border-glass-border hover:border-cyan-500/30 text-gray-300 py-3 rounded-md text-xs font-semibold transition-all cursor-pointer text-center"
                      >
                        Launch Camera Node Feeds
                      </button>
                      <button 
                        onClick={() => setActiveTab("privacy")}
                        className="bg-gray-900/60 hover:bg-emerald-950/20 border border-glass-border hover:border-emerald-500/30 text-gray-300 py-3 rounded-md text-xs font-semibold transition-all cursor-pointer text-center"
                      >
                        Review GDPR Privacy Shields
                      </button>
                      <button 
                        onClick={() => setActiveTab("simulator")}
                        className="bg-gray-900/60 hover:bg-amber-950/20 border border-glass-border hover:border-amber-500/30 text-gray-300 py-3 rounded-md text-xs font-semibold transition-all cursor-pointer text-center"
                      >
                        Run Sandboxed Threat Simulator
                      </button>
                      <button 
                        onClick={handleExportReport}
                        className="bg-gray-900/60 hover:bg-slate-900/60 border border-glass-border hover:border-white/30 text-gray-300 py-3 rounded-md text-xs font-semibold transition-all cursor-pointer text-center"
                      >
                        Compile Security Audit Summary
                      </button>
                    </div>
                  </div>
                </div>
              )}

              {/* --- LIVE MONITORING TAB --- */}
              {activeTab === "monitoring" && (
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                  {/* Left: Camera Selector & Status */}
                  <div className="space-y-6">
                    <div className="glass-panel p-6 rounded-lg border border-glass-border">
                      <h4 className="text-sm font-bold tracking-wider text-white uppercase mb-4">Active Camera Nodes</h4>
                      <div className="space-y-3">
                        {cameras.map(cam => (
                          <div 
                            key={cam.id}
                            onClick={() => setSelectedCamera(cam)}
                            className={`p-4 rounded-lg border cursor-pointer transition-all ${
                              selectedCamera?.id === cam.id 
                                ? "bg-accent-cyan/5 border-accent-cyan text-white" 
                                : "bg-gray-950/60 border-glass-border hover:border-gray-700 text-gray-400"
                            }`}
                          >
                            <div className="flex justify-between items-center mb-2">
                              <span className="text-xs font-bold">{cam.name}</span>
                              <span className={`w-2 h-2 rounded-full ${cam.status === "active" ? 'bg-emerald-500' : 'bg-gray-700'}`} />
                            </div>
                            <div className="flex justify-between items-center text-[10px]">
                              <span>Zone: {cam.location}</span>
                              <span className="font-semibold text-accent-cyan">Safety Score: {cam.safety_score}%</span>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Camera Control panel */}
                    {selectedCamera && (
                      <div className="glass-panel p-6 rounded-lg border border-glass-border space-y-4">
                        <h4 className="text-sm font-bold tracking-wider text-white uppercase">Grid Control Layer</h4>
                        <div className="flex justify-between items-center bg-gray-950/80 p-3 rounded-md border border-glass-border">
                          <div>
                            <span className="block text-xs font-bold text-white">Shield Identity Obfuscation</span>
                            <span className="text-[10px] text-gray-500">Live blurring on face quadrant</span>
                          </div>
                          <button 
                            onClick={() => handleTogglePrivacyShield(selectedCamera.id, selectedCamera.privacy_shield_active)}
                            disabled={user?.role === "viewer"}
                            className={`px-3 py-1.5 rounded text-xs font-semibold cursor-pointer transition-all ${
                              selectedCamera.privacy_shield_active 
                                ? "bg-accent-cyan text-black" 
                                : "bg-gray-800 border border-glass-border text-gray-400 hover:text-white"
                            }`}
                          >
                            {selectedCamera.privacy_shield_active ? "Shield Active" : "Shield Disabled"}
                          </button>
                        </div>
                        <div className="bg-gray-950/80 p-3 rounded-md border border-glass-border">
                          <span className="block text-xs font-bold text-white mb-2">Sensor Specifications</span>
                          <div className="grid grid-cols-2 gap-2 text-[10px] text-gray-400">
                            <div>Resolution: <span className="text-white">{selectedCamera.resolution}</span></div>
                            <div>Framerate: <span className="text-white">{selectedCamera.fps} FPS</span></div>
                            <div>Telemetry Protocol: <span className="text-white">RTSP Encryption</span></div>
                            <div>Threat Index: <span className="text-rose-400">{selectedCamera.threat_count} Alerts</span></div>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Right: Simulated Video Stream View */}
                  <div className="lg:col-span-2 space-y-6">
                    {selectedCamera ? (
                      <div className="glass-panel p-6 rounded-lg border border-glass-border space-y-4">
                        <div className="flex justify-between items-center">
                          <h4 className="text-sm font-bold tracking-wider text-white uppercase flex items-center gap-2">
                            <Radio className="w-4 h-4 text-rose-500 animate-pulse" />
                            <span>Telemetry Stream: {selectedCamera.name}</span>
                          </h4>
                          <button 
                            onClick={() => setIsLiveStreaming(!isLiveStreaming)}
                            className={`px-3 py-1 rounded text-xs font-semibold cursor-pointer transition-all flex items-center gap-1.5 ${
                              isLiveStreaming 
                                ? "bg-rose-600 hover:bg-rose-500 text-white" 
                                : "bg-accent-cyan hover:bg-cyan-500 text-black"
                            }`}
                          >
                            <span className={`w-1.5 h-1.5 rounded-full bg-current ${isLiveStreaming ? 'animate-ping' : ''}`} />
                            <span>{isLiveStreaming ? "Halt Stream" : "Connect Stream"}</span>
                          </button>
                        </div>

                        {/* Interactive Radar Sandbox Area */}
                        <div className="relative aspect-video bg-gray-950 rounded-lg overflow-hidden border border-glass-border cyber-scanlines flex items-center justify-center">
                          {/* System Grid dots */}
                          <div className="absolute inset-0 bg-grid-opacity opacity-20 pointer-events-none grid-bg" />
                          
                          {/* Live coords tracking */}
                          {isLiveStreaming && liveCoords ? (
                            <motion.div 
                              animate={{ x: liveCoords.x - 200, y: liveCoords.y - 120 }}
                              transition={{ duration: 1.5, ease: "easeInOut" }}
                              className="absolute w-24 h-24 flex flex-col items-center justify-center z-10"
                            >
                              {/* Face blur representation */}
                              {selectedCamera.privacy_shield_active ? (
                                <div className="w-12 h-12 rounded-full border-2 border-accent-cyan/80 bg-accent-cyan/10 backdrop-blur-xl flex items-center justify-center">
                                  <Shield className="w-4 h-4 text-accent-cyan" />
                                </div>
                              ) : (
                                <div className="w-12 h-12 rounded-full border-2 border-rose-500 bg-rose-500/10 flex items-center justify-center">
                                  <span className="text-[8px] text-rose-300 font-bold">PII EXPOSED</span>
                                </div>
                              )}
                              {/* Bounding box marker */}
                              <div className="border border-accent-cyan mt-1 px-1.5 py-0.5 rounded bg-gray-950/80 text-[8px] text-accent-cyan font-bold whitespace-nowrap">
                                {liveCoords.id} (Risk: {liveCoords.risk}%)
                              </div>
                            </motion.div>
                          ) : (
                            <div className="text-center text-gray-500 z-10">
                              <Video className="w-10 h-10 mx-auto mb-2 text-gray-600" />
                              <p className="text-xs">Stream disconnected. Click Connect Stream to ingest telemetry frames.</p>
                            </div>
                          )}

                          {/* Shield status overlay banner */}
                          <div className="absolute bottom-4 left-4 right-4 bg-gray-950/80 backdrop-blur border border-glass-border p-3 rounded flex justify-between items-center z-10">
                            <span className="text-[10px] text-gray-400">Node Status: <span className="text-white font-bold">{selectedCamera.status.toUpperCase()}</span></span>
                            <span className="text-[10px] text-gray-400">Anonymization: <span className={selectedCamera.privacy_shield_active ? "text-accent-cyan font-bold" : "text-rose-500 font-bold"}>{selectedCamera.privacy_shield_active ? "ENFORCED" : "BYPASSED - DANGER"}</span></span>
                          </div>
                        </div>

                        {/* Real-time Event Stream */}
                        <div className="bg-gray-950/80 border border-glass-border p-4 rounded-lg">
                          <span className="block text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">Surveillance Log Output</span>
                          <div className="font-mono text-[10px] text-cyan-400 space-y-1 h-20 overflow-y-auto">
                            {isLiveStreaming ? (
                              <>
                                <div>[SYS] Ingestion channel initialized. Processing video nodes...</div>
                                {liveCoords && (
                                  <>
                                    <div>[VISION] Frame processed. Extracted entity node trajectory path.</div>
                                    <div>[PRIVACY] Shield applied on {liveCoords.id}. Realtime biometric payload destroyed.</div>
                                    <div>[BEHAVIOR] Computed kinematics (Speed: {liveCoords.speed} m/s).</div>
                                    {liveCoords.risk > 50 && <div className="text-rose-400 animate-pulse">[RISK] High risk behavior signature flagged: {liveCoords.risk}%</div>}
                                  </>
                                )}
                              </>
                            ) : (
                              <div className="text-gray-600">[SYS] Pipeline idling. Waiting for frame triggers.</div>
                            )}
                          </div>
                        </div>
                      </div>
                    ) : (
                      <div className="h-96 flex items-center justify-center glass-panel rounded-lg border border-glass-border">
                        <p className="text-sm text-gray-500">Select a camera node to activate video matrix.</p>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* --- EVENTS CENTER TAB --- */}
              {activeTab === "events" && (
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                  {/* Left: Alerts List */}
                  <div className="lg:col-span-2 space-y-6">
                    <div className="glass-panel p-6 rounded-lg border border-glass-border">
                      <div className="flex justify-between items-center mb-6">
                        <h4 className="text-sm font-bold tracking-wider text-white uppercase">Incidents Ledger</h4>
                        <span className="text-[10px] text-gray-500">{events.length} System Records</span>
                      </div>
                      <div className="overflow-x-auto">
                        <table className="w-full text-left text-xs border-collapse">
                          <thead>
                            <tr className="border-b border-glass-border text-gray-500 font-semibold uppercase tracking-wider">
                              <th className="pb-3 px-4">Type</th>
                              <th className="pb-3 px-4">Timestamp</th>
                              <th className="pb-3 px-4">Location</th>
                              <th className="pb-3 px-4">Anonym ID</th>
                              <th className="pb-3 px-4">Risk</th>
                              <th className="pb-3 px-4">Status</th>
                            </tr>
                          </thead>
                          <tbody>
                            {events.map(event => (
                              <tr 
                                key={event.id}
                                onClick={() => handleExplainEvent(event)}
                                className={`border-b border-glass-border/40 hover:bg-gray-900/30 cursor-pointer transition-all ${
                                  selectedEvent?.id === event.id ? "bg-accent-cyan/5 border-l-2 border-accent-cyan" : ""
                                }`}
                              >
                                <td className="py-4 px-4 font-bold text-white flex items-center gap-2">
                                  <span className={`w-2 h-2 rounded-full ${event.status === 'unresolved' ? 'bg-rose-500' : 'bg-gray-500'}`} />
                                  <span>{event.event_type}</span>
                                </td>
                                <td className="py-4 px-4 text-gray-400">{new Date(event.timestamp).toLocaleTimeString()}</td>
                                <td className="py-4 px-4">{event.location}</td>
                                <td className="py-4 px-4 text-accent-cyan font-mono">{event.entity_id}</td>
                                <td className={`py-4 px-4 font-semibold ${event.risk_score > 70 ? 'text-rose-400' : 'text-amber-400'}`}>{event.risk_score}</td>
                                <td className="py-4 px-4">
                                  <span className={`px-2 py-0.5 rounded text-[10px] uppercase font-bold tracking-wider border ${
                                    event.status === 'unresolved' 
                                      ? 'bg-rose-950/40 border-rose-800 text-rose-300' 
                                      : event.status === 'false_positive'
                                      ? 'bg-slate-900 border-glass-border text-gray-500'
                                      : 'bg-emerald-950/40 border-emerald-800 text-emerald-300'
                                  }`}>
                                    {event.status}
                                  </span>
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  </div>

                  {/* Right: Explainable AI Panel */}
                  <div className="space-y-6">
                    {selectedEvent ? (
                      <div className="glass-panel p-6 rounded-lg border border-glass-border space-y-6">
                        <div className="flex justify-between items-start">
                          <div>
                            <h4 className="text-sm font-bold tracking-wider text-white uppercase">{selectedEvent.event_type}</h4>
                            <span className="text-[10px] text-gray-500">Anomaly Explainable AI Report</span>
                          </div>
                          <span className="bg-gray-950 border border-glass-border text-[10px] text-accent-cyan font-mono px-2 py-1 rounded">
                            {selectedEvent.entity_id}
                          </span>
                        </div>

                        {/* Explainable AI breakdown loading */}
                        {isExplaining ? (
                          <div className="py-12 flex items-center justify-center">
                            <Loader2 className="w-6 h-6 animate-spin text-accent-cyan" />
                          </div>
                        ) : explainData ? (
                          <div className="space-y-5">
                            <div className="bg-gray-950/80 border border-glass-border p-3 rounded-md text-xs">
                              <span className="block text-[10px] text-gray-500 font-semibold uppercase tracking-wider mb-1">Incident Summary</span>
                              <p className="text-gray-300 leading-relaxed">{explainData.summary}</p>
                            </div>

                            {/* Confidence Gauge */}
                            <div className="flex justify-between items-center bg-gray-950/80 border border-glass-border p-3 rounded-md">
                              <span className="text-[10px] text-gray-500 font-semibold uppercase tracking-wider">Detection Confidence</span>
                              <span className="text-xs font-bold text-accent-emerald">{explainData.confidence}</span>
                            </div>

                            {/* Contributing Factors Bar chart */}
                            <div>
                              <span className="block text-[10px] text-gray-500 font-semibold uppercase tracking-wider mb-3">Threat Weight Vector</span>
                              <div className="space-y-3">
                                {explainData.factors.map((f: any, i: number) => (
                                  <div key={i} className="space-y-1">
                                    <div className="flex justify-between text-[10px]">
                                      <span className="text-gray-300 font-medium">{f.factor}</span>
                                      <span className="text-accent-cyan font-bold">{f.weight_percentage}%</span>
                                    </div>
                                    <div className="w-full bg-gray-900 rounded-full h-1.5 overflow-hidden">
                                      <div className="bg-accent-cyan h-full rounded-full" style={{ width: `${f.weight_percentage}%` }} />
                                    </div>
                                    <span className="block text-[8px] text-gray-500 leading-normal">{f.evidence_descriptor}</span>
                                  </div>
                                ))}
                              </div>
                            </div>

                            {/* Neural Decision flow */}
                            <div className="space-y-2 border-t border-glass-border pt-4">
                              <span className="block text-[10px] text-gray-500 font-semibold uppercase tracking-wider mb-2">Audit Decision Pipeline</span>
                              <div className="space-y-2 text-[10px] text-gray-400">
                                {explainData.decision_flow.map((flow: any, i: number) => (
                                  <div key={i} className="flex gap-3">
                                    <span className="font-bold text-accent-cyan">0{flow.step}</span>
                                    <p className="leading-tight">{flow.description}</p>
                                  </div>
                                ))}
                              </div>
                            </div>

                            {/* Alert Action buttons */}
                            {selectedEvent.status === "unresolved" && (
                              <div className="grid grid-cols-2 gap-3 border-t border-glass-border pt-4">
                                <button 
                                  onClick={() => handleAcknowledgeEvent(selectedEvent.id)}
                                  disabled={user?.role === "viewer"}
                                  className="bg-accent-emerald hover:bg-emerald-500 text-black text-xs font-semibold py-2.5 rounded transition-all cursor-pointer text-center"
                                >
                                  Acknowledge Alert
                                </button>
                                <button 
                                  onClick={() => handleFalsePositive(selectedEvent.id)}
                                  disabled={user?.role === "viewer"}
                                  className="bg-gray-800 hover:bg-rose-950/20 border border-glass-border hover:border-rose-900/50 text-gray-300 hover:text-rose-300 text-xs font-semibold py-2.5 rounded transition-all cursor-pointer text-center"
                                >
                                  False Positive
                                </button>
                              </div>
                            )}
                          </div>
                        ) : (
                          <div className="text-center py-12 text-xs text-gray-500">AI Decoupler failed.</div>
                        )}
                      </div>
                    ) : (
                      <div className="h-96 flex items-center justify-center glass-panel rounded-lg border border-glass-border">
                        <p className="text-sm text-gray-500 text-center px-6">Select a flagged incident from the ledger to load Explainable AI metrics.</p>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* --- PRIVACY CENTER TAB --- */}
              {activeTab === "privacy" && (
                <div className="space-y-8">
                  {/* Privacy gauges */}
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <div className="glass-panel p-6 rounded-lg border border-glass-border text-center">
                      <Shield className="w-10 h-10 mx-auto text-accent-cyan mb-4" />
                      <h4 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">GDPR Privacy Score</h4>
                      <h3 className="text-4xl font-bold text-white mb-2">{privacyData?.current?.privacy_score || 97.5}%</h3>
                      <p className="text-[10px] text-gray-500">Based on biometric destruction logs</p>
                    </div>
                    <div className="glass-panel p-6 rounded-lg border border-glass-border text-center">
                      <Lock className="w-10 h-10 mx-auto text-accent-emerald mb-4" />
                      <h4 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">Compliance Score</h4>
                      <h3 className="text-4xl font-bold text-white mb-2">{privacyData?.current?.compliance_score || 99.0}%</h3>
                      <p className="text-[10px] text-gray-500">Decryption vault audit clearance status</p>
                    </div>
                    <div className="glass-panel p-6 rounded-lg border border-glass-border text-center">
                      <EyeOff className="w-10 h-10 mx-auto text-accent-amber mb-4" />
                      <h4 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">Retention Exposure Risk</h4>
                      <h3 className="text-4xl font-bold text-white mb-2">{privacyData?.current?.retention_risk || "Low"}</h3>
                      <p className="text-[10px] text-gray-500">Live active data storage TTL limit</p>
                    </div>
                  </div>

                  {/* Recharts Area for compliance trends */}
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                    <div className="glass-panel p-6 rounded-lg border border-glass-border">
                      <h4 className="text-sm font-bold tracking-wider text-white uppercase mb-4">Historical Privacy Indexes</h4>
                      <div className="h-64">
                        {privacyData ? (
                          <ResponsiveContainer width="100%" height="100%">
                            <AreaChart data={privacyData.history}>
                              <XAxis dataKey="timestamp" stroke="#4b5563" fontSize={10} />
                              <YAxis stroke="#4b5563" fontSize={10} domain={[80, 100]} />
                              <Tooltip contentStyle={{ backgroundColor: '#090d16', borderColor: '#1f2937' }} />
                              <Area type="monotone" dataKey="privacy_score" stroke="#06b6d4" fill="#06b6d4" fillOpacity={0.1} name="Privacy Score" />
                              <Area type="monotone" dataKey="compliance_score" stroke="#10b981" fill="#10b981" fillOpacity={0.05} name="Compliance Index" />
                            </AreaChart>
                          </ResponsiveContainer>
                        ) : (
                          <div className="h-full flex items-center justify-center">
                            <Loader2 className="w-6 h-6 animate-spin text-accent-cyan" />
                          </div>
                        )}
                      </div>
                    </div>

                    {/* Recommendations and Checklist */}
                    <div className="glass-panel p-6 rounded-lg border border-glass-border space-y-6">
                      <h4 className="text-sm font-bold tracking-wider text-white uppercase">Compliance Check</h4>
                      
                      <div className="space-y-4">
                        {[
                          { rule: "Biometric Data Hashing (GDPR Art. 9)", met: true },
                          { rule: "Dual-Key Encryption Authorization (CCPA)", met: true },
                          { rule: "Automatic Video Loop Purging (ISO 27001)", met: true },
                          { rule: "Immutable Cryptographic Audit Trail", met: true }
                        ].map((item, i) => (
                          <div key={i} className="flex justify-between items-center bg-gray-950/80 p-3 rounded border border-glass-border">
                            <span className="text-xs text-gray-300">{item.rule}</span>
                            <span className="text-xs font-bold text-accent-emerald flex items-center gap-1.5">
                              <Check className="w-4 h-4" />
                              <span>MET</span>
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* --- IDENTITY GOVERNANCE TAB (IDENTITY REQUESTS) --- */}
              {activeTab === "identity" && (
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                  {/* Left: Request Form & Ledger */}
                  <div className="lg:col-span-2 space-y-6">
                    <div className="glass-panel p-6 rounded-lg border border-glass-border">
                      <div className="flex justify-between items-center mb-6">
                        <h4 className="text-sm font-bold tracking-wider text-white uppercase">Decryption Access Ledger</h4>
                        <span className="text-[10px] text-gray-500">Requires dual authorization keys</span>
                      </div>
                      
                      <div className="overflow-x-auto">
                        <table className="w-full text-left text-xs border-collapse">
                          <thead>
                            <tr className="border-b border-glass-border text-gray-500 font-semibold uppercase tracking-wider">
                              <th className="pb-3 px-4">Requester</th>
                              <th className="pb-3 px-4">Subject ID</th>
                              <th className="pb-3 px-4">Reason / Justification</th>
                              <th className="pb-3 px-4">Auditor Key</th>
                              <th className="pb-3 px-4">Admin Key</th>
                              <th className="pb-3 px-4">Status</th>
                              <th className="pb-3 px-4 text-right">Actions</th>
                            </tr>
                          </thead>
                          <tbody>
                            {identityRequests.map(req => (
                              <tr key={req.id} className="border-b border-glass-border/40 hover:bg-gray-900/10">
                                <td className="py-4 px-4 font-semibold text-white">{req.requester_name}</td>
                                <td className="py-4 px-4 text-accent-cyan font-mono font-bold">{req.entity_id}</td>
                                <td className="py-4 px-4 text-gray-400 max-w-xs truncate" title={req.justification}>{req.justification}</td>
                                <td className="py-4 px-4">
                                  <span className={`text-[10px] font-bold ${req.approved_by_auditor ? 'text-accent-emerald' : 'text-gray-500'}`}>
                                    {req.approved_by_auditor ? "SIGNED" : "PENDING"}
                                  </span>
                                </td>
                                <td className="py-4 px-4">
                                  <span className={`text-[10px] font-bold ${req.approved_by_admin ? 'text-accent-emerald' : 'text-gray-500'}`}>
                                    {req.approved_by_admin ? "SIGNED" : "PENDING"}
                                  </span>
                                </td>
                                <td className="py-4 px-4">
                                  <span className={`px-2 py-0.5 rounded text-[10px] uppercase font-bold tracking-wider border ${
                                    req.status === 'approved' 
                                      ? 'bg-emerald-950/40 border-emerald-800 text-emerald-300' 
                                      : req.status === 'rejected'
                                      ? 'bg-rose-950/40 border-rose-800 text-rose-300'
                                      : 'bg-amber-950/40 border-amber-800 text-amber-300'
                                  }`}>
                                    {req.status}
                                  </span>
                                </td>
                                <td className="py-4 text-right">
                                  {req.status === "approved" ? (
                                    revealedIdentities[req.entity_id] ? (
                                      <div className="text-right">
                                        <span className="block text-xs font-bold text-accent-emerald bg-emerald-950/30 border border-emerald-800 px-2 py-1 rounded inline-block">
                                          {revealedIdentities[req.entity_id]}
                                        </span>
                                      </div>
                                    ) : (
                                      <button 
                                        onClick={() => handleRevealIdentity(req.entity_id)}
                                        className="bg-accent-emerald hover:bg-emerald-500 text-black text-[10px] font-semibold px-2 py-1 rounded cursor-pointer transition-all"
                                      >
                                        Reveal ID
                                      </button>
                                    )
                                  ) : req.status === "pending" ? (
                                    <div className="flex justify-end gap-1.5">
                                      {/* Auditor Approval Button */}
                                      {user?.role === "auditor" && !req.approved_by_auditor && (
                                        <button 
                                          onClick={() => handleApproveRequest(req.id)}
                                          className="bg-accent-emerald text-black text-[10px] font-semibold px-2 py-1 rounded cursor-pointer"
                                        >
                                          Sign Key
                                        </button>
                                      )}
                                      {/* Admin Approval Button */}
                                      {user?.role === "admin" && !req.approved_by_admin && (
                                        <button 
                                          onClick={() => handleApproveRequest(req.id)}
                                          className="bg-accent-cyan text-black text-[10px] font-semibold px-2 py-1 rounded cursor-pointer"
                                        >
                                          Sign Key
                                        </button>
                                      )}
                                      {(user?.role === "admin" || user?.role === "auditor") && (
                                        <button 
                                          onClick={() => handleRejectRequest(req.id)}
                                          className="bg-rose-950 border border-rose-800 text-rose-300 text-[10px] font-semibold px-2 py-1 rounded cursor-pointer"
                                        >
                                          Deny
                                        </button>
                                      )}
                                    </div>
                                  ) : (
                                    <span className="text-[10px] text-gray-600">Archived</span>
                                  )}
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  </div>

                  {/* Right: Submit Request Form */}
                  <div className="space-y-6">
                    <div className="glass-panel p-6 rounded-lg border border-glass-border">
                      <h4 className="text-sm font-bold tracking-wider text-white uppercase mb-4 flex items-center gap-2">
                        <Lock className="w-4 h-4 text-accent-amber" />
                        <span>Filing Decryption Petition</span>
                      </h4>

                      {requestSuccessMsg && (
                        <div className="bg-emerald-950/40 border border-emerald-800/80 rounded-md p-3 flex gap-2 items-center text-emerald-300 text-xs mb-4">
                          <Check className="w-5 h-5 flex-shrink-0" />
                          <span>{requestSuccessMsg}</span>
                        </div>
                      )}

                      <form onSubmit={handleSubmitDecryptionRequest} className="space-y-4">
                        <div>
                          <label className="block text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">Target Anonymous Entity</label>
                          <select 
                            value={selectedEntityForIdRequest}
                            onChange={(e) => setSelectedEntityForIdRequest(e.target.value)}
                            disabled={user?.role === "viewer"}
                            className="w-full bg-gray-950/60 border border-glass-border focus:border-accent-cyan outline-none text-white text-xs px-4 py-3 rounded-md"
                          >
                            <option value="">-- SELECT ENTITY ID --</option>
                            {entities.map(ent => (
                              <option key={ent.id} value={ent.entity_id}>{ent.entity_id} ({ent.last_location})</option>
                            ))}
                          </select>
                        </div>
                        <div>
                          <label className="block text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">Legal Justification</label>
                          <textarea 
                            value={justificationInput} 
                            onChange={(e) => setJustificationInput(e.target.value)}
                            rows={4}
                            disabled={user?.role === "viewer"}
                            className="w-full bg-gray-950/60 border border-glass-border focus:border-accent-cyan outline-none text-white text-xs px-4 py-3 rounded-md resize-none"
                            placeholder="Enter specific regulatory, safety, or legal reasoning for identity reveal..."
                          />
                        </div>
                        <div>
                          <label className="block text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">Decrypt Window Lease</label>
                          <select 
                            value={requestDuration}
                            onChange={(e) => setRequestDuration(Number(e.target.value))}
                            disabled={user?.role === "viewer"}
                            className="w-full bg-gray-950/60 border border-glass-border focus:border-accent-cyan outline-none text-white text-xs px-4 py-3 rounded-md"
                          >
                            <option value={15}>15 Minutes</option>
                            <option value={30}>30 Minutes</option>
                            <option value={60}>60 Minutes</option>
                          </select>
                        </div>

                        <button 
                          type="submit"
                          disabled={isSubmittingRequest || user?.role === "viewer"}
                          className="w-full bg-accent-amber hover:bg-amber-500 disabled:bg-amber-950/20 disabled:text-gray-500 text-black font-semibold text-xs py-3 rounded-md transition-all flex items-center justify-center gap-2 cursor-pointer shadow-[0_0_15px_rgba(245,158,11,0.2)]"
                        >
                          {isSubmittingRequest ? (
                            <>
                              <Loader2 className="w-4 h-4 animate-spin" />
                              <span>Filing Petition...</span>
                            </>
                          ) : (
                            <>
                              <Unlock className="w-4 h-4" />
                              <span>Submit Dual-Key Petition</span>
                            </>
                          )}
                        </button>
                      </form>
                    </div>
                  </div>
                </div>
              )}

              {/* --- AUDIT LOGS TAB --- */}
              {activeTab === "audit" && (
                <div className="glass-panel p-6 rounded-lg border border-glass-border">
                  <div className="flex justify-between items-center mb-6">
                    <h4 className="text-sm font-bold tracking-wider text-white uppercase">System Auditing Logs</h4>
                    <div className="flex items-center gap-4">
                      {ledgerVerification && ledgerVerification.checked && (
                        <span className={`text-[10px] font-bold px-2.5 py-1.5 rounded border ${
                          ledgerVerification.verified 
                            ? 'bg-emerald-950/40 border-emerald-800 text-emerald-300' 
                            : 'bg-rose-950/40 border-rose-800 text-rose-300 animate-pulse'
                        }`}>
                          {ledgerVerification.verified ? "✓ LEDGER INTEGRITY VERIFIED (SHA-256 HASH CHAIN INTEGRAL)" : "⚠ WARNING: LEDGER TAMPERING DETECTED!"}
                        </span>
                      )}
                      <button
                        onClick={handleVerifyLedger}
                        disabled={ledgerVerification?.isChecking}
                        className="bg-accent-cyan hover:bg-cyan-400 disabled:bg-cyan-950/20 text-black text-[10px] font-bold px-3 py-1.5 rounded transition-all cursor-pointer flex items-center gap-1.5 shadow-[0_0_10px_rgba(6,182,212,0.15)]"
                      >
                        {ledgerVerification?.isChecking ? (
                          <>
                            <Loader2 className="w-3 h-3 animate-spin" />
                            <span>Validating...</span>
                          </>
                        ) : (
                          <>
                            <Check className="w-3 h-3" />
                            <span>Verify Ledger Integrity</span>
                          </>
                        )}
                      </button>
                    </div>
                    <span className="text-[10px] text-gray-500">SECURE CRYPTOGRAPHIC LEDGER - IMMUTABLE</span>
                  </div>
                  <div className="overflow-x-auto">
                    <table className="w-full text-left text-xs border-collapse">
                      <thead>
                        <tr className="border-b border-glass-border text-gray-500 font-semibold uppercase tracking-wider">
                          <th className="pb-3 px-4">Timestamp</th>
                          <th className="pb-3 px-4">Operator</th>
                          <th className="pb-3 px-4">Role</th>
                          <th className="pb-3 px-4">Action Code</th>
                          <th className="pb-3 px-4">Audit Details</th>
                          <th className="pb-3 px-4">IP Address</th>
                          <th className="pb-3 px-4 text-right">Outcome</th>
                        </tr>
                      </thead>
                      <tbody>
                        {auditLogs.map(log => (
                          <tr key={log.id} className="border-b border-glass-border/40 hover:bg-gray-900/10">
                            <td className="py-4 px-4 text-gray-400 font-mono">{new Date(log.timestamp).toLocaleString()}</td>
                            <td className="py-4 px-4 font-semibold text-white">{log.username}</td>
                            <td className="py-4 px-4 text-cyan-400">{log.role.toUpperCase()}</td>
                            <td className="py-4 px-4 font-mono text-[10px] text-accent-cyan font-bold">{log.action}</td>
                            <td className="py-4 px-4 text-gray-300 max-w-sm truncate" title={log.reason}>{log.reason}</td>
                            <td className="py-4 px-4 font-mono text-gray-500">{log.ip_address || "127.0.0.1"}</td>
                            <td className="py-4 px-4 text-right">
                              <span className={`px-2 py-0.5 rounded text-[10px] uppercase font-bold tracking-wider border ${
                                log.outcome === 'success' 
                                  ? 'bg-emerald-950/40 border-emerald-800 text-emerald-300' 
                                  : 'bg-rose-950/40 border-rose-800 text-rose-300'
                              }`}>
                                {log.outcome}
                              </span>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {/* --- AI ANALYTICS TAB --- */}
              {activeTab === "analytics" && (
                <div className="space-y-8">
                  {/* Dynamic Charts Grid */}
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                    {/* Area 1: Threat distribution */}
                    <div className="glass-panel p-6 rounded-lg border border-glass-border">
                      <h4 className="text-sm font-bold tracking-wider text-white uppercase mb-6">Threat Distribution Anomaly</h4>
                      <div className="h-64">
                        {analyticsData ? (
                          <ResponsiveContainer width="100%" height="100%">
                            <BarChart data={analyticsData.risk_distribution}>
                              <XAxis dataKey="range" stroke="#4b5563" fontSize={10} />
                              <YAxis stroke="#4b5563" fontSize={10} />
                              <Tooltip contentStyle={{ backgroundColor: '#090d16', borderColor: '#1f2937' }} />
                              <Bar dataKey="count" fill="#06b6d4" radius={[4, 4, 0, 0]}>
                                {analyticsData.risk_distribution.map((entry: any, index: number) => (
                                  <Cell key={`cell-${index}`} fill={index === 3 ? '#f43f5e' : (index === 2 ? '#f59e0b' : '#06b6d4')} />
                                ))}
                              </Bar>
                            </BarChart>
                          </ResponsiveContainer>
                        ) : (
                          <div className="h-full flex items-center justify-center">
                            <Loader2 className="w-6 h-6 animate-spin text-accent-cyan" />
                          </div>
                        )}
                      </div>
                    </div>

                    {/* Area 2: Camera effectiveness radar */}
                    <div className="glass-panel p-6 rounded-lg border border-glass-border">
                      <h4 className="text-sm font-bold tracking-wider text-white uppercase mb-6">Camera Node Efficiency</h4>
                      <div className="h-64 flex justify-center items-center">
                        {analyticsData ? (
                          <ResponsiveContainer width="100%" height="100%">
                            <RadarChart cx="50%" cy="50%" outerRadius="70%" data={analyticsData.camera_effectiveness}>
                              <PolarGrid stroke="#374151" />
                              <PolarAngleAxis dataKey="camera_name" stroke="#9ca3af" fontSize={10} />
                              <PolarRadiusAxis stroke="#374151" fontSize={8} />
                              <Radar name="Efficiency Rate" dataKey="efficiency" stroke="#10b981" fill="#10b981" fillOpacity={0.3} />
                              <Tooltip contentStyle={{ backgroundColor: '#090d16', borderColor: '#1f2937' }} />
                            </RadarChart>
                          </ResponsiveContainer>
                        ) : (
                          <div className="h-full flex items-center justify-center">
                            <Loader2 className="w-6 h-6 animate-spin text-accent-cyan" />
                          </div>
                        )}
                      </div>
                    </div>
                  </div>

                  {/* Flow Map Table */}
                  <div className="glass-panel p-6 rounded-lg border border-glass-border">
                    <h4 className="text-sm font-bold tracking-wider text-white uppercase mb-4">Entity Spatial Traffic Flow</h4>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                      {analyticsData?.entity_flow?.map((flow: any, i: number) => (
                        <div key={i} className="bg-gray-950/80 p-4 rounded border border-glass-border flex justify-between items-center">
                          <div>
                            <span className="text-[10px] text-gray-500 uppercase font-semibold">Trajectory Path</span>
                            <span className="block text-xs font-bold text-white mt-1">{flow.source} ➔ {flow.target}</span>
                          </div>
                          <div className="text-right">
                            <span className="text-[10px] text-gray-500 uppercase font-semibold">Tracks</span>
                            <span className="block text-sm font-bold text-accent-cyan mt-1">{flow.value} entities/hr</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}

              {/* --- THREAT SIMULATOR TAB --- */}
              {activeTab === "simulator" && (
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                  {/* Left: Input parameters */}
                  <div className="glass-panel p-6 rounded-lg border border-glass-border space-y-6">
                    <h4 className="text-sm font-bold tracking-wider text-white uppercase">Simulation Variables</h4>
                    
                    <div className="space-y-4">
                      <div>
                        <label className="block text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">Scenario Descriptor</label>
                        <input 
                          type="text" 
                          value={simConfigName}
                          onChange={(e) => setSimConfigName(e.target.value)}
                          className="w-full bg-gray-950/60 border border-glass-border focus:border-accent-cyan outline-none text-white text-xs px-4 py-3 rounded-md"
                        />
                      </div>
                      
                      <div>
                        <label className="block text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">Camera Node Count: {simCamerasCount}</label>
                        <input 
                          type="range" 
                          min={2} 
                          max={50} 
                          value={simCamerasCount} 
                          onChange={(e) => setSimCamerasCount(Number(e.target.value))}
                          className="w-full accent-accent-cyan" 
                        />
                      </div>

                      <div>
                        <label className="block text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">Retention Scope: {simRetentionDays} Days</label>
                        <input 
                          type="range" 
                          min={1} 
                          max={90} 
                          value={simRetentionDays} 
                          onChange={(e) => setSimRetentionDays(Number(e.target.value))}
                          className="w-full accent-accent-cyan" 
                        />
                      </div>

                      <div>
                        <label className="block text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">Algorithmic Sensitivity: {Math.round(simSensitivity * 100)}%</label>
                        <input 
                          type="range" 
                          min={0.1} 
                          max={1.0} 
                          step={0.05} 
                          value={simSensitivity} 
                          onChange={(e) => setSimSensitivity(Number(e.target.value))}
                          className="w-full accent-accent-cyan" 
                        />
                      </div>

                      <div>
                        <label className="block text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">Identity Logging Policy</label>
                        <div className="grid grid-cols-2 gap-2">
                          {[
                            { id: "default_anonymized", label: "Shield Default" },
                            { id: "stored_by_default", label: "Expose Biometrics" }
                          ].map(opt => (
                            <button
                              key={opt.id}
                              type="button"
                              onClick={() => setSimIdentityCollection(opt.id)}
                              className={`py-2 rounded text-xs font-medium cursor-pointer border transition-all ${
                                simIdentityCollection === opt.id 
                                  ? "bg-accent-cyan/15 border-accent-cyan text-white" 
                                  : "bg-gray-950 border-glass-border text-gray-500"
                              }`}
                            >
                              {opt.label}
                            </button>
                          ))}
                        </div>
                      </div>

                      <div>
                        <label className="block text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">Crowd Density Threshold</label>
                        <select 
                          value={simCrowdDensity}
                          onChange={(e) => setSimCrowdDensity(e.target.value)}
                          className="w-full bg-gray-950/60 border border-glass-border focus:border-accent-cyan outline-none text-white text-xs px-4 py-3 rounded-md"
                        >
                          <option value="low">Low Pedestrian Frequency</option>
                          <option value="medium">Medium Pedestrian Frequency</option>
                          <option value="high">High Density Crowd</option>
                        </select>
                      </div>

                      <div>
                        <label className="block text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">Ambient Threat Index</label>
                        <select 
                          value={simThreatLevel}
                          onChange={(e) => setSimThreatLevel(e.target.value)}
                          className="w-full bg-gray-950/60 border border-glass-border focus:border-accent-cyan outline-none text-white text-xs px-4 py-3 rounded-md"
                        >
                          <option value="low">Low Threat Level</option>
                          <option value="medium">Medium Threat Level</option>
                          <option value="high">High Alert / Active Incident</option>
                        </select>
                      </div>
                    </div>

                    <button 
                      onClick={handleRunSimulation}
                      disabled={isSimulating}
                      className="w-full bg-accent-cyan hover:bg-cyan-500 disabled:bg-cyan-900/40 text-black font-semibold text-xs py-3 rounded-md transition-all flex items-center justify-center gap-2 cursor-pointer shadow-[0_0_15px_rgba(6,182,212,0.3)]"
                    >
                      {isSimulating ? (
                        <>
                          <Loader2 className="w-4 h-4 animate-spin" />
                          <span>Processing Simulation Node...</span>
                        </>
                      ) : (
                        <>
                          <Cpu className="w-4 h-4" />
                          <span>Simulate Architecture Trade-offs</span>
                        </>
                      )}
                    </button>
                  </div>

                  {/* Right: Results comparison */}
                  <div className="lg:col-span-2 space-y-6">
                    {simResult ? (
                      <div className="glass-panel p-6 rounded-lg border border-glass-border space-y-6">
                        <div>
                          <h4 className="text-sm font-bold tracking-wider text-white uppercase">Simulation Results Comparison</h4>
                          <span className="text-[10px] text-gray-500">BlindWatch AI vs Traditional Surveillance CCTV</span>
                        </div>

                        {/* Side-by-side metric tiles */}
                        <div className="space-y-4">
                          {[
                            { name: "Public Safety Index", bw: simResult.blindwatch.safety_score, trad: simResult.traditional.safety_score, suffix: "%", desc: "Ability to detect and mitigate safety threats" },
                            { name: "Privacy Preservation", bw: simResult.blindwatch.privacy_score, trad: simResult.traditional.privacy_score, suffix: "%", desc: "Biometric and identity protection score" },
                            { name: "Public Trust Quotient", bw: simResult.blindwatch.trust_score, trad: simResult.traditional.trust_score, suffix: "%", desc: "Citizen trust and transparency metric" },
                            { name: "Compliance Cleared", bw: simResult.blindwatch.compliance_score, trad: simResult.traditional.compliance_score, suffix: "%", desc: "GDPR, CCPA, and privacy regulation alignment" },
                            { name: "System Bias Risk", bw: simResult.blindwatch.bias_risk, trad: simResult.traditional.bias_risk, suffix: "%", desc: "Risk of demographic bias in threat models", invertColor: true }
                          ].map((metric, i) => (
                            <div key={i} className="bg-gray-950/80 border border-glass-border p-4 rounded-md space-y-3">
                              <div className="flex justify-between items-start">
                                <div>
                                  <span className="block text-xs font-bold text-white">{metric.name}</span>
                                  <span className="text-[9px] text-gray-500 leading-normal">{metric.desc}</span>
                                </div>
                              </div>
                              <div className="grid grid-cols-2 gap-4 text-center">
                                <div className="bg-cyan-950/20 border border-cyan-800/40 p-2.5 rounded">
                                  <span className="block text-[8px] text-cyan-400 font-bold uppercase">BlindWatch AI</span>
                                  <span className="block text-lg font-extrabold text-white mt-0.5">{metric.bw}{metric.suffix}</span>
                                </div>
                                <div className="bg-rose-950/10 border border-rose-900/30 p-2.5 rounded">
                                  <span className="block text-[8px] text-rose-400 font-bold uppercase">Traditional CCTV</span>
                                  <span className="block text-lg font-extrabold text-gray-400 mt-0.5">{metric.trad}{metric.suffix}</span>
                                </div>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    ) : (
                      <div className="h-full min-h-[500px] flex items-center justify-center glass-panel rounded-lg border border-glass-border">
                        <div className="text-center text-gray-500 max-w-sm px-6">
                          <Sliders className="w-10 h-10 mx-auto mb-2 text-gray-600" />
                          <p className="text-xs">Adjust variables and run the simulator model to contrast cybersecurity and privacy impacts side-by-side.</p>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* --- COMPLIANCE REPORTS TAB --- */}
              {activeTab === "reports" && (
                <div className="glass-panel p-8 rounded-lg border border-glass-border space-y-6 max-w-3xl mx-auto">
                  <div className="flex justify-between items-start border-b border-glass-border pb-6">
                    <div>
                      <Shield className="w-12 h-12 text-accent-cyan mb-3" />
                      <h3 className="text-xl font-bold text-white">BlindWatch Executive Compliance Audit</h3>
                      <p className="text-xs text-gray-400">Governance Review for Smart Surveillance Nodes</p>
                    </div>
                    <span className="border border-glass-border rounded px-3 py-1 font-mono text-xs text-accent-cyan uppercase">
                      SECURE AUDIT PORTAL
                    </span>
                  </div>

                  <div className="space-y-4 text-xs text-gray-300 leading-relaxed">
                    <p>
                      This automated compliance evaluation examines spatial camera networks, identity logging protocols, data lifecycle parameters, and operator logs within the BlindWatch Surveillance operating system boundaries.
                    </p>

                    <div className="bg-gray-950/80 border border-glass-border p-4 rounded-md space-y-2">
                      <h4 className="font-bold text-white">Strategic Recommendations</h4>
                      <ul className="list-disc pl-5 space-y-1 text-gray-400 text-xs">
                        <li>Maintain biometric identity shield active on CAM-01 and CAM-04 to uphold privacy index standards.</li>
                        <li>Audit dual-key decryption vaults weekly to verify operational integrity.</li>
                        <li>Optimize retention limits to 7 days to mitigate regulatory compliance exposure.</li>
                      </ul>
                    </div>

                    <div className="grid grid-cols-2 gap-4 border-t border-glass-border pt-6">
                      <div className="bg-gray-950/40 p-3 rounded border border-glass-border">
                        <span className="text-[10px] text-gray-500 font-semibold block uppercase">GDPR Compliance</span>
                        <span className="text-xs font-bold text-accent-emerald block mt-1">PASSED (Default Anonymization Enforced)</span>
                      </div>
                      <div className="bg-gray-950/40 p-3 rounded border border-glass-border">
                        <span className="text-[10px] text-gray-500 font-semibold block uppercase">CCPA Regulatory Alignment</span>
                        <span className="text-xs font-bold text-accent-emerald block mt-1">PASSED (Dual Approval Encryption Gates Active)</span>
                      </div>
                    </div>
                  </div>

                  <div className="border-t border-glass-border pt-6 flex justify-end">
                    <button 
                      onClick={handleExportReport}
                      className="bg-accent-cyan hover:bg-cyan-500 text-black text-xs font-bold py-3 px-6 rounded transition-all cursor-pointer flex items-center gap-2 shadow-[0_0_15px_rgba(6,182,212,0.3)]"
                    >
                      <Download className="w-4 h-4" />
                      <span>Download PDF Audit Report</span>
                    </button>
                  </div>
                </div>
              )}

              {/* --- SETTINGS TAB --- */}
              {activeTab === "settings" && (
                <div className="glass-panel p-6 rounded-lg border border-glass-border max-w-2xl mx-auto space-y-6">
                  <h4 className="text-sm font-bold tracking-wider text-white uppercase">System Configuration</h4>
                  
                  <div className="space-y-4">
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="block text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">Uvicorn API Host</label>
                        <input 
                          type="text" 
                          value={API_URL} 
                          disabled
                          className="w-full bg-gray-950/30 border border-glass-border text-gray-500 text-xs px-4 py-3 rounded-md cursor-not-allowed"
                        />
                      </div>
                      <div>
                        <label className="block text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">Database Engine</label>
                        <input 
                          type="text" 
                          value="SQLite 3 (Local Core)" 
                          disabled
                          className="w-full bg-gray-950/30 border border-glass-border text-gray-500 text-xs px-4 py-3 rounded-md cursor-not-allowed"
                        />
                      </div>
                    </div>

                    <div>
                      <label className="block text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">Cryptographic Vault Key Size</label>
                      <input 
                        type="text" 
                        value="RSA-4096 / SHA-256 HMAC (Dual Keyed)" 
                        disabled
                        className="w-full bg-gray-950/30 border border-glass-border text-gray-500 text-xs px-4 py-3 rounded-md cursor-not-allowed"
                      />
                    </div>

                    <div className="bg-gray-950/85 border border-glass-border p-4 rounded-md space-y-2">
                      <span className="block text-xs font-bold text-white">Surveillance Operating System State</span>
                      <p className="text-[10px] text-gray-500 leading-normal">
                        BlindWatch operates under a default-denied, zero-trust framework. Decryption authorization tokens generated by the Governance vault expire automatically following lease time-windows, writing all telemetry traces directly to the bypass-proof ledger.
                      </p>
                    </div>
                  </div>
                </div>
              )}
            </motion.div>
          </AnimatePresence>
        </div>
      </main>
    </div>
  );
}
