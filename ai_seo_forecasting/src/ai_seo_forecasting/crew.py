from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
import os
import json
from pathlib import Path

# Import ALL AWR tools including new ones
from ai_seo_forecasting.tools.awr_tools import (
    AWRProjectsTool,
    AWRProjectDetailsTool,
    AWRProjectDatesTool,
    AWRRankingsTool,
    AWRKeywordDifficultyTool,
    AWRSearchVolumeTool
)


@CrewBase
class AiSeoForecastingCrew:
    """AI SEO Forecasting crew for analyzing AWR data with human-in-the-loop interaction"""
    
    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'
    
    def __init__(self):
        """Initialize the crew with ALL AWR tools"""
        # Create memory directory if it doesn't exist
        self.memory_dir = Path("knowledge/agent_memory")
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize ALL AWR tools (existing + new)
        self.awr_projects_tool = AWRProjectsTool()
        self.awr_details_tool = AWRProjectDetailsTool()
        self.awr_dates_tool = AWRProjectDatesTool()
        
        # NEW TOOLS
        self.awr_rankings_tool = AWRRankingsTool()
        self.awr_difficulty_tool = AWRKeywordDifficultyTool()
        self.awr_volume_tool = AWRSearchVolumeTool()
        
        # Load existing memory if available
        self.load_memory()
    
    def load_memory(self):
        """Load agent memory from storage"""
        self.memory = {}
        memory_files = {
            'data_specialist': self.memory_dir / 'data_specialist_memory.json',
            'strategy_analyst': self.memory_dir / 'strategy_analyst_memory.json',
            'shared': self.memory_dir / 'shared_memory.json'
        }
        
        for key, file_path in memory_files.items():
            if file_path.exists():
                try:
                    with open(file_path, 'r') as f:
                        self.memory[key] = json.load(f)
                    print(f"✓ Loaded {key} memory: {len(self.memory[key])} items")
                except Exception as e:
                    print(f"⚠ Could not load {key} memory: {e}")
                    self.memory[key] = {}
            else:
                self.memory[key] = {}
    
    def save_memory(self, agent_name: str, data: dict):
        """Save agent memory to persistent storage"""
        memory_file = self.memory_dir / f'{agent_name}_memory.json'
        
        # Update memory
        if agent_name not in self.memory:
            self.memory[agent_name] = {}
        
        # Add timestamp to data
        data['timestamp'] = str(Path.cwd())
        
        # Merge with existing memory
        self.memory[agent_name].update(data)
        
        # Save to file
        try:
            with open(memory_file, 'w') as f:
                json.dump(self.memory[agent_name], f, indent=2)
            print(f"✓ Saved {agent_name} memory to {memory_file}")
        except Exception as e:
            print(f"⚠ Could not save {agent_name} memory: {e}")
    
    def get_memory(self, agent_name: str, key: str = None):
        """Retrieve agent memory"""
        if agent_name not in self.memory:
            return None
        
        if key:
            return self.memory[agent_name].get(key)
        else:
            return self.memory[agent_name]
    
    @agent
    def awr_data_specialist(self) -> Agent:
        """
        AWR Data Retrieval Specialist
        Handles all interactions with the AWR Cloud API
        Now with ALL tools including rankings, difficulty, and volume
        """
        return Agent(
            config=self.agents_config['awr_data_specialist'],
            tools=[
                # Original tools
                self.awr_projects_tool,
                self.awr_details_tool,
                self.awr_dates_tool,
                # NEW TOOLS - The most important ones!
                self.awr_rankings_tool,  # Get keyword rankings over time
                self.awr_difficulty_tool,  # Get keyword difficulty scores
                self.awr_volume_tool,  # Get search volume data
            ],
            verbose=True,
            memory=False  # Using custom JSON memory instead
        )
    
    @agent
    def seo_strategy_analyst(self) -> Agent:
        """
        SEO Strategy Analyst and Interactive Advisor
        Analyzes data, engages with user, and makes strategic recommendations
        """
        return Agent(
            config=self.agents_config['seo_strategy_analyst'],
            tools=[],  # Analyst primarily delegates to data specialist for tool usage
            verbose=True,
            memory=False  # Using custom JSON memory instead
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
        """Task to present project options to user and get their selection ONLY"""
        return Task(
            config=self.tasks_config['present_options_task'],
            agent=self.seo_strategy_analyst(),
            context=[self.retrieve_projects_task()],
            human_input=True  # Get project name, nothing else
        )
    
    @task
    def fetch_detailed_data_task(self) -> Task:
        """
        Task to fetch ALL data immediately after project selection
        NO questions asked - just collect everything!
        """
        return Task(
            config=self.tasks_config['fetch_detailed_data_task'],
            agent=self.awr_data_specialist(),
            context=[self.present_options_task()]  # Runs right after project selection
        )
    
    @task
    def gather_preferences_task(self) -> Task:
        """Task to ask user about analysis preferences AFTER data collection"""
        return Task(
            config=self.tasks_config['gather_preferences_task'],
            agent=self.seo_strategy_analyst(),
            context=[self.fetch_detailed_data_task()],  # Runs AFTER data is collected
            human_input=True
        )
    
    @task
    def analyze_rankings_task(self) -> Task:
        """NEW TASK: Analyze keyword ranking trends"""
        return Task(
            config=self.tasks_config['analyze_rankings_task'],
            agent=self.seo_strategy_analyst(),
            context=[self.fetch_detailed_data_task()]
        )
    
    @task
    def analyze_opportunities_task(self) -> Task:
        """NEW TASK: Identify keyword opportunities based on difficulty and volume"""
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
        """Creates the AI SEO Forecasting crew with human-in-the-loop and custom JSON memory"""
        return Crew(
            agents=self.agents,  # Automatically populated
            tasks=self.tasks,    # Automatically populated
            process=Process.sequential,  # Tasks run in order with human input at key points
            verbose=True,
            memory=False,  # Disable built-in memory (using custom JSON memory instead)
        )