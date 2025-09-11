from crewai import Agent, Crew, Process, Task, LLM
from crewai.project import CrewBase, agent, crew, task, before_kickoff, after_kickoff
from crewai.agents.agent_builder.base_agent import BaseAgent
from typing import List
import os
from dotenv import load_dotenv
load_dotenv()

@CrewBase
class ReplyAgentCrew():
    """Crew for handling customer support replies."""

    agents: List[BaseAgent]
    tasks: List[Task]

    llm = LLM(
        model="gemini/gemini-2.5-flash",
        temperature=0,
        top_p=0.5
    )

    @agent
    def reply_drafter(self) -> Agent:
        return Agent(
            config=self.agents_config['reply_drafter'],
            verbose=True,
            llm=self.llm
        )
    
    @agent
    def refiner(self) -> Agent:
        return Agent(
            config=self.agents_config['refiner'],
            verbose=True,
            llm=self.llm
        )
    
    @task
    def draft_task(self) -> Task:
        return Task(
            config=self.tasks_config['draft_task'],
            input_variables=['ticket_text', 'context']
        )
    
    @task
    def refine_task(self) -> Task:
        return Task(
            config=self.tasks_config['refine_task'],
            output_file='final_reply.txt',
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True
        )
    
    @before_kickoff
    def before_kickoff_function(self, inputs):
        print(f"Before kickoff function with inputs: {inputs}")
        return inputs

    @after_kickoff
    def after_kickoff_function(self, result):
        print(f"After kickoff function with result: {result}")
        return result   