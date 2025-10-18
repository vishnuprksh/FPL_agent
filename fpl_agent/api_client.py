"""
FPL API Client for fetching data from Fantasy Premier League API.
"""

import json
import urllib.request
from typing import Dict


class FPLAPIClient:
    """Client for interacting with the FPL API."""
    
    BASE_URL = "https://fantasy.premierleague.com/api"
    
    @classmethod
    def fetch_bootstrap_data(cls) -> Dict:
        """Fetch FPL bootstrap data from API."""
        url = f"{cls.BASE_URL}/bootstrap-static/"
        
        try:
            with urllib.request.urlopen(url) as response:
                data = json.loads(response.read().decode())
                return data
        except Exception as e:
            raise Exception(f"Failed to fetch FPL data: {e}")