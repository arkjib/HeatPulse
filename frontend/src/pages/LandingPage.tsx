import { useEffect, useRef } from 'react';
import './LandingPage.css';

interface LandingPageProps {
  onEnter: () => void;
}

export default function LandingPage({ onEnter }: LandingPageProps) {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function fitToScreen() {
      const container = containerRef.current;
      if (!container) return;
      const designWidth = 4073;
      const designHeight = 4922;
      const scale = window.innerWidth / designWidth;
      container.style.transform = `scale(${scale})`;
      container.style.transformOrigin = 'top left';
      container.style.marginBottom = `${(designHeight * scale) - designHeight}px`;
    }
    
    window.addEventListener('resize', fitToScreen);
    fitToScreen();
    
    return () => window.removeEventListener('resize', fitToScreen);
  }, []);

  return (
    <div className="landing-wrapper">
      <div className="main-container" ref={containerRef}>
        <div className="heatpulse">
            <span className="heat">Heat</span><span className="pulse">pulse</span>
        </div>
        <span className="know-the-heat">
            <span className="blur-word" style={{ animationDelay: "0ms" }}>Know</span>
            <span className="blur-word" style={{ animationDelay: "120ms" }}>the</span>
            <span className="blur-word" style={{ animationDelay: "240ms" }}>heat</span>
            <span className="blur-word" style={{ animationDelay: "360ms" }}>before</span>
            <span className="blur-word" style={{ animationDelay: "480ms" }}>it</span>
            <span className="blur-word" style={{ animationDelay: "600ms" }}>becomes</span>
            <span className="blur-word" style={{ animationDelay: "720ms" }}>a</span>
            <span className="blur-word" style={{ animationDelay: "840ms" }}>crisis.</span>
        </span>
        <span className="intelligent-heat-risk">
            HeatPulse is an intelligent heat-risk prediction and response platform
            that combines weather data, thermal stress analysis, machine learning,
            human vulnerability, and GIS to predict ward-level heat risk 3–5 days
            ahead.
        </span>
        <div className="rectangle" onClick={onEnter}>
            <span className="explore-risk-map">Explore Risk Map</span>
            <div className="arrow"></div>
        </div>
        <div className="frame"></div>
        <span className="heat-pulse">What is HeatPulse?</span>
        <div className="flex-row-ada">
            <div className="ellipse"></div>
            <span className="weather-data">Weather Data</span>
            <span className="heat-risk-info">
                HeatPulse is an intelligent heat-risk prediction and early-warning
                platform designed to help cities identify where extreme heat will
                become dangerous, who is most vulnerable, and what action should be
                taken.<br />Unlike systems that only report temperature, HeatPulse
                combines weather, thermal stress, machine learning, population
                vulnerability, and GIS to create a detailed heat-risk picture at the
                ward/zone level.
            </span>
            <div className="ellipse-1"></div>
            <div className="line"></div>
            <span className="temp-humidity-wind">Temperature + Humidity + Wind + Solar Radiation</span>
            <span className="thermal-stress-analysis">Thermal Stress Analysis</span>
            <div className="ellipse-2"></div>
            <span className="wbgt-utci-heat">WBGT + UTCI + Heat Index</span>
            <span className="ml-forecasting">ML Forecasting</span>
            <div className="ellipse-3"></div>
            <div className="gemini-generated-image"></div>
            <span className="predicts-thermal-stress">Predicts thermal stress 3–5 days ahead</span>
            <span className="human-vulnerability">Human Vulnerability</span>
            <div className="ellipse-4"></div>
            <span className="vulnerable-population">Elderly population + outdoor workers + exposure + local vulnerability</span>
            <span className="gis-risk-mapping">GIS Risk Mapping</span>
            <div className="ellipse-5"></div>
            <span className="high-risk-identification">Identifies high-risk wards and hotspots</span>
            <span className="action-alerts">Action &amp; Alerts</span>
            <div className="ellipse-6"></div>
            <span className="cooling-centres-water">Cooling centres + water availability + work-hour changes + SMS/WhatsApp alerts</span>
        </div>
        <div className="beautiful-shining-stars"></div>
        <div className="rectangle-7"></div>
        <div className="firefly"></div>
        <div className="wild-grass-hills"></div>
        <div className="rectangle-8"></div>
      </div>
    </div>
  );
}
