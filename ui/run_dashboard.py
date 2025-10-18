#!/usr/bin/env python3
"""
FPL Agent Dashboard Launcher

Simple script to start the FPL Agent dashboard application.
"""

import sys
import os

# Add the parent directory to the path so we can import fpl_agent
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ui.dashboard import FPLDashboard

if __name__ == "__main__":
    print("=" * 60)
    print("🏆 FPL AGENT DASHBOARD")
    print("=" * 60)
    print("📊 Web-based interface for FPL data management")
    print("🔄 Features: Database updates and table viewing")
    print("=" * 60)
    
    try:
        dashboard = FPLDashboard()
        dashboard.run(debug=True, host='0.0.0.0', port=8050)
    except KeyboardInterrupt:
        print("\n👋 Dashboard stopped by user")
    except Exception as e:
        print(f"❌ Error starting dashboard: {e}")
        sys.exit(1)