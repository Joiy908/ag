import asyncio
import unittest

from llama_index.core.storage.chat_store import SimpleChatStore
from llama_index.core.tools import FunctionTool
from llama_index.core.workflow import HumanResponseEvent, InputRequiredEvent

from agent.my_llm import CozeLLM
from agent.react_agent import ReActAgent
from llama_index.tools.mcp import (
    aget_tools_from_mcp_url,
    get_tools_from_mcp_url,
) 


class TestReActAgent(unittest.TestCase):
    """Test cases for the ReActAgent."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        def add_tool(a: int, b: int):
            return a + b
        add_tool = FunctionTool.from_defaults(add_tool)
        self.chat_store = SimpleChatStore()
        self.llm = CozeLLM(user_id="test_user")
        self.agent_bob1 = ReActAgent(
            llm=self.llm,
            chat_store=self.chat_store,
            memory_key='bob1',
            tools=[add_tool],
        )
        self.agent_bob2 = ReActAgent(
            llm=self.llm,
            chat_store=self.chat_store,
            memory_key='bob2',
            tools=[add_tool],
        )
        self.agent_confirm_tool = ReActAgent(
            llm=self.llm,
            chat_store=self.chat_store,
            memory_key='confirm_tool_test',
            tools=[add_tool],
            tools_need_confirm=['add_tool']
        )

    def test_hello_message(self):
        """Test sending a simple 'hello' message to the ReAct agent."""
        async def run_test():
            handler = self.agent_bob1.run(input="123 + 123 = ?")
            # async for ev in handler.stream_events():
                # print(repr(ev))
                # match ev:
                #     case InputEvent():
                #         # print(Colors.USER_PROMPT, end="", flush=True)
                #         print(ev.input, end="", flush=True)
                #         # print(Colors.RESET, end="", flush=True)
                #         print()
                #     case StreamEvent():
                #         # print(Colors.RESPONSE, end="", flush=True)
                #         print(ev.delta, end="", flush=True)
                #         # print(Colors.RESET, end="", flush=True)
                #     case ToolCallResultMessage():
                #         # print(Colors.BLUE, end="", flush=True)
                #         print()
                #         print(ev.output, end="", flush=True)
                #         print()
                #         # print(Colors.RESET, end="", flush=True)
                #     case StopSignal():
                #         print("\n === end ===")
                #     case _:
                #         continue

            await handler
            handler1 = self.agent_bob2.run(input="123 + 1 = ?")
            await handler1

        # Run the async test
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(run_test())
        finally:
            loop.close()


        # (conversation_key might be a tuple, so check if any messages exist)
        all_keys = list(self.chat_store.store.keys())
        self.assertEqual(len(all_keys),  2, "Chat store should have stored the conversation")
        print(f"Chat store contains {len(all_keys)} conversation(s)")
        # print all chats of each key
        for key in all_keys:
            print(f'{key}:', self.chat_store.store.get(key))
        # self.chat_store.persist(persist_path="chat_store.json")


    def test_confirm_tool(self):
        """Test using tool needed confirmation"""
        async def run_test():
            handler = self.agent_confirm_tool.run(input="123 + 1 = ?")
            async for ev in handler.stream_events():
                # print(repr(ev))
                match ev:
                #     case InputEvent():
                #         # print(Colors.USER_PROMPT, end="", flush=True)
                #         print(ev.input, end="", flush=True)
                #         # print(Colors.RESET, end="", flush=True)
                #         print()
                #     case StreamEvent():
                #         # print(Colors.RESPONSE, end="", flush=True)
                #         print(ev.delta, end="", flush=True)
                #         # print(Colors.RESET, end="", flush=True)
                #     case ToolCallResultMessage():
                #         # print(Colors.BLUE, end="", flush=True)
                #         print()
                #         print(ev.output, end="", flush=True)
                #         print()
                #         # print(Colors.RESET, end="", flush=True)
                #     case StopSignal():
                #         print("\n === end ===")
                    case InputRequiredEvent():
                        # response = input(ev.prefix)
                        # send our response back
                        handler.ctx.send_event(
                            HumanResponseEvent(
                                response='n'
                            )
                        )
                    case _:
                        continue

            await handler

        # Run the async test
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(run_test())
        finally:
            loop.close()
        self.chat_store.persist(persist_path="chat_store.json")

    def test_mcp_tool(self):
        """Test mcp tools"""
        from agent import MCP_SERVERS
        tools = []
        for url in MCP_SERVERS:
            tools.append(*get_tools_from_mcp_url(url))
        agent = ReActAgent(
            llm=self.llm,
            chat_store=self.chat_store,
            memory_key='confirm_tool_test',
            tools=tools,
            # tools_need_confirm=['add_tool']
        )
        async def run_test():
            handler = agent.run(input="123 + 1 = ?")
            async for ev in handler.stream_events():
                # print(repr(ev))
                match ev:
                #     case InputEvent():
                #         # print(Colors.USER_PROMPT, end="", flush=True)
                #         print(ev.input, end="", flush=True)
                #         # print(Colors.RESET, end="", flush=True)
                #         print()
                #     case StreamEvent():
                #         # print(Colors.RESPONSE, end="", flush=True)
                #         print(ev.delta, end="", flush=True)
                #         # print(Colors.RESET, end="", flush=True)
                #     case ToolCallResultMessage():
                #         # print(Colors.BLUE, end="", flush=True)
                #         print()
                #         print(ev.output, end="", flush=True)
                #         print()
                #         # print(Colors.RESET, end="", flush=True)
                #     case StopSignal():
                #         print("\n === end ===")
                    case InputRequiredEvent():
                        # response = input(ev.prefix)
                        # send our response back
                        handler.ctx.send_event(
                            HumanResponseEvent(
                                response='n'
                            )
                        )
                    case _:
                        continue

            await handler

        # Run the async test
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(run_test())
        finally:
            loop.close()
        self.chat_store.persist(persist_path="chat_store.json")

if __name__ == '__main__':
    unittest.main()
