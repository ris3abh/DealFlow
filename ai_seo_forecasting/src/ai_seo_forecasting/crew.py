from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
import os
import json
from pathlib import Path

# Import optimized AWR tools
from ai_seo_forecasting.tools.awr_tools import (
    AWRProjectsTool,
    AWRProjectDetailsTool,
    AWRProjectDatesTool,
    AWRRankingsTool,
    AWRKeywordDifficultyTool,
    AWRSearchVolumeTool
)

# Import analysis helper tools
from ai_seo_forecasting.tools.analysis_tools import (
    QueryMetadataTool,
    QueryKeywordsByPositionTool,
    QueryLowDifficultyKeywordsTool,
    QueryHighVolumeKeywordsTool,
    CrossReferenceOpportunitiesTool
)


@CrewBase
class AiSeoForecastingCrew:
    """AI SEO Forecasting crew - OPTIMIZED for compact context usage"""
    
    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'
    
    def __init__(self):
        """Initialize the crew with ALL tools (collection + analysis)"""
        # Ensure data directories exist
        Path("knowledge/api_data").mkdir(parents=True, exist_ok=True)
        Path("knowledge/agent_memory").mkdir(parents=True, exist_ok=True)
        
        # Collection tools (return compact summaries)
        self.awr_projects_tool = AWRProjectsTool()
        self.awr_details_tool = AWRProjectDetailsTool()
        self.awr_dates_tool = AWRProjectDatesTool()
        self.awr_rankings_tool = AWRRankingsTool()
        self.awr_difficulty_tool = AWRKeywordDifficultyTool()
        self.awr_volume_tool = AWRSearchVolumeTool()
        
        # Analysis tools (query stored files)
        self.query_metadata_tool = QueryMetadataTool()
        self.query_position_tool = QueryKeywordsByPositionTool()
        self.query_difficulty_tool = QueryLowDifficultyKeywordsTool()
        self.query_volume_tool = QueryHighVolumeKeywordsTool()
        self.cross_ref_tool = CrossReferenceOpportunitiesTool()
    
    @agent
    def awr_data_specialist(self) -> Agent:
        """
        AWR Data Retrieval Specialist
        Handles data collection with compact summaries
        """
        return Agent(
            config=self.agents_config['awr_data_specialist'],
            tools=[
                # Collection tools
                self.awr_projects_tool,
                self.awr_details_tool,
                self.awr_dates_tool,
                self.awr_rankings_tool,
                self.awr_difficulty_tool,
                self.awr_volume_tool,
            ],
            verbose=True,
            max_iter=10  # May need multiple tool calls for data collection
        )
    
    @agent
    def seo_strategy_analyst(self) -> Agent:
        """
        SEO Strategy Analyst
        Analyzes stored data and provides insights
        """
        return Agent(
            config=self.agents_config['seo_strategy_analyst'],
            tools=[
                # Analysis tools for querying stored data
                self.query_metadata_tool,
                self.query_position_tool,
                self.query_difficulty_tool,
                self.query_volume_tool,
                self.cross_ref_tool,
            ],
            verbose=True,
            allow_delegation=False,  # Works independently with data files
            max_iter=10
        )
    
    @task
    def retrieve_projects_task(self) -> Task:
        """Task to retrieve all AWR projects"""
        return Task(
            config=self.tasks_config['retrieve_projects_task'],
            agent=self.awr_data_specialist()
        )
    
    @task
    def present_options_task(self) -> Task:
        """Task to present projects to user and get selection"""
        return Task(
            config=self.tasks_config['present_options_task'],
            agent=self.seo_strategy_analyst(),
            context=[self.retrieve_projects_task()],
            human_input=True,
            tools=[]  # CRITICAL: No tools! Just present list and collect selection
        )
    
    @task
    def fetch_detailed_data_task(self) -> Task:
        """Task to fetch ALL AWR data for selected project"""
        return Task(
            config=self.tasks_config['fetch_detailed_data_task'],
            agent=self.awr_data_specialist(),
            context=[self.present_options_task()]
        )
    
    @task
    def gather_preferences_task(self) -> Task:
        """Task to ask user about analysis preferences"""
        return Task(
            config=self.tasks_config['gather_preferences_task'],
            agent=self.seo_strategy_analyst(),
            context=[self.fetch_detailed_data_task()],
            human_input=True
        )
    
    @task
    def analyze_rankings_task(self) -> Task:
        """Task to analyze keyword ranking trends from stored files"""
        return Task(
            config=self.tasks_config['analyze_rankings_task'],
            agent=self.seo_strategy_analyst(),
            context=[self.fetch_detailed_data_task()]
        )
    
    @task
    def analyze_opportunities_task(self) -> Task:
        """Task to identify keyword opportunities from stored files"""
        return Task(
            config=self.tasks_config['analyze_opportunities_task'],
            agent=self.seo_strategy_analyst(),
            context=[self.fetch_detailed_data_task()]
        )
    
    @task
    def generate_analysis_report_task(self) -> Task:
        """Task to generate comprehensive SEO analysis report"""
        return Task(
            config=self.tasks_config['generate_analysis_report_task'],
            agent=self.seo_strategy_analyst(),
            context=[
                self.fetch_detailed_data_task(),
                self.analyze_rankings_task(),
                self.analyze_opportunities_task(),
                self.gather_preferences_task()
            ]
        )
    
    @crew
    def crew(self) -> Crew:
        """Creates the AI SEO Forecasting crew"""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
            memory=False,  # Using custom file-based storage instead
        )