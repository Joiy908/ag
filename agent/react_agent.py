import sys
from typing import Any

from llama_index.core.agent.react import ReActChatFormatter, ReActOutputParser
from llama_index.core.agent.react.types import (
    ActionReasoningStep,
    ObservationReasoningStep,
)
from llama_index.core.llms import ChatMessage
from llama_index.core.llms.llm import LLM
from llama_index.core.memory import ChatMemoryBuffer
from llama_index.core.storage.chat_store.base import BaseChatStore
from llama_index.core.tools import ToolSelection
from llama_index.core.tools.types import BaseTool
from llama_index.core.workflow import (
    Context,
    Event,
    HumanResponseEvent,
    InputRequiredEvent,
    StartEvent,
    StopEvent,
    Workflow,
    step,
)


class PrepEvent(Event):
    pass


class InputEvent(Event):
    input: list[ChatMessage]


class ToolCallEvent(Event):
    tool_calls: list[ToolSelection]


class StreamEvent(Event):
    """content can be answer or tool call"""
    delta: str

class ToolCallResultMessage(Event):
    output: str

class StopSignal(Event):
    pass


class ReActAgent(Workflow):
    def __init__(
        self,
        *args: Any,
        llm: LLM,
        memory_key: str,
        chat_store: BaseChatStore,
        tools: list[BaseTool] | None = None,
        tools_need_confirm: list[str] | None = None,
        extra_context: str | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.tools = tools or []
        self.tools_need_confirm = tools_need_confirm or []
        self.llm = llm
        self.chat_store = chat_store
        self.memory_key = memory_key
        self.formatter = ReActChatFormatter.from_defaults(context=extra_context or "")
        self.output_parser = ReActOutputParser()

    @step
    async def new_user_msg(self, ctx: Context, ev: StartEvent) -> PrepEvent:
        """init prompt and memory"""
        # clear sources
        await ctx.store.set("sources", [])

        # init memory if needed
        memory = await ctx.store.get("memory", default=None)
        if not memory:
            memory = ChatMemoryBuffer.from_defaults(
                token_limit=sys.maxsize, llm=self.llm, chat_store=self.chat_store, chat_store_key=self.memory_key
            )

        # get user input
        user_input = ev.input
        user_msg = ChatMessage(role="user", content=user_input)
        await memory.aput(user_msg)

        # clear current reasoning
        await ctx.store.set("current_reasoning", [])

        # set memory
        await ctx.store.set("memory", memory)

        return PrepEvent()

    @step
    async def prepare_chat_history(self, ctx: Context, ev: PrepEvent) -> InputEvent:
        # get chat history
        memory: ChatMemoryBuffer = await ctx.store.get("memory")
        chat_history = memory.get()
        current_reasoning = await ctx.store.get("current_reasoning", default=[])

        # format the prompt with react instructions
        llm_input_chatlist = self.formatter.format(self.tools, chat_history, current_reasoning=current_reasoning)

        if self.llm.metadata.model_name == 'coze' and len(llm_input_chatlist) > 2:
            # if llm is coze_api, only put the current msg, the coze_api has memory
            llm_input_chatlist = [llm_input_chatlist[-1]]
        ctx.write_event_to_stream(InputEvent(input=llm_input_chatlist))
        await memory.aput_messages(llm_input_chatlist)
        print('llm_input', llm_input_chatlist)
        return InputEvent(input=llm_input_chatlist)

    @step
    async def handle_llm_input(self, ctx: Context, ev: InputEvent) -> ToolCallEvent | StopEvent | PrepEvent:
        chat_history = ev.input
        current_reasoning = await ctx.store.get("current_reasoning", default=[])
        memory = await ctx.store.get("memory")

        response_gen = await self.llm.astream_chat(chat_history)
        async for response in response_gen:
            ctx.write_event_to_stream(StreamEvent(delta=response.delta or ""))

        # Always store the assistant's response in memory first
        assistant_msg = ChatMessage(role="assistant", content=response.message.content)


        try:
            reasoning_step = self.output_parser.parse(response.message.content)
            current_reasoning.append(reasoning_step)

            if reasoning_step.is_done:
                await memory.aput(ChatMessage(role="assistant", content=reasoning_step.response))
                await ctx.store.set("memory", memory)
                await ctx.store.set("current_reasoning", current_reasoning)

                sources = await ctx.store.get("sources", default=[])

                ctx.write_event_to_stream(StopSignal())
                return StopEvent(
                    result={
                        "response": reasoning_step.response,
                        "sources": [sources],
                        "reasoning": current_reasoning,
                    }
                )
            elif isinstance(reasoning_step, ActionReasoningStep):
                # Store the reasoning step content, but don't finalize yet
                await memory.aput(ChatMessage(role="assistant", content=reasoning_step.get_content()))
                await ctx.store.set("memory", memory)
                await ctx.store.set("current_reasoning", current_reasoning)

                tool_name = reasoning_step.action
                tool_args = reasoning_step.action_input
                return ToolCallEvent(
                    tool_calls=[
                        ToolSelection(
                            tool_id="fake",
                            tool_name=tool_name,
                            tool_kwargs=tool_args,
                        )
                    ]
                )

        except Exception as e:
            # Even if parsing fails, store the response in memory
            await memory.aput(assistant_msg)
            await ctx.store.set("memory", memory)

            current_reasoning.append(
                ObservationReasoningStep(observation=f"There was an error in parsing my reasoning: {e}")
            )
            await ctx.store.set("current_reasoning", current_reasoning)

        # if no tool calls or final response, iterate again
        return PrepEvent()

    @step
    async def handle_tool_calls(self, ctx: Context, ev: ToolCallEvent) -> PrepEvent:
        memory = await ctx.store.get("memory")

        tool_calls = ev.tool_calls
        tools_by_name = {tool.metadata.get_name(): tool for tool in self.tools}
        current_reasoning = await ctx.store.get("current_reasoning", default=[])
        sources = await ctx.store.get("sources", default=[])

        # call tools -- safely!
        # for tool_call in tool_calls:
        tool_call = tool_calls[0]
        tool = tools_by_name.get(tool_call.tool_name)
        if not tool:
            current_reasoning.append(
                ObservationReasoningStep(observation=f"Tool {tool_call.tool_name} does not exist")
            )
        else:
            try:
                if tool_call.tool_name in self.tools_need_confirm:
                        ctx.write_event_to_stream(
                            InputRequiredEvent(
                                prefix=f"{tool_call.tool_name}({tool_call.tool_kwargs}), ok?",
                            )
                        )
                        res = await ctx.wait_for_event(HumanResponseEvent)
                        print('==', res.response, flush=True)
                        if res.response != 'y':
                            raise Exception('Fail to get confirmation.')

                tool_output = tool(**tool_call.tool_kwargs)
                sources.append(tool_output)
                ctx.write_event_to_stream(ToolCallResultMessage(output=tool_output.content))
                await memory.aput(ChatMessage(role="tool", content=tool_output.content))
                current_reasoning.append(ObservationReasoningStep(observation=tool_output.content))

            except Exception as e:
                # this will never achived, assert tool is err-free(catch err inside)
                current_reasoning.append(
                    ObservationReasoningStep(observation=f"Error calling tool {tool.metadata.get_name()}: {e}")
                )

        # save new state in context
        await ctx.store.set("sources", sources)
        await ctx.store.set("current_reasoning", current_reasoning)

        # prep the next iteraiton
        return PrepEvent()

