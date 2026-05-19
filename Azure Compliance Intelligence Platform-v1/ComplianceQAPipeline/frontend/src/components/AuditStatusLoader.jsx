import React from 'react';

const AuditStatusLoader = ({ status }) => {
  return (
    <div className="loader-container">
      <div className="spinner"></div>
      <h2 className="status-text">
        {status === 'pending' ? 'Initiating Audit...' : 'Analyzing Video Content...'}
      </h2>
      <p className="status-subtext">
        This involves downloading the video, extracting the transcript and OCR, and running AI compliance checks. Please wait...
      </p>
    </div>
  );
};

export default AuditStatusLoader;
