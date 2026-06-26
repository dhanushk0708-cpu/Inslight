"use client";
import React, { useState, useEffect, useRef, useCallback } from "react";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   STYLES
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */
const injectStyles = () => {
  if (document.getElementById("dashai-styles")) return;
  const el = document.createElement("style");
  el.id = "dashai-styles";
  el.textContent = `
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

*{margin:0;padding:0;box-sizing:border-box}
:root{
  --bg-primary:#06080d;--bg-secondary:#0a0d14;--bg-chat:#080b12;
  --bg-card:#111520;--bg-card-hover:#161b28;--bg-elevated:#1a1f2e;
  --bg-glass:rgba(17,21,32,.72);
  --bg-msg-user:linear-gradient(135deg,#6366f1,#4f46e5);
  --bg-msg-ai:#12162080;
  --border:rgba(255,255,255,.06);--border-chat:rgba(255,255,255,.04);
  --border-active:rgba(99,102,241,.4);
  --text-primary:#f1f3f9;--text-secondary:#8b93a7;--text-muted:#505872;--text-dim:#3a4058;
  --accent:#6366f1;--accent-light:#818cf8;--accent-dark:#4f46e5;
  --accent-glow:rgba(99,102,241,.12);--accent-glow-strong:rgba(99,102,241,.25);
  --green:#10b981;--green-glow:rgba(16,185,129,.12);
  --red:#ef4444;--red-glow:rgba(239,68,68,.12);
  --amber:#f59e0b;--amber-glow:rgba(245,158,11,.12);
  --blue:#3b82f6;--cyan:#06b6d4;--purple:#8b5cf6;
  --gradient-accent:linear-gradient(135deg,#6366f1,#8b5cf6,#a78bfa);
  --gradient-card:linear-gradient(145deg,rgba(17,21,32,.9),rgba(26,31,46,.6));
  --gradient-glow:radial-gradient(ellipse at 50% 0%,rgba(99,102,241,.1) 0%,transparent 60%);
  --radius:16px;--radius-sm:10px;--radius-xs:6px;--radius-full:9999px;
  --shadow-sm:0 2px 8px rgba(0,0,0,.3);--shadow-md:0 8px 32px rgba(0,0,0,.4);
  --shadow-glow:0 0 40px rgba(99,102,241,.15);
  --transition:all .25s cubic-bezier(.4,0,.2,1);
  --transition-spring:all .4s cubic-bezier(.34,1.56,.64,1);
  --chat-width:420px;
}
body{
  font-family:'Inter',-apple-system,BlinkMacSystemFont,sans-serif;
  background:var(--bg-primary);color:var(--text-primary);
  line-height:1.6;overflow:hidden;
  -webkit-font-smoothing:antialiased;
}

/* ━━━ LAYOUT ━━━ */
.app{display:flex;height:100vh;overflow:hidden;position:relative}
.app::before{
  content:'';position:fixed;inset:0;
  background:radial-gradient(circle at 25% 15%,rgba(99,102,241,.04) 0%,transparent 50%),
             radial-gradient(circle at 75% 85%,rgba(139,92,246,.03) 0%,transparent 50%);
  pointer-events:none;z-index:0;
}

/* ━━━━━━━━━━━━━━━━━━━━━━━━━━
   LEFT: CHAT PANEL
   ━━━━━━━━━━━━━━━━━━━━━━━━━━ */
.chat-panel{
  width:var(--chat-width);min-width:var(--chat-width);
  background:linear-gradient(180deg,#080b12,#0a0e17,#080c14);
  border-right:1px solid var(--border-chat);
  display:flex;flex-direction:column;
  position:relative;z-index:10;overflow:hidden;
}
.chat-panel::before{
  content:'';position:absolute;top:-100px;left:-60px;
  width:250px;height:250px;
  background:radial-gradient(circle,rgba(99,102,241,.06) 0%,transparent 70%);
  pointer-events:none;animation:chat-glow 10s ease-in-out infinite alternate;
}
@keyframes chat-glow{
  0%{transform:translate(0,0);opacity:.5}
  50%{transform:translate(30px,80px);opacity:.8}
  100%{transform:translate(-20px,160px);opacity:.4}
}
.chat-panel::after{
  content:'';position:absolute;top:0;right:0;width:1px;height:100%;
  background:linear-gradient(180deg,transparent,rgba(99,102,241,.12),rgba(139,92,246,.15),rgba(99,102,241,.12),transparent);
  z-index:5;
}

/* Chat Header */
.chat-header{
  padding:20px;border-bottom:1px solid var(--border-chat);
  position:relative;z-index:2;flex-shrink:0;
}
.chat-brand{display:flex;align-items:center;gap:14px;margin-bottom:14px}
.chat-logo{
  width:42px;height:42px;border-radius:14px;
  background:var(--gradient-accent);
  display:flex;align-items:center;justify-content:center;
  font-size:20px;flex-shrink:0;
  box-shadow:0 4px 16px rgba(99,102,241,.35),0 0 0 1px rgba(255,255,255,.08) inset;
  position:relative;
}
.chat-logo::after{
  content:'';position:absolute;inset:0;border-radius:14px;
  background:linear-gradient(135deg,rgba(255,255,255,.15) 0%,transparent 50%);
}
.chat-brand-text{display:flex;flex-direction:column;gap:1px}
.chat-brand-name{
  font-size:20px;font-weight:900;letter-spacing:-.5px;
  background:linear-gradient(135deg,#fff 30%,#818cf8);
  -webkit-background-clip:text;-webkit-text-fill-color:transparent;
}
.chat-brand-sub{font-size:10px;font-weight:600;letter-spacing:1.5px;text-transform:uppercase;color:var(--text-dim)}

/* Status bar */
.chat-status{
  display:flex;align-items:center;gap:8px;
  padding:8px 12px;background:rgba(255,255,255,.02);
  border:1px solid var(--border-chat);border-radius:var(--radius-sm);
}
.status-dot{width:7px;height:7px;border-radius:50%;flex-shrink:0}
.status-dot.on{background:var(--green);box-shadow:0 0 8px rgba(16,185,129,.4);animation:pulse-dot 2s infinite}
.status-dot.off{background:var(--red)}
@keyframes pulse-dot{0%,100%{opacity:1}50%{opacity:.4}}
.chat-status-text{font-size:11px;color:var(--text-muted);flex:1}
.chat-status-badge{
  font-size:9px;padding:2px 8px;border-radius:var(--radius-full);
  background:var(--accent-glow);color:var(--accent-light);
  font-weight:700;border:1px solid rgba(99,102,241,.15);
}

/* Upload button in header */
.chat-upload-btn{
  margin-top:10px;width:100%;padding:9px;
  background:rgba(255,255,255,.02);
  border:1px dashed var(--border);border-radius:var(--radius-sm);
  color:var(--text-muted);font-size:12px;font-weight:600;
  cursor:pointer;transition:var(--transition);
  font-family:inherit;display:flex;align-items:center;justify-content:center;gap:6px;
}
.chat-upload-btn:hover{
  border-color:var(--accent);color:var(--accent-light);
  background:var(--accent-glow);
}

/* Chat Messages Area */
.chat-messages{
  flex:1;overflow-y:auto;padding:16px;
  display:flex;flex-direction:column;gap:12px;
  position:relative;z-index:2;
  scroll-behavior:smooth;
}

/* Message bubbles */
.msg{display:flex;gap:10px;max-width:100%;animation:msgIn .3s ease-out}
@keyframes msgIn{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:translateY(0)}}

.msg.user{flex-direction:row-reverse}
.msg.ai{flex-direction:row}

.msg-avatar{
  width:30px;height:30px;border-radius:10px;
  display:flex;align-items:center;justify-content:center;
  font-size:14px;flex-shrink:0;
}
.msg.user .msg-avatar{background:var(--gradient-accent);box-shadow:0 2px 8px rgba(99,102,241,.3)}
.msg.ai .msg-avatar{background:rgba(255,255,255,.04);border:1px solid var(--border)}

.msg-bubble{
  padding:12px 16px;border-radius:16px;
  font-size:13.5px;line-height:1.6;
  max-width:calc(100% - 50px);word-wrap:break-word;
}
.msg.user .msg-bubble{
  background:var(--bg-msg-user);color:#fff;
  border-bottom-right-radius:4px;
  box-shadow:0 4px 16px rgba(99,102,241,.25);
}
.msg.ai .msg-bubble{
  background:var(--bg-msg-ai);color:var(--text-primary);
  border:1px solid var(--border);
  border-bottom-left-radius:4px;
}

.msg-time{font-size:9px;color:var(--text-dim);margin-top:4px;padding:0 4px}
.msg.user .msg-time{text-align:right}

/* Typing indicator */
.typing{display:flex;gap:4px;padding:12px 16px;align-items:center}
.typing span{
  width:6px;height:6px;border-radius:50%;background:var(--text-muted);
  animation:typeDot 1.2s infinite ease-in-out;
}
.typing span:nth-child(2){animation-delay:.2s}
.typing span:nth-child(3){animation-delay:.4s}
@keyframes typeDot{0%,60%,100%{transform:translateY(0);opacity:.3}30%{transform:translateY(-6px);opacity:1}}

/* Quick actions in chat */
.chat-actions{
  padding:10px 16px;border-top:1px solid var(--border-chat);
  display:flex;gap:6px;flex-shrink:0;position:relative;z-index:2;
  overflow-x:auto;
}
.chat-action-btn{
  padding:7px 14px;border-radius:var(--radius-full);
  background:rgba(255,255,255,.03);border:1px solid var(--border);
  color:var(--text-muted);font-size:11.5px;font-weight:600;
  cursor:pointer;transition:var(--transition);
  font-family:inherit;white-space:nowrap;
  display:flex;align-items:center;gap:5px;
}
.chat-action-btn:hover{
  border-color:var(--accent);color:var(--accent-light);
  background:var(--accent-glow);transform:translateY(-1px);
}
.chat-action-btn.active{
  background:var(--accent-glow-strong);border-color:var(--border-active);
  color:var(--accent-light);
}

/* Chat Input */
.chat-input-area{
  padding:14px 16px 18px;border-top:1px solid var(--border-chat);
  position:relative;z-index:2;flex-shrink:0;
}
.chat-input-wrap{
  display:flex;align-items:center;gap:8px;
  background:rgba(255,255,255,.03);
  border:1px solid var(--border);border-radius:14px;
  padding:4px 4px 4px 16px;transition:var(--transition);
}
.chat-input-wrap:focus-within{
  border-color:var(--accent);
  box-shadow:0 0 0 3px var(--accent-glow),0 0 20px rgba(99,102,241,.1);
}
.chat-input{
  flex:1;padding:10px 0;background:transparent;border:none;
  color:var(--text-primary);font-size:13.5px;font-family:inherit;outline:none;
}
.chat-input::placeholder{color:var(--text-dim)}
.chat-send-btn{
  width:38px;height:38px;border-radius:12px;border:none;
  background:var(--gradient-accent);color:#fff;
  cursor:pointer;font-size:16px;
  display:flex;align-items:center;justify-content:center;
  transition:var(--transition);flex-shrink:0;
  box-shadow:0 2px 8px rgba(99,102,241,.3);
}
.chat-send-btn:hover{transform:scale(1.05);box-shadow:0 4px 16px rgba(99,102,241,.4)}
.chat-send-btn:disabled{opacity:.3;cursor:not-allowed;transform:none;box-shadow:none}

/* ━━━━━━━━━━━━━━━━━━━━━━━━━━
   RIGHT: RESULTS PANEL
   ━━━━━━━━━━━━━━━━━━━━━━━━━━ */
.results-panel{
  flex:1;display:flex;flex-direction:column;
  overflow:hidden;position:relative;z-index:1;
}
.results-topbar{
  padding:14px 24px;border-bottom:1px solid var(--border);
  background:var(--bg-glass);backdrop-filter:blur(20px);
  display:flex;align-items:center;justify-content:space-between;
  flex-shrink:0;position:relative;
}
.results-topbar::after{
  content:'';position:absolute;bottom:0;left:0;width:100%;height:1px;
  background:linear-gradient(90deg,transparent,rgba(99,102,241,.12),transparent);
}
.results-topbar-left{display:flex;align-items:center;gap:10px}
.results-topbar h2{font-size:16px;font-weight:700;letter-spacing:-.3px}
.results-badge{
  font-size:9px;padding:3px 10px;border-radius:var(--radius-full);
  background:var(--accent-glow);color:var(--accent-light);
  border:1px solid rgba(99,102,241,.15);font-weight:700;
  text-transform:uppercase;letter-spacing:.8px;
}
.results-topbar-right{display:flex;align-items:center;gap:8px}
.results-chip{
  font-size:10.5px;color:var(--text-muted);padding:4px 10px;
  background:rgba(255,255,255,.03);border-radius:var(--radius-full);
  border:1px solid var(--border);display:flex;align-items:center;gap:4px;
}

.results-content{
  flex:1;overflow-y:auto;padding:24px;
  background:var(--gradient-glow);scroll-behavior:smooth;
}

/* ━━━ WHAT-IF INLINE ━━━ */
.whatif-panel{
  background:var(--gradient-card);border:1px solid var(--border);
  border-radius:var(--radius);padding:22px;margin-bottom:20px;
}

/* ━━━ CARDS ━━━ */
.card{
  background:var(--gradient-card);border:1px solid var(--border);
  border-radius:var(--radius);padding:22px;margin-bottom:20px;
  box-shadow:var(--shadow-sm);backdrop-filter:blur(10px);
  transition:var(--transition);position:relative;overflow:hidden;
}
.card::before{
  content:'';position:absolute;top:0;left:0;right:0;height:1px;
  background:linear-gradient(90deg,transparent,rgba(255,255,255,.06),transparent);
}
.card:hover{border-color:rgba(255,255,255,.1)}
.card-title{
  font-size:11px;font-weight:700;color:var(--text-muted);
  text-transform:uppercase;letter-spacing:1.2px;
  margin-bottom:16px;display:flex;align-items:center;gap:8px;
}
.card-title::before{content:'';width:3px;height:14px;border-radius:2px;background:var(--gradient-accent)}

/* ━━━ KPI ━━━ */
.kpi-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:14px;margin-bottom:20px}
.kpi-card{
  background:var(--gradient-card);border:1px solid var(--border);
  border-radius:var(--radius);padding:18px 20px;
  transition:var(--transition);position:relative;overflow:hidden;
}
.kpi-card::before{
  content:'';position:absolute;top:0;left:0;right:0;height:2px;
  background:var(--gradient-accent);opacity:0;transition:opacity .3s ease;
}
.kpi-card:hover{border-color:var(--border-active);transform:translateY(-2px);box-shadow:var(--shadow-glow)}
.kpi-card:hover::before{opacity:1}
.kpi-header{display:flex;align-items:center;justify-content:space-between;margin-bottom:6px}
.kpi-label{font-size:10.5px;color:var(--text-muted);text-transform:uppercase;letter-spacing:.8px;font-weight:600}
.kpi-icon{
  width:30px;height:30px;border-radius:8px;
  display:flex;align-items:center;justify-content:center;font-size:15px;
}
.kpi-icon.revenue{background:var(--accent-glow);color:var(--accent-light)}
.kpi-icon.units{background:var(--green-glow);color:var(--green)}
.kpi-icon.orders{background:rgba(59,130,246,.12);color:var(--blue)}
.kpi-icon.rating{background:var(--amber-glow);color:var(--amber)}
.kpi-value{font-size:26px;font-weight:800;letter-spacing:-.5px;line-height:1.2}
.kpi-trend{
  font-size:11px;font-weight:600;padding:2px 8px;margin-top:4px;
  border-radius:var(--radius-full);display:inline-flex;align-items:center;gap:3px;
}
.kpi-trend.up{background:var(--green-glow);color:var(--green)}
.kpi-trend.down{background:var(--red-glow);color:var(--red)}

/* ━━━ CHARTS ━━━ */
.chart-grid{display:grid;grid-template-columns:1fr 1fr;gap:18px}
.chart-grid.single{grid-template-columns:1fr}
.bar-chart{display:flex;align-items:flex-end;gap:6px;height:240px;padding:10px 0}
.bar-group{flex:1;display:flex;flex-direction:column;align-items:center;height:100%;justify-content:flex-end;cursor:pointer}
.bar{width:100%;max-width:50px;border-radius:5px 5px 2px 2px;transition:all .4s cubic-bezier(.34,1.56,.64,1);min-height:4px}
.bar:hover{filter:brightness(1.2);transform:scaleY(1.03) scaleX(1.08)}
.bar-value{font-size:10px;color:var(--text-secondary);margin-bottom:4px;font-weight:700;opacity:.7}
.bar-group:hover .bar-value{opacity:1;color:var(--text-primary)}
.bar-label{font-size:9.5px;color:var(--text-dim);margin-top:7px;text-align:center;max-width:70px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}

.pie-container{display:flex;align-items:center;justify-content:center;gap:30px;padding:16px}
.pie-svg{width:180px;height:180px;filter:drop-shadow(0 4px 12px rgba(0,0,0,.3))}
.pie-legend{display:flex;flex-direction:column;gap:9px}
.legend-item{display:flex;align-items:center;gap:9px;font-size:12px;color:var(--text-secondary)}
.legend-dot{width:9px;height:9px;border-radius:4px;flex-shrink:0}
.legend-pct{color:var(--text-muted);font-size:10.5px;margin-left:auto;font-weight:600}

.line-chart-container{padding:8px 0}
.line-chart-svg{width:100%;height:240px}

/* ━━━ NARRATIVE ━━━ */
.narrative{
  background:linear-gradient(135deg,var(--accent-glow),rgba(139,92,246,.04),transparent);
  border-left:3px solid;border-image:var(--gradient-accent) 1;
  padding:16px 20px;border-radius:0 var(--radius-sm) var(--radius-sm) 0;
  font-size:13.5px;line-height:1.8;margin-bottom:18px;position:relative;
}
.narrative::before{
  content:'💡';position:absolute;top:-10px;left:-14px;font-size:20px;
  background:var(--bg-primary);padding:2px;border-radius:50%;
}

/* ━━━ TABLE ━━━ */
.data-table-wrap{overflow-x:auto;max-height:380px;overflow-y:auto;border-radius:var(--radius-sm)}
.data-table{width:100%;border-collapse:collapse;font-size:12px}
.data-table th{
  background:rgba(255,255,255,.03);padding:10px 12px;text-align:left;
  font-weight:700;color:var(--text-muted);position:sticky;top:0;
  border-bottom:1px solid var(--border);text-transform:uppercase;
  letter-spacing:.5px;font-size:10px;backdrop-filter:blur(10px);z-index:2;
}
.data-table td{padding:9px 12px;border-bottom:1px solid rgba(255,255,255,.03);color:var(--text-secondary)}
.data-table tbody tr:hover td{background:rgba(99,102,241,.04);color:var(--text-primary)}

/* ━━━ SQL ━━━ */
.sql-block{
  background:rgba(0,0,0,.4);border:1px solid var(--border);
  border-radius:var(--radius-sm);padding:12px 16px;
  font-family:'JetBrains Mono','Fira Code',monospace;
  font-size:11.5px;color:#a9dc76;overflow-x:auto;margin-top:10px;position:relative;
}
.sql-block::before{
  content:'SQL';position:absolute;top:5px;right:8px;
  font-size:8px;color:var(--text-dim);font-family:'Inter',sans-serif;
  font-weight:700;letter-spacing:1px;
}

/* ━━━ SLIDERS ━━━ */
.slider-group{margin-bottom:18px}
.slider-header{display:flex;justify-content:space-between;margin-bottom:6px;align-items:center}
.slider-label{font-size:12.5px;font-weight:600;color:var(--text-secondary)}
.slider-val{
  font-size:13px;font-weight:800;background:var(--gradient-accent);
  -webkit-background-clip:text;-webkit-text-fill-color:transparent;min-width:48px;text-align:right;
}
.slider-input{
  width:100%;-webkit-appearance:none;appearance:none;height:5px;
  border-radius:3px;background:var(--border);outline:none;
}
.slider-input::-webkit-slider-thumb{
  -webkit-appearance:none;width:18px;height:18px;border-radius:50%;
  background:var(--gradient-accent);cursor:pointer;
  border:3px solid var(--bg-card);box-shadow:0 2px 8px rgba(99,102,241,.4);
}

/* ━━━ BTN ━━━ */
.btn{
  padding:10px 20px;border-radius:var(--radius-sm);border:none;cursor:pointer;
  font-size:13px;font-weight:600;font-family:inherit;transition:var(--transition);
  display:inline-flex;align-items:center;gap:6px;position:relative;overflow:hidden;
}
.btn-primary{background:var(--gradient-accent);color:#fff;box-shadow:0 4px 16px rgba(99,102,241,.3)}
.btn-primary:hover{transform:translateY(-1px);box-shadow:0 6px 24px rgba(99,102,241,.4)}
.btn-primary:disabled{opacity:.4;cursor:not-allowed;transform:none;box-shadow:none}
.btn-ghost{background:transparent;color:var(--text-secondary);padding:6px 12px;font-size:12px}
.btn-ghost:hover{background:rgba(255,255,255,.04);color:var(--accent-light)}

/* ━━━ ANOMALY ━━━ */
.anomaly-card{
  padding:14px 18px;border-radius:var(--radius-sm);
  border-left:3px solid var(--amber);background:var(--amber-glow);
  margin-bottom:10px;transition:var(--transition);
}
.anomaly-card:hover{transform:translateX(3px)}
.anomaly-card.high{border-left-color:var(--red);background:var(--red-glow)}
.anomaly-card.low{border-left-color:var(--green);background:var(--green-glow)}
.anomaly-metric{font-weight:700;font-size:13.5px;margin-bottom:3px}
.anomaly-desc{font-size:12.5px;color:var(--text-secondary);line-height:1.5}
.anomaly-action{font-size:11.5px;color:var(--accent-light);margin-top:6px;font-weight:600}

/* ━━━ PROFILE ━━━ */
.profile-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:14px}
.profile-stat{
  padding:18px;background:var(--bg-elevated);border-radius:var(--radius-sm);
  text-align:center;border:1px solid var(--border);transition:var(--transition);
}
.profile-stat:hover{border-color:var(--border-active);transform:translateY(-2px)}
.profile-stat-value{
  font-size:28px;font-weight:800;background:var(--gradient-accent);
  -webkit-background-clip:text;-webkit-text-fill-color:transparent;line-height:1.1;
}
.profile-stat-label{font-size:10px;color:var(--text-muted);margin-top:4px;text-transform:uppercase;letter-spacing:.8px;font-weight:600}

/* ━━━ UPLOAD ZONE ━━━ */
.upload-zone-mini{
  border:2px dashed var(--border);border-radius:var(--radius);
  padding:40px;text-align:center;cursor:pointer;
  transition:var(--transition);background:var(--bg-card);
}
.upload-zone-mini:hover{border-color:var(--accent);background:var(--accent-glow)}

/* ━━━ LOADING ━━━ */
.loading-container{display:flex;flex-direction:column;align-items:center;padding:40px;gap:14px}
.loading-spinner{width:36px;height:36px;border-radius:50%;border:3px solid var(--border);border-top-color:var(--accent);animation:spin .8s linear infinite}
@keyframes spin{to{transform:rotate(360deg)}}
.loading-text{font-size:12.5px;color:var(--text-muted);animation:pulseT 1.5s ease-in-out infinite}
@keyframes pulseT{0%,100%{opacity:.4}50%{opacity:1}}

/* ━━━ WELCOME ━━━ */
.welcome-results{text-align:center;padding:80px 30px;max-width:500px;margin:0 auto}
.welcome-results .icon{font-size:56px;margin-bottom:16px;animation:float 3s ease-in-out infinite}
@keyframes float{0%,100%{transform:translateY(0)}50%{transform:translateY(-8px)}}
.welcome-results h3{font-size:22px;font-weight:800;margin-bottom:8px;letter-spacing:-.4px}
.welcome-results p{color:var(--text-muted);font-size:13.5px;line-height:1.7}

/* ━━━ ERROR ━━━ */
.error-box{
  padding:16px;background:var(--red-glow);border:1px solid rgba(239,68,68,.2);
  border-radius:var(--radius-sm);color:var(--red);font-size:13px;
  display:flex;align-items:flex-start;gap:10px;margin-bottom:16px;
}

/* ━━━ FOLLOW-UPS IN CHAT ━━━ */
.chat-suggestions{
  display:flex;flex-wrap:wrap;gap:6px;margin-top:6px;
}
.chat-suggestion-chip{
  padding:5px 12px;background:rgba(99,102,241,.06);
  border:1px solid rgba(99,102,241,.12);border-radius:var(--radius-full);
  color:var(--accent-light);font-size:11px;font-weight:500;
  cursor:pointer;transition:var(--transition);font-family:inherit;
}
.chat-suggestion-chip:hover{
  background:var(--accent-glow-strong);border-color:var(--border-active);
  transform:translateY(-1px);
}

/* ━━━ SCROLLBAR ━━━ */
::-webkit-scrollbar{width:4px;height:4px}
::-webkit-scrollbar-track{background:transparent}
::-webkit-scrollbar-thumb{background:rgba(255,255,255,.05);border-radius:10px}
::-webkit-scrollbar-thumb:hover{background:rgba(255,255,255,.1)}

/* ━━━ RESPONSIVE ━━━ */
@media(max-width:900px){
  .app{flex-direction:column}
  .chat-panel{width:100%;min-width:100%;height:50vh;border-right:none;border-bottom:1px solid var(--border)}
  .results-panel{height:50vh}
  .chart-grid{grid-template-columns:1fr}
  .kpi-grid{grid-template-columns:repeat(2,1fr)}
  .profile-grid{grid-template-columns:repeat(2,1fr)}
}
@media(max-width:480px){
  .kpi-grid{grid-template-columns:1fr}
  .profile-grid{grid-template-columns:1fr}
}

.fade-in{animation:fadeIn .35s ease-out}
@keyframes fadeIn{from{opacity:0;transform:translateY(6px)}to{opacity:1;transform:translateY(0)}}
.slide-up{animation:slideUp .45s cubic-bezier(.34,1.56,.64,1)}
@keyframes slideUp{from{opacity:0;transform:translateY(16px)}to{opacity:1;transform:translateY(0)}}
  `;
  document.head.prepend(el);
};

/* ━━━ CONSTANTS ━━━ */
const COLORS = ["#6366f1","#8b5cf6","#06b6d4","#10b981","#f59e0b","#ef4444","#ec4899","#14b8a6","#3b82f6","#a78bfa"];

function fmt(v) {
  if (v == null || isNaN(v)) return "0";
  const n = Number(v);
  if (Math.abs(n) >= 1e9) return `${(n / 1e9).toFixed(2)}B`;
  if (Math.abs(n) >= 1e6) return `${(n / 1e6).toFixed(1)}M`;
  if (Math.abs(n) >= 1e3) return `${(n / 1e3).toFixed(1)}K`;
  return n % 1 === 0 ? n.toLocaleString() : n.toFixed(1);
}

function kpiIcon(label) {
  const l = (label || "").toLowerCase();
  if (l.includes("revenue") || l.includes("sales") || l.includes("total")) return { i: "💰", c: "revenue" };
  if (l.includes("unit") || l.includes("quantity")) return { i: "📦", c: "units" };
  if (l.includes("order") || l.includes("count")) return { i: "🛒", c: "orders" };
  if (l.includes("rating") || l.includes("score")) return { i: "⭐", c: "rating" };
  if (l.includes("profit")) return { i: "📈", c: "revenue" };
  if (l.includes("discount")) return { i: "🏷️", c: "units" };
  return { i: "📊", c: "revenue" };
}

function timeNow() {
  return new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   CHART COMPONENTS
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */

function BarChart({ data, xKey, yKey, title }) {
  if (!data?.length) return null;
  const vals = data.map(d => Number(d[yKey]) || 0);
  const mx = Math.max(...vals, 1);
  return (
    <div className="card fade-in">
      <div className="card-title">{title}</div>
      <div className="bar-chart">
        {data.slice(0, 20).map((d, i) => {
          const v = Number(d[yKey]) || 0, h = Math.max((v / mx) * 100, 3);
          return (<div className="bar-group" key={i}><div className="bar-value">{fmt(v)}</div><div className="bar" style={{ height: `${h}%`, background: `linear-gradient(180deg,${COLORS[i % COLORS.length]},${COLORS[i % COLORS.length]}55)`, boxShadow: `0 0 10px ${COLORS[i % COLORS.length]}22` }} title={`${d[xKey]}: ${fmt(v)}`} /><div className="bar-label" title={String(d[xKey])}>{String(d[xKey]).slice(0, 12)}</div></div>);
        })}
      </div>
    </div>
  );
}

function LineChart({ data, xKey, yKey, title }) {
  if (!data?.length) return null;
  const vals = data.map(d => Number(d[yKey]) || 0);
  const mx = Math.max(...vals, 1), mn = Math.min(...vals, 0), rng = mx - mn || 1;
  const w = 700, h = 230, pad = 46, pw = w - pad * 2, ph = h - pad * 2;
  const pts = data.map((d, i) => ({ x: pad + (i / Math.max(data.length - 1, 1)) * pw, y: pad + ph - ((Number(d[yKey]) || 0) - mn) / rng * ph }));
  const pathD = pts.map((p, i) => `${i === 0 ? "M" : "L"} ${p.x} ${p.y}`).join(" ");
  const areaD = `${pathD} L ${pts[pts.length - 1].x} ${pad + ph} L ${pts[0].x} ${pad + ph} Z`;
  const uid = `lg-${(title || "x").replace(/\W/g, "")}`;
  return (
    <div className="card fade-in">
      <div className="card-title">{title}</div>
      <div className="line-chart-container">
        <svg className="line-chart-svg" viewBox={`0 0 ${w} ${h}`} preserveAspectRatio="xMidYMid meet">
          <defs><linearGradient id={uid} x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor={COLORS[0]} stopOpacity="0.2" /><stop offset="100%" stopColor={COLORS[0]} stopOpacity="0" /></linearGradient></defs>
          {[0, .25, .5, .75, 1].map((f, i) => { const y = pad + ph * (1 - f); return (<g key={i}><line x1={pad} y1={y} x2={w - pad} y2={y} stroke="rgba(255,255,255,.04)" /><text x={pad - 8} y={y + 4} textAnchor="end" fill="#505872" fontSize="10" fontWeight="600">{fmt(mn + rng * f)}</text></g>); })}
          <path d={areaD} fill={`url(#${uid})`} /><path d={pathD} fill="none" stroke={COLORS[0]} strokeWidth="2.5" strokeLinecap="round" style={{ filter: `drop-shadow(0 0 5px ${COLORS[0]}44)` }} />
          {pts.map((p, i) => (<circle key={i} cx={p.x} cy={p.y} r="3.5" fill={COLORS[0]} stroke="#111520" strokeWidth="2"><title>{`${data[i][xKey]}: ${fmt(data[i][yKey])}`}</title></circle>))}
          {data.length <= 14 && pts.map((p, i) => (<text key={`l${i}`} x={p.x} y={h - 6} textAnchor="middle" fill="#505872" fontSize="9.5">{String(data[i][xKey]).slice(0, 7)}</text>))}
        </svg>
      </div>
    </div>
  );
}

function PieChart({ data, xKey, yKey, title }) {
  if (!data?.length) return null;
  const slices = data.slice(0, 8);
  const total = slices.reduce((s, d) => s + (Number(d[yKey]) || 0), 0) || 1;
  let cum = 0;
  const paths = slices.map((d, i) => {
    const v = Number(d[yKey]) || 0, ang = (v / total) * 360, sa = cum; cum += ang;
    const r = 82, cx = 100, cy = 100, s = (sa - 90) * Math.PI / 180, e = (cum - 90) * Math.PI / 180;
    return { d: `M ${cx} ${cy} L ${cx + r * Math.cos(s)} ${cy + r * Math.sin(s)} A ${r} ${r} 0 ${ang > 180 ? 1 : 0} 1 ${cx + r * Math.cos(e)} ${cy + r * Math.sin(e)} Z`, color: COLORS[i % COLORS.length], label: String(d[xKey]), pct: ((v / total) * 100).toFixed(1), val: v };
  });
  return (
    <div className="card fade-in">
      <div className="card-title">{title}</div>
      <div className="pie-container">
        <svg className="pie-svg" viewBox="0 0 200 200">
          {paths.map((p, i) => (<path key={i} d={p.d} fill={p.color} stroke="#111520" strokeWidth="2" style={{ filter: `drop-shadow(0 2px 4px ${p.color}33)` }}><title>{`${p.label}: ${fmt(p.val)} (${p.pct}%)`}</title></path>))}
          <circle cx="100" cy="100" r="40" fill="#111520" /><text x="100" y="96" textAnchor="middle" fill="#f1f3f9" fontSize="15" fontWeight="800">{fmt(total)}</text><text x="100" y="110" textAnchor="middle" fill="#505872" fontSize="8.5" fontWeight="600">TOTAL</text>
        </svg>
        <div className="pie-legend">{paths.map((p, i) => (<div className="legend-item" key={i}><div className="legend-dot" style={{ background: p.color }} /><span>{p.label.slice(0, 18)}</span><span className="legend-pct">{p.pct}%</span></div>))}</div>
      </div>
    </div>
  );
}

function ChartRenderer({ config }) {
  if (!config?.data?.length) return null;
  const { type, data, x_axis, y_axis, title } = config;
  if (type === "line" || type === "area") return <LineChart data={data} xKey={x_axis} yKey={y_axis} title={title} />;
  if (type === "pie") return <PieChart data={data} xKey={x_axis} yKey={y_axis} title={title} />;
  return <BarChart data={data} xKey={x_axis} yKey={y_axis} title={title} />;
}

function DataTable({ data, title }) {
  if (!data?.length) return null;
  const cols = Object.keys(data[0]);
  return (
    <div className="card fade-in">
      <div className="card-title">{title || "Data"}</div>
      <div className="data-table-wrap">
        <table className="data-table">
          <thead><tr>{cols.map(c => <th key={c}>{c.replace(/_/g, " ")}</th>)}</tr></thead>
          <tbody>{data.slice(0, 50).map((row, i) => (<tr key={i}>{cols.map(c => (<td key={c}>{typeof row[c] === "number" ? fmt(row[c]) : String(row[c] ?? "")}</td>))}</tr>))}</tbody>
        </table>
      </div>
    </div>
  );
}

function Loading({ text = "Analyzing..." }) {
  return <div className="loading-container fade-in"><div className="loading-spinner" /><div className="loading-text">{text}</div></div>;
}

/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   MAIN APP — SINGLE PAGE
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */

export default function App() {
  const [health, setHealth] = useState(null);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [activeView, setActiveView] = useState("welcome"); // welcome | query | deepdive | whatif | anomalies | upload
  const [viewData, setViewData] = useState(null);
  const [showSql, setShowSql] = useState(false);
  const [history, setHistory] = useState([]);
  const msgEndRef = useRef(null);
  const fileRef = useRef(null);

  // What-If state
  const [wiPrice, setWiPrice] = useState(0);
  const [wiDiscount, setWiDiscount] = useState(0);
  const [wiUnits, setWiUnits] = useState(0);

  useEffect(() => {
    injectStyles();
    fetch(`${API}/api/health`).then(r => r.json()).then(h => {
      setHealth(h);
      if (h.status === "healthy" && h.row_count > 0) {
        addAiMessage(`Welcome! I have **${h.row_count.toLocaleString()} rows** loaded from \`${h.table_name}\` with ${h.columns?.length || 0} columns. Ask me anything or use the quick actions below!`);
      } else {
        addAiMessage("Welcome to DASH.AI! Upload a CSV file to get started — use the 📁 button above.");
      }
    }).catch(() => {
      setHealth({ status: "error" });
      addAiMessage("⚠️ Cannot connect to backend. Make sure the server is running on port 8000.");
    });
  }, []);

  useEffect(() => {
    msgEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  function addAiMessage(text, suggestions = []) {
    setMessages(prev => [...prev, { role: "ai", text, time: timeNow(), suggestions }]);
  }

  function addUserMessage(text) {
    setMessages(prev => [...prev, { role: "user", text, time: timeNow() }]);
  }

  /* ── QUERY ── */
  const handleQuery = useCallback(async (q = "") => {
    const query = q || input;
    if (!query.trim() || loading) return;
    setInput("");
    addUserMessage(query);
    setLoading(true);
    setActiveView("query");
    setViewData(null);
    setShowSql(false);

    try {
      const res = await fetch(`${API}/api/query`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: query, conversation_history: history.slice(-6) }),
      });
      const data = await res.json();
      setViewData(data);
      setHistory(h => [...h, { role: "user", content: query }]);

      if (data.error) {
        addAiMessage(`⚠️ ${data.error}${data.suggestion ? `\n\n💡 ${data.suggestion}` : ""}`);
      } else {
        const kpiSummary = data.kpi_cards?.map(k => `**${k.label}**: ${k.value}`).join(" · ") || "";
        addAiMessage(
          `${data.narrative || "Here are your results."}\n\n${kpiSummary ? `📊 ${kpiSummary}` : ""}`,
          data.suggested_followups || []
        );
      }
    } catch (err) {
      addAiMessage(`❌ Connection failed: ${err.message}`);
    }
    setLoading(false);
  }, [input, history, loading]);

  /* ── DEEP DIVE ── */
  const runDeepDive = async () => {
    addUserMessage("🔬 Run Deep Dive Analysis");
    setLoading(true); setActiveView("deepdive"); setViewData(null);
    try {
      const data = await (await fetch(`${API}/api/deep-dive`, { method: "POST" })).json();
      setViewData(data);
      addAiMessage(data.root_cause_analysis || "Deep dive analysis complete. Check the results panel →", []);
    } catch (err) { addAiMessage(`❌ ${err.message}`); }
    setLoading(false);
  };

  /* ── WHAT-IF ── */
  const runWhatIf = async () => {
    addUserMessage(`🎯 What-If: Price ${wiPrice > 0 ? "+" : ""}${wiPrice}%, Discount ${wiDiscount > 0 ? "+" : ""}${wiDiscount}%, Volume ${wiUnits > 0 ? "+" : ""}${wiUnits}%`);
    setLoading(true); setActiveView("whatif"); setViewData(null);
    try {
      const res = await fetch(`${API}/api/what-if`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ price_change: wiPrice, discount_change: wiDiscount, units_change: wiUnits }),
      });
      const data = await res.json();
      setViewData(data);
      addAiMessage(data.ai_commentary || "Scenario analysis complete.", []);
    } catch (err) { addAiMessage(`❌ ${err.message}`); }
    setLoading(false);
  };

  /* ── ANOMALIES ── */
  const runAnomalies = async () => {
    addUserMessage("🔍 Scan for Anomalies");
    setLoading(true); setActiveView("anomalies"); setViewData(null);
    try {
      const data = await (await fetch(`${API}/api/anomalies`)).json();
      setViewData(data);
      addAiMessage(
        data.count > 0
          ? `Found **${data.count} anomalies** in your data. Check details in the results panel →`
          : "✅ No significant anomalies detected. Your data looks clean!",
        []
      );
    } catch (err) { addAiMessage(`❌ ${err.message}`); }
    setLoading(false);
  };

  /* ── UPLOAD ── */
  const doUpload = async (file) => {
    if (!file) return;
    addUserMessage(`📁 Uploading: ${file.name}`);
    setLoading(true); setActiveView("upload"); setViewData(null);
    try {
      const fd = new FormData(); fd.append("file", file);
      const res = await fetch(`${API}/api/upload`, { method: "POST", body: fd });
      const data = await res.json();
      if (data.profile) {
        setViewData(data.profile);
        setHealth(prev => ({ ...prev, status: "healthy", row_count: data.profile.rows, columns: data.profile.column_info?.map(c => c.name) || [], table_name: data.profile.filename?.replace(".csv", "") }));
        addAiMessage(
          `✅ Loaded **${data.profile.rows.toLocaleString()} rows** × **${data.profile.columns} columns** (Quality: ${data.profile.data_quality_score}%). Ready to analyze!`,
          data.profile.suggested_questions || []
        );
      } else {
        addAiMessage(`⚠️ Upload issue: ${data.detail || "Unknown error"}`);
      }
    } catch (err) { addAiMessage(`❌ Upload failed: ${err.message}`); }
    setLoading(false);
  };

  const isOnline = health?.status === "healthy";
  const rowCount = health?.row_count || 0;

  return (
    <div className="app">
      {/* ━━━ LEFT: CHAT PANEL ━━━ */}
      <div className="chat-panel">

        {/* Header */}
        <div className="chat-header">
          <div className="chat-brand">
            <div className="chat-logo">⚡</div>
            <div className="chat-brand-text">
              <span className="chat-brand-name">DASH.AI</span>
              <span className="chat-brand-sub">BI Co-Pilot</span>
            </div>
          </div>
          <div className="chat-status">
            <div className={`status-dot ${isOnline ? "on" : "off"}`} />
            <span className="chat-status-text">
              {isOnline ? `${rowCount.toLocaleString()} rows` : "Offline"}
            </span>
            <span className="chat-status-badge">{isOnline ? "LIVE" : "OFF"}</span>
          </div>
          <button id="chat-upload-btn" name="chat-upload-btn" className="chat-upload-btn" type="button"
            onClick={() => fileRef.current?.click()}>
            📁 Upload CSV
          </button>
          <input id="file-upload" name="file-upload" type="file" accept=".csv" ref={fileRef}
            style={{ display: "none" }} onChange={e => doUpload(e.target.files[0])} aria-label="Upload CSV" />
        </div>

        {/* Messages */}
        <div className="chat-messages">
          {messages.map((msg, i) => (
            <div key={i} className={`msg ${msg.role}`}>
              <div className="msg-avatar">{msg.role === "user" ? "👤" : "✨"}</div>
              <div>
                <div className="msg-bubble">
                  {msg.text.split("**").map((part, j) =>
                    j % 2 === 1 ? <strong key={j}>{part}</strong> : <span key={j}>{part}</span>
                  )}
                </div>
                {msg.suggestions?.length > 0 && (
                  <div className="chat-suggestions">
                    {msg.suggestions.map((s, j) => (
                      <button key={j} id={`sug-${i}-${j}`} name={`sug-${i}-${j}`}
                        className="chat-suggestion-chip" type="button"
                        onClick={() => handleQuery(s)}>{s}</button>
                    ))}
                  </div>
                )}
                <div className="msg-time">{msg.time}</div>
              </div>
            </div>
          ))}
          {loading && (
            <div className="msg ai">
              <div className="msg-avatar">✨</div>
              <div className="msg-bubble"><div className="typing"><span /><span /><span /></div></div>
            </div>
          )}
          <div ref={msgEndRef} />
        </div>

        {/* Quick Actions */}
        <div className="chat-actions">
          <button id="act-deepdive" name="act-deepdive" className={`chat-action-btn ${activeView === "deepdive" ? "active" : ""}`}
            type="button" onClick={runDeepDive} disabled={loading}>🔬 Deep Dive</button>
          <button id="act-whatif" name="act-whatif" className={`chat-action-btn ${activeView === "whatif" ? "active" : ""}`}
            type="button" onClick={() => { setActiveView("whatif"); setViewData(null); }} disabled={loading}>🎯 What-If</button>
          <button id="act-anomalies" name="act-anomalies" className={`chat-action-btn ${activeView === "anomalies" ? "active" : ""}`}
            type="button" onClick={runAnomalies} disabled={loading}>🔍 Anomalies</button>
        </div>

        {/* Input */}
        <div className="chat-input-area">
          <form id="chat-form" name="chat-form" onSubmit={e => { e.preventDefault(); handleQuery(); }}
            autoComplete="off" style={{ display: "contents" }}>
            <div className="chat-input-wrap">
              <input id="chat-input" name="chat-input" className="chat-input" type="text"
                value={input} onChange={e => setInput(e.target.value)}
                placeholder="Ask about your data..."
                disabled={loading} autoComplete="off" aria-label="Chat input" />
              <button id="chat-send" name="chat-send" className="chat-send-btn" type="submit"
                disabled={loading || !input.trim()}>→</button>
            </div>
          </form>
        </div>
      </div>

      {/* ━━━ RIGHT: RESULTS PANEL ━━━ */}
      <div className="results-panel">
        <div className="results-topbar">
          <div className="results-topbar-left">
            <h2>
              {activeView === "query" && "Query Results"}
              {activeView === "deepdive" && "Deep Dive Analysis"}
              {activeView === "whatif" && "What-If Scenario"}
              {activeView === "anomalies" && "Anomaly Detection"}
              {activeView === "upload" && "Dataset Profile"}
              {activeView === "welcome" && "Dashboard"}
            </h2>
            <span className="results-badge">
              {activeView === "welcome" ? "READY" : activeView === "whatif" ? "SIMULATE" : "LIVE"}
            </span>
          </div>
          <div className="results-topbar-right">
            {health?.columns && <span className="results-chip">📐 {health.columns.length} cols</span>}
            {rowCount > 0 && <span className="results-chip">📊 {rowCount.toLocaleString()}</span>}
          </div>
        </div>

        <div className="results-content">
          {/* ── WELCOME ── */}
          {activeView === "welcome" && !loading && (
            <div className="welcome-results fade-in">
              <div className="icon">🚀</div>
              <h3>Your AI Dashboard</h3>
              <p>Ask questions in the chat, run Deep Dive, What-If simulations, or detect anomalies. Results appear here instantly.</p>
            </div>
          )}

          {/* ── LOADING ── */}
          {loading && <Loading text={
            activeView === "deepdive" ? "Running deep analysis..." :
            activeView === "anomalies" ? "Scanning for anomalies..." :
            activeView === "whatif" ? "Simulating scenario..." :
            activeView === "upload" ? "Processing dataset..." :
            "Generating insights..."
          } />}

          {/* ── QUERY RESULTS ── */}
          {activeView === "query" && viewData && !viewData.error && !loading && (
            <div className="slide-up">
              {viewData.kpi_cards?.length > 0 && (
                <div className="kpi-grid">
                  {viewData.kpi_cards.map((kpi, i) => {
                    const { i: icon, c: cls } = kpiIcon(kpi.label);
                    return (
                      <div className="kpi-card" key={i}>
                        <div className="kpi-header"><div className="kpi-label">{kpi.label}</div><div className={`kpi-icon ${cls}`}>{icon}</div></div>
                        <div className="kpi-value">{kpi.value}</div>
                        {kpi.trend && <span className={`kpi-trend ${kpi.trend_direction || "neutral"}`}>{kpi.trend_direction === "up" ? "↑" : "↓"} {kpi.trend}</span>}
                      </div>
                    );
                  })}
                </div>
              )}
              {viewData.narrative && <div className="narrative">{viewData.narrative}</div>}
              <div className={`chart-grid ${!viewData.secondary_chart ? "single" : ""}`}>
                {viewData.main_chart && <ChartRenderer config={viewData.main_chart} />}
                {viewData.secondary_chart && <ChartRenderer config={viewData.secondary_chart} />}
              </div>
              {viewData.main_chart?.data && <DataTable data={viewData.main_chart.data} title="Data" />}
              {viewData.sql_query && (
                <div>
                  <button id="btn-sql" name="btn-sql" className="btn btn-ghost" type="button" onClick={() => setShowSql(!showSql)}>{showSql ? "▾ Hide" : "▸ Show"} SQL</button>
                  {showSql && <div className="sql-block">{viewData.sql_query}</div>}
                </div>
              )}
            </div>
          )}

          {/* ── QUERY ERROR ── */}
          {activeView === "query" && viewData?.error && !loading && (
            <div className="error-box fade-in"><span>⚠️</span><div><strong>{viewData.error}</strong>{viewData.suggestion && <p style={{ marginTop: 4, opacity: .8, fontSize: 12 }}>{viewData.suggestion}</p>}</div></div>
          )}

          {/* ── DEEP DIVE ── */}
          {activeView === "deepdive" && viewData && !viewData.error && !loading && (
            <div className="slide-up">
              {viewData.root_cause_analysis && <div className="narrative">{viewData.root_cause_analysis}</div>}
              {viewData.monthly_trend && <LineChart data={viewData.monthly_trend} xKey="month" yKey="total_revenue" title="Monthly Revenue Trend" />}
              {viewData.revenue_by_category && (
                <div className="chart-grid">
                  <BarChart data={viewData.revenue_by_category} xKey="product_category" yKey="total_revenue" title="Revenue by Category" />
                  <PieChart data={viewData.revenue_by_category} xKey="product_category" yKey="total_revenue" title="Revenue Share" />
                </div>
              )}
              {viewData.recommendations?.length > 0 && (
                <div className="card">
                  <div className="card-title">Recommendations</div>
                  {viewData.recommendations.map((r, i) => (
                    <div key={i} style={{ padding: "10px 0", borderBottom: "1px solid var(--border)", display: "flex", gap: 10 }}>
                      <span style={{ fontSize: 18 }}>{r.priority === "high" ? "🔴" : r.priority === "medium" ? "🟡" : "🟢"}</span>
                      <div><strong style={{ fontSize: 13.5 }}>{r.action}</strong><p style={{ fontSize: 12, color: "var(--text-muted)", marginTop: 2 }}>Expected: {r.expected_impact}</p></div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* ── WHAT-IF CONTROLS + RESULTS ── */}
          {activeView === "whatif" && !loading && (
            <div className="slide-up">
              <div className="whatif-panel">
                <div className="card-title">Scenario Parameters</div>
                <form id="whatif-form" name="whatif-form" onSubmit={e => e.preventDefault()}>
                  <div className="slider-group">
                    <div className="slider-header"><label className="slider-label" htmlFor="wi-price">💰 Price</label><span className="slider-val">{wiPrice > 0 ? "+" : ""}{wiPrice}%</span></div>
                    <input id="wi-price" name="wi-price" className="slider-input" type="range" min={-50} max={50} value={wiPrice} onChange={e => setWiPrice(Number(e.target.value))} aria-label="Price" />
                  </div>
                  <div className="slider-group">
                    <div className="slider-header"><label className="slider-label" htmlFor="wi-disc">🏷️ Discount</label><span className="slider-val">{wiDiscount > 0 ? "+" : ""}{wiDiscount}%</span></div>
                    <input id="wi-disc" name="wi-disc" className="slider-input" type="range" min={-50} max={50} value={wiDiscount} onChange={e => setWiDiscount(Number(e.target.value))} aria-label="Discount" />
                  </div>
                  <div className="slider-group">
                    <div className="slider-header"><label className="slider-label" htmlFor="wi-units">📦 Volume</label><span className="slider-val">{wiUnits > 0 ? "+" : ""}{wiUnits}%</span></div>
                    <input id="wi-units" name="wi-units" className="slider-input" type="range" min={-50} max={50} value={wiUnits} onChange={e => setWiUnits(Number(e.target.value))} aria-label="Volume" />
                  </div>
                  <button id="btn-run-whatif" name="btn-run-whatif" className="btn btn-primary" type="button" onClick={runWhatIf} disabled={loading} style={{ marginTop: 8, width: "100%" }}>
                    ▶ Run Scenario
                  </button>
                </form>
              </div>

              {viewData && !viewData.error && (
                <>
                  <div className="kpi-grid">
                    <div className="kpi-card"><div className="kpi-header"><div className="kpi-label">Current</div><div className="kpi-icon revenue">💰</div></div><div className="kpi-value">{fmt(viewData.current?.revenue)}</div></div>
                    <div className="kpi-card"><div className="kpi-header"><div className="kpi-label">Projected</div><div className="kpi-icon revenue">🎯</div></div><div className="kpi-value" style={{ color: viewData.change?.revenue_diff >= 0 ? "var(--green)" : "var(--red)" }}>{fmt(viewData.projected?.revenue)}</div></div>
                    <div className="kpi-card"><div className="kpi-header"><div className="kpi-label">Impact</div><div className={`kpi-icon ${viewData.change?.revenue_pct_change >= 0 ? "units" : "orders"}`}>{viewData.change?.revenue_pct_change >= 0 ? "📈" : "📉"}</div></div><div className="kpi-value" style={{ color: viewData.change?.revenue_pct_change >= 0 ? "var(--green)" : "var(--red)" }}>{viewData.change?.revenue_pct_change >= 0 ? "+" : ""}{viewData.change?.revenue_pct_change}%</div></div>
                  </div>
                  {viewData.ai_commentary && <div className="narrative">{viewData.ai_commentary}</div>}
                  {viewData.monthly_comparison?.length > 0 && <BarChart data={viewData.monthly_comparison} xKey="month" yKey="projected_revenue" title="Projected Monthly Revenue" />}
                  {viewData.category_impact?.length > 0 && <DataTable data={viewData.category_impact} title="Category Impact" />}
                </>
              )}
            </div>
          )}

          {/* ── ANOMALIES ── */}
          {activeView === "anomalies" && viewData && !loading && (
            <div className="slide-up">
              <div className="kpi-grid" style={{ marginBottom: 20 }}>
                <div className="kpi-card">
                  <div className="kpi-header"><div className="kpi-label">Found</div><div className={`kpi-icon ${viewData.count > 0 ? "rating" : "units"}`}>{viewData.count > 0 ? "⚠️" : "✅"}</div></div>
                  <div className="kpi-value" style={{ color: viewData.count > 0 ? "var(--amber)" : "var(--green)" }}>{viewData.count}</div>
                </div>
              </div>
              {viewData.ai_analysis?.map((a, i) => (
                <div className={`anomaly-card ${a.severity}`} key={i}>
                  <div className="anomaly-metric">{a.severity === "high" ? "🔴" : a.severity === "medium" ? "🟡" : "🟢"} {a.metric}</div>
                  <div className="anomaly-desc">{a.description}</div>
                  <div className="anomaly-action">💡 {a.suggestion}</div>
                </div>
              ))}
              {viewData.count === 0 && (
                <div className="card" style={{ textAlign: "center", padding: 36 }}>
                  <div style={{ fontSize: 44, marginBottom: 10 }}>✅</div>
                  <h3 style={{ fontSize: 16, marginBottom: 4 }}>All Clear</h3>
                  <p style={{ color: "var(--text-muted)", fontSize: 13 }}>No anomalies detected.</p>
                </div>
              )}
            </div>
          )}

          {/* ── UPLOAD PROFILE ── */}
          {activeView === "upload" && viewData && !loading && (
            <div className="slide-up">
              <div className="card">
                <div className="card-title">Dataset Profile</div>
                <div className="profile-grid">
                  <div className="profile-stat"><div className="profile-stat-value">{viewData.rows?.toLocaleString()}</div><div className="profile-stat-label">Rows</div></div>
                  <div className="profile-stat"><div className="profile-stat-value">{viewData.columns}</div><div className="profile-stat-label">Columns</div></div>
                  <div className="profile-stat"><div className="profile-stat-value">{viewData.data_quality_score}%</div><div className="profile-stat-label">Quality</div></div>
                </div>
              </div>
              {viewData.column_info && (
                <DataTable data={viewData.column_info.map(c => ({ Column: c.name, Type: c.semantic_type, Unique: c.unique_count, Nulls: c.null_count, Samples: c.sample_values?.slice(0, 3).join(", ") }))} title="Columns" />
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
