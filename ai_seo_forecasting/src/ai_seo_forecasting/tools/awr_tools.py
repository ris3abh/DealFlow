"""
NEW AWR API TOOLS - Add these to your existing awr_tools.py
Based on API test results
"""

import os
import requests
from typing import Type, Optional, Dict, Any
from pydantic import BaseModel, Field
from crewai.tools import BaseTool
from datetime import datetime, timedelta
import csv
from io import StringIO


# ============================================================================
# TOOL 4: GET KEYWORD RANKINGS (THE MOST IMPORTANT!)
# ============================================================================

class AWRRankingsInput(BaseModel):
    """Input schema for AWRRankingsTool."""
    project: str = Field(..., description="Project name (e.g., 'pella.com')")
    days: int = Field(default=7, description="Number of days of data to retrieve (default: 7)")
    format: str = Field(default="csv", description="Format: csv or json")


class AWRRankingsTool(BaseTool):
    name: str = "Get AWR Keyword Rankings"
    description: str = (
        "Retrieves actual keyword ranking positions over time - THE MOST CRITICAL SEO DATA. "
        "Returns rankings for all keywords across all search engines and dates. "
        "This data shows: keyword, date, rank position, URL, search engine, location. "
        "Use this for SEO performance analysis and tracking ranking changes. "
        "Required: project name. Optional: days (default 7)."
    )
    args_schema: Type[BaseModel] = AWRRankingsInput
    
    api_key: str = Field(default="")
    base_url: str = Field(default="https://api.awrcloud.com/v2/get.php")
    
    def __init__(self, api_key: Optional[str] = None, **kwargs):
        from ai_seo_forecasting.tools.awr_tools import get_api_key
        actual_api_key = api_key or get_api_key()
        super().__init__(api_key=actual_api_key, **kwargs)
    
    def _run(self, project: str, days: int = 7, format: str = "csv") -> Dict[str, Any]:
        """Execute the tool to schedule and retrieve rankings data."""
        try:
            # Calculate date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            # Step 1: Schedule the export
            schedule_url = (
                f"{self.base_url}?token={self.api_key}&action=export_ranking"
                f"&project={project}"
                f"&startDate={start_date.strftime('%Y-%m-%d')}"
                f"&stopDate={end_date.strftime('%Y-%m-%d')}"
                f"&format={format}"
                f"&searchEngineId=-1"
                f"&keywordGroupId=-1"
                f"&websiteId=-1"
            )
            
            response = requests.get(schedule_url, headers={"accept": "application/json"}, timeout=30)
            response.raise_for_status()
            
            # Parse the response (might be text, not JSON)
            response_text = response.text
            
            # Try to extract fileName from response
            # Response format: "Export scheduled. fileName: project-name-dates-123"
            file_name = None
            if "fileName" in response_text:
                # Extract fileName from text response
                parts = response_text.split("fileName:")
                if len(parts) > 1:
                    file_name = parts[1].strip().split()[0].strip()
            
            if not file_name:
                return {
                    "success": False,
                    "project_name": project,
                    "error": "Export scheduled but no fileName received. The export may still be processing.",
                    "schedule_response": response_text[:200]
                }
            
            # Step 2: Download the export
            download_url = (
                f"{self.base_url}?token={self.api_key}&action=get_export"
                f"&project={project}"
                f"&fileName={file_name}"
            )
            
            download_response = requests.get(download_url, timeout=60)
            download_response.raise_for_status()
            
            # Parse CSV data
            if format == "csv":
                csv_data = StringIO(download_response.text)
                reader = csv.DictReader(csv_data)
                rankings = list(reader)
                
                return {
                    "success": True,
                    "project_name": project,
                    "date_range": f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}",
                    "days": days,
                    "rankings_count": len(rankings),
                    "rankings": rankings[:100],  # Return first 100 to avoid context overflow
                    "total_rankings": len(rankings),
                    "message": f"Retrieved {len(rankings)} ranking data points. Showing first 100.",
                    "file_name": file_name
                }
            else:
                return {
                    "success": True,
                    "project_name": project,
                    "data": download_response.text[:5000],  # First 5000 chars
                    "message": "Rankings data retrieved in JSON format"
                }
            
        except Exception as e:
            return {
                "success": False,
                "project_name": project,
                "error": f"Failed to retrieve rankings: {str(e)}"
            }


# ============================================================================
# TOOL 5: GET KEYWORD DIFFICULTY
# ============================================================================

class AWRKeywordDifficultyInput(BaseModel):
    """Input schema for AWRKeywordDifficultyTool."""
    project: str = Field(..., description="Project name (e.g., 'pella.com')")
    project_id: str = Field(..., description="Project ID (e.g., '27')")


class AWRKeywordDifficultyTool(BaseTool):
    name: str = "Get AWR Keyword Difficulty"
    description: str = (
        "Retrieves keyword difficulty/competitiveness scores for all keywords in a project. "
        "Difficulty scores help prioritize which keywords to target. "
        "Returns: keyword, difficulty score, competition level. "
        "Use this to identify low-competition, high-value keyword opportunities. "
        "Required: project name AND project ID."
    )
    args_schema: Type[BaseModel] = AWRKeywordDifficultyInput
    
    api_key: str = Field(default="")
    base_url: str = Field(default="https://api.awrcloud.com/v2/get.php")
    
    def __init__(self, api_key: Optional[str] = None, **kwargs):
        from ai_seo_forecasting.tools.awr_tools import get_api_key
        actual_api_key = api_key or get_api_key()
        super().__init__(api_key=actual_api_key, **kwargs)
    
    def _run(self, project: str, project_id: str) -> Dict[str, Any]:
        """Execute the tool to get keyword difficulty data."""
        try:
            url = (
                f"{self.base_url}?token={self.api_key}"
                f"&action=export_keyword_difficulty"
                f"&projectId={project_id}"
                f"&searchEngineId=-1"
                f"&keywordGroupId=-1"
                f"&mode=plain"
            )
            
            response = requests.get(url, timeout=60)
            response.raise_for_status()
            
            # Parse CSV data
            csv_data = StringIO(response.text)
            reader = csv.DictReader(csv_data)
            difficulty_data = list(reader)
            
            # Calculate summary stats
            if difficulty_data:
                difficulties = [float(row.get('Difficulty', 0)) for row in difficulty_data if row.get('Difficulty')]
                avg_difficulty = sum(difficulties) / len(difficulties) if difficulties else 0
                
                # Categorize keywords
                easy = len([d for d in difficulties if d < 30])
                medium = len([d for d in difficulties if 30 <= d < 60])
                hard = len([d for d in difficulties if d >= 60])
            else:
                avg_difficulty = 0
                easy = medium = hard = 0
            
            return {
                "success": True,
                "project_name": project,
                "project_id": project_id,
                "total_keywords": len(difficulty_data),
                "average_difficulty": round(avg_difficulty, 2),
                "difficulty_distribution": {
                    "easy": easy,
                    "medium": medium,
                    "hard": hard
                },
                "keywords": difficulty_data[:50],  # First 50 keywords
                "message": f"Retrieved difficulty scores for {len(difficulty_data)} keywords. Showing first 50."
            }
            
        except Exception as e:
            return {
                "success": False,
                "project_name": project,
                "error": f"Failed to retrieve keyword difficulty: {str(e)}"
            }


# ============================================================================
# TOOL 6: GET SEARCH VOLUME
# ============================================================================

class AWRSearchVolumeInput(BaseModel):
    """Input schema for AWRSearchVolumeTool."""
    project_id: str = Field(..., description="Project ID (e.g., '27')")


class AWRSearchVolumeTool(BaseTool):
    name: str = "Get AWR Search Volume Data"
    description: str = (
        "Retrieves AdWords search volume data for keywords in a project. "
        "Shows monthly search volume estimates for each keyword. "
        "Use this to understand keyword traffic potential and prioritize targets. "
        "Required: project ID."
    )
    args_schema: Type[BaseModel] = AWRSearchVolumeInput
    
    api_key: str = Field(default="")
    base_url: str = Field(default="https://api.awrcloud.com/v2/get.php")
    
    def __init__(self, api_key: Optional[str] = None, **kwargs):
        from ai_seo_forecasting.tools.awr_tools import get_api_key
        actual_api_key = api_key or get_api_key()
        super().__init__(api_key=actual_api_key, **kwargs)
    
    def _run(self, project_id: str) -> Dict[str, Any]:
        """Execute the tool to get search volume data."""
        try:
            url = (
                f"{self.base_url}?token={self.api_key}"
                f"&action=export_search_volume"
                f"&projectId={project_id}"
                f"&dataType=searchVolume"
                f"&keywordGroupIds=-1"
                f"&mode=plain"
            )
            
            response = requests.get(url, timeout=60)
            response.raise_for_status()
            
            # Parse CSV data
            csv_data = StringIO(response.text)
            reader = csv.DictReader(csv_data)
            volume_data = list(reader)
            
            # Calculate summary
            if volume_data:
                volumes = [int(row.get('Searches', 0)) for row in volume_data if row.get('Searches', '').isdigit()]
                total_volume = sum(volumes)
                avg_volume = total_volume / len(volumes) if volumes else 0
            else:
                total_volume = avg_volume = 0
            
            return {
                "success": True,
                "project_id": project_id,
                "total_keywords": len(volume_data),
                "total_monthly_searches": total_volume,
                "average_monthly_searches": round(avg_volume, 0),
                "keywords": volume_data[:50],  # First 50 keywords
                "message": f"Retrieved search volume for {len(volume_data)} keywords. Total monthly searches: {total_volume:,}"
            }
            
        except Exception as e:
            return {
                "success": False,
                "project_id": project_id,
                "error": f"Failed to retrieve search volume: {str(e)}"
            }