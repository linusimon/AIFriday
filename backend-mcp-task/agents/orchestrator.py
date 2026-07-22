"""
Orchestrator for managing multi-agent execution flow
"""
from typing import List, Dict, Any
from agents import Agent
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed

class AgentOrchestrator:
    """
    Orchestrates the execution of multiple agents in sequence or parallel.
    Manages shared context and agent coordination.
    """
    
    def __init__(self):
        self.agents: List[Agent] = []
        self.context: Dict[str, Any] = {}
    
    def add_agent(self, agent: Agent):
        """Add an agent to the orchestration pipeline"""
        self.agents.append(agent)
    
    def execute_sequential(self, initial_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Execute all agents sequentially
        
        Args:
            initial_context: Initial context data
        
        Returns:
            Final context with all agent results
        """
        if initial_context:
            self.context = initial_context.copy()
        else:
            self.context = {}
        
        results = []
        
        for agent in self.agents:
            try:
                print(f"[Orchestrator] Executing agent: {agent.name}")
                result = agent.execute(self.context)
                
                # Store result in context
                self.context[agent.name] = result
                results.append({
                    "agent": agent.name,
                    "status": "success",
                    "result": result
                })
                
                print(f"[Orchestrator] Agent {agent.name} completed successfully")
            
            except Exception as e:
                print(f"[Orchestrator] Agent {agent.name} failed: {str(e)}")
                traceback.print_exc()
                results.append({
                    "agent": agent.name,
                    "status": "failed",
                    "error": str(e)
                })
                # Continue execution even if one agent fails
        
        self.context['_execution_results'] = results
        return self.context
    
    def execute_parallel(self, agents: List[Agent], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute multiple agents in parallel
        
        Args:
            agents: List of agents to execute in parallel
            context: Shared context
        
        Returns:
            Combined results from all parallel agents
        """
        results = {}
        
        with ThreadPoolExecutor(max_workers=min(len(agents), 4)) as executor:
            # Submit all agent executions
            future_to_agent = {
                executor.submit(agent.execute, context): agent
                for agent in agents
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_agent):
                agent = future_to_agent[future]
                try:
                    result = future.result()
                    results[agent.name] = {
                        "status": "success",
                        "result": result
                    }
                    print(f"[Orchestrator] Parallel agent {agent.name} completed")
                
                except Exception as e:
                    print(f"[Orchestrator] Parallel agent {agent.name} failed: {str(e)}")
                    traceback.print_exc()
                    results[agent.name] = {
                        "status": "failed",
                        "error": str(e)
                    }
        
        return results
    
    def execute_custom_flow(self, initial_context: Dict[str, Any], 
                           sequential_agents: List[Agent],
                           parallel_agents: List[Agent],
                           final_agents: List[Agent]) -> Dict[str, Any]:
        """
        Execute agents in a custom flow: sequential -> parallel -> sequential
        
        This implements the pattern: 1→2→3→4→5, then 6-7-8-9 parallel, then 10→11
        
        Args:
            initial_context: Initial context data
            sequential_agents: Agents to execute sequentially first
            parallel_agents: Agents to execute in parallel
            final_agents: Agents to execute sequentially at the end
        
        Returns:
            Final context with all results
        """
        self.context = initial_context.copy() if initial_context else {}
        
        # Phase 1: Execute sequential agents
        print("[Orchestrator] Phase 1: Sequential agents")
        for agent in sequential_agents:
            try:
                print(f"[Orchestrator] Executing {agent.name}")
                result = agent.execute(self.context)
                self.context[agent.name] = result
            except Exception as e:
                print(f"[Orchestrator] Agent {agent.name} failed: {str(e)}")
                traceback.print_exc()
                self.context[agent.name] = {"error": str(e)}
        
        # Phase 2: Execute parallel agents
        if parallel_agents:
            print("[Orchestrator] Phase 2: Parallel agents")
            parallel_results = self.execute_parallel(parallel_agents, self.context)
            
            # Merge parallel results into context
            for agent_name, result_data in parallel_results.items():
                if result_data['status'] == 'success':
                    self.context[agent_name] = result_data['result']
                else:
                    self.context[agent_name] = {"error": result_data.get('error', 'Unknown error')}
        
        # Phase 3: Execute final sequential agents
        print("[Orchestrator] Phase 3: Final sequential agents")
        for agent in final_agents:
            try:
                print(f"[Orchestrator] Executing {agent.name}")
                result = agent.execute(self.context)
                self.context[agent.name] = result
            except Exception as e:
                print(f"[Orchestrator] Agent {agent.name} failed: {str(e)}")
                traceback.print_exc()
                self.context[agent.name] = {"error": str(e)}
        
        print("[Orchestrator] All agents completed")
        return self.context
