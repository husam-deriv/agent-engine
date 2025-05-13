import os
import json
from datetime import datetime
from typing import List, Dict, Optional, Any, Union
from sqlalchemy import select, func, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from database import ProjectModel, DepartmentModel, AgentModel, ProjectSolutionModel, CompanyModel, ConversationModel, MessageModel

# Predefined departments for the Gargash AI Builder
DEFAULT_DEPARTMENTS = [
    {"name": "AI Fundamentals", "description": "Core AI capabilities and foundational projects"},
    {"name": "Marketing AI", "description": "AI solutions for marketing and advertising"},
    {"name": "Sales AI", "description": "AI solutions for sales optimization and lead generation"},
    {"name": "HR AI", "description": "AI solutions for human resources and employee experience"},
    {"name": "IT Operations", "description": "AI solutions for IT infrastructure and operations"},
    {"name": "Procurement AI", "description": "AI solutions for procurement and supply chain"}
]

# Predefined goals
GOALS = ["Productivity", "Cost Savings", "Win new Customers", "Learning and Governance"]

async def ensure_default_departments(db: AsyncSession):
    """Ensure that the default departments exist in the database."""
    for dept in DEFAULT_DEPARTMENTS:
        # Check if department already exists
        result = await db.execute(
            select(DepartmentModel).where(DepartmentModel.name == dept["name"])
        )
        existing_dept = result.scalars().first()
        
        if not existing_dept:
            # Create new department
            new_dept = DepartmentModel(
                name=dept["name"],
                description=dept["description"]
            )
            db.add(new_dept)
    
    await db.commit()

async def get_all_departments(db: AsyncSession) -> List[Dict[str, Any]]:
    """Get all departments with project counts."""
    # First ensure defaults exist
    await ensure_default_departments(db)
    
    # Query departments
    result = await db.execute(
        select(DepartmentModel)
    )
    departments = result.scalars().all()
    
    # Get project counts for each department
    dept_list = []
    for dept in departments:
        # Count projects in this department
        project_count = await db.execute(
            select(func.count(ProjectModel.id)).where(ProjectModel.department_id == dept.id)
        )
        count = project_count.scalar()
        
        dept_dict = {
            "id": dept.id,
            "name": dept.name,
            "description": dept.description,
            "project_count": count,
            "created_at": dept.created_at.isoformat() if dept.created_at else None,
            "updated_at": dept.updated_at.isoformat() if dept.updated_at else None
        }
        dept_list.append(dept_dict)
    
    return dept_list

async def get_department_by_name(db: AsyncSession, name: str) -> Optional[Dict[str, Any]]:
    """Get a department by name."""
    result = await db.execute(
        select(DepartmentModel).where(DepartmentModel.name == name)
    )
    dept = result.scalars().first()
    
    if not dept:
        return None
    
    # Count projects
    project_count = await db.execute(
        select(func.count(ProjectModel.id)).where(ProjectModel.department_id == dept.id)
    )
    count = project_count.scalar()
    
    return {
        "id": dept.id,
        "name": dept.name,
        "description": dept.description,
        "project_count": count,
        "created_at": dept.created_at.isoformat() if dept.created_at else None,
        "updated_at": dept.updated_at.isoformat() if dept.updated_at else None
    }

async def create_project(
    db: AsyncSession,
    title: str,
    department_name: str,
    goal: str,
    description: Optional[str] = None,
    expected_value: float = 3.0,
    company_id: Optional[int] = None,
    is_scheduled: bool = False,
    schedule_frequency: Optional[str] = None,
    slack_channel: Optional[str] = None,
    solution_ids: Optional[List[int]] = None
) -> Dict[str, Any]:
    """Create a new AI project."""
    # Get or create department
    dept_result = await db.execute(
        select(DepartmentModel).where(DepartmentModel.name == department_name)
    )
    dept = dept_result.scalars().first()
    
    if not dept:
        # Create the department if it doesn't exist
        dept = DepartmentModel(name=department_name)
        db.add(dept)
        await db.flush()
    
    # Create the project
    new_project = ProjectModel(
        title=title,
        description=description,
        department_id=dept.id,
        company_id=company_id,
        goal=goal,
        expected_value=expected_value,
        is_scheduled=is_scheduled,
        schedule_frequency=schedule_frequency,
        slack_channel=slack_channel,
        status="Not Started"
    )
    db.add(new_project)
    await db.flush()
    
    # Associate solutions (AI agents) if provided
    if solution_ids:
        for agent_id in solution_ids:
            # Check if agent exists
            agent_result = await db.execute(
                select(AgentModel).where(AgentModel.id == agent_id)
            )
            agent = agent_result.scalars().first()
            
            if agent:
                # Create association
                project_solution = ProjectSolutionModel(
                    project_id=new_project.id,
                    agent_id=agent_id
                )
                db.add(project_solution)
    
    await db.commit()
    await db.refresh(new_project)
    
    # Get company name if company_id is provided
    company_name = None
    if company_id:
        company_result = await db.execute(
            select(CompanyModel).where(CompanyModel.id == company_id)
        )
        company = company_result.scalars().first()
        if company:
            company_name = company.name
    
    # Return project details
    return {
        "id": new_project.id,
        "title": new_project.title,
        "description": new_project.description,
        "department": dept.name,
        "company_id": company_id,
        "company": company_name,
        "goal": new_project.goal,
        "expected_value": new_project.expected_value,
        "is_scheduled": new_project.is_scheduled,
        "schedule_frequency": new_project.schedule_frequency,
        "slack_channel": new_project.slack_channel,
        "status": new_project.status,
        "created_at": new_project.created_at.isoformat() if new_project.created_at else None,
        "updated_at": new_project.updated_at.isoformat() if new_project.updated_at else None
    }

async def get_projects_by_department(db: AsyncSession, department_name: str) -> List[Dict[str, Any]]:
    """Get all projects in a department."""
    # Get department ID
    dept_result = await db.execute(
        select(DepartmentModel).where(DepartmentModel.name == department_name)
    )
    dept = dept_result.scalars().first()
    
    if not dept:
        return []
    
    # Get projects
    projects_result = await db.execute(
        select(ProjectModel).where(ProjectModel.department_id == dept.id)
    )
    projects = projects_result.scalars().all()
    
    # Format results
    project_list = []
    for project in projects:
        # Get solutions (agents) for this project
        solutions_result = await db.execute(
            select(AgentModel)
            .join(ProjectSolutionModel, ProjectSolutionModel.agent_id == AgentModel.id)
            .where(ProjectSolutionModel.project_id == project.id)
        )
        solutions = solutions_result.scalars().all()
        
        solution_list = [{
            "id": solution.id,
            "name": solution.name,
            "role": solution.role
        } for solution in solutions]
        
        project_dict = {
            "id": project.id,
            "title": project.title,
            "description": project.description,
            "department": dept.name,
            "goal": project.goal,
            "expected_value": project.expected_value,
            "status": project.status,
            "solutions": solution_list,
            "created_at": project.created_at.isoformat() if project.created_at else None,
            "updated_at": project.updated_at.isoformat() if project.updated_at else None
        }
        project_list.append(project_dict)
    
    return project_list

async def get_project_by_id(db: AsyncSession, project_id: int) -> Optional[Dict[str, Any]]:
    """Get a project by ID."""
    project_result = await db.execute(
        select(ProjectModel).where(ProjectModel.id == project_id)
    )
    project = project_result.scalars().first()
    
    if not project:
        return None
    
    # Get department
    dept_result = await db.execute(
        select(DepartmentModel).where(DepartmentModel.id == project.department_id)
    )
    dept = dept_result.scalars().first()
    
    # Get solutions (agents) for this project
    solutions_result = await db.execute(
        select(AgentModel)
        .join(ProjectSolutionModel, ProjectSolutionModel.agent_id == AgentModel.id)
        .where(ProjectSolutionModel.project_id == project.id)
    )
    solutions = solutions_result.scalars().all()
    
    solution_list = [{
        "id": solution.id,
        "name": solution.name,
        "role": solution.role
    } for solution in solutions]
    
    return {
        "id": project.id,
        "title": project.title,
        "description": project.description,
        "department": dept.name if dept else None,
        "department_id": project.department_id,
        "goal": project.goal,
        "expected_value": project.expected_value,
        "status": project.status,
        "solutions": solution_list,
        "created_at": project.created_at.isoformat() if project.created_at else None,
        "updated_at": project.updated_at.isoformat() if project.updated_at else None
    }

async def update_project(
    db: AsyncSession,
    project_id: int,
    updates: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """Update a project."""
    # Get the project
    project_result = await db.execute(
        select(ProjectModel).where(ProjectModel.id == project_id)
    )
    project = project_result.scalars().first()
    
    if not project:
        return None
    
    # Handle department update if provided
    if "department" in updates:
        dept_name = updates.pop("department")
        dept_result = await db.execute(
            select(DepartmentModel).where(DepartmentModel.name == dept_name)
        )
        dept = dept_result.scalars().first()
        
        if dept:
            project.department_id = dept.id
    
    # Handle solutions update if provided
    if "solution_ids" in updates:
        solution_ids = updates.pop("solution_ids")
        
        # Remove existing associations
        await db.execute(
            text("DELETE FROM project_solutions WHERE project_id = :project_id"),
            {"project_id": project_id}
        )
        
        # Add new associations
        for agent_id in solution_ids:
            project_solution = ProjectSolutionModel(
                project_id=project_id,
                agent_id=agent_id
            )
            db.add(project_solution)
    
    # Update other fields
    for key, value in updates.items():
        if hasattr(project, key):
            setattr(project, key, value)
    
    # Update timestamp
    project.updated_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(project)
    
    # Return updated project
    return await get_project_by_id(db, project_id)

async def delete_project(db: AsyncSession, project_id: int) -> bool:
    """Delete a project and all associated data."""
    # Get the project
    project_result = await db.execute(
        select(ProjectModel).where(ProjectModel.id == project_id)
    )
    project = project_result.scalars().first()
    
    if not project:
        return False
    
    try:
        # First, delete all project_solutions associations
        await db.execute(
            text("DELETE FROM project_solutions WHERE project_id = :project_id"),
            {"project_id": project_id}
        )
        await db.flush()
        
        # Delete associated conversations
        # First find all conversations linked to this project
        conversations_result = await db.execute(
            select(ConversationModel).where(ConversationModel.project_id == project_id)
        )
        conversations = conversations_result.scalars().all()
        
        # Delete all messages from these conversations
        for conversation in conversations:
            await db.execute(
                text("DELETE FROM messages WHERE conversation_id = :conversation_id"),
                {"conversation_id": conversation.id}
            )
            
            # Delete the conversation
            await db.delete(conversation)
        
        # Now delete the project itself
        await db.delete(project)
        await db.commit()
        
        return True
    except Exception as e:
        # Log the error and rollback
        print(f"Error deleting project {project_id}: {str(e)}")
        await db.rollback()
        raise

async def get_roadmap(db: AsyncSession) -> Dict[str, Any]:
    """Get the roadmap view with all departments and their projects."""
    # Ensure default departments exist
    await ensure_default_departments(db)
    
    # Get all departments
    dept_result = await db.execute(select(DepartmentModel))
    departments = dept_result.scalars().all()
    
    roadmap = {}
    for dept in departments:
        # Get projects for this department
        projects = await get_projects_by_department(db, dept.name)
        
        # Add to roadmap
        roadmap[dept.name] = {
            "id": dept.id,
            "name": dept.name,
            "description": dept.description,
            "project_count": len(projects),
            "projects": projects
        }
    
    return roadmap

async def get_project_conversations(db, project_id: int) -> List[Dict[str, Any]]:
    """Get all conversations for a specific project."""
    result = await db.execute(
        select(db.ConversationModel)
        .where(db.ConversationModel.project_id == project_id)
        .order_by(db.ConversationModel.updated_at.desc())
    )
    conversations = result.scalars().all()
    
    return [
        {
            "id": str(conversation.id),
            "title": conversation.title,
            "agent_id": conversation.agent_id,
            "created_at": conversation.created_at.isoformat() if conversation.created_at else None,
            "updated_at": conversation.updated_at.isoformat() if conversation.updated_at else None,
        }
        for conversation in conversations
    ] 