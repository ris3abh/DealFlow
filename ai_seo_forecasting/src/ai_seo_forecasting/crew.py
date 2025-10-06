from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task

# Import AWR tools from consolidated file
from ai_seo_forecasting.tools.awr_tools import (
    AWRProjectsTool,
    AWRProjectDetailsTool,
    AWRProjectDatesTool
)


@CrewBase
class AiSeoForecastingCrew:
    """AI SEO Forecasting crew for analyzing AWR data with human-in-the-loop interaction"""
    
    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'
    
    def __init__(self):
        """Initialize the crew with AWR tools"""
        # Initialize all AWR tools
        self.awr_projects_tool = AWRProjectsTool()
        self.awr_details_tool = AWRProjectDetailsTool()
        self.awr_dates_tool = AWRProjectDatesTool()
    
    @agent
    def awr_data_specialist(self) -> Agent:
        """
        AWR Data Retrieval Specialist
        Handles all interactions with the AWR Cloud API
        """
        return Agent(
            config=self.agents_config['awr_data_specialist'],
            tools=[
                self.awr_projects_tool,
                self.awr_details_tool,
                self.awr_dates_tool,
            ],
            verbose=True
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
            verbose=True
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
        """Task to present project options to user and get their selection"""
        return Task(
            config=self.tasks_config['present_options_task'],
            agent=self.seo_strategy_analyst(),
            context=[self.retrieve_projects_task()],
            human_input=True  # Enable human-in-the-loop
        )
    
    @task
    def gather_preferences_task(self) -> Task:
        """Task to ask user about their analysis preferences"""
        return Task(
            config=self.tasks_config['gather_preferences_task'],
            agent=self.seo_strategy_analyst(),
            context=[self.present_options_task()],
            human_input=True
        )
    
    @task
    def fetch_detailed_data_task(self) -> Task:
        """Task to fetch detailed project data based on user selection"""
        return Task(
            config=self.tasks_config['fetch_detailed_data_task'],
            agent=self.awr_data_specialist(),
            context=[self.gather_preferences_task()]
        )
    
    @task
    def generate_analysis_report_task(self) -> Task:
        """Task to generate comprehensive SEO analysis report"""
        return Task(
            config=self.tasks_config['generate_analysis_report_task'],
            agent=self.seo_strategy_analyst(),
            context=[
                self.fetch_detailed_data_task(),
                self.gather_preferences_task()
            ]
        )
    
    @crew
    def crew(self) -> Crew:
        """Creates the AI SEO Forecasting crew with human-in-the-loop"""
        return Crew(
            agents=self.agents,  # Automatically populated
            tasks=self.tasks,    # Automatically populated
            process=Process.sequential,  # Tasks run in order with human input at key points
            verbose=True,
        )