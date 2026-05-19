import React from 'react';
import { CheckCircle, AlertTriangle, AlertCircle } from 'lucide-react';

const ComplianceReportDashboard = ({ result, onReset }) => {
  const { video_id, status, final_report, compliance_results } = result;

  return (
    <section className="dashboard container">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
        <h2 className="hero-title" style={{ fontSize: '2.5rem', marginBottom: 0 }}>Audit Results</h2>
        <button className="btn-outline" onClick={onReset}>Audit Another Video</button>
      </div>

      <div className="card">
        <div className="card-title">
          <span>Overview: {video_id}</span>
          <span className={`badge ${status === 'PASS' ? 'badge-pass' : 'badge-fail'}`}>
            {status}
          </span>
        </div>
        
        <p style={{ color: 'var(--text-light)', marginBottom: '2rem' }}>
          {final_report}
        </p>

        {compliance_results && compliance_results.length > 0 ? (
          <>
            <h3 style={{ marginBottom: '1rem', fontSize: '1.1rem' }}>Identified Violations ({compliance_results.length})</h3>
            <div className="violation-list">
              {compliance_results.map((issue, idx) => (
                <div key={idx} className={`violation-item ${issue.severity.toLowerCase()}`}>
                  <div className="violation-header">
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                      {issue.severity.toUpperCase() === 'CRITICAL' ? 
                        <AlertCircle size={18} color="#DC2626" /> : 
                        <AlertTriangle size={18} color="#D97706" />
                      }
                      <span className="violation-category">{issue.category}</span>
                    </div>
                    <span className={`badge ${issue.severity.toUpperCase() === 'CRITICAL' ? 'badge-critical' : 'badge-warning'}`}>
                      {issue.severity}
                    </span>
                  </div>
                  <p className="violation-desc">{issue.description}</p>
                </div>
              ))}
            </div>
          </>
        ) : (
          <div style={{ padding: '2rem', textAlign: 'center', backgroundColor: '#F8FAFC', borderRadius: '8px' }}>
            <CheckCircle size={48} color="#10B981" style={{ margin: '0 auto 1rem' }} />
            <h3 style={{ color: '#065F46' }}>Perfect Compliance</h3>
            <p style={{ color: 'var(--text-light)' }}>No violations were found in this video content.</p>
          </div>
        )}
      </div>
    </section>
  );
};

export default ComplianceReportDashboard;
