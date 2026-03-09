'use client';

import React, { useState, useEffect, useRef } from 'react';
import {
  BarChart, Bar, LineChart, Line, PieChart, Pie, Cell,
  AreaChart, Area, ScatterChart, Scatter,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  ReferenceLine,
} from 'recharts';
import {
  Send, Mic, MicOff, Upload, Trash2, Zap, MessageSquare,
  TrendingUp, TrendingDown, Minus, BookOpen, Lightbulb,
  Database, CheckCircle, AlertTriangle,
  Search, Sliders, AlertCircle, Download,
  Target, Shield, ArrowUpRight, ArrowDownRight, X,
} from 'lucide-react';

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const COLORS = ['#6366F1', '#8B5CF6', '#EC4899', '#F59E0B', '#10B981', '#3B82F6', '#EF4444', '#06B6D4'];

// ━━━━━━━━━━━━━ TYPES ━━━━━━━━━━━━━

interface KPICardData { label: string; value: string; trend?: string | null; trend_direction?: string | null; }
interface ChartConfig { type: string; title: string; x_axis?: string; y_axis?: string; series?: string[] | null; data: Record<string, any>[]; highlight?: any; }
interface DashboardData {
  kpi_cards: KPICardData[]; main_chart: ChartConfig; secondary_chart?: ChartConfig | null;
  narrative: string; suggested_followups: string[]; sql_query?: string | null; error?: string | null;
  available_columns?: string[]; data_quality?: any;
}
interface ProfileData {
  filename: string; rows: number; columns: number;
  column_info: { name: string; semantic_type: string; unique_count: number; sample_values: string[]; null_count: number }[];
  data_quality_score: number; missing_values: Record<string, number>; suggested_questions: string[];
}
interface ChatMsg { role: 'user' | 'assistant'; content: string; time: Date }
interface DeepDiveData {
  top_profit_drivers?: any[]; loss_risk_areas?: any[]; root_cause_analysis?: string;
  recommendations?: any[]; monthly_pnl?: any[]; profit_by_product?: any[]; profit_by_region?: any[]; error?: string;
}
interface WhatIfData {
  current?: any; projected?: any; change?: any; monthly_comparison?: any[];
  category_impact?: any[]; ai_commentary?: string; error?: string;
}
interface AnomalyData { anomalies?: string[]; count?: number; ai_analysis?: any[]; }

// ━━━━━━━━━━━━━ TOOLTIP ━━━━━━━━━━━━━

const CTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-dark-card border border-dark-border rounded-lg p-3 shadow-xl">
      <p className="text-xs text-gray-400 mb-1">{label}</p>
      {payload.map((e: any, i: number) => (
        <p key={i} className="text-xs font-medium" style={{ color: e.color }}>
          {e.name}: {typeof e.value === 'number' ? e.value.toLocaleString() : e.value}
        </p>
      ))}
    </div>
  );
};

// ━━━━━━━━━━━━━ CHART RENDERER ━━━━━━━━━━━━━

function ChartRenderer({ config, height = 320, onBarClick }: { config: ChartConfig; height?: number; onBarClick?: (data: any) => void }) {
  const { type, data, x_axis, y_axis, series } = config;
  if (!data?.length) return <div className="flex items-center justify-center h-64 text-gray-600">No data</div>;

  const numKeys = Object.keys(data[0]).filter(k => k !== x_axis && typeof data[0][k] === 'number');
  const keys = series?.length ? series : [y_axis || numKeys[0]].filter(Boolean);

  const handleClick = (d: any) => { if (onBarClick && d?.activePayload?.[0]) onBarClick(d.activePayload[0].payload); };

  switch (type) {
    case 'line':
      return (
        <ResponsiveContainer width="100%" height={height}>
          <LineChart data={data} onClick={handleClick} style={{ cursor: onBarClick ? 'pointer' : 'default' }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#2A2D3A" />
            <XAxis dataKey={x_axis} stroke="#6B7280" tick={{ fontSize: 11 }} />
            <YAxis stroke="#6B7280" tick={{ fontSize: 11 }} />
            <Tooltip content={<CTooltip />} />
            <Legend />
            {(keys.length > 0 ? keys : numKeys.slice(0, 5)).map((k, i) => (
              <Line key={k} type="monotone" dataKey={k!} stroke={COLORS[i % COLORS.length]} strokeWidth={2} dot={{ r: 4 }} activeDot={{ r: 7, stroke: '#fff', strokeWidth: 2 }} />
            ))}
          </LineChart>
        </ResponsiveContainer>
      );
    case 'area':
      return (
        <ResponsiveContainer width="100%" height={height}>
          <AreaChart data={data} onClick={handleClick} style={{ cursor: onBarClick ? 'pointer' : 'default' }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#2A2D3A" />
            <XAxis dataKey={x_axis} stroke="#6B7280" tick={{ fontSize: 11 }} />
            <YAxis stroke="#6B7280" tick={{ fontSize: 11 }} />
            <Tooltip content={<CTooltip />} />
            <Legend />
            {(keys.length > 0 ? keys : numKeys.slice(0, 5)).map((k, i) => (
              <Area key={k} type="monotone" dataKey={k!} stroke={COLORS[i % COLORS.length]} fill={COLORS[i % COLORS.length]} fillOpacity={0.15} strokeWidth={2} />
            ))}
          </AreaChart>
        </ResponsiveContainer>
      );
    case 'pie':
      return (
        <ResponsiveContainer width="100%" height={height}>
          <PieChart>
            <Pie data={data.slice(0, 8)} dataKey={y_axis || numKeys[0]} nameKey={x_axis} cx="50%" cy="50%" outerRadius={height * 0.35} innerRadius={height * 0.18} label={({ percent }: any) => `${(percent * 100).toFixed(0)}%`}>
              {data.slice(0, 8).map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
            </Pie>
            <Tooltip content={<CTooltip />} />
            <Legend />
          </PieChart>
        </ResponsiveContainer>
      );
    case 'scatter':
      return (
        <ResponsiveContainer width="100%" height={height}>
          <ScatterChart onClick={handleClick} style={{ cursor: onBarClick ? 'pointer' : 'default' }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#2A2D3A" />
            <XAxis dataKey={x_axis} stroke="#6B7280" tick={{ fontSize: 11 }} />
            <YAxis dataKey={y_axis} stroke="#6B7280" tick={{ fontSize: 11 }} />
            <Tooltip content={<CTooltip />} />
            <Scatter data={data} fill={COLORS[0]} />
          </ScatterChart>
        </ResponsiveContainer>
      );
    case 'stacked_bar':
      return (
        <ResponsiveContainer width="100%" height={height}>
          <BarChart data={data} onClick={handleClick} style={{ cursor: onBarClick ? 'pointer' : 'default' }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#2A2D3A" />
            <XAxis dataKey={x_axis} stroke="#6B7280" tick={{ fontSize: 11 }} />
            <YAxis stroke="#6B7280" tick={{ fontSize: 11 }} />
            <Tooltip content={<CTooltip />} />
            <Legend />
            {(keys.length > 0 ? keys : numKeys.slice(0, 5)).map((k, i) => (
              <Bar key={k} dataKey={k!} stackId="a" fill={COLORS[i % COLORS.length]} />
            ))}
          </BarChart>
        </ResponsiveContainer>
      );
    default:
      return (
        <ResponsiveContainer width="100%" height={height}>
          <BarChart data={data} onClick={handleClick} style={{ cursor: onBarClick ? 'pointer' : 'default' }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#2A2D3A" />
            <XAxis dataKey={x_axis} stroke="#6B7280" tick={{ fontSize: 11 }} />
            <YAxis stroke="#6B7280" tick={{ fontSize: 11 }} />
            <Tooltip content={<CTooltip />} />
            <Legend />
            {(keys.length > 0 ? keys : numKeys.slice(0, 1)).map((k, i) => (
              <Bar key={k} dataKey={k!} fill={COLORS[i % COLORS.length]} radius={[4, 4, 0, 0]} />
            ))}
          </BarChart>
        </ResponsiveContainer>
      );
  }
}

// ━━━━━━━━━━━━━ MAIN PAGE ━━━━━━━━━━━━━

export default function Home() {
  const [dashboard, setDashboard] = useState<DashboardData | null>(null);
  const [messages, setMessages] = useState<ChatMsg[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [profile, setProfile] = useState<ProfileData | null>(null);
  const [input, setInput] = useState('');
  const [listening, setListening] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [mounted, setMounted] = useState(false);
  const [hasVoice, setHasVoice] = useState(false);

  const [deepDive, setDeepDive] = useState<DeepDiveData | null>(null);
  const [deepDiveLoading, setDeepDiveLoading] = useState(false);
  const [showDeepDive, setShowDeepDive] = useState(false);
  const [whatIf, setWhatIf] = useState<WhatIfData | null>(null);
  const [whatIfLoading, setWhatIfLoading] = useState(false);
  const [showWhatIf, setShowWhatIf] = useState(false);
  const [priceChange, setPriceChange] = useState(0);
  const [costChange, setCostChange] = useState(0);
  const [unitsChange, setUnitsChange] = useState(0);
  const [anomalies, setAnomalies] = useState<AnomalyData | null>(null);
  const [anomalyLoading, setAnomalyLoading] = useState(false);
  const [showAnomalies, setShowAnomalies] = useState(false);
  const [drillDownInfo, setDrillDownInfo] = useState<string | null>(null);

  const msgEndRef = useRef<HTMLDivElement>(null);
  const recRef = useRef<any>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  const borderColors = ['border-l-accent-primary', 'border-l-accent-secondary', 'border-l-accent-success', 'border-l-accent-info'];

  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => { setMounted(true); setHasVoice('SpeechRecognition' in window || 'webkitSpeechRecognition' in window); }, []);
  useEffect(() => { msgEndRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [messages]);
  useEffect(() => { if (transcript) setInput(transcript); }, [transcript]);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => { if (!listening && transcript) { sendQuery(transcript); setTranscript(''); } }, [listening]);

  const startVoice = () => {
    if (!hasVoice) return;
    const SR = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    const rec = new SR();
    rec.continuous = false; rec.interimResults = true; rec.lang = 'en-US';
    rec.onstart = () => { setListening(true); setTranscript(''); };
    rec.onresult = (e: any) => {
      let f = '', interim = '';
      for (let i = e.resultIndex; i < e.results.length; i++) {
        const t = e.results[i][0].transcript;
        if (e.results[i].isFinal) f += t; else interim += t;
      }
      setTranscript(f || interim);
    };
    rec.onend = () => setListening(false);
    rec.onerror = () => setListening(false);
    recRef.current = rec;
    rec.start();
  };

  const stopVoice = () => recRef.current?.stop();

  const sendQuery = async (q: string) => {
    if (!q.trim()) return;
    const text = q.trim();
    setInput(''); setLoading(true); setError(null);
    setShowDeepDive(false); setShowWhatIf(false); setShowAnomalies(false);
    setDeepDive(null); setWhatIf(null); setAnomalies(null);

    setMessages(prev => [...prev, { role: 'user', content: text, time: new Date() }]);

    try {
      const history = messages.slice(-6).map(m => ({ role: m.role, content: m.content }));
      const res = await fetch(`${API}/api/query`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: text, conversation_history: history }),
      });
      const data: DashboardData = await res.json();

      if (data.error) {
        setError(data.error);
        setDashboard(null);
        setMessages(prev => [...prev, { role: 'assistant', content: `⚠️ ${data.error}`, time: new Date() }]);
      } else {
        setDashboard(data);
        setError(null);
        setMessages(prev => [...prev, { role: 'assistant', content: data.narrative || 'Dashboard updated.', time: new Date() }]);
      }
    } catch (e: any) {
      setError(e.message);
      setDashboard(null);
      setMessages(prev => [...prev, { role: 'assistant', content: `❌ ${e.message}`, time: new Date() }]);
    } finally {
      setLoading(false);
    }
  };

  const handleUpload = async (file: File) => {
    setLoading(true); setError(null);
    try {
      const form = new FormData(); form.append('file', file);
      const res = await fetch(`${API}/api/upload`, { method: 'POST', body: form });
      const data = await res.json();
      if (data.profile) setProfile(data.profile);
      setMessages(prev => [...prev, {
        role: 'assistant', time: new Date(),
        content: `✅ ${data.message}\n📊 Quality: ${data.profile?.data_quality_score || 100}%\n\nTry:\n${(data.profile?.suggested_questions || []).map((q2: string, i: number) => `${i + 1}. "${q2}"`).join('\n')}`
      }]);
    } catch (e: any) { setError(e.message); }
    finally { setLoading(false); }
  };

  const fetchDeepDive = async () => {
    setDeepDiveLoading(true); setShowDeepDive(true);
    try {
      const res = await fetch(`${API}/api/deep-dive`, { method: 'POST' });
      setDeepDive(await res.json());
    } catch (e: any) { setDeepDive({ error: e.message }); }
    finally { setDeepDiveLoading(false); }
  };

  const fetchWhatIf = async () => {
    setWhatIfLoading(true); setShowWhatIf(true);
    try {
      const res = await fetch(`${API}/api/what-if`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ price_change: priceChange, cost_change: costChange, units_change: unitsChange }),
      });
      setWhatIf(await res.json());
    } catch (e: any) { setWhatIf({ error: e.message }); }
    finally { setWhatIfLoading(false); }
  };

  const fetchAnomalies = async () => {
    setAnomalyLoading(true); setShowAnomalies(true);
    try {
      const res = await fetch(`${API}/api/anomalies`);
      setAnomalies(await res.json());
    } catch (e: any) { setAnomalies({ anomalies: [], count: 0 }); }
    finally { setAnomalyLoading(false); }
  };

  const handleBarClick = (data: any) => {
    const parts = Object.entries(data).map(([k, v]) =>
      typeof v === 'number' ? `${k}: ${(v as number).toLocaleString()}` : `${k}: ${v}`
    );
    setDrillDownInfo(parts.join(' | '));
    setTimeout(() => setDrillDownInfo(null), 5000);
  };

  const exportDashboard = () => {
    if (!dashboard) return;
    const exp = {
      kpi_cards: dashboard.kpi_cards, narrative: dashboard.narrative,
      sql_query: dashboard.sql_query, chart_data: dashboard.main_chart.data,
      exported_at: new Date().toISOString(),
    };
    const blob = new Blob([JSON.stringify(exp, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url; a.download = `dashai-export-${Date.now()}.json`; a.click();
    URL.revokeObjectURL(url);
  };

  const clear = () => {
    setMessages([]); setDashboard(null); setError(null); setProfile(null);
    setDeepDive(null); setWhatIf(null); setAnomalies(null);
    setShowDeepDive(false); setShowWhatIf(false); setShowAnomalies(false);
  };

  const handleKey = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendQuery(input); }
  };

  if (!mounted) {
    return (
      <div className="h-screen flex items-center justify-center bg-dark-bg">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-accent-primary rounded-lg flex items-center justify-center animate-pulse">
            <Zap className="w-5 h-5 text-white" />
          </div>
          <span className="text-xl font-bold text-white">Loading DASH.AI...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="h-screen flex flex-col overflow-hidden bg-dark-bg">

      {/* ═══ HEADER ═══ */}
      <header className="h-14 bg-dark-card border-b border-dark-border flex items-center justify-between px-6 flex-shrink-0">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-accent-primary rounded-lg flex items-center justify-center">
            <Zap className="w-5 h-5 text-white" />
          </div>
          <h1 className="text-xl font-bold">
            <span className="text-accent-primary">DASH</span>
            <span className="text-gray-500">.</span>
            <span>AI</span>
          </h1>
          <span className="text-[10px] text-gray-500 bg-dark-bg px-2 py-0.5 rounded-full">AI BI Co-Pilot</span>
        </div>
        <div className="flex gap-2">
          {dashboard && (
            <button onClick={exportDashboard} className="flex items-center gap-1.5 px-3 py-1.5 bg-dark-bg border border-dark-border rounded-lg text-xs text-gray-300 hover:border-accent-success hover:text-accent-success transition-all">
              <Download className="w-3.5 h-3.5" />Export
            </button>
          )}
          <button onClick={() => fileRef.current?.click()} className="flex items-center gap-1.5 px-3 py-1.5 bg-dark-bg border border-dark-border rounded-lg text-xs text-gray-300 hover:border-accent-primary hover:text-accent-primary transition-all">
            <Upload className="w-3.5 h-3.5" />Upload CSV
          </button>
          <input ref={fileRef} type="file" accept=".csv" onChange={e => e.target.files?.[0] && handleUpload(e.target.files[0])} className="hidden" />
          <button onClick={clear} className="flex items-center gap-1.5 px-3 py-1.5 bg-dark-bg border border-dark-border rounded-lg text-xs text-gray-400 hover:border-accent-danger hover:text-accent-danger transition-all">
            <Trash2 className="w-3.5 h-3.5" />Clear
          </button>
        </div>
      </header>

      {/* ═══ DRILL DOWN TOAST ═══ */}
      {drillDownInfo && (
        <div className="absolute top-16 left-1/2 -translate-x-1/2 z-50 bg-accent-primary text-white px-6 py-3 rounded-xl shadow-2xl text-sm flex items-center gap-2 animate-slide-up">
          <Target className="w-4 h-4" />
          <span className="max-w-lg truncate">{drillDownInfo}</span>
          <button onClick={() => setDrillDownInfo(null)}><X className="w-4 h-4" /></button>
        </div>
      )}

      {/* ═══ MAIN LAYOUT ═══ */}
      <div className="flex-1 flex overflow-hidden">

        {/* ─── CHAT SIDEBAR ─── */}
        <div className="w-80 bg-dark-card border-r border-dark-border flex flex-col flex-shrink-0">
          <div className="p-4 border-b border-dark-border">
            <div className="flex items-center gap-2">
              <MessageSquare className="w-4 h-4 text-accent-primary" />
              <span className="text-sm font-semibold text-gray-300">Chat</span>
            </div>
          </div>

          <div className="flex-1 overflow-y-auto p-4 space-y-3">
            {messages.length === 0 && (
              <div className="text-center py-8">
                <p className="text-gray-600 text-sm">Ask about your data</p>
                <p className="text-gray-700 text-xs mt-1">or use 🎤 voice</p>
              </div>
            )}
            {messages.map((m, i) => (
              <div key={i} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div className={`max-w-[90%] rounded-xl px-3 py-2 text-sm ${m.role === 'user' ? 'bg-accent-primary text-white' : 'bg-dark-bg text-gray-300 border border-dark-border'}`}>
                  <p className="whitespace-pre-wrap">{m.content}</p>
                  <p className="text-[10px] mt-1 opacity-40">{m.time.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</p>
                </div>
              </div>
            ))}
            {loading && (
              <div className="flex justify-start">
                <div className="bg-dark-bg rounded-xl px-4 py-3 border border-dark-border flex gap-1">
                  <div className="w-2 h-2 bg-accent-primary rounded-full animate-bounce" />
                  <div className="w-2 h-2 bg-accent-primary rounded-full animate-bounce" style={{ animationDelay: '0.1s' }} />
                  <div className="w-2 h-2 bg-accent-primary rounded-full animate-bounce" style={{ animationDelay: '0.2s' }} />
                </div>
              </div>
            )}
            <div ref={msgEndRef} />
          </div>

          <div className="p-3 border-t border-dark-border">
            {listening && (
              <div className="mb-2 px-3 py-1.5 bg-accent-danger/10 border border-accent-danger/30 rounded-lg">
                <p className="text-xs text-accent-danger animate-pulse">🎤 Listening...</p>
                {transcript && <p className="text-xs text-gray-400 mt-1">&quot;{transcript}&quot;</p>}
              </div>
            )}
            <div className="flex items-center gap-2">
              {hasVoice && (
                <button onClick={listening ? stopVoice : startVoice} className={`p-2.5 rounded-xl transition-all ${listening ? 'bg-accent-danger text-white recording-pulse' : 'bg-dark-hover text-gray-400 hover:text-accent-primary'}`}>
                  {listening ? <MicOff className="w-4 h-4" /> : <Mic className="w-4 h-4" />}
                </button>
              )}
              <input
                value={input} onChange={e => setInput(e.target.value)} onKeyDown={handleKey}
                placeholder="Ask about your data..." disabled={loading}
                className="flex-1 bg-dark-bg border border-dark-border rounded-xl px-3 py-2.5 text-sm text-white placeholder-gray-600 focus:outline-none focus:border-accent-primary transition-colors"
              />
              <button onClick={() => sendQuery(input)} disabled={!input.trim() || loading} className="p-2.5 bg-accent-primary rounded-xl text-white disabled:opacity-30 hover:bg-accent-primary/80 transition-all">
                <Send className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>

        {/* ─── DASHBOARD CANVAS ─── */}
        <div className="flex-1 overflow-y-auto">

          {/* LOADING SKELETON */}
          {loading && !dashboard && (
            <div className="p-6 space-y-6">
              <div className="grid grid-cols-4 gap-4">
                {[1, 2, 3, 4].map(i => (
                  <div key={i} className="bg-dark-card rounded-xl p-4 border border-dark-border">
                    <div className="skeleton h-4 w-24 rounded mb-3" />
                    <div className="skeleton h-8 w-32 rounded mb-2" />
                    <div className="skeleton h-3 w-16 rounded" />
                  </div>
                ))}
              </div>
              <div className="grid grid-cols-3 gap-4">
                <div className="col-span-2 bg-dark-card rounded-xl p-6 border border-dark-border">
                  <div className="skeleton h-64 w-full rounded" />
                </div>
                <div className="bg-dark-card rounded-xl p-6 border border-dark-border">
                  <div className="skeleton h-64 w-full rounded" />
                </div>
              </div>
            </div>
          )}

          {/* SMART ERROR WITH SUGGESTIONS */}
          {error && !dashboard && !loading && (
            <div className="flex flex-col items-center justify-center h-full p-6 space-y-6">
              <div className="bg-dark-card rounded-xl p-8 border border-accent-warning/30 max-w-2xl w-full">
                <div className="flex items-center gap-3 mb-4">
                  <div className="w-10 h-10 bg-accent-warning/10 rounded-full flex items-center justify-center">
                    <AlertTriangle className="w-5 h-5 text-accent-warning" />
                  </div>
                  <div>
                    <h3 className="text-sm font-semibold text-white">Couldn&apos;t process that query</h3>
                    <p className="text-xs text-gray-500">But here&apos;s how to fix it</p>
                  </div>
                </div>

                <p className="text-sm text-gray-400 mb-4">{error}</p>

                <div className="bg-dark-bg rounded-lg p-4 mb-4">
                  <p className="text-xs text-accent-primary font-semibold mb-3">💡 Try these queries instead:</p>
                  <div className="space-y-2">
                    {[
                      'Show total revenue by region',
                      'Show monthly revenue trends',
                      'Top 10 products by profit',
                      'Compare product categories by revenue',
                      'Show revenue and profit by region',
                      'What is the average unit price by category',
                    ].map((q2, i) => (
                      <button key={i} onClick={() => { setError(null); sendQuery(q2); }}
                        className="w-full text-left text-sm px-3 py-2 bg-dark-card rounded-lg text-gray-300 hover:text-accent-primary hover:bg-dark-hover transition-all border border-transparent hover:border-accent-primary/30 flex items-center gap-2">
                        <span className="text-accent-primary">→</span> {q2}
                      </button>
                    ))}
                  </div>
                </div>

                <details className="bg-dark-bg rounded-lg p-4">
                  <summary className="text-xs text-gray-500 cursor-pointer hover:text-gray-400">📋 View available data columns</summary>
                  <div className="flex flex-wrap gap-2 mt-3">
                    {['date', 'region', 'product_category', 'product_name', 'units_sold', 'unit_price', 'revenue', 'cost', 'profit', 'salesperson'].map((col, i) => (
                      <span key={i} className="text-xs px-2 py-1 rounded-full bg-dark-card border border-dark-border text-gray-400">{col}</span>
                    ))}
                  </div>
                  <p className="text-[10px] text-gray-600 mt-2">Tip: Use these column names in your questions for best results</p>
                </details>
              </div>
            </div>
          )}

          {/* WELCOME SCREEN */}
          {!dashboard && !profile && !loading && !error && (
            <div className="flex flex-col items-center justify-center h-full p-6 space-y-8">
              <div className="text-center">
                <div className="w-20 h-20 bg-accent-primary/10 rounded-2xl flex items-center justify-center mx-auto mb-4">
                  <Zap className="w-10 h-10 text-accent-primary" />
                </div>
                <h2 className="text-2xl font-bold mb-2">Welcome to DASH.AI</h2>
                <p className="text-gray-500 max-w-md">Your AI-powered BI co-pilot with Deep Dive Analysis, What-If Simulator &amp; Anomaly Detection.</p>
              </div>
              <div onClick={() => fileRef.current?.click()} className="border-2 border-dashed border-dark-border hover:border-accent-primary/50 rounded-xl p-10 text-center cursor-pointer transition-all w-full max-w-lg">
                <Upload className="w-14 h-14 text-gray-600 mx-auto" />
                <p className="text-gray-400 mt-3">Click to upload CSV</p>
              </div>
              <div className="text-center">
                <p className="text-gray-600 text-xs mb-3">Or try with pre-loaded sample data:</p>
                <div className="flex flex-wrap gap-2 justify-center max-w-lg">
                  {['Show total revenue by region', 'Monthly sales trends', 'Top 5 products by profit', 'Compare revenue across categories'].map((q2, i) => (
                    <button key={i} onClick={() => sendQuery(q2)} className="text-xs px-4 py-2 bg-dark-card border border-dark-border rounded-full text-gray-400 hover:text-accent-primary hover:border-accent-primary transition-all">{q2}</button>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* PROFILE SCREEN */}
          {!dashboard && profile && !loading && (
            <div className="p-6">
              <div className="bg-dark-card rounded-xl p-6 border border-dark-border animate-slide-up">
                <div className="flex items-center gap-2 mb-4">
                  <Database className="w-5 h-5 text-accent-primary" />
                  <h3 className="font-semibold">{profile.filename}</h3>
                </div>
                <div className="grid grid-cols-3 gap-4 mb-4">
                  <div className="bg-dark-bg rounded-lg p-3"><p className="text-xs text-gray-500">Rows</p><p className="text-lg font-bold">{profile.rows.toLocaleString()}</p></div>
                  <div className="bg-dark-bg rounded-lg p-3"><p className="text-xs text-gray-500">Columns</p><p className="text-lg font-bold">{profile.columns}</p></div>
                  <div className="bg-dark-bg rounded-lg p-3"><p className="text-xs text-gray-500">Quality</p>
                    <div className="flex items-center gap-1">
                      {profile.data_quality_score >= 90 ? <CheckCircle className="w-4 h-4 text-accent-success" /> : <AlertTriangle className="w-4 h-4 text-accent-warning" />}
                      <p className="text-lg font-bold">{profile.data_quality_score}%</p>
                    </div>
                  </div>
                </div>
                <div className="mb-4">
                  <p className="text-xs text-gray-500 mb-2">Columns:</p>
                  <div className="flex flex-wrap gap-2">
                    {profile.column_info.map((c, i) => (
                      <span key={i} className={`text-xs px-2 py-1 rounded-full ${c.semantic_type === 'numeric' ? 'bg-accent-info/20 text-accent-info' : c.semantic_type === 'date' ? 'bg-accent-warning/20 text-accent-warning' : 'bg-accent-secondary/20 text-accent-secondary'}`}>{c.name}</span>
                    ))}
                  </div>
                </div>
                <div>
                  <p className="text-xs text-gray-500 mb-2">💡 Try asking:</p>
                  {profile.suggested_questions.map((q2, i) => (
                    <button key={i} onClick={() => sendQuery(q2)} className="w-full text-left text-sm px-3 py-2 mb-1 bg-dark-bg rounded-lg text-gray-300 hover:text-accent-primary hover:bg-dark-hover transition-all border border-transparent hover:border-accent-primary/30">
                      &quot;{q2}&quot;
                    </button>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* ═══════════════════════════════════════ */}
          {/* ═══ FULL DASHBOARD ═══ */}
          {/* ═══════════════════════════════════════ */}
          {dashboard && !dashboard.error && (
            <div className="p-6 space-y-6">

              {/* KPI CARDS */}
              {dashboard.kpi_cards.length > 0 && (
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  {dashboard.kpi_cards.map((card, i) => (
                    <div key={i} className={`bg-dark-card rounded-xl p-4 border border-dark-border ${borderColors[i % 4]} border-l-4 animate-slide-up`} style={{ animationDelay: `${i * 80}ms` }}>
                      <p className="text-[10px] text-gray-400 uppercase tracking-wider mb-1">{card.label}</p>
                      <p className="text-2xl font-bold mb-1">{card.value}</p>
                      {card.trend && (
                        <div className="flex items-center gap-1">
                          {card.trend_direction === 'up' ? <TrendingUp className="w-3.5 h-3.5 text-accent-success" /> : card.trend_direction === 'down' ? <TrendingDown className="w-3.5 h-3.5 text-accent-danger" /> : <Minus className="w-3.5 h-3.5 text-gray-500" />}
                          <span className={`text-xs ${card.trend_direction === 'up' ? 'text-accent-success' : card.trend_direction === 'down' ? 'text-accent-danger' : 'text-gray-500'}`}>{card.trend}</span>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}

              {/* DATA QUALITY WARNING */}
              {dashboard.data_quality && Object.keys(dashboard.data_quality.missing_in_query || {}).length > 0 && (
                <div className="bg-accent-warning/5 border border-accent-warning/20 rounded-xl p-4 flex items-start gap-3 animate-slide-up">
                  <AlertTriangle className="w-5 h-5 text-accent-warning flex-shrink-0 mt-0.5" />
                  <div>
                    <p className="text-sm font-medium text-accent-warning">Some data has missing values</p>
                    <p className="text-xs text-gray-400 mt-1">
                      {Object.entries(dashboard.data_quality.missing_in_query || {}).map(([col, count]: [string, any]) => (
                        <span key={col} className="inline-block mr-3">
                          {col}: <span className="text-accent-warning">{count} missing</span>
                        </span>
                      ))}
                    </p>
                    <p className="text-[10px] text-gray-600 mt-1">Results may be partial. Missing values were excluded from calculations.</p>
                  </div>
                </div>
              )}

              {/* CHARTS — INTERACTIVE */}
              <div className={`grid gap-4 ${dashboard.secondary_chart ? 'grid-cols-1 lg:grid-cols-3' : 'grid-cols-1'}`}>
                <div className={`${dashboard.secondary_chart ? 'lg:col-span-2' : ''} bg-dark-card rounded-xl p-6 border border-dark-border animate-slide-up`}>
                  <h3 className="text-sm font-semibold text-gray-300 mb-1">{dashboard.main_chart.title}</h3>
                  <p className="text-[10px] text-gray-600 mb-4">Click any data point to drill down</p>
                  <ChartRenderer config={dashboard.main_chart} onBarClick={handleBarClick} />
                </div>
                {dashboard.secondary_chart && (
                  <div className="bg-dark-card rounded-xl p-6 border border-dark-border animate-slide-up">
                    <h3 className="text-sm font-semibold text-gray-300 mb-4">{dashboard.secondary_chart.title}</h3>
                    <ChartRenderer config={dashboard.secondary_chart} height={280} onBarClick={handleBarClick} />
                  </div>
                )}
              </div>

              {/* NARRATIVE + POWER BUTTONS */}
              {dashboard.narrative && (
                <div className="bg-dark-card rounded-xl p-6 border border-dark-border border-l-4 border-l-accent-primary animate-slide-up">
                  <div className="flex items-center gap-2 mb-3">
                    <BookOpen className="w-4 h-4 text-accent-primary" />
                    <h3 className="text-sm font-semibold text-accent-primary">AI Executive Insight</h3>
                  </div>
                  <p className="text-gray-300 leading-relaxed text-sm mb-4">{dashboard.narrative}</p>
                  <div className="flex flex-wrap gap-3">
                    <button onClick={fetchDeepDive} disabled={deepDiveLoading}
                      className="flex items-center gap-2 px-4 py-2 bg-accent-primary/10 border border-accent-primary/30 rounded-lg text-sm text-accent-primary hover:bg-accent-primary/20 transition-all disabled:opacity-50">
                      <Search className="w-4 h-4" />{deepDiveLoading ? 'Analyzing...' : '🔍 Deep Dive P&L Analysis'}
                    </button>
                    <button onClick={() => { setShowWhatIf(true); fetchWhatIf(); }} disabled={whatIfLoading}
                      className="flex items-center gap-2 px-4 py-2 bg-accent-secondary/10 border border-accent-secondary/30 rounded-lg text-sm text-accent-secondary hover:bg-accent-secondary/20 transition-all disabled:opacity-50">
                      <Sliders className="w-4 h-4" />{whatIfLoading ? 'Simulating...' : '📊 What-If Simulator'}
                    </button>
                    <button onClick={fetchAnomalies} disabled={anomalyLoading}
                      className="flex items-center gap-2 px-4 py-2 bg-accent-warning/10 border border-accent-warning/30 rounded-lg text-sm text-accent-warning hover:bg-accent-warning/20 transition-all disabled:opacity-50">
                      <AlertCircle className="w-4 h-4" />{anomalyLoading ? 'Scanning...' : '🚨 Detect Anomalies'}
                    </button>
                  </div>
                </div>
              )}

              {/* ═══ DEEP DIVE PANEL ═══ */}
              {showDeepDive && (
                <div className="bg-dark-card rounded-xl border border-accent-primary/30 overflow-hidden animate-slide-up">
                  <div className="flex items-center justify-between px-6 py-4 border-b border-dark-border bg-accent-primary/5">
                    <div className="flex items-center gap-2">
                      <Search className="w-5 h-5 text-accent-primary" />
                      <h3 className="font-semibold text-accent-primary">Deep Dive: Profit &amp; Loss Analysis</h3>
                    </div>
                    <button onClick={() => setShowDeepDive(false)}><X className="w-5 h-5 text-gray-500 hover:text-white" /></button>
                  </div>

                  {deepDiveLoading ? (
                    <div className="p-6 space-y-4">
                      <div className="skeleton h-8 w-64 rounded" />
                      <div className="skeleton h-48 w-full rounded" />
                      <div className="skeleton h-32 w-full rounded" />
                    </div>
                  ) : deepDive && !deepDive.error ? (
                    <div className="p-6 space-y-6">

                      {deepDive.profit_by_product && (
                        <div>
                          <h4 className="text-sm font-semibold text-gray-300 mb-1">📈 Profit by Product (Click to explore)</h4>
                          <p className="text-[10px] text-gray-600 mb-3">Green = high margin, Yellow = medium, Red = low</p>
                          <ResponsiveContainer width="100%" height={280}>
                            <BarChart data={deepDive.profit_by_product} onClick={(d: any) => d?.activePayload?.[0] && handleBarClick(d.activePayload[0].payload)}>
                              <CartesianGrid strokeDasharray="3 3" stroke="#2A2D3A" />
                              <XAxis dataKey="product_name" stroke="#6B7280" tick={{ fontSize: 10 }} />
                              <YAxis stroke="#6B7280" tick={{ fontSize: 11 }} />
                              <Tooltip content={<CTooltip />} />
                              <Bar dataKey="profit" radius={[4, 4, 0, 0]}>
                                {deepDive.profit_by_product.map((entry: any, i: number) => (
                                  <Cell key={i} fill={entry.margin_pct > 30 ? '#10B981' : entry.margin_pct > 20 ? '#F59E0B' : '#EF4444'} />
                                ))}
                              </Bar>
                              <ReferenceLine y={0} stroke="#6B7280" />
                            </BarChart>
                          </ResponsiveContainer>
                        </div>
                      )}

                      {deepDive.profit_by_region && (
                        <div>
                          <h4 className="text-sm font-semibold text-gray-300 mb-3">🗺️ Profit by Region</h4>
                          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                            {deepDive.profit_by_region.map((r: any, i: number) => (
                              <div key={i} className="bg-dark-bg rounded-lg p-3">
                                <p className="text-xs text-gray-500">{r.region}</p>
                                <p className="text-lg font-bold">${(r.profit / 1000).toFixed(0)}K</p>
                                <p className={`text-xs ${r.margin_pct > 30 ? 'text-accent-success' : r.margin_pct > 20 ? 'text-accent-warning' : 'text-accent-danger'}`}>
                                  {r.margin_pct}% margin
                                </p>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {deepDive.root_cause_analysis && (
                        <div className="bg-dark-bg rounded-lg p-4 border-l-4 border-l-accent-warning">
                          <h4 className="text-sm font-semibold text-accent-warning mb-2">🤖 Root Cause Analysis</h4>
                          <p className="text-sm text-gray-300 leading-relaxed">{deepDive.root_cause_analysis}</p>
                        </div>
                      )}

                      {deepDive.recommendations && deepDive.recommendations.length > 0 && (
                        <div>
                          <h4 className="text-sm font-semibold text-gray-300 mb-3">💡 AI Recommendations</h4>
                          <div className="space-y-2">
                            {deepDive.recommendations.map((rec: any, i: number) => (
                              <div key={i} className={`flex items-start gap-3 p-3 rounded-lg bg-dark-bg border-l-4 ${rec.priority === 'high' ? 'border-l-accent-danger' : rec.priority === 'medium' ? 'border-l-accent-warning' : 'border-l-accent-info'}`}>
                                <span className={`text-xs px-2 py-0.5 rounded-full flex-shrink-0 ${rec.priority === 'high' ? 'bg-accent-danger/20 text-accent-danger' : rec.priority === 'medium' ? 'bg-accent-warning/20 text-accent-warning' : 'bg-accent-info/20 text-accent-info'}`}>
                                  {rec.priority}
                                </span>
                                <div>
                                  <p className="text-sm text-gray-300">{rec.action}</p>
                                  <p className="text-xs text-gray-500 mt-1">Impact: {rec.expected_impact}</p>
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {deepDive.monthly_pnl && deepDive.monthly_pnl.length > 0 && (
                        <div>
                          <h4 className="text-sm font-semibold text-gray-300 mb-3">📊 Monthly P&amp;L Trend</h4>
                          <ResponsiveContainer width="100%" height={250}>
                            <LineChart data={deepDive.monthly_pnl} onClick={(d: any) => d?.activePayload?.[0] && handleBarClick(d.activePayload[0].payload)}>
                              <CartesianGrid strokeDasharray="3 3" stroke="#2A2D3A" />
                              <XAxis dataKey="month" stroke="#6B7280" tick={{ fontSize: 10 }} />
                              <YAxis stroke="#6B7280" tick={{ fontSize: 11 }} />
                              <Tooltip content={<CTooltip />} />
                              <Legend />
                              <Line type="monotone" dataKey="revenue" stroke="#6366F1" strokeWidth={2} dot={{ r: 4 }} activeDot={{ r: 7 }} />
                              <Line type="monotone" dataKey="cost" stroke="#EF4444" strokeWidth={2} dot={{ r: 4 }} activeDot={{ r: 7 }} />
                              <Line type="monotone" dataKey="profit" stroke="#10B981" strokeWidth={2.5} dot={{ r: 4 }} activeDot={{ r: 7 }} />
                              <ReferenceLine y={0} stroke="#6B7280" />
                            </LineChart>
                          </ResponsiveContainer>
                        </div>
                      )}
                    </div>
                  ) : (
                    <div className="p-6 text-gray-500 text-sm">{deepDive?.error || 'No data available'}</div>
                  )}
                </div>
              )}

              {/* ═══ WHAT-IF SIMULATOR ═══ */}
              {showWhatIf && (
                <div className="bg-dark-card rounded-xl border border-accent-secondary/30 overflow-hidden animate-slide-up">
                  <div className="flex items-center justify-between px-6 py-4 border-b border-dark-border bg-accent-secondary/5">
                    <div className="flex items-center gap-2">
                      <Sliders className="w-5 h-5 text-accent-secondary" />
                      <h3 className="font-semibold text-accent-secondary">What-If Scenario Simulator</h3>
                    </div>
                    <button onClick={() => setShowWhatIf(false)}><X className="w-5 h-5 text-gray-500 hover:text-white" /></button>
                  </div>
                  <div className="p-6 space-y-6">
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                      <div>
                        <label className="text-xs text-gray-400 mb-2 block">
                          Price Change: <span className={`font-bold ${priceChange >= 0 ? 'text-accent-success' : 'text-accent-danger'}`}>{priceChange >= 0 ? '+' : ''}{priceChange}%</span>
                        </label>
                        <input type="range" min="-30" max="30" value={priceChange} onChange={e => setPriceChange(Number(e.target.value))} className="w-full h-2 bg-dark-bg rounded-lg appearance-none cursor-pointer accent-accent-primary" />
                      </div>
                      <div>
                        <label className="text-xs text-gray-400 mb-2 block">
                          Cost Change: <span className={`font-bold ${costChange <= 0 ? 'text-accent-success' : 'text-accent-danger'}`}>{costChange >= 0 ? '+' : ''}{costChange}%</span>
                        </label>
                        <input type="range" min="-30" max="30" value={costChange} onChange={e => setCostChange(Number(e.target.value))} className="w-full h-2 bg-dark-bg rounded-lg appearance-none cursor-pointer accent-accent-secondary" />
                      </div>
                      <div>
                        <label className="text-xs text-gray-400 mb-2 block">
                          Units Growth: <span className={`font-bold ${unitsChange >= 0 ? 'text-accent-success' : 'text-accent-danger'}`}>{unitsChange >= 0 ? '+' : ''}{unitsChange}%</span>
                        </label>
                        <input type="range" min="-30" max="30" value={unitsChange} onChange={e => setUnitsChange(Number(e.target.value))} className="w-full h-2 bg-dark-bg rounded-lg appearance-none cursor-pointer accent-accent-success" />
                      </div>
                    </div>

                    <button onClick={fetchWhatIf} disabled={whatIfLoading} className="px-6 py-2 bg-accent-secondary rounded-lg text-white text-sm font-medium hover:bg-accent-secondary/80 disabled:opacity-50 transition-all">
                      {whatIfLoading ? 'Simulating...' : '▶ Run Simulation'}
                    </button>

                    {whatIfLoading && <div className="skeleton h-48 w-full rounded" />}

                    {whatIf && !whatIf.error && (
                      <>
                        <div className="grid grid-cols-3 gap-4">
                          <div className="bg-dark-bg rounded-lg p-4 text-center">
                            <p className="text-xs text-gray-500">Current Profit</p>
                            <p className="text-xl font-bold">${((whatIf.current?.profit || 0) / 1000).toFixed(0)}K</p>
                          </div>
                          <div className="bg-dark-bg rounded-lg p-4 text-center">
                            <p className="text-xs text-gray-500">Projected Profit</p>
                            <p className="text-xl font-bold text-accent-primary">${((whatIf.projected?.profit || 0) / 1000).toFixed(0)}K</p>
                          </div>
                          <div className={`bg-dark-bg rounded-lg p-4 text-center border-2 ${(whatIf.change?.profit_diff || 0) >= 0 ? 'border-accent-success/30' : 'border-accent-danger/30'}`}>
                            <p className="text-xs text-gray-500">Change</p>
                            <div className="flex items-center justify-center gap-1">
                              {(whatIf.change?.profit_diff || 0) >= 0 ? <ArrowUpRight className="w-5 h-5 text-accent-success" /> : <ArrowDownRight className="w-5 h-5 text-accent-danger" />}
                              <p className={`text-xl font-bold ${(whatIf.change?.profit_diff || 0) >= 0 ? 'text-accent-success' : 'text-accent-danger'}`}>
                                {whatIf.change?.profit_pct_change >= 0 ? '+' : ''}{whatIf.change?.profit_pct_change}%
                              </p>
                            </div>
                          </div>
                        </div>

                        {whatIf.monthly_comparison && whatIf.monthly_comparison.length > 0 && (
                          <div>
                            <h4 className="text-sm font-semibold text-gray-300 mb-3">Actual vs Projected</h4>
                            <ResponsiveContainer width="100%" height={250}>
                              <LineChart data={whatIf.monthly_comparison}>
                                <CartesianGrid strokeDasharray="3 3" stroke="#2A2D3A" />
                                <XAxis dataKey="month" stroke="#6B7280" tick={{ fontSize: 10 }} />
                                <YAxis stroke="#6B7280" tick={{ fontSize: 11 }} />
                                <Tooltip content={<CTooltip />} />
                                <Legend />
                                <Line type="monotone" dataKey="actual_revenue" stroke="#6B7280" strokeWidth={2} strokeDasharray="5 5" name="Actual Revenue" dot={{ r: 3 }} />
                                <Line type="monotone" dataKey="projected_revenue" stroke="#6366F1" strokeWidth={2.5} name="Projected Revenue" dot={{ r: 4 }} activeDot={{ r: 7 }} />
                                <Line type="monotone" dataKey="actual_profit" stroke="#9CA3AF" strokeWidth={1.5} strokeDasharray="5 5" name="Actual Profit" dot={{ r: 3 }} />
                                <Line type="monotone" dataKey="projected_profit" stroke="#10B981" strokeWidth={2.5} name="Projected Profit" dot={{ r: 4 }} activeDot={{ r: 7 }} />
                              </LineChart>
                            </ResponsiveContainer>
                          </div>
                        )}

                        {whatIf.category_impact && whatIf.category_impact.length > 0 && (
                          <div>
                            <h4 className="text-sm font-semibold text-gray-300 mb-3">Impact by Category</h4>
                            <ResponsiveContainer width="100%" height={200}>
                              <BarChart data={whatIf.category_impact}>
                                <CartesianGrid strokeDasharray="3 3" stroke="#2A2D3A" />
                                <XAxis dataKey="category" stroke="#6B7280" tick={{ fontSize: 11 }} />
                                <YAxis stroke="#6B7280" tick={{ fontSize: 11 }} />
                                <Tooltip content={<CTooltip />} />
                                <Legend />
                                <Bar dataKey="current_profit" fill="#6B7280" name="Current" radius={[4, 4, 0, 0]} />
                                <Bar dataKey="projected_profit" fill="#6366F1" name="Projected" radius={[4, 4, 0, 0]} />
                              </BarChart>
                            </ResponsiveContainer>
                          </div>
                        )}

                        {whatIf.ai_commentary && (
                          <div className="bg-dark-bg rounded-lg p-4 border-l-4 border-l-accent-secondary">
                            <div className="flex items-center gap-2 mb-2">
                              <Shield className="w-4 h-4 text-accent-secondary" />
                              <h4 className="text-sm font-semibold text-accent-secondary">AI Scenario Analysis</h4>
                            </div>
                            <p className="text-sm text-gray-300 leading-relaxed">{whatIf.ai_commentary}</p>
                          </div>
                        )}
                      </>
                    )}
                  </div>
                </div>
              )}

              {/* ═══ ANOMALY DETECTION ═══ */}
              {showAnomalies && (
                <div className="bg-dark-card rounded-xl border border-accent-warning/30 overflow-hidden animate-slide-up">
                  <div className="flex items-center justify-between px-6 py-4 border-b border-dark-border bg-accent-warning/5">
                    <div className="flex items-center gap-2">
                      <AlertCircle className="w-5 h-5 text-accent-warning" />
                      <h3 className="font-semibold text-accent-warning">
                        Anomaly Detection {anomalies?.count ? `(${anomalies.count} found)` : ''}
                      </h3>
                    </div>
                    <button onClick={() => setShowAnomalies(false)}><X className="w-5 h-5 text-gray-500 hover:text-white" /></button>
                  </div>

                  {anomalyLoading ? (
                    <div className="p-6 space-y-3">
                      <div className="skeleton h-16 w-full rounded" />
                      <div className="skeleton h-16 w-full rounded" />
                      <div className="skeleton h-16 w-full rounded" />
                    </div>
                  ) : anomalies?.ai_analysis && anomalies.ai_analysis.length > 0 ? (
                    <div className="p-6 space-y-3">
                      {anomalies.ai_analysis.map((a: any, i: number) => (
                        <div key={i} className={`flex items-start gap-3 p-4 rounded-lg bg-dark-bg border-l-4 ${a.severity === 'high' ? 'border-l-accent-danger' : a.severity === 'medium' ? 'border-l-accent-warning' : 'border-l-accent-info'}`}>
                          <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${a.severity === 'high' ? 'bg-accent-danger/20' : a.severity === 'medium' ? 'bg-accent-warning/20' : 'bg-accent-info/20'}`}>
                            <AlertTriangle className={`w-4 h-4 ${a.severity === 'high' ? 'text-accent-danger' : a.severity === 'medium' ? 'text-accent-warning' : 'text-accent-info'}`} />
                          </div>
                          <div className="flex-1">
                            <div className="flex items-center gap-2 mb-1">
                              <p className="text-sm font-medium text-white">{a.metric}</p>
                              <span className={`text-[10px] px-2 py-0.5 rounded-full ${a.severity === 'high' ? 'bg-accent-danger/20 text-accent-danger' : a.severity === 'medium' ? 'bg-accent-warning/20 text-accent-warning' : 'bg-accent-info/20 text-accent-info'}`}>
                                {a.severity}
                              </span>
                            </div>
                            <p className="text-sm text-gray-400">{a.description}</p>
                            {a.suggestion && <p className="text-xs text-accent-primary mt-2">💡 {a.suggestion}</p>}
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="p-6 text-center">
                      <CheckCircle className="w-12 h-12 text-accent-success mx-auto mb-3" />
                      <p className="text-gray-300">No significant anomalies detected!</p>
                      <p className="text-gray-500 text-sm mt-1">Your data looks healthy.</p>
                    </div>
                  )}
                </div>
              )}

              {/* SQL QUERY VIEWER */}
              {dashboard.sql_query && (
                <details className="bg-dark-card rounded-xl border border-dark-border">
                  <summary className="px-6 py-3 text-xs text-gray-500 cursor-pointer hover:text-gray-400">🔍 View Generated SQL</summary>
                  <pre className="px-6 pb-4 text-xs text-accent-primary font-mono overflow-x-auto">{dashboard.sql_query}</pre>
                </details>
              )}

              {/* SUGGESTED FOLLOW-UPS */}
              {dashboard.suggested_followups?.length > 0 && (
                <div className="flex items-center gap-2 flex-wrap">
                  <Lightbulb className="w-4 h-4 text-accent-warning flex-shrink-0" />
                  <span className="text-xs text-gray-500">Try:</span>
                  {dashboard.suggested_followups.map((q2, i) => (
                    <button key={i} onClick={() => sendQuery(q2)} className="text-xs px-3 py-1.5 bg-dark-hover border border-dark-border rounded-full text-gray-400 hover:text-accent-primary hover:border-accent-primary transition-all">
                      {q2}
                    </button>
                  ))}
                </div>
              )}

            </div>
          )}

        </div>
      </div>
    </div>
  );
}