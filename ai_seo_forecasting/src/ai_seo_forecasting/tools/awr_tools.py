"""
AWR Cloud API Tools - OPTIMIZED VERSION
Returns compact programmatic summaries and stores raw data to files
"""

import os
import csv
import json
import time
import statistics
from io import StringIO
from pathlib import Path
from typing import Dict, Any, Optional, Type, List
from datetime import datetime

import requests
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()

# Constants
DATA_DIR = Path("knowledge/api_data")
DATA_DIR.mkdir(parents=True, exist_ok=True)


def get_api_key() -> str:
    """Get AWR API key from environment"""
    api_key = os.getenv("AWR_API_KEY")
    if not api_key:
        raise ValueError("AWR_API_KEY not found in environment variables")
    return api_key


def call_awr_api_with_retry(url: str, max_retries: int = 3, timeout: int = 60) -> requests.Response:
    """Call AWR API with retry logic"""
    for attempt in range(max_retries):
        try:
            response = requests.get(url, headers={"accept": "application/json"}, timeout=timeout)
            response.raise_for_status()
            return response
        except requests.Timeout:
            if attempt == max_retries - 1:
                raise
            wait_time = 2 ** attempt
            print(f"⏳ Timeout. Retrying in {wait_time}s... (attempt {attempt + 1}/{max_retries})")
            time.sleep(wait_time)
        except requests.HTTPError:
            raise


def save_data_file(project: str, data_type: str, data: Any, extension: str = "json") -> str:
    """Save data to file and return file path"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{project}_{data_type}_{timestamp}.{extension}"
    filepath = DATA_DIR / filename
    
    if extension == "json":
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
    else:
        with open(filepath, 'w') as f:
            f.write(str(data))
    
    return str(filepath)


def create_metadata(project: str, project_id: str = None) -> dict:
    """Create or update metadata file for a project"""
    metadata_file = DATA_DIR / f"{project}_metadata.json"
    
    if metadata_file.exists():
        with open(metadata_file) as f:
            metadata = json.load(f)
    else:
        metadata = {
            "project": project,
            "project_id": project_id,
            "last_updated": datetime.now().isoformat(),
            "files": {},
            "stats": {}
        }
    
    return metadata


def save_metadata(metadata: dict):
    """Save metadata file"""
    metadata_file = DATA_DIR / f"{metadata['project']}_metadata.json"
    metadata["last_updated"] = datetime.now().isoformat()
    with open(metadata_file, 'w') as f:
        json.dump(metadata, f, indent=2)


# ============================================================================
# TOOL 1: GET ALL PROJECTS (OPTIMIZED)
# ============================================================================

class AWRProjectsInput(BaseModel):
    """Input schema for AWRProjectsTool."""
    pass


class AWRProjectsTool(BaseTool):
    name: str = "Get AWR Projects List"
    description: str = (
        "Retrieves all SEO projects from the AWR Cloud account. "
        "Returns SUMMARY with project counts and top projects by keyword count. "
        "Use this to see what projects are available for analysis."
    )
    args_schema: Type[BaseModel] = AWRProjectsInput
    
    api_key: str = Field(default="")
    base_url: str = Field(default="https://api.awrcloud.com/v2/get.php")
    
    def __init__(self, api_key: Optional[str] = None, **kwargs):
        actual_api_key = api_key or get_api_key()
        super().__init__(api_key=actual_api_key, **kwargs)
    
    def _run(self) -> Dict[str, Any]:
        """Execute the tool to get all projects - returns compact summary"""
        try:
            url = f"{self.base_url}?token={self.api_key}&action=projects"
            response = call_awr_api_with_retry(url, timeout=60)
            data = response.json()
            projects = data.get('projects', [])
            
            # Save raw data
            filepath = save_data_file("all_projects", "list", projects)
            
            # Calculate summary statistics in Python (NO LLM)
            total = len(projects)
            total_keywords = sum(int(p.get('kwcount', 0)) for p in projects)
            avg_keywords = total_keywords / total if total > 0 else 0
            
            # Get top 10 by keyword count
            sorted_projects = sorted(projects, key=lambda x: int(x.get('kwcount', 0)), reverse=True)
            top_10 = [
                {
                    "name": p['name'],
                    "id": p['id'],
                    "keywords": int(p.get('kwcount', 0)),
                    "frequency": p.get('frequency', 'unknown')
                }
                for p in sorted_projects[:10]
            ]
            
            return {
                "success": True,
                "total_projects": total,
                "total_keywords": total_keywords,
                "avg_keywords_per_project": round(avg_keywords, 0),
                "top_10_projects": top_10,
                "data_file": filepath,
                "message": f"Retrieved {total} projects with {total_keywords} total keywords. Data stored in {filepath}"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to retrieve projects: {str(e)}"
            }


# ============================================================================
# TOOL 2: GET PROJECT DETAILS (OPTIMIZED)
# ============================================================================

class AWRProjectDetailsInput(BaseModel):
    """Input schema for AWRProjectDetailsTool."""
    project: str = Field(..., description="Project name (e.g., 'pella.com')")


class AWRProjectDetailsTool(BaseTool):
    name: str = "Get AWR Project Details"
    description: str = (
        "Retrieves detailed configuration for a project. "
        "Returns SUMMARY with keyword groups, competitor counts, tracking info. "
        "Required: project name."
    )
    args_schema: Type[BaseModel] = AWRProjectDetailsInput
    
    api_key: str = Field(default="")
    base_url: str = Field(default="https://api.awrcloud.com/v2/get.php")
    
    def __init__(self, api_key: Optional[str] = None, **kwargs):
        actual_api_key = api_key or get_api_key()
        super().__init__(api_key=actual_api_key, **kwargs)
    
    def _run(self, project: str) -> Dict[str, Any]:
        """Execute the tool to get project details - returns compact summary"""
        try:
            url = f"{self.base_url}?token={self.api_key}&action=details&project={project}"
            response = call_awr_api_with_retry(url, timeout=60)
            data = response.json()
            
            # Extract project ID
            project_id = data.get('project_details', {}).get('id', 'unknown')
            
            # Save raw data
            filepath = save_data_file(project, "details", data)
            
            # Create/update metadata
            metadata = create_metadata(project, project_id)
            metadata['files']['details'] = filepath
            
            # Calculate summary (Python, not LLM)
            keywords = data.get('keywords', [])
            websites = data.get('websites', [])
            
            # Extract keyword groups
            all_groups = set()
            for kw in keywords:
                groups = kw.get('kw_groups', [])
                all_groups.update(groups)
            
            # Project info
            project_info = data.get('project_details', {})
            
            summary = {
                "project_id": project_id,
                "frequency": project_info.get('frequency', 'unknown'),
                "last_updated": project_info.get('last_updated', 'unknown'),
                "total_keywords": len(keywords),
                "total_competitors": len(websites),
                "keyword_groups": list(all_groups),
                "keyword_group_count": len(all_groups)
            }
            
            metadata['stats'].update(summary)
            save_metadata(metadata)
            
            return {
                "success": True,
                "project": project,
                **summary,
                "data_file": filepath,
                "metadata_file": str(DATA_DIR / f"{project}_metadata.json"),
                "message": f"Project has {len(keywords)} keywords, {len(websites)} competitors, tracked {project_info.get('frequency', 'unknown')}"
            }
            
        except Exception as e:
            return {
                "success": False,
                "project": project,
                "error": f"Failed to retrieve project details: {str(e)}"
            }


# ============================================================================
# TOOL 3: GET PROJECT UPDATE DATES (OPTIMIZED)
# ============================================================================

class AWRProjectDatesInput(BaseModel):
    """Input schema for AWRProjectDatesTool."""
    project: str = Field(..., description="Project name (e.g., 'pella.com')")


class AWRProjectDatesTool(BaseTool):
    name: str = "Get AWR Project Update Dates"
    description: str = (
        "Retrieves historical update dates. "
        "Returns SUMMARY with date range and update frequency. "
        "Required: project name."
    )
    args_schema: Type[BaseModel] = AWRProjectDatesInput
    
    api_key: str = Field(default="")
    base_url: str = Field(default="https://api.awrcloud.com/v2/get.php")
    
    def __init__(self, api_key: Optional[str] = None, **kwargs):
        actual_api_key = api_key or get_api_key()
        super().__init__(api_key=actual_api_key, **kwargs)
    
    def _run(self, project: str) -> Dict[str, Any]:
        """Execute the tool to get project dates - returns compact summary"""
        try:
            url = f"{self.base_url}?token={self.api_key}&action=get_dates&project={project}"
            response = call_awr_api_with_retry(url, timeout=60)
            data = response.json()
            dates = data.get('dates', [])
            
            # Save raw data
            filepath = save_data_file(project, "dates", dates)
            
            # Calculate summary
            summary = {
                "total_updates": len(dates),
                "latest_update": dates[0] if dates else None,
                "oldest_update": dates[-1] if dates else None,
                "date_range_days": (
                    (datetime.strptime(dates[0], "%Y-%m-%d") - 
                     datetime.strptime(dates[-1], "%Y-%m-%d")).days
                    if len(dates) > 1 else 0
                )
            }
            
            # Update metadata
            metadata = create_metadata(project)
            metadata['files']['dates'] = filepath
            metadata['stats'].update(summary)
            save_metadata(metadata)
            
            return {
                "success": True,
                "project": project,
                **summary,
                "data_file": filepath,
                "message": f"Found {len(dates)} update dates from {dates[-1] if dates else 'N/A'} to {dates[0] if dates else 'N/A'}"
            }
            
        except Exception as e:
            return {
                "success": False,
                "project": project,
                "error": f"Failed to retrieve dates: {str(e)}"
            }


# ============================================================================
# TOOL 4: GET KEYWORD RANKINGS (OPTIMIZED - CRITICAL)
# ============================================================================

class AWRRankingsInput(BaseModel):
    """Input schema for AWRRankingsTool."""
    project: str = Field(..., description="Project name (e.g., 'pella.com')")
    days: int = Field(default=90, description="Number of days of data (default: 90)")


class AWRRankingsTool(BaseTool):
    name: str = "Get AWR Keyword Rankings"
    description: str = (
        "Retrieves keyword ranking positions - THE MOST CRITICAL SEO DATA. "
        "Returns SUMMARY with position distributions and trends (calculated in Python). "
        "Raw data stored to file for later analysis. "
        "Required: project name. Optional: days (default 90)."
    )
    args_schema: Type[BaseModel] = AWRRankingsInput
    
    api_key: str = Field(default="")
    base_url: str = Field(default="https://api.awrcloud.com/v2/get.php")
    
    def __init__(self, api_key: Optional[str] = None, **kwargs):
        actual_api_key = api_key or get_api_key()
        super().__init__(api_key=actual_api_key, **kwargs)
    
    def _run(self, project: str, days: int = 90) -> Dict[str, Any]:
        """Execute the tool - returns compact summary, stores raw data"""
        try:
            # Step 1: Schedule export
            schedule_url = (
                f"{self.base_url}?token={self.api_key}"
                f"&action=export_ranking"
                f"&project={project}"
                f"&days={days}"
                f"&format=csv"
            )
            
            print(f"📊 Scheduling rankings export for {project}...")
            schedule_response = call_awr_api_with_retry(schedule_url, timeout=60)
            schedule_data = schedule_response.json()
            
            if not schedule_data.get('success'):
                return {
                    "success": False,
                    "error": f"Failed to schedule: {schedule_data.get('message', 'Unknown error')}"
                }
            
            file_name = schedule_data['fileName']
            print(f"⏳ Export scheduled: {file_name}")
            
            # Step 2: Wait and download
            max_wait = 180
            wait_time = 0
            interval = 10
            
            while wait_time < max_wait:
                time.sleep(interval)
                wait_time += interval
                
                download_url = f"{self.base_url}?token={self.api_key}&action=get_export&fileName={file_name}"
                
                try:
                    download_response = call_awr_api_with_retry(download_url, timeout=120)
                    
                    if download_response.status_code == 200:
                        print(f"✅ Rankings data ready!")
                        break
                except:
                    print(f"⏳ Still processing... ({wait_time}s)")
                    continue
            
            # Step 3: Parse CSV and calculate statistics (PYTHON, not LLM)
            csv_content = download_response.text
            csv_data = StringIO(csv_content)
            reader = csv.DictReader(csv_data)
            rankings = list(reader)
            
            # Save raw data
            filepath = save_data_file(project, f"rankings_{days}d", rankings)
            
            # Calculate comprehensive statistics in Python
            positions = []
            changes = []
            keywords_by_position = {
                "top_3": [],
                "positions_4_10": [],
                "positions_11_20": [],
                "positions_21_50": [],
                "beyond_50": []
            }
            
            for row in rankings:
                try:
                    rank = int(row.get('Rank', 0))
                    if rank > 0:
                        positions.append(rank)
                        
                        # Categorize by position
                        keyword = row.get('Keyword', 'unknown')
                        if rank <= 3:
                            keywords_by_position["top_3"].append(keyword)
                        elif rank <= 10:
                            keywords_by_position["positions_4_10"].append(keyword)
                        elif rank <= 20:
                            keywords_by_position["positions_11_20"].append(keyword)
                        elif rank <= 50:
                            keywords_by_position["positions_21_50"].append(keyword)
                        else:
                            keywords_by_position["beyond_50"].append(keyword)
                    
                    # Track changes if available
                    change = row.get('Change', '')
                    if change and change != '-':
                        changes.append(int(change))
                        
                except (ValueError, TypeError):
                    continue
            
            # Calculate summary stats
            summary = {
                "total_rankings": len(rankings),
                "tracked_keywords": len(set(r.get('Keyword', '') for r in rankings)),
                "avg_position": round(statistics.mean(positions), 2) if positions else 0,
                "median_position": round(statistics.median(positions), 1) if positions else 0,
                "top_3_count": len(keywords_by_position["top_3"]),
                "top_10_count": len(keywords_by_position["top_3"]) + len(keywords_by_position["positions_4_10"]),
                "positions_4_10_count": len(keywords_by_position["positions_4_10"]),
                "positions_11_20_count": len(keywords_by_position["positions_11_20"]),
                "positions_21_50_count": len(keywords_by_position["positions_21_50"]),
                "beyond_50_count": len(keywords_by_position["beyond_50"]),
                "improved_count": len([c for c in changes if c > 0]),
                "declined_count": len([c for c in changes if c < 0]),
                "stable_count": len([c for c in changes if c == 0]),
                "avg_change": round(statistics.mean(changes), 2) if changes else 0
            }
            
            # Update metadata
            metadata = create_metadata(project)
            metadata['files'][f'rankings_{days}d'] = filepath
            metadata['stats'].update(summary)
            save_metadata(metadata)
            
            return {
                "success": True,
                "project": project,
                "days": days,
                **summary,
                "data_file": filepath,
                "metadata_file": str(DATA_DIR / f"{project}_metadata.json"),
                "message": (
                    f"Rankings: {summary['tracked_keywords']} keywords, "
                    f"avg position {summary['avg_position']}, "
                    f"{summary['top_10_count']} in top 10, "
                    f"{summary['improved_count']} improved"
                )
            }
            
        except Exception as e:
            return {
                "success": False,
                "project": project,
                "error": f"Failed to retrieve rankings: {str(e)}"
            }


# ============================================================================
# TOOL 5: GET KEYWORD DIFFICULTY (OPTIMIZED)
# ============================================================================

class AWRKeywordDifficultyInput(BaseModel):
    """Input schema for AWRKeywordDifficultyTool."""
    project: str = Field(..., description="Project name (e.g., 'pella.com')")
    project_id: str = Field(..., description="Project ID (e.g., '27')")


class AWRKeywordDifficultyTool(BaseTool):
    name: str = "Get AWR Keyword Difficulty"
    description: str = (
        "Retrieves keyword difficulty/competitiveness scores. "
        "Returns SUMMARY with difficulty distribution (calculated in Python). "
        "Required: project name AND project ID."
    )
    args_schema: Type[BaseModel] = AWRKeywordDifficultyInput
    
    api_key: str = Field(default="")
    base_url: str = Field(default="https://api.awrcloud.com/v2/get.php")
    
    def __init__(self, api_key: Optional[str] = None, **kwargs):
        actual_api_key = api_key or get_api_key()
        super().__init__(api_key=actual_api_key, **kwargs)
    
    def _run(self, project: str, project_id: str) -> Dict[str, Any]:
        """Execute the tool - returns compact summary"""
        try:
            url = (
                f"{self.base_url}?token={self.api_key}"
                f"&action=export_keyword_difficulty"
                f"&projectId={project_id}"
                f"&mode=plain"
            )
            
            print(f"🎯 Fetching keyword difficulty data...")
            response = call_awr_api_with_retry(url, timeout=120)
            
            # Parse CSV
            csv_data = StringIO(response.text)
            reader = csv.DictReader(csv_data)
            difficulty_data = list(reader)
            
            # Save raw data
            filepath = save_data_file(project, "difficulty", difficulty_data)
            
            # Calculate statistics (Python)
            difficulties = []
            difficulty_categories = {
                "easy": [],  # 0-30
                "medium": [],  # 31-60
                "hard": [],  # 61-80
                "very_hard": []  # 81-100
            }
            
            for row in difficulty_data:
                try:
                    diff = int(row.get('Difficulty', 0))
                    if 0 <= diff <= 100:
                        difficulties.append(diff)
                        keyword = row.get('Keyword', 'unknown')
                        
                        if diff <= 30:
                            difficulty_categories["easy"].append(keyword)
                        elif diff <= 60:
                            difficulty_categories["medium"].append(keyword)
                        elif diff <= 80:
                            difficulty_categories["hard"].append(keyword)
                        else:
                            difficulty_categories["very_hard"].append(keyword)
                except (ValueError, TypeError):
                    continue
            
            summary = {
                "total_keywords": len(difficulty_data),
                "avg_difficulty": round(statistics.mean(difficulties), 1) if difficulties else 0,
                "median_difficulty": round(statistics.median(difficulties), 1) if difficulties else 0,
                "easy_count": len(difficulty_categories["easy"]),
                "medium_count": len(difficulty_categories["medium"]),
                "hard_count": len(difficulty_categories["hard"]),
                "very_hard_count": len(difficulty_categories["very_hard"]),
                "opportunities": len(difficulty_categories["easy"])  # Easy keywords = opportunities
            }
            
            # Update metadata
            metadata = create_metadata(project, project_id)
            metadata['files']['difficulty'] = filepath
            metadata['stats'].update(summary)
            save_metadata(metadata)
            
            return {
                "success": True,
                "project": project,
                **summary,
                "data_file": filepath,
                "message": (
                    f"Difficulty: avg {summary['avg_difficulty']}/100, "
                    f"{summary['easy_count']} easy opportunities, "
                    f"{summary['hard_count'] + summary['very_hard_count']} challenging"
                )
            }
            
        except Exception as e:
            return {
                "success": False,
                "project": project,
                "error": f"Failed to retrieve difficulty: {str(e)}"
            }


# ============================================================================
# TOOL 6: GET SEARCH VOLUME (OPTIMIZED)
# ============================================================================

class AWRSearchVolumeInput(BaseModel):
    """Input schema for AWRSearchVolumeTool."""
    project_id: str = Field(..., description="Project ID (e.g., '27')")


class AWRSearchVolumeTool(BaseTool):
    name: str = "Get AWR Search Volume Data"
    description: str = (
        "Retrieves monthly search volume data. "
        "Returns SUMMARY with volume distribution (calculated in Python). "
        "Required: project ID."
    )
    args_schema: Type[BaseModel] = AWRSearchVolumeInput
    
    api_key: str = Field(default="")
    base_url: str = Field(default="https://api.awrcloud.com/v2/get.php")
    
    def __init__(self, api_key: Optional[str] = None, **kwargs):
        actual_api_key = api_key or get_api_key()
        super().__init__(api_key=actual_api_key, **kwargs)
    
    def _run(self, project_id: str) -> Dict[str, Any]:
        """Execute the tool - returns compact summary"""
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
            response = call_awr_api_with_retry(url, timeout=180)
            
            # Parse CSV
            csv_data = StringIO(response.text)
            reader = csv.DictReader(csv_data)
            volume_data = list(reader)
            
            # Save raw data
            filepath = save_data_file(f"project_{project_id}", "volume", volume_data)
            
            # Calculate statistics (Python)
            volumes = []
            volume_categories = {
                "high_volume": [],  # >10k/month
                "medium_volume": [],  # 1k-10k/month
                "low_volume": [],  # 100-1k/month
                "very_low_volume": []  # <100/month
            }
            
            for row in volume_data:
                try:
                    vol = int(row.get('Searches', 0))
                    if vol >= 0:
                        volumes.append(vol)
                        keyword = row.get('Keyword', 'unknown')
                        
                        if vol > 10000:
                            volume_categories["high_volume"].append(keyword)
                        elif vol > 1000:
                            volume_categories["medium_volume"].append(keyword)
                        elif vol > 100:
                            volume_categories["low_volume"].append(keyword)
                        else:
                            volume_categories["very_low_volume"].append(keyword)
                except (ValueError, TypeError):
                    continue
            
            summary = {
                "total_keywords": len(volume_data),
                "total_monthly_searches": sum(volumes),
                "avg_monthly_searches": round(statistics.mean(volumes), 0) if volumes else 0,
                "median_monthly_searches": round(statistics.median(volumes), 0) if volumes else 0,
                "high_volume_count": len(volume_categories["high_volume"]),
                "medium_volume_count": len(volume_categories["medium_volume"]),
                "low_volume_count": len(volume_categories["low_volume"]),
                "very_low_volume_count": len(volume_categories["very_low_volume"])
            }
            
            # Update metadata
            metadata = create_metadata(f"project_{project_id}", project_id)
            metadata['files']['volume'] = filepath
            metadata['stats'].update(summary)
            save_metadata(metadata)
            
            return {
                "success": True,
                "project_id": project_id,
                **summary,
                "data_file": filepath,
                "message": (
                    f"Volume: {summary['total_monthly_searches']:,} total searches/month, "
                    f"{summary['high_volume_count']} high-volume keywords (>10k)"
                )
            }
            
        except Exception as e:
            return {
                "success": False,
                "project_id": project_id,
                "error": f"Failed to retrieve volume: {str(e)}"
            }