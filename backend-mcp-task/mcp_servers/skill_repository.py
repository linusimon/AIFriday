"""
Skill Repository MCP Server
Provides tools for skill search and matching
"""
from mcp_servers import MCPServer
from database import get_db_connection
from typing import List, Dict

# Create MCP server instance
skill_server = MCPServer("skill", "Skill Repository Server")

def search_skills(query) -> List[Dict]:
    """
    Search for resources with specific skills
    
    Args:
        query: Skill search query (comma-separated, list, or single skill)
    
    Returns:
        List of resources matching the skill query
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Normalize query
    if isinstance(query, str):
        skills = [s.strip().lower() for s in query.split(',')]
    elif isinstance(query, (list, set)):
        skills = [str(s).strip().lower() for s in query]
    else:
        skills = []
    
    resources = []
    
    # Search human resources
    cursor.execute("SELECT * FROM human_resources")
    for row in cursor.fetchall():
        resource = dict(row)
        resource_skills = [s.strip().lower() for s in resource['skills'].split(',')]
        
        # Check if any of the queried skills match
        matches = [skill for skill in skills if any(skill in rs for rs in resource_skills)]
        if matches:
            resource['matched_skills'] = matches
            resource['type'] = 'human'
            resources.append(resource)
    
    # Search AI agents
    cursor.execute("SELECT * FROM ai_agents")
    for row in cursor.fetchall():
        agent = dict(row)
        agent_skills = [s.strip().lower() for s in agent['capabilities'].split(',')]
        
        # Check if any of the queried skills match
        matches = [skill for skill in skills if any(skill in ags for ags in agent_skills)]
        if matches:
            agent['matched_skills'] = matches
            agent['type'] = 'ai'
            agent['skills'] = agent['capabilities']
            resources.append(agent)
    
    conn.close()
    return resources

def match_skills(required_skills) -> List[Dict]:
    """
    Match required skills against available resources and calculate match scores
    
    Args:
        required_skills: Comma-separated list or list/set of required skills
    
    Returns:
        List of resources with match scores (0-100)
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Parse required skills
    if isinstance(required_skills, str):
        required = set([s.strip().lower() for s in required_skills.split(',')])
    elif isinstance(required_skills, (list, set)):
        required = set([str(s).strip().lower() for s in required_skills])
    else:
        required = set()
        
    matches = []
    
    # Match human resources
    cursor.execute("SELECT * FROM human_resources WHERE availability = 'Available'")
    for row in cursor.fetchall():
        resource = dict(row)
        resource_skills = set([s.strip().lower() for s in resource['skills'].split(',')])
        
        # Calculate match score
        matched = required & resource_skills
        match_score = (len(matched) / len(required)) * 100 if required else 0
        
        if match_score > 0:
            resource['match_score'] = round(match_score, 2)
            resource['matched_skills'] = list(matched)
            resource['missing_skills'] = list(required - resource_skills)
            resource['type'] = 'human'
            matches.append(resource)
    
    # Match AI agents
    cursor.execute("SELECT * FROM ai_agents WHERE availability = 'Available'")
    for row in cursor.fetchall():
        agent = dict(row)
        agent_skills = set([s.strip().lower() for s in agent['capabilities'].split(',')])
        
        # Calculate match score
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
    
    conn.close()
    
    # Sort by match score descending
    matches.sort(key=lambda x: x['match_score'], reverse=True)
    
    return matches

def get_skill_profiles(resource_id: int, resource_type: str = 'human') -> Dict:
    """
    Get detailed skill profile for a specific resource
    
    Args:
        resource_id: Resource ID
        resource_type: 'human' or 'ai'
    
    Returns:
        Detailed skill profile
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if resource_type == 'human':
        cursor.execute("""
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
        """, (resource_id,))
    else:
        cursor.execute("""
            SELECT 
                agent_id as id,
                agent_name as name,
                specialization as role,
                capabilities as skills,
                quality_score,
                performance_score
            FROM ai_agents
            WHERE agent_id = ?
        """, (resource_id,))
    
    resource = cursor.fetchone()
    conn.close()
    
    if resource:
        profile = dict(resource)
        profile['skills_list'] = [s.strip() for s in profile['skills'].split(',')]
        profile['type'] = resource_type
        return profile
    else:
        return {"error": "Resource not found"}

# Register tools
skill_server.register_tool("search_skills", search_skills)
skill_server.register_tool("match_skills", match_skills)
skill_server.register_tool("get_skill_profiles", get_skill_profiles)
