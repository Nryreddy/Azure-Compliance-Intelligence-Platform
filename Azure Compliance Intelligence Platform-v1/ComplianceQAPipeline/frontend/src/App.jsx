import React, { useState, useEffect } from 'react';
import Navbar from './components/Navbar';
import NetworkBackground from './components/NetworkBackground';
import HeroSection from './components/HeroSection';
import AuditStatusLoader from './components/AuditStatusLoader';
import ComplianceReportDashboard from './components/ComplianceReportDashboard';
import HistoryPage from './components/HistoryPage';
import { pollAuditStatus } from './api';

function App() {
  const [currentView, setCurrentView] = useState('home'); // 'home' | 'history'
  const [currentSession, setCurrentSession] = useState(null);
  const [jobState, setJobState] = useState(null); // { status: 'pending'|'processing'|'completed'|'failed', result: null, error: null }

  // Polling logic
  useEffect(() => {
    let intervalId;

    if (currentSession && jobState?.status !== 'completed' && jobState?.status !== 'failed') {
      intervalId = setInterval(async () => {
        try {
          const data = await pollAuditStatus(currentSession);
          setJobState(data);
        } catch (error) {
          console.error("Polling error", error);
        }
      }, 5000); // Poll every 5 seconds
    }

    return () => {
      if (intervalId) clearInterval(intervalId);
    };
  }, [currentSession, jobState?.status]);

  const handleAuditStart = (sessionId) => {
    setCurrentSession(sessionId);
    setJobState({ status: 'pending' });
  };

  const handleReset = () => {
    setCurrentSession(null);
    setJobState(null);
    setCurrentView('home');
  };

  const handleNavigate = (view) => {
    setCurrentView(view);
    if (view === 'home' && currentSession && jobState?.status === 'completed') {
       // keep session if we go back to home? usually home means new audit
       handleReset();
    }
  };

  const handleViewPastAudit = async (sessionId) => {
    setCurrentSession(sessionId);
    setCurrentView('home'); // switch to home flow to show dashboard
    
    // Set to processing temporarily to show loader while we fetch
    setJobState({ status: 'processing' });
    
    try {
      const data = await pollAuditStatus(sessionId);
      setJobState(data);
    } catch (e) {
      setJobState({ status: 'failed', error: 'Failed to load past audit.' });
    }
  };

  return (
    <div className="app-container">
      <Navbar currentView={currentView} onNavigate={handleNavigate} />
      
      <main className="main-content">
        {currentView === 'history' ? (
          <>
            <NetworkBackground />
            <HistoryPage onViewAudit={handleViewPastAudit} />
          </>
        ) : (
          <>
            {!currentSession && <NetworkBackground />}
            
            {!currentSession ? (
              <HeroSection onAuditStart={handleAuditStart} />
            ) : (
              <>
                {(jobState?.status === 'pending' || jobState?.status === 'processing') && (
                  <AuditStatusLoader status={jobState.status} />
                )}
                
                {jobState?.status === 'completed' && jobState.result && (
                  <ComplianceReportDashboard result={jobState.result} onReset={handleReset} />
                )}

                {jobState?.status === 'failed' && (
                  <div className="container" style={{ textAlign: 'center', padding: '4rem 0', position: 'relative', zIndex: 2 }}>
                    <h2 style={{ color: 'var(--status-failed)' }}>Audit Failed</h2>
                    <p>{jobState.error || 'An unexpected error occurred during the audit.'}</p>
                    <button className="btn-outline" onClick={handleReset} style={{ marginTop: '1rem' }}>Try Again</button>
                  </div>
                )}
              </>
            )}
          </>
        )}
      </main>
    </div>
  );
}

export default App;
