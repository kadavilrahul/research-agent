from agno.agent import Agent
from agno.models.google.gemini import Gemini
import subprocess
import os
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright
import requests

load_dotenv()

# Get API keys from environment variables
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
REDDIT_USERNAME = os.getenv('REDDIT_USERNAME')
REDDIT_PASSWORD = os.getenv('REDDIT_PASSWORD')

# Check if all required environment variables are set
if not all([GEMINI_API_KEY, GITHUB_TOKEN, REDDIT_USERNAME, REDDIT_PASSWORD]):
    raise ValueError("Missing required environment variables")

# Define a tool for the Shell Agent to execute shell commands
def shell_tool(command: str) -> str:
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, check=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        return f"Error: {e.stderr}"
shell_tool.__name__ = "ShellTool"
shell_tool.description = "Execute shell commands"
shell_tool.parameters = {
    "command": {"type": "string", "description": "The command to execute"}
}

def github_search_tool(topic: str, github_token: str, num_repos: int = 5) -> dict:
    headers = {
        "Authorization": f"token {github_token}",
        "Accept": "application/vnd.github.v3+json",
    }
    url = f"https://api.github.com/search/repositories?q={topic}&per_page={num_repos}"
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
        return response.json()
    except requests.exceptions.RequestException as e:
        return f"GitHub API error: {e}"
github_search_tool.__name__ = "GithubSearchTool"
github_search_tool.description = "Search GitHub repositories based on a topic"
github_search_tool.parameters = {
    "topic": {"type": "string", "description": "The topic to search for", "type": "string"},
    "github_token": {"type": "string", "description": "The GitHub API token", "type": "string"},
    "num_repos": {"type": "integer", "description": "The number of repositories to return", "type": "integer"},
}

def report_generation_tool(repositories: list, filename: str = "github_report.txt") -> str:
    try:
        with open(filename, "w") as f:
            f.write("GitHub Repository Report\n\n")
            for repo in repositories:
                f.write(f"Name: {repo['name']}\n")
                f.write(f"URL: {repo['html_url']}\n")
                f.write(f"Description: {repo['description']}\n")
                f.write(f"Stars: {repo['stargazers_count']}\n")
                f.write("\n")
        return f"Report generated successfully in {filename}"
    except Exception as e:
        return f"Error generating report: {e}"
report_generation_tool.__name__ = "ReportGenerationTool"
report_generation_tool.description = "Generate a report from a list of GitHub repositories"
report_generation_tool.parameters = {
    "repositories": {"type": "array", "description": "The list of repositories to generate the report from", "type": "array"},
    "filename": {"type": "string", "description": "The name of the file to save the report to", "type": "string"},
}

def github_search_and_report(topic: str) -> str:
    repositories = github_search_tool(topic, GITHUB_TOKEN)
    if isinstance(repositories, str):
        return repositories  # Return the error message if there's an error
    report_file = report_generation_tool(repositories['items'])
    return report_file
github_search_and_report.__name__ = "GithubSearchAndReport"

def reddit_login_tool(username: str, password: str) -> str:
    """Tool to login to Reddit and extract latest posts"""
    try:
        with sync_playwright() as p:
            browser = p.firefox.launch(headless=True)
            page = browser.new_page()
            
            # Navigate to Reddit login
            page.goto("https://www.reddit.com/login/")
            page.fill('input[name="username"]', username)
            page.fill('input[name="password"]', password)
            page.click('button[type="submit"]')
            page.wait_for_load_state('networkidle')
            
            # Wait for login and navigation
            page.wait_for_timeout(5000)  # Wait for 5 seconds
            
            # Go to Reddit homepage
            page.goto("https://www.reddit.com")
            page.wait_for_load_state('networkidle')
            
            # Extract latest posts
            posts = []
            post_elements = page.query_selector_all('div[data-testid="post-container"]')
            
            for post in post_elements[:10]:  # Get first 10 posts
                try:
                    title_element = post.query_selector('h3')
                    if title_element:
                        title = title_element.inner_text()
                        posts.append(title)
                except Exception as e:
                    print(f"Error extracting post: {e}")
            
            # Save posts to file
            filename = "reddit_posts.txt"
            with open(filename, "w", encoding='utf-8') as f:
                f.write("Latest Reddit Posts:\n\n")
                for idx, post in enumerate(posts, 1):
                    f.write(f"{idx}. {post}\n")
            
            browser.close()
            return f"Login successful. {len(posts)} latest Reddit posts saved to {filename}"
    except Exception as e:
        return f"Login failed: {str(e)}"

def summary_tool(shell_output: str, github_report: str, reddit_posts: str) -> str:
    try:
        filename = "summary_report.txt"
        with open(filename, "w") as f:
            f.write("Multi-Agent System Summary Report\n\n")
            f.write("Shell Agent Output:\n")
            f.write(f"{shell_output}\n\n")
            f.write("GitHub Search Agent Report:\n")
            f.write(f"{github_report}\n\n")
            f.write("Reddit Login Agent Posts:\n")
            f.write(f"{reddit_posts}\n\n")
        return f"Summary report generated successfully in {filename}"
    except Exception as e:
        return f"Error generating summary report: {e}"
summary_tool.__name__ = "SummaryTool"
summary_tool.description = "Combine the results from all agents and provide a summary in a text file"
summary_tool.parameters = {
    "shell_output": {"type": "string", "description": "Output from the Shell Agent"},
    "github_report": {"type": "string", "description": "Report from the GitHub Search Agent"},
    "reddit_posts": {"type": "string", "description": "Posts from the Reddit Login Agent"},
}

# Create the Shell Agent
shell_agent = Agent(
    name="Shell Agent",
    role="Execute shell commands",
    model=Gemini(id="gemini-2.0-flash-exp", api_key=GEMINI_API_KEY, generative_model_kwargs={}, generation_config={}),
    tools=[shell_tool],
    instructions="Execute shell commands to manage files and interact with the system.",
    show_tool_calls=True,
    markdown=True,
)

# Create the Playwright Agent
playwright_agent = Agent(
    name="Playwright Agent",
    role="Automate web browser interactions using Playwright",
    model=Gemini(id="gemini-2.0-flash-exp", api_key=GEMINI_API_KEY, generative_model_kwargs={}, generation_config={}),
    tools=[reddit_login_tool],
    instructions="Use Playwright to interact with websites, fill forms, and extract data.",
    show_tool_calls=True,
    markdown=True,
)

# Create the GitHub Search Agent
github_search_agent = Agent(
    name="GitHub Search Agent",
    role="Search GitHub repositories and generate reports",
    model=Gemini(id="gemini-2.0-flash-exp", api_key="AIzaSyA5bfenANZwEDV5vfSWWaFWuX4cD2ejJSQ", generative_model_kwargs={}, generation_config={}),
    tools=[github_search_and_report],
    instructions="Search GitHub repositories based on a topic and generate a report with the results.",
    show_tool_calls=True,
    markdown=True,
)

# Create the Team Agent
agent_team = Agent(
    team=[shell_agent, playwright_agent, github_search_agent],
    model=Gemini(id="gemini-2.0-flash-exp", api_key="AIzaSyB48vuy896DMMBUJZYWURZwdKD-DDHM41U", generative_model_kwargs={}, generation_config={}),
    tools=[shell_tool, github_search_and_report, reddit_login_tool, summary_tool],
    instructions=[
        "You are a team coordinator. Delegate tasks to the Shell Agent, Playwright Agent, or GitHub Search Agent based on their roles.",
        "If a task involves shell command execution, delegate it to the Shell Agent.",
        "If a task involves web browser automation, delegate it to the Playwright Agent.",
        "If a task involves searching GitHub repositories, delegate it to the GitHub Search Agent.",
        "If the user asks to login to reddit, use the reddit_login_tool with the provided credentials and save the latest posts to a file.",
        "Combine the results from the agents and provide a summary in a text file in the current directory.",
    ],
    show_tool_calls=True,
    markdown=True,
)

def display_menu():
    """Display the main menu options"""
    print("\n=== Agent Selection Menu ===")
    print("1. Run Shell Agent (List files)")
    print("2. Run GitHub Search Agent")
    print("3. Run Reddit Playwright Agent")
    print("4. Generate Summary Report")
    print("5. Exit")
    return input("Enter your choice (1-5): ")

def run_shell_agent(agent_team):
    """Run the Shell Agent"""
    shell_command = "ls -la"
    print("\nExecuting Shell Agent...")
    shell_response = agent_team.print_response(
        f"Execute the command '{shell_command}' in the shell.", 
        stream=True
    )
    print(f"Shell Agent Response: {shell_response}")
    return shell_response

def run_github_agent(agent_team):
    """Run the GitHub Search Agent"""
    github_topic = input("\nEnter the topic to search on GitHub: ")
    print("\nExecuting GitHub Search Agent...")
    github_response = agent_team.print_response(
        f"Search GitHub for repositories related to '{github_topic}' and generate a report.", 
        stream=True
    )
    print(f"GitHub Agent Response: {github_response}")
    return github_response

def run_reddit_agent(agent_team):
    """Run the Reddit Playwright Agent"""
    print("\nExecuting Reddit Playwright Agent...")
    reddit_response = agent_team.print_response(
        f"Login to Reddit with username '{REDDIT_USERNAME}' and password '{REDDIT_PASSWORD}' "
        "and search for latest posts and save it in a file in the current directory.", 
        stream=True
    )
    print(f"Reddit Agent Response: {reddit_response}")
    return reddit_response

def generate_summary(agent_team, responses):
    """Generate a summary report"""
    print("\nGenerating Summary Report...")
    summary_response = agent_team.print_response(
        f"Combine the results from all agents and provide a summary in a text file in the current directory. "
        f"Shell Agent Response: {responses.get('shell', 'Not Run')}. "
        f"GitHub Agent Response: {responses.get('github', 'Not Run')}. "
        f"Reddit Agent Response: {responses.get('reddit', 'Not Run')}", 
        stream=True
    )
    print(f"Summary Report: {summary_response}")

def main():
    responses = {}
    while True:
        choice = display_menu()
        
        if choice == '1':
            responses['shell'] = run_shell_agent(agent_team)
        elif choice == '2':
            responses['github'] = run_github_agent(agent_team)
        elif choice == '3':
            responses['reddit'] = run_reddit_agent(agent_team)
        elif choice == '4':
            if not responses:
                print("\nNo agent responses available. Please run at least one agent first.")
            else:
                generate_summary(agent_team, responses)
        elif choice == '5':
            print("\nExiting program...")
            break
        else:
            print("\nInvalid choice. Please select a number between 1 and 5.")

# Replace the existing get_api_key_and_list_files() call with:
if __name__ == "__main__":
    main()
