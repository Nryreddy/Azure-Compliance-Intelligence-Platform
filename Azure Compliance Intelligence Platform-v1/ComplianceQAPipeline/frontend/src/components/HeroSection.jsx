import React, { useState } from 'react';
import { submitVideoForAudit } from '../api';
import { Search } from 'lucide-react';

const HeroSection = ({ onAuditStart }) => {
  const [videoUrl, setVideoUrl] = useState('');
  const [videoName, setVideoName] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!videoUrl) return;
    
    setLoading(true);
    setError(null);
    
    try {
      const response = await submitVideoForAudit(videoUrl, videoName);
      onAuditStart(response.session_id);
    } catch (err) {
      setError(err.message || 'Failed to submit video. Please try again.');
      setLoading(false);
    }
  };

  return (
    <section className="hero container">
      <h1 className="hero-title">
        Bridging Innovation and <br />
        <span className="text-primary">Compliance</span>
      </h1>
      
      <p className="hero-subtitle">
        Empowering brands with cutting-edge AI. Automatically audit your video content against strict brand guidelines, detecting misleading claims, absolute guarantees, and missing disclaimers in minutes.
      </p>

      <form className="audit-form" onSubmit={handleSubmit}>
        <div style={{ position: 'relative' }}>
          <input
            type="text"
            className="input-field"
            placeholder="Project / Video Name (Optional)"
            value={videoName}
            onChange={(e) => setVideoName(e.target.value)}
            disabled={loading}
          />
        </div>

        <div style={{ position: 'relative' }}>
          <div style={{ position: 'absolute', top: '50%', left: '1rem', transform: 'translateY(-50%)', color: 'var(--text-light)' }}>
            <Search size={20} />
          </div>
          <input
            type="url"
            className="input-field"
            placeholder="Paste YouTube Video URL..."
            value={videoUrl}
            onChange={(e) => setVideoUrl(e.target.value)}
            style={{ paddingLeft: '3rem' }}
            required
            disabled={loading}
          />
        </div>
        
        <button type="submit" className="btn-primary" disabled={loading}>
          {loading ? 'Submitting...' : 'Start Audit'}
        </button>
        
        {error && <p style={{ color: 'var(--status-failed)', fontSize: '0.9rem' }}>{error}</p>}
      </form>
    </section>
  );
};

export default HeroSection;
