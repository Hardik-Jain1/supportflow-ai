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
    
    @agent
    def feedback_analyzer(self) -> Agent:
        return Agent(
            config=self.agents_config['feedback_analyzer'],
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
            config=self.tasks_config['refine_task']
        )
    
    @task
    def analyze_feedback_task(self) -> Task:
        return Task(
            config=self.tasks_config['analyze_feedback_task'],
            input_variables=['previous_draft', 'human_feedback', 'ticket_text']
        )
    
    @task
    def redraft_task(self) -> Task:
        return Task(
            config=self.tasks_config['redraft_task'],
            input_variables=['ticket_text', 'context', 'previous_draft'],
            context=[self.analyze_feedback_task()]
        )

    @crew
    def crew(self, mode="draft", verbose = False) -> Crew:
        """
        Create crew with different task flows based on mode:
        - 'draft': Initial drafting (draft_task -> refine_task)
        - 'redraft': Redrafting with feedback (analyze_feedback_task -> redraft_task -> refine_task)
        """
        if mode == "redraft":
            # Redrafting workflow: analyze feedback -> redraft -> refine
            selected_agents = [self.feedback_analyzer(), self.reply_drafter(), self.refiner()]
            selected_tasks = [self.analyze_feedback_task(), self.redraft_task(), self.refine_task()]
        else:
            # Default: Initial drafting workflow: draft -> refine
            selected_agents = [self.reply_drafter(), self.refiner()]
            selected_tasks = [self.draft_task(), self.refine_task()]
        
        return Crew(
            agents=selected_agents,
            tasks=selected_tasks,
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
    """Initial drafting function - unchanged for backward compatibility"""
    inputs = {
        "ticket_text": ticket,
        "context": context,
    }

    return ReplyAgentCrew(model).crew(mode="draft", verbose=verbose).kickoff(inputs)

def redraft_reply_agent(ticket, context, previous_draft, human_feedback, model = "gemini/gemini-2.5-flash", verbose = False):
    """Redrafting function based on human feedback"""
    inputs = {
        "ticket_text": ticket,
        "context": context,
        "previous_draft": previous_draft,
        "human_feedback": human_feedback,
    }

    return ReplyAgentCrew(model).crew(mode="redraft", verbose=verbose).kickoff(inputs) 