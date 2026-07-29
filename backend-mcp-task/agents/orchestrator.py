"""
Orchestrator for managing multi-agent execution flow
"""
from typing import List, Dict, Any
from agents import Agent
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed

def sanitize_for_json(obj, max_depth=5, memo=None):
    """Safely converts context objects to JSON-serializable dictionaries without circular references."""
    if memo is None:
        memo = set()
    if max_depth <= 0:
        return "[Max Depth Exceeded]"
    obj_id = id(obj)
    if obj_id in memo:
        return "[Circular Reference]"
    
    if isinstance(obj, (int, float, bool, type(None))):
        return obj
    elif isinstance(obj, str):
        return obj[:1000] if len(obj) > 1000 else obj
    elif isinstance(obj, dict):
        memo.add(obj_id)
        res = {str(k): sanitize_for_json(v, max_depth - 1, memo) for k, v in obj.items() if not str(k).startswith('_')}
        memo.remove(obj_id)
        return res
    elif isinstance(obj, (list, tuple, set)):
        memo.add(obj_id)
        res = [sanitize_for_json(v, max_depth - 1, memo) for v in obj]
        memo.remove(obj_id)
        return res
    else:
        return str(obj)

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
                           final_agents: List[Agent],
                           callback=None) -> Dict[str, Any]:
        """
        Execute agents in a custom flow: sequential -> parallel -> sequential
        with optional progress callback.
        """
        self.context = initial_context.copy() if initial_context else {}
        
        total_steps = len(sequential_agents) + (1 if parallel_agents else 0) + len(final_agents)
        current_step = 0

        # Phase 1: Execute sequential agents
        print("[Orchestrator] Phase 1: Sequential agents")
        for agent in sequential_agents:
            current_step += 1
            try:
                print(f"[Orchestrator] Executing {agent.name}")
                input_payload = sanitize_for_json(self.context)
                if callback:
                    callback(agent.name, "started", None, {"step": current_step, "total_steps": total_steps}, input_payload)
                result = agent.execute(self.context)
                self.context[agent.name] = result
                if callback:
                    callback(agent.name, "completed", result, {"step": current_step, "total_steps": total_steps}, input_payload)
            except Exception as e:
                print(f"[Orchestrator] Agent {agent.name} failed: {str(e)}")
                traceback.print_exc()
                self.context[agent.name] = {"error": str(e)}
                if callback:
                    callback(agent.name, "failed", {"error": str(e)}, {"step": current_step, "total_steps": total_steps}, input_payload)
        
        # Phase 2: Execute parallel agents
        if parallel_agents:
            current_step += 1
            print("[Orchestrator] Phase 2: Parallel agents")
            input_payload = sanitize_for_json(self.context)
            if callback:
                callback("ParallelOptimizationPhase", "started", None, {"step": current_step, "total_steps": total_steps, "agents": [a.name for a in parallel_agents]}, input_payload)
            
            parallel_results = self.execute_parallel(parallel_agents, self.context)
            
            # Merge parallel results into context
            for agent_name, result_data in parallel_results.items():
                if result_data['status'] == 'success':
                    self.context[agent_name] = result_data['result']
                else:
                    self.context[agent_name] = {"error": result_data.get('error', 'Unknown error')}
            
            if callback:
                callback("ParallelOptimizationPhase", "completed", parallel_results, {"step": current_step, "total_steps": total_steps}, input_payload)
        
        # Phase 3: Execute final sequential agents
        print("[Orchestrator] Phase 3: Final sequential agents")
        for agent in final_agents:
            current_step += 1
            try:
                print(f"[Orchestrator] Executing {agent.name}")
                input_payload = sanitize_for_json(self.context)
                if callback:
                    callback(agent.name, "started", None, {"step": current_step, "total_steps": total_steps}, input_payload)
                result = agent.execute(self.context)
                self.context[agent.name] = result
                if callback:
                    callback(agent.name, "completed", result, {"step": current_step, "total_steps": total_steps}, input_payload)
            except Exception as e:
                print(f"[Orchestrator] Agent {agent.name} failed: {str(e)}")
                traceback.print_exc()
                self.context[agent.name] = {"error": str(e)}
                if callback:
                    callback(agent.name, "failed", {"error": str(e)}, {"step": current_step, "total_steps": total_steps}, input_payload)
        
        print("[Orchestrator] All agents completed")
        return self.context

    def execute_dynamic_intent_flow(self, initial_context: Dict[str, Any], text_query: str, callback=None) -> Dict[str, Any]:
        """
        Dynamically analyzes intent, selects appropriate specialist agents,
        and executes them asynchronously in sequence or parallel.
        """
        from agents.intent_agent import task_intent_agent
        intent_result = task_intent_agent.classify(text_query)
        intent = intent_result['intent']
        
        print(f"[Orchestrator] Classified Input Intent: {intent} (Confidence: {intent_result['confidence']})")
        if initial_context is None:
            initial_context = {}
        initial_context['_classified_intent'] = intent_result

        # Import available specialist agents
        from agents.document_analysis_agent import DocumentAnalysisAgent
        from agents.data_cleansing_agent import DataCleansingAgent
        from agents.data_enrichment_agent import DataEnrichmentAgent
        from agents.task_classification_agent import TaskClassificationAgent
        from agents.resource_matching_agent import ResourceMatchingAgent
        from agents.workload_optimization_agent import WorkloadOptimizationAgent
        from agents.cost_optimization_agent import CostOptimizationAgent
        from agents.risk_sla_agent import RiskSLAAgent
        from agents.decision_agent import DecisionAgent
        from agents.summary_agent import SummaryAgent
        from agents.execution_plan_agent import ProjectExecutionAgent

        sequential_agents = []
        parallel_agents = []
        final_agents = []

        if intent == 'EXECUTION_PLAN_GENERATION':
            sequential_agents = [DocumentAnalysisAgent()]
            final_agents = [ProjectExecutionAgent(), SummaryAgent()]

        elif intent == 'RESOURCE_MATCHING_INQUIRY':
            sequential_agents = [DocumentAnalysisAgent(), ResourceMatchingAgent()]
            parallel_agents = [WorkloadOptimizationAgent(), CostOptimizationAgent(), RiskSLAAgent()]
            final_agents = [DecisionAgent(), SummaryAgent()]

        elif intent == 'COST_SLA_OPTIMIZATION':
            sequential_agents = [DocumentAnalysisAgent(), ResourceMatchingAgent()]
            parallel_agents = [WorkloadOptimizationAgent(), CostOptimizationAgent(), RiskSLAAgent()]
            final_agents = [DecisionAgent(), SummaryAgent()]

        elif intent == 'POLICY_FAQ_INQUIRY' or intent == 'GENERAL_ASSISTANT_CONVERSATION':
            final_agents = [SummaryAgent()]

        else:  # FULL_TASK_ROUTING_ANALYSIS (Default)
            sequential_agents = [
                DocumentAnalysisAgent(),
                DataCleansingAgent(),
                DataEnrichmentAgent(),
                TaskClassificationAgent(),
                ResourceMatchingAgent()
            ]
            parallel_agents = [
                WorkloadOptimizationAgent(),
                CostOptimizationAgent(),
                RiskSLAAgent()
            ]
            final_agents = [
                DecisionAgent(),
                SummaryAgent()
            ]

        return self.execute_custom_flow(
            initial_context=initial_context,
            sequential_agents=sequential_agents,
            parallel_agents=parallel_agents,
            final_agents=final_agents,
            callback=callback
        )
