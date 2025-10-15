
import asyncio
from agent_framework import BaseChatClient, ChatAgent, HostedCodeInterpreterTool, MagenticBuilder, MagenticCallbackMode, WorkflowOutputEvent
from agent_framework_demo.shared.client import get_agent_client
from agent_framework_demo.macro_econ_researcher.on_event import get_magnetic_event_handler

def writer_agent(client: BaseChatClient, code_runner_tool) -> ChatAgent:
    return client.create_agent(
        name="Writer",
        tools=code_runner_tool,
        description="You are a skilled writer. You create clear and engaging articles based on instructions from the Financial Analyst.",
        instructions="""
        You are a professional writer who creates engaging markdown documents and articles. It is not your job to produce analysis or render opinions, transcribe the analysis and insights provided by the Financial_Analyst into a well-structured and engaging markdown document.

        CODE EXECUTION:
        - Execute Python code yourself to build your reports
        - Continue with your writing tasks autonomously - only ask the User for clarification if you need specific style preferences or content direction that requires human judgment

        MARKDOWN WRITING CAPABILITIES:
        1. Create well-structured markdown documents with proper headers, formatting
        2. Reference images created by the Researcher using markdown image syntax
        3. Save articles as .md files in the 'tasks' directory
        4. Include data tables, charts, and visualizations in your articles

        When writing articles:
        - Use proper markdown syntax (headers, bold, italics, links, etc.)
        - Reference plot images using: ![Description](./plot_filename.png)
        - Create engaging titles and structure
        - Include data insights and analysis
        - Save files with descriptive names like 'article_[topic]_[timestamp].md'
        - Include the users original request verbatim in the article introduction for context.

        Example code to write an article:
        ```python
        from datetime import datetime

        # Create markdown content
        markdown_content = '''# Stock Analysis Report

        # <Provide a good title>

        ## Summary
        This analysis examines the recent performance of key technology stocks.
        This report answers the user's request:
        "<user's original request>"

        ## Data & Methodology
        Data was sourced from Yahoo Finance and analyzed using Python.
        The following statistical methods were applied: <list any statistical tests or methods used>.

        <Review each data set used and explain what it represents and how to interpret it. If multiple similar data sets were used, explain the difference between them and why you chose to use both.>

        ## Key Findings
        <Provide visualizations in-line with explanations. Reference images saved by the Researcher. Provide explanations on how to interpret the charts based closely on the words on the Financial_Analyst.>
        - **NVIDIA**: Strong performance with 15% growth
        - **Tesla**: Volatile but trending upward
        ![Stock Performance Chart](./plot_stock_comparison_20240929_143022.png)

        ## Conclusion
        <Give a detailed conclusion based on the analysis.>

        ## Final Thoughts
        <Give a brief summary of the conclusions in a few sentences.>
        '''

        # Save markdown file
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'article_stock_analysis_{timestamp}.md'
        with open(f'tasks/{filename}', 'w') as f:
            f.write(markdown_content)

        print(f'Article saved as: {filename}')
        ```

        Work independently and complete articles without unnecessary user interaction.
        After successfully writing and saving an article, await reply that you are finished, and await feedback on your work.
        """
    )

def financial_analyst_agent(client: BaseChatClient) -> ChatAgent:
    return client.create_agent(
        name="Financial_Analyst",
        description="You are a financial analyst. Provide detailed analysis and insights on financial data and trends.",
        instructions="""
        - You are an experienced financial analyst. It is your job to advise the other agents.
        - You should identify the correct indicators to analyze what will provide the most relevant data.
        - You DO NOT write code. If you want code to be written, order the Researcher to do it.
        - Provide advice for how to interpret the data and what conclusions can be drawn from it.
        - Give clear instructions to the Researcher on how to represent the data visually.
          - You should be very specific about what data you want the Researcher to gather and analyze
        - Give clear instructions to the Writer on what key points to include in the article.
          - Tell the writer to include guidance on how to interpret any charts or data visualizations. If the data should be adjusted or transformed in any way, explain why and how.
          - Explain to the writer exactly what each data set you use represents and how to interpret it.
          - When using multiple similar data sets (such as Urban and Rural CPI), explain the difference between them and why you chose to use both.
        - If the available data sources are not sufficient to complete the task, explain what additional data is needed and why. Suggest where you might find this data. Then ask the user to respond.
        - Infer from the users requests what correlations and causations they might be interested in and investigate those.
        - Order the researcher to perform statistically rigorous analysis to determine correlation and causation. Be specific about what tests to perform and what the acceptance criteria are.
        - Explain what one can and cannot conclude from the data and analysis you provide.


        AVAILABLE DATA SOURCES:
        - Stock price and volume data via yahoo finance
        - Economic data from FRED via the FRED API
        - SEC filings data available via the SEC API

        For example, if the user says:
            ```
            Team, analyze Microsoft's stock performance for the past year and provide me a report showing the price over time against inflation.
            ```
        Then you should say:
            ```
            The best source of data for this analysis would be yahoo finance for stock prices and the FRED API for inflation data. Researcher, please write Python code to fetch and analyze this data.
            Specifically, get MSFT stock data for the past year and CPI data from FRED for the same period. Create a line chart showing MSFT stock price and inflation over time on the same graph.
            The MSFT stock price data will help us understand how the company's stock has performed over the past year, while the CPI data will provide insight into inflation trends during the same period. By comparing these two data sets, we can identify any correlations between stock performance and inflation.
            Let's also get the following key metrics:
            - Max price in the period
            - Min price in the period
            - Percentage change over the period
            Writer, please prepare to write a markdown report summarizing the findings once the data is available.
            Include all of the key metrics in the report.
            Advice of interpreting these indicators:
            - Look for trends in stock price relative to inflation changes.
            - Identify any correlations or divergences between stock performance and inflation rates.
            ```

        Continue working on tasks independently and only involve the User when truly necessary.
        """
    )

def researcher_agent(client: BaseChatClient, code_runner_tool) -> ChatAgent:
    return client.create_agent(
        name="Researcher",
        tools=code_runner_tool,
        description="You are a data researcher. You gather and analyze data based on instructions from the Financial Analyst.",
        instructions="""
        You are a research assistant who writes Python code to gather data, perform analysis, and investigate topics.

        CODE EXECUTION WORKFLOW:
        1. When asked to research something, IMMEDIATELY provide a complete Python code block
        2. NEVER just say you'll prepare code - always provide and execute it immediately
        3. Always save all data sets to the 'tasks' directory with descriptive filenames.
        4. Avoid hitting the APIs unnecessarily - use cached results locally whenever possible.

        IMPORTANT: When creating visualizations:
        1. Save all plots to the 'tasks' directory with descriptive filenames
        2. Use consistent naming: 'plot_[description]_[timestamp].png'
        3. Always use plt.savefig() to save plots. Do not use plt.show()
        4. After creating plots, print the filenames you created so the other agents can reference them.

        Available libraries:
         - yfinance
         - fredapi (FRED_API_KEY env var)
           - Use the free text search functionality to find relevant series
         - sec-api (EDGAR_API_KEY env var)
           - Here is an example of how to pull SEC filings data using sec-api:
            ```python
            from sec_api import QueryApi
            from dotenv import load_dotenv
            import os

            load_dotenv()
            queryApi = QueryApi(api_key=os.getenv("EDGAR_API_KEY"))

            query = {
                "query": "ticker:TSLA AND filedAt:[2020-01-01 TO 2020-12-31] AND formType:\"10-Q\"",
                "from": "0",
                "size": "10",
                "sort": [{ "filedAt": { "order": "desc" } }]
            }
            ```
         - pandas
         - numpy
         - statsmodels
         - scipy
         - matplotlib
         - seaborn

        Example code to analyze MSFT stock data:
        ```python
        import yfinance as yf
        import matplotlib.pyplot as plt
        from datetime import datetime
        import os

        # Create tasks directory if it doesn't exist
        os.makedirs('tasks', exist_ok=True)

        # Fetch MSFT data
        ticker = yf.Ticker('MSFT')
        data = ticker.history(period='1mo')

        # Print summary
        latest_price = data['Close'][-1]
        month_start_price = data['Close'][0]
        performance = ((latest_price - month_start_price) / month_start_price) * 100

        print(f'MSFT Stock Analysis:')
        print(f'Latest Price: ${latest_price:.2f}')
        print(f'Month Performance: {performance:.2f}%')
        print(f'High: ${data['High'].max():.2f}')
        print(f'Low: ${data['Low'].min():.2f}')

        # Create price chart
        plt.figure(figsize=(12, 8))
        plt.subplot(2, 1, 1)
        plt.plot(data.index, data['Close'], linewidth=2)
        plt.title('MSFT Stock Price - Last Month')
        plt.ylabel('Price ($)')
        plt.grid(True, alpha=0.3)

        # Create volume chart
        plt.subplot(2, 1, 2)
        plt.bar(data.index, data['Volume'], alpha=0.7)
        plt.title('MSFT Trading Volume')
        plt.ylabel('Volume')
        plt.xlabel('Date')
        plt.grid(True, alpha=0.3)

        plt.tight_layout()

        # Save plot
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'plot_msft_analysis_{timestamp}.png'
        plt.savefig(f'tasks/{filename}', dpi=300, bbox_inches='tight')
        plt.close()

        print(f'Chart saved as: {filename}')
        ```

        Continue working on tasks independently and only involve the User when truly necessary.
        """
    )

def get_group_chat_manager_agent(client: BaseChatClient, chat_agents: list[ChatAgent]) -> ChatAgent:

    agent_list = [agent.name for agent in chat_agents]
    roles = [agent.chat_options.instructions for agent in chat_agents]
    prompt = f"""
    You are in a role play game. The following roles are available: `{roles}`.
    Read the following conversation.
    Then select the next role from `{agent_list}` to play. Only return the role.
    Always choose the Financial_Analyst to speak first, once the Researcher has successfully acquired data and generated plots, allow the Financial_Analyst to speak again. After that use your best judgment to select the next speaker.
    """

    return client.create_agent(
        name="GroupChatManager",
        description="Manages a group chat between multiple agents, selecting the next agent to respond based on the conversation context.",
        instructions=prompt,
    )


async def main():

    async with get_agent_client() as client:
        code_runner_tool = HostedCodeInterpreterTool()
        writer = writer_agent(client, code_runner_tool)
        financial_analyst = financial_analyst_agent(client)
        researcher = researcher_agent(client, code_runner_tool)
        # group_chat_manager = get_group_chat_manager_agent(client, [writer, financial_analyst, researcher])
        agents = {
            agent.name: agent for agent in [writer, financial_analyst, researcher]
        }

        on_event = await get_magnetic_event_handler()
        result = await writer.run("Hello team. Let's wait for the Financial_Analyst to provide our first task.")
        workflow = (
            MagenticBuilder()
                .participants(**agents)
                .on_event(on_event, mode=MagenticCallbackMode.NON_STREAMING)
                .with_standard_manager(
                    chat_client=client,
                    max_round_count=10,
                    max_stall_count=3,
                    max_reset_count=2,
                )
                .build()
        )

        task = (
            input("Enter a task for the team (or 'exit' to quit):\n")
        )

        print(f"\nTask: {task}")
        print("\nStarting workflow execution...")

        try:
            output: str | None = None
            async for event in workflow.run_stream(task):
                print(event)
                if isinstance(event, WorkflowOutputEvent):
                    output = str(event.data)

            if output is not None:
                print(f"Workflow completed with result:\n\n{output}")

        except Exception as e:
            print(f"Workflow execution failed: {e}")


    print(f"Writer: {result}")
    #thread = group_chat_manager.get_new_thread()
    #max_iterations = 50
    #for i in range(max_iterations):
        #...
    #print("Max iterations reached, ending chat.")




if __name__ == "__main__":
    asyncio.run(main())