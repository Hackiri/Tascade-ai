"""
Task Verifier for Tascade AI.

This module provides functionality for verifying task completion and ensuring
that tasks meet their defined verification criteria.

Inspired by the task verification system in mcp-shrimp-task-manager.
"""

from typing import Dict, List, Optional, Any, Union
from .models import Task, TaskStatus
from .ai_providers.base import BaseAIProvider
import json
from datetime import datetime

class TaskVerifier:
    """
    Verifies task completion and ensures tasks meet their verification criteria.
    
    This class provides methods for validating that completed tasks meet their
    defined verification criteria, generating verification reports, and
    suggesting improvements for tasks that don't pass verification.
    """
    
    def __init__(self, ai_provider: Optional[BaseAIProvider] = None):
        """
        Initialize the TaskVerifier.
        
        Args:
            ai_provider: Optional AI provider for enhanced verification capabilities
        """
        self.ai_provider = ai_provider
        
        # Define verification criteria categories
        self.criteria_categories = {
            "functional": "Does the implementation meet all functional requirements?",
            "performance": "Does the implementation meet performance requirements?",
            "security": "Does the implementation address security concerns?",
            "code_quality": "Does the code meet quality standards?",
            "testing": "Are there sufficient tests for the implementation?"
        }
    
    def verify_task(self, task: Task, artifacts: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Verify that a task meets its verification criteria.
        
        Args:
            task: The task to verify
            artifacts: Optional dictionary of artifacts related to the task (e.g., code, test results)
            
        Returns:
            Dictionary with verification results
        """
        # Check if task has verification criteria
        if not task.verification_criteria:
            return {
                "verified": False,
                "score": 0,
                "message": "No verification criteria defined for this task",
                "recommendations": ["Define verification criteria for the task"]
            }
        
        # If using AI provider for enhanced verification
        if self.ai_provider:
            try:
                return self._verify_task_with_ai(task, artifacts)
            except Exception as e:
                print(f"Error using AI provider for task verification: {str(e)}")
                # Fall back to heuristic verification if AI fails
        
        # Heuristic-based verification (fallback)
        return self._verify_task_heuristic(task, artifacts)
    
    def _verify_task_with_ai(self, task: Task, artifacts: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Verify a task using AI.
        
        Args:
            task: The task to verify
            artifacts: Optional dictionary of artifacts related to the task
            
        Returns:
            Dictionary with verification results
        """
        if not self.ai_provider:
            raise ValueError("No AI provider available for task verification")
        
        # Prepare task data for AI
        task_data = {
            "id": task.id,
            "title": task.title,
            "description": task.description or "",
            "verification_criteria": task.verification_criteria or "",
            "implementation_guide": task.implementation_guide or ""
        }
        
        # Prepare artifacts data
        artifacts_data = {}
        if artifacts:
            # Limit the size of artifacts to avoid token limits
            for key, value in artifacts.items():
                if isinstance(value, str) and len(value) > 1000:
                    artifacts_data[key] = value[:1000] + "... [truncated]"
                else:
                    artifacts_data[key] = value
        
        # Create prompt for AI
        prompt = f"""
        Verify the following task against its verification criteria:
        
        Task: {json.dumps(task_data, indent=2)}
        
        Artifacts: {json.dumps(artifacts_data, indent=2) if artifacts_data else "No artifacts provided"}
        
        Please evaluate the task completion against the verification criteria and provide:
        1. A verification score (0-100)
        2. A detailed assessment of how well the task meets each criterion
        3. Specific recommendations for improvement if the score is below 80
        
        Provide your response as a JSON object with the following structure:
        {{
            "verified": <boolean>,
            "score": <number 0-100>,
            "assessment": "Detailed assessment of the task verification",
            "criteria_scores": {{
                "criterion1": <number 0-100>,
                "criterion2": <number 0-100>,
                ...
            }},
            "recommendations": [
                "Recommendation 1",
                "Recommendation 2",
                ...
            ]
        }}
        """
        
        # Get verification results from AI provider
        system_prompt = "You are an expert task verification specialist. Evaluate task completion against verification criteria."
        response = self.ai_provider.generate_text(prompt, system_prompt)
        
        # Parse response as JSON
        try:
            # Extract JSON from response (in case there's markdown or other text)
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                json_str = response[json_start:json_end]
                verification_result = json.loads(json_str)
                
                # Add timestamp
                verification_result["timestamp"] = datetime.now().isoformat()
                
                return verification_result
            else:
                raise ValueError("Could not extract JSON from AI response")
        except json.JSONDecodeError as e:
            raise ValueError(f"Could not parse AI response as JSON: {str(e)}")
    
    def _verify_task_heuristic(self, task: Task, artifacts: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Verify a task using heuristic methods.
        
        Args:
            task: The task to verify
            artifacts: Optional dictionary of artifacts related to the task
            
        Returns:
            Dictionary with verification results
        """
        # Simple heuristic verification
        verification_result = {
            "verified": False,
            "score": 0,
            "assessment": "",
            "criteria_scores": {},
            "recommendations": [],
            "timestamp": datetime.now().isoformat()
        }
        
        # Parse verification criteria into individual criteria
        criteria = []
        if task.verification_criteria:
            # Simple parsing (could be improved)
            criteria = [c.strip() for c in task.verification_criteria.split('\n') if c.strip()]
        
        if not criteria:
            verification_result["assessment"] = "No specific verification criteria found"
            verification_result["recommendations"].append("Define specific verification criteria for the task")
            return verification_result
        
        # Evaluate each criterion
        total_score = 0
        for i, criterion in enumerate(criteria):
            criterion_key = f"criterion_{i+1}"
            
            # Simple keyword matching (could be improved)
            criterion_score = 0
            if artifacts:
                # Check if criterion keywords are present in artifacts
                keywords = [word.lower() for word in criterion.split() if len(word) > 3]
                matches = 0
                
                for artifact_value in artifacts.values():
                    if isinstance(artifact_value, str):
                        artifact_text = artifact_value.lower()
                        for keyword in keywords:
                            if keyword in artifact_text:
                                matches += 1
                
                if keywords:
                    criterion_score = min(100, int((matches / len(keywords)) * 100))
                else:
                    criterion_score = 50  # Default if no keywords
            else:
                # No artifacts to verify against
                criterion_score = 0
            
            verification_result["criteria_scores"][criterion_key] = criterion_score
            total_score += criterion_score
        
        # Calculate overall score
        if criteria:
            verification_result["score"] = total_score // len(criteria)
        
        # Set verified status
        verification_result["verified"] = verification_result["score"] >= 80
        
        # Generate assessment
        if verification_result["verified"]:
            verification_result["assessment"] = f"Task verified with a score of {verification_result['score']}%"
        else:
            verification_result["assessment"] = f"Task verification failed with a score of {verification_result['score']}%"
            
            # Generate recommendations
            verification_result["recommendations"].append("Review the verification criteria and ensure the implementation meets them")
            verification_result["recommendations"].append("Provide more detailed artifacts for verification")
            
            # Add specific recommendations based on low-scoring criteria
            for criterion_key, score in verification_result["criteria_scores"].items():
                if score < 60:
                    criterion_index = int(criterion_key.split('_')[1]) - 1
                    if criterion_index < len(criteria):
                        verification_result["recommendations"].append(f"Address criterion: {criteria[criterion_index]}")
        
        return verification_result
    
    def generate_verification_report(self, task: Task, verification_result: Dict[str, Any]) -> str:
        """
        Generate a human-readable verification report.
        
        Args:
            task: The verified task
            verification_result: The verification result dictionary
            
        Returns:
            Formatted verification report
        """
        report = [
            f"# Verification Report for Task: {task.title} (ID: {task.id})",
            "",
            f"## Verification Status: {'PASSED' if verification_result.get('verified', False) else 'FAILED'}",
            f"## Score: {verification_result.get('score', 0)}%",
            "",
            "## Assessment",
            verification_result.get('assessment', 'No assessment provided'),
            ""
        ]
        
        # Add criteria scores if available
        criteria_scores = verification_result.get('criteria_scores', {})
        if criteria_scores:
            report.append("## Criteria Scores")
            for criterion, score in criteria_scores.items():
                report.append(f"- {criterion}: {score}%")
            report.append("")
        
        # Add recommendations if available
        recommendations = verification_result.get('recommendations', [])
        if recommendations:
            report.append("## Recommendations")
            for recommendation in recommendations:
                report.append(f"- {recommendation}")
            report.append("")
        
        # Add timestamp
        timestamp = verification_result.get('timestamp', datetime.now().isoformat())
        report.append(f"Generated at: {timestamp}")
        
        return "\n".join(report)
    
    def suggest_improvements(self, task: Task, verification_result: Dict[str, Any]) -> List[str]:
        """
        Suggest improvements for a task that failed verification.
        
        Args:
            task: The task that failed verification
            verification_result: The verification result dictionary
            
        Returns:
            List of improvement suggestions
        """
        if verification_result.get('verified', False):
            return ["Task passed verification, no improvements needed"]
        
        # Start with recommendations from verification result
        suggestions = verification_result.get('recommendations', [])
        
        # Add general suggestions based on score
        score = verification_result.get('score', 0)
        if score < 50:
            suggestions.append("Consider revising the task implementation completely")
        elif score < 70:
            suggestions.append("Focus on addressing the specific criteria that scored lowest")
        else:
            suggestions.append("Make minor adjustments to meet all verification criteria")
        
        # Add specific suggestions based on criteria scores
        criteria_scores = verification_result.get('criteria_scores', {})
        for criterion, score in criteria_scores.items():
            if score < 60:
                suggestions.append(f"Prioritize improving {criterion} which scored only {score}%")
        
        # If using AI provider, get more detailed suggestions
        if self.ai_provider and task.verification_criteria:
            try:
                prompt = f"""
                A task has failed verification with a score of {score}%.
                
                Task: {task.title}
                Description: {task.description or 'No description'}
                Verification Criteria: {task.verification_criteria}
                
                Please suggest 3-5 specific improvements that would help this task pass verification.
                Focus on practical, actionable suggestions.
                """
                
                system_prompt = "You are an expert task improvement specialist. Provide specific, actionable suggestions to help tasks pass verification."
                response = self.ai_provider.generate_text(prompt, system_prompt)
                
                # Extract suggestions (simple parsing)
                ai_suggestions = []
                for line in response.split('\n'):
                    line = line.strip()
                    if line.startswith('-') or line.startswith('*') or (line.startswith(str(len(ai_suggestions)+1)) and '.' in line):
                        suggestion = line.split('.', 1)[-1].split(':', 1)[-1].strip()
                        if suggestion and len(suggestion) > 10:
                            ai_suggestions.append(suggestion)
                
                if ai_suggestions:
                    suggestions.extend(ai_suggestions)
            except Exception as e:
                print(f"Error getting AI suggestions: {str(e)}")
        
        return suggestions
