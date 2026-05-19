import React, { useState, useEffect } from 'react';
import { fetchAuditsHistory, deleteAuditRecord } from '../api';
import { Clock, RefreshCw, ExternalLink, Trash2 } from 'lucide-react';

const HistoryPage = ({ onViewAudit }) => {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [deleteLoading, setDeleteLoading] = useState(null); // stores session ID of deleting record

  const loadHistory = async () => {
    setLoading(true);
    try {
      const data = await fetchAuditsHistory();
      setHistory(data);
      setError(null);
    } catch (err) {
      setError("Failed to load audit history from database.");
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (sessionId) => {
    if (!window.confirm("Are you sure you want to permanently delete this audit record from the database?")) {
      return;
    }
    
    setDeleteLoading(sessionId);
    try {
      await deleteAuditRecord(sessionId);
      // Remove from local state to avoid full reload jumpiness
      setHistory(prev => prev.filter(item => item.id !== sessionId));
    } catch (err) {
      alert("Failed to delete record: " + err.message);
    } finally {
      setDeleteLoading(null);
    }
  };

  useEffect(() => {
    loadHistory();
  }, []);

  return (
    <section className="container" style={{ padding: '4rem 0', position: 'relative', zIndex: 2 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
        <div>
          <h2 className="hero-title" style={{ fontSize: '2.5rem', marginBottom: '0.5rem' }}>Audit History</h2>
          <p style={{ color: 'var(--text-light)' }}>View and manage past compliance reports stored in Azure Cosmos DB.</p>
        </div>
        <button className="btn-outline" onClick={loadHistory} disabled={loading}>
          <RefreshCw size={18} className={loading ? "spin" : ""} /> Refresh
        </button>
      </div>

      {error && <div style={{ color: 'var(--status-failed)', marginBottom: '1rem' }}>{error}</div>}

      <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
        {loading ? (
          <div style={{ padding: '4rem', textAlign: 'center' }}>
            <div className="spinner" style={{ margin: '0 auto 1rem' }}></div>
            <p>Loading records...</p>
          </div>
        ) : history.length === 0 ? (
          <div style={{ padding: '4rem', textAlign: 'center', color: 'var(--text-light)' }}>
            <Clock size={48} style={{ margin: '0 auto 1rem', opacity: 0.5 }} />
            <h3>No Past Audits Found</h3>
            <p>Run your first video compliance audit to see it listed here.</p>
          </div>
        ) : (
          <div style={{ maxHeight: '480px', overflowY: 'auto', position: 'relative' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
              <thead style={{ position: 'sticky', top: 0, zIndex: 10, backgroundColor: '#F8FAFC', borderBottom: '1px solid var(--border)' }}>
                <tr>
                  <th style={{ padding: '1rem 1.5rem', fontWeight: 600 }}>Project / Video Name</th>
                  <th style={{ padding: '1rem 1.5rem', fontWeight: 600 }}>Audit Status</th>
                  <th style={{ padding: '1rem 1.5rem', fontWeight: 600 }}>Compliance Result</th>
                  <th style={{ padding: '1rem 1.5rem', fontWeight: 600 }}>Date</th>
                  <th style={{ padding: '1rem 1.5rem', fontWeight: 600 }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {history.map((record) => {
                  const date = new Date(record.timestamp).toLocaleString();
                  
                  let badgeClass = 'badge-warning'; // pending / processing
                  if (record.status === 'completed') badgeClass = 'badge-pass';
                  if (record.status === 'failed') badgeClass = 'badge-fail';

                  // Determine compliance result badge (PASS / FAIL)
                  let complianceBadge = null;
                  if (record.status === 'completed' && record.compliance_status) {
                    const isPass = record.compliance_status === 'PASS';
                    complianceBadge = (
                      <span className={`badge ${isPass ? 'badge-pass' : 'badge-fail'}`} style={{ fontSize: '0.85rem', padding: '0.2rem 0.6rem' }}>
                        {record.compliance_status}
                      </span>
                    );
                  } else if (record.status === 'failed') {
                    complianceBadge = <span style={{ color: 'var(--status-failed)', fontSize: '0.9rem' }}>Error</span>;
                  } else {
                    complianceBadge = <span style={{ color: 'var(--text-light)', fontSize: '0.9rem' }}>-</span>;
                  }
                  
                  return (
                    <tr key={record.id} style={{ borderBottom: '1px solid var(--border)' }}>
                      <td style={{ padding: '1.25rem 1.5rem', fontWeight: 500 }}>
                        {record.video_id}
                      </td>
                      <td style={{ padding: '1.25rem 1.5rem' }}>
                        <span className={`badge ${badgeClass}`} style={{ fontSize: '0.8rem', padding: '0.2rem 0.6rem' }}>
                          {record.status}
                        </span>
                      </td>
                      <td style={{ padding: '1.25rem 1.5rem' }}>
                        {complianceBadge}
                      </td>
                      <td style={{ padding: '1.25rem 1.5rem', color: 'var(--text-light)', fontSize: '0.9rem' }}>
                        {date}
                      </td>
                      <td style={{ padding: '1.25rem 1.5rem', display: 'flex', gap: '0.5rem' }}>
                        <button 
                          className="btn-outline" 
                          style={{ padding: '0.4rem 0.8rem', fontSize: '0.85rem' }}
                          onClick={() => onViewAudit(record.id)}
                          disabled={record.status !== 'completed' && record.status !== 'failed'}
                        >
                          View <ExternalLink size={14} />
                        </button>
                        <button 
                          className="btn-outline" 
                          style={{ 
                            padding: '0.4rem 0.8rem', 
                            fontSize: '0.85rem', 
                            borderColor: 'rgba(239, 68, 68, 0.2)',
                            color: 'var(--status-failed)' 
                          }}
                          onClick={() => handleDelete(record.id)}
                          disabled={deleteLoading === record.id}
                        >
                          {deleteLoading === record.id ? '...' : <Trash2 size={14} />}
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </section>
  );
};

export default HistoryPage;
