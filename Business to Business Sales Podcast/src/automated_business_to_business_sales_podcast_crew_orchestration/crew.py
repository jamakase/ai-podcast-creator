from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import PDFSearchTool
from crewai_tools import FileReadTool

@CrewBase
class AutomatedBusinessToBusinessSalesPodcastCrewOrchestrationCrew():
    """AutomatedBusinessToBusinessSalesPodcastCrewOrchestration crew"""

    @agent
    def content_curator(self) -> Agent:
        return Agent(
            config=self.agents_config['content_curator'],
            tools=[PDFSearchTool(), FileReadTool()],
        )

    @agent
    def audio_generator(self) -> Agent:
        return Agent(
            config=self.agents_config['audio_generator'],
            tools=[],
        )

    @agent
    def video_producer(self) -> Agent:
        return Agent(
            config=self.agents_config['video_producer'],
            tools=[],
        )

    @agent
    def workflow_coordinator(self) -> Agent:
        return Agent(
            config=self.agents_config['workflow_coordinator'],
            tools=[],
        )


    @task
    def content_identification_task(self) -> Task:
        return Task(
            config=self.tasks_config['content_identification_task'],
            tools=[PDFSearchTool(), FileReadTool()],
        )

    @task
    def audio_generation_task(self) -> Task:
        return Task(
            config=self.tasks_config['audio_generation_task'],
            tools=[],
        )

    @task
    def audio_quality_review_task(self) -> Task:
        return Task(
            config=self.tasks_config['audio_quality_review_task'],
            tools=[],
        )

    @task
    def video_podcast_production_task(self) -> Task:
        return Task(
            config=self.tasks_config['video_podcast_production_task'],
            tools=[],
        )

    @task
    def quality_check_and_logging_task(self) -> Task:
        return Task(
            config=self.tasks_config['quality_check_and_logging_task'],
            tools=[],
        )

    @task
    def orchestrate_monitoring_task(self) -> Task:
        return Task(
            config=self.tasks_config['orchestrate_monitoring_task'],
            tools=[],
        )


    @crew
    def crew(self) -> Crew:
        """Creates the AutomatedBusinessToBusinessSalesPodcastCrewOrchestration crew"""
        return Crew(
            agents=self.agents, # Automatically created by the @agent decorator
            tasks=self.tasks, # Automatically created by the @task decorator
            process=Process.sequential,
            verbose=True,
        )
