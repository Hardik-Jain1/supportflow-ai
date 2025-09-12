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

    def __init__(self, model= "gemini/gemini-2.5-flash", verbose = False):
        super().__init__()
        self.llm = model
        self.verbose = False

    @agent
    def reply_drafter(self) -> Agent:
        return Agent(
            config=self.agents_config['reply_drafter'],
            verbose=self.verbose,
            llm=self.llm
        )
    
    @agent
    def refiner(self) -> Agent:
        return Agent(
            config=self.agents_config['refiner'],
            verbose=self.verbose,
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
    def crew(self, verbose = False) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=self.verbose
        )
    
    # @before_kickoff
    # def before_kickoff_function(self, inputs):
    #     print(f"Before kickoff function with inputs: {inputs}")
    #     return inputs

    # @after_kickoff
    # def after_kickoff_function(self, result):
    #     print(f"After kickoff function with result: {result}")
    #     return result

def reply_agent(ticket, context, model = "gemini/gemini-2.5-flash", verbose = False):
    inputs = {
        "ticket_text": ticket,
        "context": context,
    }

    return ReplyAgentCrew(model).crew(verbose).kickoff(inputs) 