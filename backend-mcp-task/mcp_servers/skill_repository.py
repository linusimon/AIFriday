"""
Skill Repository MCP Server
Provides tools for skill search and matching using generic SQLite MCP database operations.
"""
from mcp_servers import MCPServer
from database import execute_query
from typing import List, Dict

# Create MCP server instance
skill_server = MCPServer("skill", "Skill Repository Server")

def search_skills(query) -> List[Dict]:
    """Search for resources with specific skills using generic MCP query execution."""
    if isinstance(query, str):
        skills = [s.strip().lower() for s in query.split(',')]
    elif isinstance(query, (list, set)):
        skills = [str(s).strip().lower() for s in query]
    else:
        skills = []
    
    resources = []
    
    # Search human resources
    human_rows = execute_query("SELECT * FROM human_resources")
    for resource in human_rows:
        resource_skills = [s.strip().lower() for s in resource['skills'].split(',')]
        matches = [skill for skill in skills if any(skill in rs for rs in resource_skills)]
        if matches:
            resource['matched_skills'] = matches
            resource['type'] = 'human'
            resources.append(resource)
    
    # Search AI agents
    ai_rows = execute_query("SELECT * FROM ai_agents")
    for agent in ai_rows:
        agent_skills = [s.strip().lower() for s in agent['capabilities'].split(',')]
        matches = [skill for skill in skills if any(skill in ags for ags in agent_skills)]
        if matches:
            agent['matched_skills'] = matches
            agent['type'] = 'ai'
            agent['skills'] = agent['capabilities']
            resources.append(agent)
    
    return resources

def match_skills(required_skills) -> List[Dict]:
    """Match required skills against available resources using generic MCP query execution."""
    if isinstance(required_skills, str):
        required = set([s.strip().lower() for s in required_skills.split(',')])
    elif isinstance(required_skills, (list, set)):
        required = set([str(s).strip().lower() for s in required_skills])
    else:
        required = set()
        
    matches = []
    
    # Match human resources
    human_rows = execute_query("SELECT * FROM human_resources WHERE availability = 'Available'")
    for resource in human_rows:
        resource_skills = set([s.strip().lower() for s in resource['skills'].split(',')])
        matched = required & resource_skills
        match_score = (len(matched) / len(required)) * 100 if required else 0
        
        if match_score > 0:
            resource['match_score'] = round(match_score, 2)
            resource['matched_skills'] = list(matched)
            resource['missing_skills'] = list(required - resource_skills)
            resource['type'] = 'human'
            matches.append(resource)
    
    # Match AI agents
    ai_rows = execute_query("SELECT * FROM ai_agents WHERE availability = 'Available'")
    for agent in ai_rows:
        agent_skills = set([s.strip().lower() for s in agent['capabilities'].split(',')])
        matched = required & agent_skills
        match_score = (len(matched) / len(required)) * 100 if required else 0
        
        if match_score > 0:
            agent['match_score'] = round(match_score, 2)
            agent['matched_skills'] = list(matched)
            agent['missing_skills'] = list(required - agent_skills)
            agent['type'] = 'ai'
            agent['skills'] = agent['capabilities']
            agent['name'] = agent['agent_name']
            matches.append(agent)
    
    matches.sort(key=lambda x: x['match_score'], reverse=True)
    return matches

def get_skill_profiles(resource_id: int, resource_type: str = 'human') -> Dict:
    """Get detailed skill profile for a specific resource using generic MCP query execution."""
    if resource_type == 'human':
        rows = execute_query("""
            SELECT 
                resource_id as id,
                name,
                role,
                skills,
                experience,
                quality_score,
                performance_score
            FROM human_resources
            WHERE resource_id = ?
        """, [resource_id])
    else:
        rows = execute_query("""
            SELECT 
                agent_id as id,
                agent_name as name,
                specialization as role,
                capabilities as skills,
                quality_score,
                performance_score
            FROM ai_agents
            WHERE agent_id = ?
        """, [resource_id])
    
    if rows:
        profile = rows[0]
        profile['skills_list'] = [s.strip() for s in profile['skills'].split(',')]
        profile['type'] = resource_type
        return profile
    else:
        return {"error": "Resource not found"}

# Register tools
skill_server.register_tool("search_skills", search_skills)
skill_server.register_tool("match_skills", match_skills)
skill_server.register_tool("get_skill_profiles", get_skill_profiles)
