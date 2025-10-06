"""
Complete AWR API Tools with All Endpoints and Error Handling
Includes fixes for timeouts, fileName parsing, and retry logic
"""

import os
import requests
from typing import Type, Optional, Dict, Any
from pydantic import BaseModel, Field
from crewai.tools import BaseTool
from datetime import datetime, timedelta
import csv
from io import StringIO
import time


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_api_key() -> str:
    """Get API key from environment variable"""
    api_key = os.getenv("AWR_API_KEY")
    if not api_key:
        raise ValueError("AWR_API_KEY not found in environment variables")
    return api_key


def call_awr_api_with_retry(url: str, max_retries: int = 3, timeout: int = 180) -> requests.Response:
    """
    Call AWR API with retry logic for timeout and connection errors
    
    Args:
        url: API endpoint URL
        max_retries: Maximum number of retry attempts
        timeout: Request timeout in seconds
    
    Returns:
        Response object
    """
    for attempt in range(max_retries):
        try:
            response = requests.get(url, headers={"accept": "application/json"}, timeout=timeout)
            response.raise_for_status()
            return response
        except (requests.Timeout, requests.ConnectionError) as e:
            if attempt < max_retries - 1:
                wait_time = (attempt + 1) * 5  # Exponential backoff: 5s, 10s, 15s
                print(f"⚠️ API call timeout/error. Retrying in {wait_time}s... (attempt {attempt + 1}/{max_retries})")
                time.sleep(wait_time)
                continue
            raise
        except requests.HTTPError as e:
            # Don't retry on HTTP errors (4xx, 5xx)
            raise


# ============================================================================
# TOOL 1: GET ALL PROJECTS (EXISTING - IMPROVED)
# ============================================================================

class AWRProjectsInput(BaseModel):
    """Input schema for AWRProjectsTool."""
    pass


class AWRProjectsTool(BaseTool):
    name: str = "Get AWR Projects List"
    description: str = (
        "Retrieves all SEO projects from the AWR Cloud account. "
        "Returns project names, IDs, tracking frequencies, keyword counts, and websites. "
        "Use this to see what projects are available for analysis."
    )
    args_schema: Type[BaseModel] = AWRProjectsInput
    
    api_key: str = Field(default="")
    base_url: str = Field(default="https://api.awrcloud.com/v2/get.php")
    
    def __init__(self, api_key: Optional[str] = None, **kwargs):
        actual_api_key = api_key or get_api_key()
        super().__init__(api_key=actual_api_key, **kwargs)
    
    def _run(self) -> Dict[str, Any]:
        """Execute the tool to get all projects."""
        try:
            url = f"{self.base_url}?token={self.api_key}&action=projects"
            response = call_awr_api_with_retry(url, timeout=60)
            
            data = response.json()
            projects = data.get('projects', [])
            
            return {
                "success": True,
                "total_projects": len(projects),
                "projects": projects,
                "message": f"Retrieved {len(projects)} AWR projects successfully"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to retrieve projects: {str(e)}"
            }


# ============================================================================
# TOOL 2: GET PROJECT DETAILS (EXISTING - IMPROVED)
# ============================================================================

class AWRProjectDetailsInput(BaseModel):
    """Input schema for AWRProjectDetailsTool."""
    project: str = Field(..., description="Project name (e.g., 'pella.com')")


class AWRProjectDetailsTool(BaseTool):
    name: str = "Get AWR Project Details"
    description: str = (
        "Retrieves detailed information about a specific AWR project. "
        "Returns keywords, search engines, locations, tracking frequency, and more. "
        "Required: project name."
    )
    args_schema: Type[BaseModel] = AWRProjectDetailsInput
    
    api_key: str = Field(default="")
    base_url: str = Field(default="https://api.awrcloud.com/v2/get.php")
    
    def __init__(self, api_key: Optional[str] = None, **kwargs):
        actual_api_key = api_key or get_api_key()
        super().__init__(api_key=actual_api_key, **kwargs)
    
    def _run(self, project: str) -> Dict[str, Any]:
        """Execute the tool to get project details."""
        try:
            url = f"{self.base_url}?token={self.api_key}&action=details&project={project}"
            response = call_awr_api_with_retry(url, timeout=60)
            
            data = response.json()
            
            return {
                "success": True,
                "project_name": project,
                "details": data,
                "message": f"Retrieved details for project '{project}'"
            }
            
        except Exception as e:
            return {
                "success": False,
                "project_name": project,
                "error": f"Failed to retrieve project details: {str(e)}"
            }


# ============================================================================
# TOOL 3: GET PROJECT UPDATE DATES (EXISTING - IMPROVED)
# ============================================================================

class AWRProjectDatesInput(BaseModel):
    """Input schema for AWRProjectDatesTool."""
    project: str = Field(..., description="Project name (e.g., 'pella.com')")


class AWRProjectDatesTool(BaseTool):
    name: str = "Get AWR Project Update Dates"
    description: str = (
        "Retrieves all historical update dates for a project's ranking data. "
        "Shows when rankings were tracked. Use this to understand data availability. "
        "Required: project name."
    )
    args_schema: Type[BaseModel] = AWRProjectDatesInput
    
    api_key: str = Field(default="")
    base_url: str = Field(default="https://api.awrcloud.com/v2/get.php")
    
    def __init__(self, api_key: Optional[str] = None, **kwargs):
        actual_api_key = api_key or get_api_key()
        super().__init__(api_key=actual_api_key, **kwargs)
    
    def _run(self, project: str) -> Dict[str, Any]:
        """Execute the tool to get project update dates."""
        try:
            url = f"{self.base_url}?token={self.api_key}&action=get_dates&project={project}"
            response = call_awr_api_with_retry(url, timeout=60)
            
            data = response.json()
            dates = data.get('dates', [])
            
            return {
                "success": True,
                "project_name": project,
                "total_dates": len(dates),
                "dates": dates,
                "latest_date": dates[0] if dates else None,
                "message": f"Retrieved {len(dates)} update dates for project '{project}'"
            }
            
        except Exception as e:
            return {
                "success": False,
                "project_name": project,
                "error": f"Failed to retrieve project dates: {str(e)}"
            }


# ============================================================================
# TOOL 4: GET KEYWORD RANKINGS (NEW - FIXED)
# ============================================================================

class AWRRankingsInput(BaseModel):
    """Input schema for AWRRankingsTool."""
    project: str = Field(..., description="Project name (e.g., 'pella.com')")
    days: int = Field(default=90, description="Number of days of data to retrieve (default: 90)")
    format: str = Field(default="csv", description="Format: csv or json")


class AWRRankingsTool(BaseTool):
    name: str = "Get AWR Keyword Rankings"
    description: str = (
        "Retrieves actual keyword ranking positions over time - THE MOST CRITICAL SEO DATA. "
        "Returns rankings for all keywords across all search engines and dates. "
        "This data shows: keyword, date, rank position, URL, search engine, location. "
        "Use this for SEO performance analysis and tracking ranking changes. "
        "Required: project name. Optional: days (default 90)."
    )
    args_schema: Type[BaseModel] = AWRRankingsInput
    
    api_key: str = Field(default="")
    base_url: str = Field(default="https://api.awrcloud.com/v2/get.php")
    
    def __init__(self, api_key: Optional[str] = None, **kwargs):
        actual_api_key = api_key or get_api_key()
        super().__init__(api_key=actual_api_key, **kwargs)
    
    def _run(self, project: str, days: int = 90, format: str = "csv") -> Dict[str, Any]:
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
            
            print(f"📊 Scheduling rankings export for {project} ({days} days)...")
            response = call_awr_api_with_retry(schedule_url, timeout=60)
            
            # IMPROVED: Better fileName extraction
            file_name = None
            try:
                # Try JSON response first
                data = response.json()
                
                # Check 'details' field which contains the download URL
                if 'details' in data and isinstance(data['details'], str):
                    if 'fileName=' in data['details']:
                        file_name = data['details'].split('fileName=')[-1].split('&')[0]
                
                # Fallback: check direct fileName field
                if not file_name and 'fileName' in data:
                    file_name = data['fileName']
                    
            except:
                # Fallback: try text parsing
                response_text = response.text
                if "fileName" in response_text:
                    # Try multiple parsing patterns
                    if "fileName:" in response_text:
                        file_name = response_text.split("fileName:")[-1].strip().split()[0]
                    elif "fileName=" in response_text:
                        file_name = response_text.split("fileName=")[-1].split()[0].split('&')[0]
            
            if not file_name:
                return {
                    "success": False,
                    "project_name": project,
                    "error": "Export scheduled but fileName not found in response. The export may be processing.",
                    "raw_response": response.text[:500]
                }
            
            print(f"✓ Export scheduled. FileName: {file_name}")
            print(f"⏳ Waiting for export to complete...")
            
            # Wait for export to complete (increased wait time for large projects)
            time.sleep(10)
            
            # Step 2: Download the export with retry
            download_url = (
                f"{self.base_url}?token={self.api_key}&action=get_export"
                f"&project={project}"
                f"&fileName={file_name}"
            )
            
            print(f"⬇️ Downloading rankings data...")
            download_response = call_awr_api_with_retry(download_url, timeout=180)
            
            # Parse data based on format
            if format == "csv":
                csv_data = StringIO(download_response.text)
                reader = csv.DictReader(csv_data)
                rankings = list(reader)
                
                print(f"✓ Retrieved {len(rankings)} ranking data points")
                
                return {
                    "success": True,
                    "project_name": project,
                    "date_range": f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}",
                    "days": days,
                    "rankings_count": len(rankings),
                    "rankings": rankings[:100],  # Return first 100
                    "total_rankings": len(rankings),
                    "message": f"Retrieved {len(rankings)} ranking data points. Showing first 100.",
                    "file_name": file_name
                }
            else:
                return {
                    "success": True,
                    "project_name": project,
                    "data": download_response.text[:5000],
                    "message": "Rankings data retrieved in JSON format"
                }
            
        except Exception as e:
            return {
                "success": False,
                "project_name": project,
                "error": f"Failed to retrieve rankings: {str(e)}"
            }


# ============================================================================
# TOOL 5: GET KEYWORD DIFFICULTY (NEW - FIXED)
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
            
            print(f"📊 Fetching keyword difficulty for {project}...")
            response = call_awr_api_with_retry(url, timeout=180)  # Increased timeout
            
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
            
            print(f"✓ Retrieved difficulty scores for {len(difficulty_data)} keywords")
            
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
                "keywords": difficulty_data[:50],  # First 50
                "message": f"Retrieved difficulty scores for {len(difficulty_data)} keywords. Showing first 50."
            }
            
        except Exception as e:
            return {
                "success": False,
                "project_name": project,
                "error": f"Failed to retrieve keyword difficulty: {str(e)}"
            }


# ============================================================================
# TOOL 6: GET SEARCH VOLUME (NEW - FIXED)
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
            
            print(f"📊 Fetching search volume data...")
            response = call_awr_api_with_retry(url, timeout=180)  # Increased timeout
            
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
            
            print(f"✓ Retrieved search volume for {len(volume_data)} keywords")
            
            return {
                "success": True,
                "project_id": project_id,
                "total_keywords": len(volume_data),
                "total_monthly_searches": total_volume,
                "average_monthly_searches": round(avg_volume, 0),
                "keywords": volume_data[:50],  # First 50
                "message": f"Retrieved search volume for {len(volume_data)} keywords. Total monthly searches: {total_volume:,}"
            }
            
        except Exception as e:
            return {
                "success": False,
                "project_id": project_id,
                "error": f"Failed to retrieve search volume: {str(e)}"
            }