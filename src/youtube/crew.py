from typing import List

from crewai import Agent, Crew, Process, Task
from crewai.agents.agent_builder.base_agent import BaseAgent
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import FileWriterTool

from youtube.tools import HeyGenVideoGeneratorTool, PDFParserTool, YouTubeUploaderTool


@CrewBase
class Youtube:
    """Youtube crew for B2B sales content creation"""

    agents: List[BaseAgent]
    tasks: List[Task]

    @agent
    def content_curator(self) -> Agent:
        return Agent(
            config=self.agents_config["content_curator"],
            verbose=True,
            tools=[PDFParserTool(), FileWriterTool()],
        )

    # @agent
    # def audio_generator(self) -> Agent:
    #     return Agent(
    #         config=self.agents_config['audio_generator'],
    #         verbose=True,
    #         tools=[AudioGeneratorTool()]
    #     )

    @agent
    def video_producer(self) -> Agent:
        return Agent(
            config=self.agents_config["video_producer"],
            verbose=True,
            tools=[HeyGenVideoGeneratorTool(), YouTubeUploaderTool()],
        )

    @task
    def content_sourcing_task(self) -> Task:
        return Task(
            config=self.tasks_config["content_sourcing_task"],
            expected_output="Path to text of book",
        )

    @task
    def video_production_task(self) -> Task:
        return Task(config=self.tasks_config["video_production_task"])

    @task
    def video_upload_task(self) -> Task:
        return Task(config=self.tasks_config["video_upload_task"])

    @crew
    def crew(self) -> Crew:
        """Creates the Youtube crew for B2B sales content creation"""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
