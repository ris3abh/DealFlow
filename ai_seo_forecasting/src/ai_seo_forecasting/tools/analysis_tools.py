"""
Analysis Helper Tools
Query stored AWR data files for specific analysis questions
"""

import json
from pathlib import Path
from typing import Dict, Any, Type, List
from crewai.tools import BaseTool
from pydantic import BaseModel, Field


DATA_DIR = Path("knowledge/api_data")


class QueryMetadataInput(BaseModel):
    """Input schema for QueryMetadataTool."""
    project: str = Field(..., description="Project name (e.g., 'pella.com')")


class QueryMetadataTool(BaseTool):
    name: str = "Query Project Metadata"
    description: str = (
        "Read metadata file to see what data is available for a project. "
        "Returns: files stored, collection stats, data types available. "
        "Use this FIRST before other analysis tools."
    )
    args_schema: Type[BaseModel] = QueryMetadataInput
    
    def _run(self, project: str) -> Dict[str, Any]:
        """Read metadata file"""
        try:
            metadata_file = DATA_DIR / f"{project}_metadata.json"
            
            if not metadata_file.exists():
                return {
                    "success": False,
                    "project": project,
                    "error": f"No metadata found for {project}. Run data collection first."
                }
            
            with open(metadata_file) as f:
                metadata = json.load(f)
            
            return {
                "success": True,
                "project": project,
                **metadata,
                "message": f"Metadata loaded. Available files: {', '.join(metadata.get('files', {}).keys())}"
            }
            
        except Exception as e:
            return {
                "success": False,
                "project": project,
                "error": f"Failed to read metadata: {str(e)}"
            }


class QueryKeywordsByPositionInput(BaseModel):
    """Input schema for QueryKeywordsByPositionTool."""
    project: str = Field(..., description="Project name (e.g., 'pella.com')")
    min_position: int = Field(..., description="Minimum position (e.g., 4)")
    max_position: int = Field(..., description="Maximum position (e.g., 10)")
    limit: int = Field(default=20, description="Max keywords to return (default: 20)")


class QueryKeywordsByPositionTool(BaseTool):
    name: str = "Query Keywords by Position Range"
    description: str = (
        "Get keywords within a specific position range (e.g., positions 4-10). "
        "Returns: keyword name, current position, URL, change. "
        "Use for analyzing near-top opportunities or specific position segments."
    )
    args_schema: Type[BaseModel] = QueryKeywordsByPositionInput
    
    def _run(self, project: str, min_position: int, max_position: int, limit: int = 20) -> Dict[str, Any]:
        """Query rankings data for specific position range"""
        try:
            # Find most recent rankings file
            metadata_file = DATA_DIR / f"{project}_metadata.json"
            if not metadata_file.exists():
                return {"success": False, "error": "No metadata found. Run data collection first."}
            
            with open(metadata_file) as f:
                metadata = json.load(f)
            
            # Find rankings file
            rankings_files = {k: v for k, v in metadata.get('files', {}).items() if 'rankings' in k}
            if not rankings_files:
                return {"success": False, "error": "No rankings data found."}
            
            # Use most recent rankings file
            rankings_file = list(rankings_files.values())[0]
            
            with open(rankings_file) as f:
                rankings = json.load(f)
            
            # Filter by position range
            filtered = [
                {
                    "keyword": r.get('Keyword', ''),
                    "position": int(r.get('Rank', 0)),
                    "url": r.get('URL', ''),
                    "change": r.get('Change', '-'),
                    "search_engine": r.get('Search Engine', '')
                }
                for r in rankings
                if min_position <= int(r.get('Rank', 0)) <= max_position
            ][:limit]
            
            return {
                "success": True,
                "project": project,
                "position_range": f"{min_position}-{max_position}",
                "total_found": len(filtered),
                "keywords": filtered,
                "message": f"Found {len(filtered)} keywords in positions {min_position}-{max_position}"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to query rankings: {str(e)}"
            }


class QueryLowDifficultyKeywordsInput(BaseModel):
    """Input schema for QueryLowDifficultyKeywordsTool."""
    project: str = Field(..., description="Project name (e.g., 'pella.com')")
    max_difficulty: int = Field(default=30, description="Max difficulty score (0-100, default: 30)")
    limit: int = Field(default=20, description="Max keywords to return (default: 20)")


class QueryLowDifficultyKeywordsTool(BaseTool):
    name: str = "Query Low Difficulty Keywords"
    description: str = (
        "Get keywords with low competition (easy opportunities). "
        "Returns: keyword, difficulty score, search volume if available. "
        "Use for identifying quick-win keyword targets."
    )
    args_schema: Type[BaseModel] = QueryLowDifficultyKeywordsInput
    
    def _run(self, project: str, max_difficulty: int = 30, limit: int = 20) -> Dict[str, Any]:
        """Query difficulty data for low-competition keywords"""
        try:
            # Find difficulty file
            metadata_file = DATA_DIR / f"{project}_metadata.json"
            if not metadata_file.exists():
                return {"success": False, "error": "No metadata found. Run data collection first."}
            
            with open(metadata_file) as f:
                metadata = json.load(f)
            
            difficulty_file = metadata.get('files', {}).get('difficulty')
            if not difficulty_file:
                return {"success": False, "error": "No difficulty data found."}
            
            with open(difficulty_file) as f:
                difficulty_data = json.load(f)
            
            # Filter by difficulty
            filtered = [
                {
                    "keyword": r.get('Keyword', ''),
                    "difficulty": int(r.get('Difficulty', 0)),
                    "competition": "Easy"
                }
                for r in difficulty_data
                if 0 <= int(r.get('Difficulty', 0)) <= max_difficulty
            ][:limit]
            
            return {
                "success": True,
                "project": project,
                "max_difficulty": max_difficulty,
                "total_found": len(filtered),
                "keywords": filtered,
                "message": f"Found {len(filtered)} keywords with difficulty ≤ {max_difficulty}"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to query difficulty: {str(e)}"
            }


class QueryHighVolumeKeywordsInput(BaseModel):
    """Input schema for QueryHighVolumeKeywordsTool."""
    project_id: str = Field(..., description="Project ID (e.g., '27')")
    min_volume: int = Field(default=1000, description="Min monthly searches (default: 1000)")
    limit: int = Field(default=20, description="Max keywords to return (default: 20)")


class QueryHighVolumeKeywordsTool(BaseTool):
    name: str = "Query High Volume Keywords"
    description: str = (
        "Get keywords with high search volume (traffic potential). "
        "Returns: keyword, monthly searches. "
        "Use for identifying high-impact keyword targets."
    )
    args_schema: Type[BaseModel] = QueryHighVolumeKeywordsInput
    
    def _run(self, project_id: str, min_volume: int = 1000, limit: int = 20) -> Dict[str, Any]:
        """Query volume data for high-traffic keywords"""
        try:
            # Find volume file
            project_name = f"project_{project_id}"
            metadata_file = DATA_DIR / f"{project_name}_metadata.json"
            if not metadata_file.exists():
                return {"success": False, "error": "No metadata found. Run data collection first."}
            
            with open(metadata_file) as f:
                metadata = json.load(f)
            
            volume_file = metadata.get('files', {}).get('volume')
            if not volume_file:
                return {"success": False, "error": "No volume data found."}
            
            with open(volume_file) as f:
                volume_data = json.load(f)
            
            # Filter by volume
            filtered = [
                {
                    "keyword": r.get('Keyword', ''),
                    "monthly_searches": int(r.get('Searches', 0))
                }
                for r in volume_data
                if int(r.get('Searches', 0)) >= min_volume
            ]
            
            # Sort by volume descending
            filtered = sorted(filtered, key=lambda x: x['monthly_searches'], reverse=True)[:limit]
            
            return {
                "success": True,
                "project_id": project_id,
                "min_volume": min_volume,
                "total_found": len(filtered),
                "keywords": filtered,
                "message": f"Found {len(filtered)} keywords with {min_volume}+ monthly searches"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to query volume: {str(e)}"
            }


class CrossReferenceOpportunitiesInput(BaseModel):
    """Input schema for CrossReferenceOpportunitiesTool."""
    project: str = Field(..., description="Project name (e.g., 'pella.com')")
    project_id: str = Field(..., description="Project ID (e.g., '27')")
    position_range_start: int = Field(default=11, description="Start position (e.g., 11)")
    position_range_end: int = Field(default=50, description="End position (e.g., 50)")
    max_difficulty: int = Field(default=40, description="Max difficulty (default: 40)")
    min_volume: int = Field(default=500, description="Min volume (default: 500)")
    limit: int = Field(default=15, description="Max results (default: 15)")


class CrossReferenceOpportunitiesTool(BaseTool):
    name: str = "Cross-Reference SEO Opportunities"
    description: str = (
        "Find keywords that meet MULTIPLE criteria for optimization: "
        "- Currently ranking in positions 11-50 (page 2-5) "
        "- Low to medium difficulty (winnable) "
        "- Good search volume (worthwhile) "
        "Returns: best opportunities combining position, difficulty, and volume."
    )
    args_schema: Type[BaseModel] = CrossReferenceOpportunitiesInput
    
    def _run(
        self, 
        project: str, 
        project_id: str,
        position_range_start: int = 11,
        position_range_end: int = 50,
        max_difficulty: int = 40,
        min_volume: int = 500,
        limit: int = 15
    ) -> Dict[str, Any]:
        """Cross-reference rankings, difficulty, and volume to find opportunities"""
        try:
            # Load metadata
            metadata_file = DATA_DIR / f"{project}_metadata.json"
            if not metadata_file.exists():
                return {"success": False, "error": "No metadata found."}
            
            with open(metadata_file) as f:
                metadata = json.load(f)
            
            # Load all data files
            rankings_file = next((v for k, v in metadata.get('files', {}).items() if 'rankings' in k), None)
            difficulty_file = metadata.get('files', {}).get('difficulty')
            
            volume_metadata_file = DATA_DIR / f"project_{project_id}_metadata.json"
            volume_file = None
            if volume_metadata_file.exists():
                with open(volume_metadata_file) as f:
                    volume_metadata = json.load(f)
                volume_file = volume_metadata.get('files', {}).get('volume')
            
            if not rankings_file or not difficulty_file:
                return {"success": False, "error": "Missing required data files."}
            
            # Load data
            with open(rankings_file) as f:
                rankings = {r.get('Keyword', ''): r for r in json.load(f)}
            
            with open(difficulty_file) as f:
                difficulty = {r.get('Keyword', ''): r for r in json.load(f)}
            
            volume = {}
            if volume_file:
                with open(volume_file) as f:
                    volume = {r.get('Keyword', ''): r for r in json.load(f)}
            
            # Cross-reference
            opportunities = []
            for keyword, rank_data in rankings.items():
                try:
                    position = int(rank_data.get('Rank', 0))
                    
                    # Check position range
                    if not (position_range_start <= position <= position_range_end):
                        continue
                    
                    # Check difficulty
                    if keyword not in difficulty:
                        continue
                    diff_score = int(difficulty[keyword].get('Difficulty', 999))
                    if diff_score > max_difficulty:
                        continue
                    
                    # Check volume (if available)
                    vol = 0
                    if keyword in volume:
                        vol = int(volume[keyword].get('Searches', 0))
                        if vol < min_volume:
                            continue
                    
                    opportunities.append({
                        "keyword": keyword,
                        "current_position": position,
                        "difficulty": diff_score,
                        "monthly_searches": vol if vol > 0 else "N/A",
                        "url": rank_data.get('URL', ''),
                        "opportunity_score": round(
                            (100 - diff_score) * 0.5 +  # Easier is better
                            (51 - position) * 1.0 +  # Higher ranking is better
                            (vol / 1000 if vol > 0 else 0) * 0.5,  # More volume is better
                            2
                        )
                    })
                    
                except (ValueError, TypeError):
                    continue
            
            # Sort by opportunity score
            opportunities = sorted(opportunities, key=lambda x: x['opportunity_score'], reverse=True)[:limit]
            
            return {
                "success": True,
                "project": project,
                "criteria": {
                    "position_range": f"{position_range_start}-{position_range_end}",
                    "max_difficulty": max_difficulty,
                    "min_volume": min_volume
                },
                "total_opportunities": len(opportunities),
                "top_opportunities": opportunities,
                "message": f"Found {len(opportunities)} optimization opportunities"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to cross-reference data: {str(e)}"
            }