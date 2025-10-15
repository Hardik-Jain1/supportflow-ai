from crewai import Agent, Crew, Process, Task, LLM
from crewai.project import CrewBase, agent, crew, task, before_kickoff, after_kickoff
from crewai.agents.agent_builder.base_agent import BaseAgent
from typing import List
import os
from dotenv import load_dotenv
load_dotenv()

@CrewBase
class ReplyGeneratorCrew():
    """Crew for handling customer support reply generation."""

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


def generate_reply(ticket: str, context: str, model: str = "gemini/gemini-2.5-flash", verbose: bool = False):
    """
    Generate an initial reply to a customer support ticket.
    
    Args:
        ticket: The customer support ticket text
        context: Relevant context from knowledge base
        model: The LLM model to use
        verbose: Enable verbose logging
        
    Returns:
        CrewAI output with generated reply
    """
    inputs = {
        "ticket_text": ticket,
        "context": context,
    }

    return ReplyGeneratorCrew(model).crew(mode="draft", verbose=verbose).kickoff(inputs)


def redraft_reply(ticket: str, context: str, previous_draft: str, human_feedback: str, 
                  model: str = "gemini/gemini-2.5-flash", verbose: bool = False):
    """
    Redraft a reply based on human feedback.
    
    Args:
        ticket: The customer support ticket text
        context: Relevant context from knowledge base
        previous_draft: The previous draft that needs revision
        human_feedback: Human feedback for improvement
        model: The LLM model to use
        verbose: Enable verbose logging
        
    Returns:
        CrewAI output with redrafted reply
    """
    inputs = {
        "ticket_text": ticket,
        "context": context,
        "previous_draft": previous_draft,
        "human_feedback": human_feedback,
    }

    return ReplyGeneratorCrew(model).crew(mode="redraft", verbose=verbose).kickoff(inputs)
