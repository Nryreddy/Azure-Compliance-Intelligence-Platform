import React from 'react';
import { CheckCircle, AlertTriangle, AlertCircle, FileText, ShieldCheck } from 'lucide-react';

/**
 * Renders markdown-ish text by splitting on double newlines and formatting
 * headings (## / ###) and bold (**text**) simply without a full markdown lib.
 */
const RichReport = ({ text }) => {
  if (!text) return null;

  const lines = text.split('\n');

  return (
    <div className="rich-report">
      {lines.map((line, i) => {
        if (line.startsWith('### ')) {
          return <h4 key={i} className="report-h3">{line.replace('### ', '')}</h4>;
        }
        if (line.startsWith('## ')) {
          return <h3 key={i} className="report-h2">{line.replace('## ', '')}</h3>;
        }
        if (line.startsWith('# ')) {
          return <h2 key={i} className="report-h1">{line.replace('# ', '')}</h2>;
        }
        if (line.trim() === '') {
          return <div key={i} style={{ height: '0.5rem' }} />;
        }
        // Render **bold** inline
        const parts = line.split(/(\*\*[^*]+\*\*)/g);
        return (
          <p key={i} className="report-p">
            {parts.map((part, j) =>
              part.startsWith('**') && part.endsWith('**')
                ? <strong key={j}>{part.slice(2, -2)}</strong>
                : part
            )}
          </p>
        );
      })}
    </div>
  );
};

const SeverityIcon = ({ severity }) => {
  if (severity?.toUpperCase() === 'CRITICAL') {
    return <AlertCircle size={18} color="#DC2626" />;
  }
  return <AlertTriangle size={18} color="#D97706" />;
};

const ComplianceReportDashboard = ({ result, onReset }) => {
  const { video_id, status, final_report, compliance_results } = result;

  const riskMatch = final_report?.match(/risk level[:\s]+([A-Z]+)/i);
  const riskLevel = riskMatch ? riskMatch[1] : null;

  const riskColour = {
    LOW: '#10B981',
    MEDIUM: '#D97706',
    HIGH: '#EF4444',
    CRITICAL: '#7C3AED',
  }[riskLevel] || 'var(--text-light)';

  return (
    <section className="dashboard container">

      {/* Header row */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
        <h2 className="hero-title" style={{ fontSize: '2.5rem', marginBottom: 0 }}>Audit Results</h2>
        <button className="btn-outline" onClick={onReset}>Audit Another Video</button>
      </div>

      {/* Overview card */}
      <div className="card" style={{ marginBottom: '1.5rem' }}>
        <div className="card-title">
          <span style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <FileText size={18} />
            {video_id}
          </span>
          <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
            {riskLevel && (
              <span style={{
                fontSize: '0.75rem',
                fontWeight: 700,
                padding: '0.25rem 0.6rem',
                borderRadius: '999px',
                backgroundColor: riskColour + '22',
                color: riskColour,
                border: `1px solid ${riskColour}44`,
              }}>
                {riskLevel} RISK
              </span>
            )}
            <span className={`badge ${status === 'PASS' ? 'badge-pass' : 'badge-fail'}`}>
              {status}
            </span>
          </div>
        </div>

        {/* Rich narrative report */}
        <div style={{ marginTop: '1.25rem' }}>
          <RichReport text={final_report} />
        </div>
      </div>

      {/* Violations card */}
      <div className="card">
        <div className="card-title" style={{ marginBottom: '1.25rem' }}>
          <span>Identified Violations</span>
          <span className="badge badge-fail" style={{ opacity: compliance_results?.length ? 1 : 0.4 }}>
            {compliance_results?.length ?? 0} found
          </span>
        </div>

        {compliance_results && compliance_results.length > 0 ? (
          <div className="violation-list">
            {compliance_results.map((issue, idx) => (
              <div key={idx} className={`violation-item ${issue.severity?.toLowerCase()}`}>

                {/* Violation header */}
                <div className="violation-header">
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <SeverityIcon severity={issue.severity} />
                    <span className="violation-category">{issue.category}</span>
                  </div>
                  <span className={`badge ${issue.severity?.toUpperCase() === 'CRITICAL' ? 'badge-critical' : 'badge-warning'}`}>
                    {issue.severity}
                  </span>
                </div>

                {/* Description */}
                <p className="violation-desc">{issue.description}</p>

                {/* Evidence + Rule (new fields from 5-node workflow) */}
                {issue.evidence && (
                  <div style={{
                    margin: '0.75rem 0 0',
                    padding: '0.6rem 0.85rem',
                    borderLeft: '3px solid #6366F1',
                    backgroundColor: '#6366F108',
                    borderRadius: '0 6px 6px 0',
                    fontSize: '0.82rem',
                    color: 'var(--text-light)',
                    fontStyle: 'italic',
                  }}>
                    <strong style={{ fontStyle: 'normal', color: 'var(--text)' }}>Evidence: </strong>
                    {issue.evidence}
                  </div>
                )}

                {issue.rule_breached && (
                  <div style={{
                    marginTop: '0.5rem',
                    fontSize: '0.78rem',
                    color: 'var(--text-light)',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.35rem',
                  }}>
                    <ShieldCheck size={13} />
                    <span><strong>Rule breached:</strong> {issue.rule_breached}</span>
                  </div>
                )}

              </div>
            ))}
          </div>
        ) : (
          <div style={{ padding: '2rem', textAlign: 'center', backgroundColor: '#F8FAFC', borderRadius: '8px' }}>
            <CheckCircle size={48} color="#10B981" style={{ margin: '0 auto 1rem' }} />
            <h3 style={{ color: '#065F46' }}>Perfect Compliance</h3>
            <p style={{ color: 'var(--text-light)' }}>No violations were detected in this video content.</p>
          </div>
        )}
      </div>

    </section>
  );
};

export default ComplianceReportDashboard;
