import React from 'react';

const Navbar = ({ currentView, onNavigate }) => {
  return (
    <nav className="navbar container">
      <div className="nav-brand" style={{ cursor: 'pointer' }} onClick={() => onNavigate('home')}>
        ComplianceAI
      </div>
      <ul className="nav-links">
        <li>
          <a 
            href="#" 
            onClick={(e) => { e.preventDefault(); onNavigate('home'); }}
            style={{ color: currentView === 'home' ? 'var(--primary)' : 'var(--text-light)' }}
          >
            New Audit
          </a>
        </li>
        <li>
          <a 
            href="#" 
            onClick={(e) => { e.preventDefault(); onNavigate('knowledge'); }}
            style={{ color: currentView === 'knowledge' ? 'var(--primary)' : 'var(--text-light)' }}
          >
            Knowledge Base
          </a>
        </li>
        <li>
          <a 
            href="#" 
            onClick={(e) => { e.preventDefault(); onNavigate('history'); }}
            style={{ color: currentView === 'history' ? 'var(--primary)' : 'var(--text-light)' }}
          >
            History
          </a>
        </li>
      </ul>
      <div className="nav-actions">
        <button className="btn-outline">Settings</button>
      </div>
    </nav>
  );
};

export default Navbar;
