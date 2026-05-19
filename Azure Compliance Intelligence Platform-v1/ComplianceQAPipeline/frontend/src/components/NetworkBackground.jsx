import React from 'react';

const NetworkBackground = () => {
  return (
    <div className="network-bg">
      <svg width="100%" height="100%" viewBox="0 0 1200 800" preserveAspectRatio="xMidYMid slice" xmlns="http://www.w3.org/2000/svg">
        <defs>
          <radialGradient id="globe-glow" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stopColor="rgba(37, 99, 235, 0.05)" />
            <stop offset="100%" stopColor="rgba(255, 255, 255, 0)" />
          </radialGradient>
        </defs>
        
        {/* Subtle background glow mimicking a globe */}
        <circle cx="600" cy="500" r="400" fill="url(#globe-glow)" />

        <g stroke="rgba(37, 99, 235, 0.3)" strokeWidth="1.5" fill="none">
          {/* Main geometric lines */}
          <path d="M150,300 L250,500 L400,450 L600,600 L800,450 L950,500 L1050,300" />
          <path d="M150,300 L300,650 L600,750 L900,650 L1050,300" />
          <path d="M250,500 L300,650 L400,450" />
          <path d="M800,450 L900,650 L950,500" />
          <path d="M400,450 L600,750 L800,450" />
          <path d="M600,600 L600,750" />
          
          {/* Nodes */}
          <g fill="var(--primary)" stroke="rgba(37, 99, 235, 0.4)" strokeWidth="6">
            <circle cx="150" cy="300" r="4" />
            <circle cx="250" cy="500" r="5" />
            <circle cx="400" cy="450" r="4" />
            <circle cx="600" cy="600" r="6" />
            <circle cx="800" cy="450" r="4" />
            <circle cx="950" cy="500" r="5" />
            <circle cx="1050" cy="300" r="4" />
            <circle cx="300" cy="650" r="4" />
            <circle cx="600" cy="750" r="5" />
            <circle cx="900" cy="650" r="4" />
          </g>
        </g>
      </svg>
    </div>
  );
};

export default NetworkBackground;
