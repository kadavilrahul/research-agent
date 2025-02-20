# Getting Started with the Multi-Agent System

This guide will walk you through the steps to install and run the multi-agent system, including the Shell Agent and the GitHub Search Agent.

## Prerequisites

*   Python 3.6 or higher
*   pip package installer
*   A Gemini API key
*   A GitHub API key (personal access token)

## Installation

1.  Clone the repository:

    ```bash
    git clone https://github.com/kadavilrahul/browser-agent-testing.git .
    ```

2.  Create a virtual environment (optional but recommended):
    # On Linux and macOS
    ```bash
    python3 -m venv .venv && source .venv/bin/activate  
    ```
    # On Windows
    ```powershell
    .venv\\Scripts\\activate  
    ```

3.  Install the dependencies:

    ```bash
    pip install -r requirements.txt
    ```


4.  Install Playwright:

    Install the browsers:

    ```bash
    playwright install firefox
    ```

## Configuration

1.  Set up the environment variables:

    *   Create a `.env` file in the root directory of the project.
    *   Add your Gemini API key and GitHub API key to the `.env` file:

        ```
        GEMINI_API_KEY=<your_gemini_api_key>
        GITHUB_API_KEY=<your_github_api_key>
        ```

## Running the Agent

1.  Run the `multi_agent_gemini.py` script:

    ```bash
    python multi_agent_gemini.py
    ```

2.  The script will:

    *   List the files in the current directory using the Shell Agent.
    *   Search GitHub for repositories related to 'machine learning' and generate a report using the GitHub Search Agent.
    *   Save the report to a file named `github_report.txt` in the current directory.

## Troubleshooting

*   If you encounter a `ModuleNotFoundError: No module named 'playwright'`, make sure you have installed Playwright correctly using `pip install playwright` and `playwright install firefox`.
*   If you encounter a `google.genai.errors.ClientError: 400 INVALID_ARGUMENT` error, make sure your Gemini API key is valid and that you have properly configured the tool definitions.

## Notes

*   This guide assumes you have a basic understanding of Python and command-line interfaces.
*   The GitHub API key requires the `repo` scope to search for repositories.
