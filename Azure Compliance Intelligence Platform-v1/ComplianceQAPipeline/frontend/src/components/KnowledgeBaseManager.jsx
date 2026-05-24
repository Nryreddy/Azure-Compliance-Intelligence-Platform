import React, { useState, useEffect, useRef } from 'react';
import { fetchKBFiles, uploadKBFile, deleteKBFile } from '../api';
import { Database, UploadCloud, Trash2, RefreshCw, FileText, CheckCircle2, AlertTriangle, AlertCircle, HardDrive, ShieldCheck } from 'lucide-react';

const KnowledgeBaseManager = () => {
  const [files, setFiles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState(null);
  const [dragActive, setDragActive] = useState(false);
  const [deleteLoading, setDeleteLoading] = useState(null); // stores filename of deleting record
  const fileInputRef = useRef(null);

  const loadFiles = async () => {
    setLoading(true);
    try {
      const data = await fetchKBFiles();
      setFiles(data);
      setError(null);
    } catch (err) {
      setError("Failed to load reference files from database.");
    } finally {
      setLoading(false);
    }
  };

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = async (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0];
      await processFileUpload(file);
    }
  };

  const handleFileChange = async (e) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      await processFileUpload(file);
    }
  };

  const processFileUpload = async (file) => {
    if (!file.name.toLowerCase().endsWith('.pdf')) {
      setUploadError("Only PDF files are supported.");
      return;
    }

    setUploading(true);
    setUploadError(null);

    try {
      await uploadKBFile(file);
      // Immediately load files to see 'indexing' state
      const data = await fetchKBFiles();
      setFiles(data);
    } catch (err) {
      setUploadError(err.message || "Failed to upload file.");
    } finally {
      setUploading(false);
    }
  };

  const handleDelete = async (filename) => {
    if (!window.confirm(`Are you sure you want to permanently delete "${filename}"? This will delete all its vector embeddings and text chunks from Azure AI Search.`)) {
      return;
    }

    setDeleteLoading(filename);
    try {
      await deleteKBFile(filename);
      setFiles(prev => prev.filter(f => f.filename !== filename));
    } catch (err) {
      alert(`Failed to delete file: ${err.message}`);
    } finally {
      setDeleteLoading(null);
    }
  };

  const onButtonClick = () => {
    fileInputRef.current.click();
  };

  // Poll for indexing updates
  useEffect(() => {
    let intervalId;
    const hasIndexingFile = files.some(f => f.status === 'indexing');

    if (hasIndexingFile) {
      intervalId = setInterval(async () => {
        try {
          const data = await fetchKBFiles();
          setFiles(data);
        } catch (e) {
          console.error("Polling indexing files error", e);
        }
      }, 3000); // poll every 3 seconds
    }

    return () => {
      if (intervalId) clearInterval(intervalId);
    };
  }, [files]);

  useEffect(() => {
    loadFiles();
  }, []);

  // Compute stats
  const totalFiles = files.length;
  const totalChunks = files.reduce((acc, f) => acc + (f.chunk_count || 0), 0);
  const totalCompleted = files.filter(f => f.status === 'completed').length;
  const isHealthy = error === null;

  return (
    <section className="container" style={{ padding: '4rem 0', position: 'relative', zIndex: 2 }}>
      {/* HEADER SECTION */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '3rem' }}>
        <div>
          <h2 className="hero-title" style={{ fontSize: '2.5rem', marginBottom: '0.5rem' }}>Knowledge Base</h2>
          <p style={{ color: 'var(--text-light)' }}>
            Upload and manage the regulatory documents, corporate rulebooks, and compliance policies used by RAG to audit brand assets.
          </p>
        </div>
        <button className="btn-outline" onClick={loadFiles} disabled={loading}>
          <RefreshCw size={18} className={loading ? "spin" : ""} style={{ marginRight: '0.5rem' }} /> Refresh
        </button>
      </div>

      {/* STATS OVERVIEW CARD GRID */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
        gap: '1.5rem',
        marginBottom: '3rem'
      }}>
        {/* STAT CARD 1: FILES */}
        <div className="card" style={{ display: 'flex', alignItems: 'center', gap: '1.5rem', padding: '1.5rem', marginBottom: 0 }}>
          <div style={{
            background: 'rgba(37, 99, 235, 0.08)',
            color: 'var(--primary)',
            padding: '1rem',
            borderRadius: '12px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}>
            <Database size={28} />
          </div>
          <div>
            <h4 style={{ color: 'var(--text-light)', fontSize: '0.9rem', fontWeight: 500, textTransform: 'uppercase', letterSpacing: '0.05em' }}>Referenced Guideline Files</h4>
            <div style={{ fontSize: '1.75rem', fontWeight: 700, color: 'var(--text-dark)' }}>{totalFiles}</div>
          </div>
        </div>

        {/* STAT CARD 2: CHUNKS */}
        <div className="card" style={{ display: 'flex', alignItems: 'center', gap: '1.5rem', padding: '1.5rem', marginBottom: 0 }}>
          <div style={{
            background: 'rgba(16, 185, 129, 0.08)',
            color: 'var(--status-completed)',
            padding: '1rem',
            borderRadius: '12px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}>
            <HardDrive size={28} />
          </div>
          <div>
            <h4 style={{ color: 'var(--text-light)', fontSize: '0.9rem', fontWeight: 500, textTransform: 'uppercase', letterSpacing: '0.05em' }}>Total Vector Embeddings</h4>
            <div style={{ fontSize: '1.75rem', fontWeight: 700, color: 'var(--text-dark)' }}>{totalChunks} <span style={{ fontSize: '0.9rem', fontWeight: 400, color: 'var(--text-light)' }}>chunks</span></div>
          </div>
        </div>

        {/* STAT CARD 3: STATUS */}
        <div className="card" style={{ display: 'flex', alignItems: 'center', gap: '1.5rem', padding: '1.5rem', marginBottom: 0 }}>
          <div style={{
            background: isHealthy ? 'rgba(16, 185, 129, 0.08)' : 'rgba(239, 68, 68, 0.08)',
            color: isHealthy ? 'var(--status-completed)' : 'var(--status-failed)',
            padding: '1rem',
            borderRadius: '12px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}>
            <ShieldCheck size={28} />
          </div>
          <div>
            <h4 style={{ color: 'var(--text-light)', fontSize: '0.9rem', fontWeight: 500, textTransform: 'uppercase', letterSpacing: '0.05em' }}>Indexing Core Status</h4>
            <div style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--text-dark)' }}>{isHealthy ? 'Operational' : 'Error'}</div>
          </div>
        </div>
      </div>

      {/* DASHBOARD WORKSPACE ROW */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))',
        gap: '2.5rem',
        alignItems: 'start'
      }}>
        {/* DROPZONE / FILE UPLOAD CONTAINER */}
        <div>
          <h3 style={{ fontSize: '1.25rem', fontWeight: 600, marginBottom: '1rem' }}>Upload Reference Guideline</h3>
          <div 
            className="card" 
            onDragEnter={handleDrag} 
            onDragLeave={handleDrag} 
            onDragOver={handleDrag} 
            onDrop={handleDrop}
            style={{
              border: dragActive ? '2px dashed var(--primary)' : '2px dashed var(--border)',
              backgroundColor: dragActive ? 'rgba(37, 99, 235, 0.02)' : 'white',
              textAlign: 'center',
              padding: '3rem 2rem',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              cursor: 'pointer',
              borderRadius: '16px',
              transition: 'all 0.2s ease-in-out',
              height: '320px'
            }}
            onClick={onButtonClick}
          >
            <input 
              ref={fileInputRef}
              type="file" 
              style={{ display: 'none' }} 
              accept=".pdf"
              onChange={handleFileChange}
            />

            {uploading ? (
              <>
                <div className="spinner" style={{ borderLeftColor: 'var(--primary)', marginBottom: '1.5rem' }}></div>
                <h4 style={{ fontSize: '1.1rem', fontWeight: 600, marginBottom: '0.5rem' }}>Parsing & Chunking Document...</h4>
                <p style={{ color: 'var(--text-light)', fontSize: '0.9rem' }}>Extracting PDF pages, loading embed model, and generating Azure vector indexes.</p>
              </>
            ) : (
              <>
                <div style={{
                  color: 'var(--primary)',
                  marginBottom: '1.5rem',
                  opacity: 0.85
                }}>
                  <UploadCloud size={64} strokeWidth={1.5} />
                </div>
                <h4 style={{ fontSize: '1.25rem', fontWeight: 600, marginBottom: '0.5rem', color: 'var(--text-dark)' }}>
                  Drag & drop your guidelines PDF here
                </h4>
                <p style={{ color: 'var(--text-light)', fontSize: '0.95rem', marginBottom: '1.5rem', maxWidth: '300px' }}>
                  or click to browse from your device
                </p>
                <span className="badge" style={{
                  background: '#F1F5F9',
                  color: '#475569',
                  fontSize: '0.75rem',
                  fontWeight: 600,
                  padding: '0.35rem 0.75rem'
                }}>
                  Supported: PDF only (Max 25MB)
                </span>
              </>
            )}
          </div>
          
          {uploadError && (
            <div style={{
              marginTop: '1rem',
              padding: '1rem',
              borderRadius: '8px',
              backgroundColor: 'rgba(239, 68, 68, 0.05)',
              borderLeft: '4px solid var(--status-failed)',
              color: 'var(--status-failed)',
              display: 'flex',
              alignItems: 'flex-start',
              gap: '0.75rem',
              fontSize: '0.9rem'
            }}>
              <AlertCircle size={18} style={{ flexShrink: 0, marginTop: '0.1rem' }} />
              <div>
                <strong>Upload Failed:</strong> {uploadError}
              </div>
            </div>
          )}
        </div>

        {/* LIST OF GUIDELINES */}
        <div>
          <h3 style={{ fontSize: '1.25rem', fontWeight: 600, marginBottom: '1rem' }}>Active Vector Index Documents</h3>
          <div className="card" style={{ padding: 0, minHeight: '320px', display: 'flex', flexDirection: 'column' }}>
            {error && (
              <div style={{
                margin: '1.5rem',
                padding: '1rem',
                borderRadius: '8px',
                backgroundColor: 'rgba(239, 68, 68, 0.05)',
                borderLeft: '4px solid var(--status-failed)',
                color: 'var(--status-failed)',
                display: 'flex',
                alignItems: 'center',
                gap: '0.75rem',
                fontSize: '0.9rem'
              }}>
                <AlertCircle size={18} />
                <span>{error}</span>
              </div>
            )}

            {files.length === 0 ? (
              <div style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '3rem 2rem', color: 'var(--text-light)' }}>
                <FileText size={48} style={{ opacity: 0.25, marginBottom: '1rem' }} />
                <h4 style={{ fontWeight: 600, marginBottom: '0.25rem', color: 'var(--text-dark)' }}>No guidelines uploaded</h4>
                <p style={{ fontSize: '0.9rem', textAlign: 'center', maxWidth: '280px' }}>Upload compliance manuals above to populate the search index for video auditing.</p>
              </div>
            ) : (
              <div style={{ overflowX: 'auto' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
                  <thead>
                    <tr style={{ backgroundColor: '#F8FAFC', borderBottom: '1px solid var(--border)' }}>
                      <th style={{ padding: '0.75rem 1rem', fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-light)' }}>Filename</th>
                      <th style={{ padding: '0.75rem 1rem', fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-light)' }}>Status</th>
                      <th style={{ padding: '0.75rem 1rem', fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-light)' }}>Embeddings</th>
                      <th style={{ padding: '0.75rem 1rem', fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-light)', textAlign: 'right' }}>Action</th>
                    </tr>
                  </thead>
                  <tbody>
                    {files.map((file) => {
                      let badgeStyle = { backgroundColor: '#FEF3C7', color: '#D97706' }; // Indexing
                      if (file.status === 'completed') badgeStyle = { backgroundColor: '#D1FAE5', color: '#065F46' };
                      if (file.status === 'failed') badgeStyle = { backgroundColor: '#FEE2E2', color: '#991B1B' };

                      // Format size
                      const size = file.size_bytes 
                        ? `${(file.size_bytes / (1024 * 1024)).toFixed(2)} MB`
                        : '-';

                      return (
                        <tr key={file.id} style={{ borderBottom: '1px solid var(--border)', transition: 'background 0.2s' }}>
                          <td style={{ padding: '1rem', verticalAlign: 'middle' }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                              <FileText size={18} style={{ color: 'var(--primary)', flexShrink: 0 }} />
                              <div style={{ minWidth: 0 }}>
                                <div style={{ fontWeight: 500, textOverflow: 'ellipsis', overflow: 'hidden', whiteSpace: 'nowrap', fontSize: '0.9rem', color: 'var(--text-dark)' }} title={file.filename}>
                                  {file.filename}
                                </div>
                                <span style={{ fontSize: '0.75rem', color: 'var(--text-light)' }}>{size}</span>
                              </div>
                            </div>
                          </td>
                          <td style={{ padding: '1rem', verticalAlign: 'middle' }}>
                            <span className="badge" style={{
                              ...badgeStyle,
                              fontSize: '0.7rem',
                              padding: '0.15rem 0.5rem',
                              fontWeight: 600,
                              textTransform: 'capitalize',
                              display: 'inline-flex',
                              alignItems: 'center',
                              gap: '0.25rem'
                            }}>
                              {file.status === 'indexing' && <RefreshCw size={10} className="spin" />}
                              {file.status === 'completed' && <CheckCircle2 size={10} />}
                              {file.status === 'failed' && <AlertTriangle size={10} />}
                              {file.status}
                            </span>
                          </td>
                          <td style={{ padding: '1rem', verticalAlign: 'middle', fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-light)' }}>
                            {file.status === 'completed' ? `${file.chunk_count} chunks` : '-'}
                          </td>
                          <td style={{ padding: '1rem', verticalAlign: 'middle', textAlign: 'right' }}>
                            <button
                              onClick={() => handleDelete(file.filename)}
                              disabled={deleteLoading === file.filename}
                              style={{
                                background: 'transparent',
                                border: 'none',
                                color: deleteLoading === file.filename ? 'var(--text-light)' : 'var(--status-failed)',
                                cursor: 'pointer',
                                padding: '0.35rem',
                                borderRadius: '6px',
                                display: 'inline-flex',
                                alignItems: 'center',
                                transition: 'background 0.2s'
                              }}
                              className="delete-hover-effect"
                              title="Delete Guideline File"
                            >
                              {deleteLoading === file.filename ? '...' : <Trash2 size={16} />}
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
        </div>
      </div>
    </section>
  );
};

export default KnowledgeBaseManager;
