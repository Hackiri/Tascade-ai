import markdown
from bs4 import BeautifulSoup
from typing import List, Dict, Optional

class MarkdownPRDParser:
    def __init__(self):
        pass

    def parse_file(self, file_path: str) -> List[Dict[str, str]]:
        """Parses a Markdown file and extracts potential tasks."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                md_content = f.read()
            return self.parse_content(md_content)
        except FileNotFoundError:
            print(f"Error: PRD file not found at {file_path}")
            return []
        except Exception as e:
            print(f"Error reading PRD file {file_path}: {e}")
            return []

    def parse_content(self, md_content: str) -> List[Dict[str, str]]:
        """Parses Markdown content and extracts potential tasks."""
        if not md_content.strip():
            return []

        html_content = markdown.markdown(md_content)
        soup = BeautifulSoup(html_content, 'html.parser')

        potential_tasks = []
        
        # Look for H2 and H3 headings as potential task titles
        for heading in soup.find_all(['h2', 'h3']):
            title = heading.get_text(strip=True)
            description_parts = []
            current_sibling = heading.next_sibling
            
            while current_sibling:
                if current_sibling.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                    # Stop if we hit another heading of same or higher level
                    break
                if current_sibling.name == 'p':
                    description_parts.append(current_sibling.get_text(strip=True))
                elif current_sibling.name is None and current_sibling.string and current_sibling.string.strip():
                    # Handle navitagablestrings that are not wrapped in a tag, if meaningful
                    pass # Usually, we care more about <p> tags for description
                current_sibling = current_sibling.next_sibling
            
            description = "\n".join(description_parts).strip()
            
            if title:
                task_data = {"title": title}
                if description:
                    task_data["description"] = description
                potential_tasks.append(task_data)
                
        return potential_tasks

# Example Usage (can be run directly for testing)
if __name__ == '__main__':
    parser = MarkdownPRDParser()
    
    # Create a dummy PRD content for testing
    dummy_prd_content = """
# Project XYZ

This is an introduction.

## Feature A: User Authentication
Implement a full user authentication system.
This includes sign-up, sign-in, and password reset.

## Feature B: Dashboard
Create a user dashboard to display key information.
It should be responsive.

### Sub-feature B1: Profile Section
Allow users to view and edit their profiles.

Some other text not related to a task directly.

## Feature C: Reporting
Generate monthly reports for administrators.
"""
    
    print("--- Parsing dummy content ---")
    tasks_from_content = parser.parse_content(dummy_prd_content)
    for i, task in enumerate(tasks_from_content):
        print(f"Task {i+1}:")
        print(f"  Title: {task.get('title')}")
        print(f"  Description: {task.get('description', 'N/A')}")
        print("---")

    # To test file parsing, you would create a sample.md file
    # with open("sample.md", "w") as f:
    #     f.write(dummy_prd_content)
    # print("\n--- Parsing dummy file sample.md ---")
    # tasks_from_file = parser.parse_file("sample.md")
    # for i, task in enumerate(tasks_from_file):
    #     print(f"Task {i+1}:")
    #     print(f"  Title: {task.get('title')}")
    #     print(f"  Description: {task.get('description', 'N/A')}")
    #     print("---")
    # import os
    # os.remove("sample.md")

