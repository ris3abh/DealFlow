"""
Advanced Web Ranking (AWR) API Tools
Consolidated tools for all AWR Cloud API endpoints
"""

import os
import requests
from typing import Type, Optional, Dict, Any
from pydantic import BaseModel, Field
from crewai.tools import BaseTool


# ============================================================================
# BASE CONFIGURATION
# ============================================================================

AWR_BASE_URL = "https://api.awrcloud.com/v2/get.php"


def get_api_key() -> str:
    """Get AWR API key from environment"""
    api_key = os.getenv("AWR_API_KEY")
    if not api_key:
        raise ValueError(
            "AWR API key is required. Set AWR_API_KEY environment variable."
        )
    return api_key


# ============================================================================
# TOOL 1: GET ALL PROJECTS
# ============================================================================

class AWRProjectsInput(BaseModel):
    """Input schema for AWRProjectsTool."""
    pass


class AWRProjectsTool(BaseTool):
    name: str = "Get AWR Projects"
    description: str = (
        "Retrieves all projects from your Advanced Web Ranking (AWR) account. "
        "Returns project details including name, ID, tracking frequency, depth, "
        "keyword count, main website URL, and last update timestamp. "
        "Use this tool when you need to list all available SEO projects or "
        "find a specific project ID for further analysis."
    )
    args_schema: Type[BaseModel] = AWRProjectsInput
    
    api_key: str = Field(default="")
    base_url: str = Field(default=AWR_BASE_URL)
    
    def __init__(self, api_key: Optional[str] = None, **kwargs):
        actual_api_key = api_key or get_api_key()
        super().__init__(api_key=actual_api_key, **kwargs)
    
    def _run(self) -> Dict[str, Any]:
        """Execute the tool to fetch AWR projects."""
        try:
            url = f"{self.base_url}?token={self.api_key}&action=projects"
            headers = {"accept": "application/json"}
            
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            projects = data.get("projects", [])
            
            return {
                "success": True,
                "projects": projects,
                "project_count": len(projects),
                "message": f"Successfully retrieved {len(projects)} projects"
            }
            
        except requests.exceptions.Timeout:
            return {
                "success": False,
                "projects": [],
                "project_count": 0,
                "error": "Request timed out. Please try again."
            }
            
        except requests.exceptions.HTTPError as e:
            return self._handle_http_error(e, "retrieving projects")
            
        except Exception as e:
            return {
                "success": False,
                "projects": [],
                "project_count": 0,
                "error": f"Unexpected error: {str(e)}"
            }
    
    def _handle_http_error(self, error, action):
        """Common HTTP error handling"""
        status_code = error.response.status_code
        error_msg = f"HTTP {status_code} error"
        
        if status_code == 401:
            error_msg = "Authentication failed. Check your API key."
        elif status_code == 403:
            error_msg = "Access forbidden. Verify your API permissions."
        elif status_code == 404:
            error_msg = f"Not found while {action}."
        elif status_code == 429:
            error_msg = "Rate limit exceeded. Please wait before retrying."
        elif status_code >= 500:
            error_msg = "AWR server error. Please try again later."
        
        return {
            "success": False,
            "error": error_msg
        }


# ============================================================================
# TOOL 2: GET PROJECT DETAILS
# ============================================================================

class AWRProjectDetailsInput(BaseModel):
    """Input schema for AWRProjectDetailsTool."""
    project: str = Field(..., description="The name or ID of the project")


class AWRProjectDetailsTool(BaseTool):
    name: str = "Get AWR Project Details"
    description: str = (
        "Retrieves comprehensive details about a specific AWR project including: "
        "project configuration, tracked websites, complete keyword list, "
        "search engines being monitored, and geographic locations. "
        "Use this when you need in-depth information about a specific project. "
        "Required input: project name or ID."
    )
    args_schema: Type[BaseModel] = AWRProjectDetailsInput
    
    api_key: str = Field(default="")
    base_url: str = Field(default=AWR_BASE_URL)
    
    def __init__(self, api_key: Optional[str] = None, **kwargs):
        actual_api_key = api_key or get_api_key()
        super().__init__(api_key=actual_api_key, **kwargs)
    
    def _run(self, project: str) -> Dict[str, Any]:
        """Execute the tool to fetch detailed project information."""
        try:
            url = f"{self.base_url}?token={self.api_key}&action=details&project={project}"
            headers = {"accept": "application/json"}
            
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            # Extract key information
            details = data.get("details", {})
            websites = data.get("websites", [])
            keywords = data.get("keywords", [])
            search_engines = data.get("search_engines", [])
            locations = data.get("locations", [])
            
            return {
                "success": True,
                "project_name": project,
                "details": details,
                "websites": websites,
                "keywords": keywords,
                "search_engines": search_engines,
                "locations": locations,
                "keyword_count": len(keywords),
                "website_count": len(websites),
                "search_engine_count": len(search_engines),
                "location_count": len(locations),
                "message": f"Successfully retrieved details for project: {project}"
            }
            
        except requests.exceptions.Timeout:
            return {
                "success": False,
                "project_name": project,
                "error": "Request timed out. Please try again."
            }
            
        except requests.exceptions.HTTPError as e:
            return self._handle_http_error(e, project)
            
        except Exception as e:
            return {
                "success": False,
                "project_name": project,
                "error": f"Unexpected error: {str(e)}"
            }
    
    def _handle_http_error(self, error, project):
        """HTTP error handling for project details"""
        status_code = error.response.status_code
        error_msg = f"HTTP {status_code} error"
        
        if status_code == 401:
            error_msg = "Authentication failed. Check your API key."
        elif status_code == 403:
            error_msg = "Access forbidden. Verify your API permissions."
        elif status_code == 404:
            error_msg = f"Project '{project}' not found. Check the project name."
        elif status_code == 429:
            error_msg = "Rate limit exceeded. Please wait before retrying."
        elif status_code >= 500:
            error_msg = "AWR server error. Please try again later."
        
        return {
            "success": False,
            "project_name": project,
            "error": error_msg
        }


# ============================================================================
# TOOL 3: GET PROJECT UPDATE DATES
# ============================================================================

class AWRProjectDatesInput(BaseModel):
    """Input schema for AWRProjectDatesTool."""
    project: str = Field(..., description="The name or ID of the project")


class AWRProjectDatesTool(BaseTool):
    name: str = "Get AWR Project Update Dates"
    description: str = (
        "Retrieves all dates on which a specific AWR project was updated. "
        "This is useful for understanding tracking history, identifying data gaps, "
        "and determining the time range available for analysis. "
        "Returns a chronological list of all update timestamps. "
        "Required input: project name or ID."
    )
    args_schema: Type[BaseModel] = AWRProjectDatesInput
    
    api_key: str = Field(default="")
    base_url: str = Field(default=AWR_BASE_URL)
    
    def __init__(self, api_key: Optional[str] = None, **kwargs):
        actual_api_key = api_key or get_api_key()
        super().__init__(api_key=actual_api_key, **kwargs)
    
    def _run(self, project: str) -> Dict[str, Any]:
        """Execute the tool to fetch project update dates."""
        try:
            url = f"{self.base_url}?token={self.api_key}&action=get_dates&project={project}"
            headers = {"accept": "application/json"}
            
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            dates = data.get("dates", [])
            
            # Calculate metadata
            date_count = len(dates)
            first_update = dates[0] if dates else None
            last_update = dates[-1] if dates else None
            
            return {
                "success": True,
                "project_name": project,
                "dates": dates,
                "date_count": date_count,
                "first_update": first_update,
                "last_update": last_update,
                "message": f"Successfully retrieved {date_count} update dates for project: {project}"
            }
            
        except requests.exceptions.Timeout:
            return {
                "success": False,
                "project_name": project,
                "error": "Request timed out. Please try again."
            }
            
        except requests.exceptions.HTTPError as e:
            return self._handle_http_error(e, project)
            
        except Exception as e:
            return {
                "success": False,
                "project_name": project,
                "error": f"Unexpected error: {str(e)}"
            }
    
    def _handle_http_error(self, error, project):
        """HTTP error handling for project dates"""
        status_code = error.response.status_code
        error_msg = f"HTTP {status_code} error"
        
        if status_code == 401:
            error_msg = "Authentication failed. Check your API key."
        elif status_code == 403:
            error_msg = "Access forbidden. Verify your API permissions."
        elif status_code == 404:
            error_msg = f"Project '{project}' not found. Check the project name."
        elif status_code == 429:
            error_msg = "Rate limit exceeded. Please wait before retrying."
        elif status_code >= 500:
            error_msg = "AWR server error. Please try again later."
        
        return {
            "success": False,
            "project_name": project,
            "error": error_msg
        }


# ============================================================================
# FUTURE TOOLS - Add more AWR API endpoints here as needed
# ============================================================================

# TODO: Add AWRRankingsTool for get_ranks
# TODO: Add AWRKeywordsTool for keyword-specific data
# TODO: Add AWRCompetitorsTool for competitor analysis