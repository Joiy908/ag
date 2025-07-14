import argparse
import platform
import sys

from llama_index.core.storage.chat_store import SimpleChatStore
from llama_index.core.workflow import HumanResponseEvent, InputRequiredEvent
from llama_index.tools.mcp import (
    aget_tools_from_mcp_url,
)

from agent.my_llm import CozeLLM
from agent.react_agent import ReActAgent, StopSignal, StreamEvent, ToolCallResultMessage

from . import MCP_SERVERS


# ANSI 颜色代码
class Colors:
    GREEN = "\033[92m"
    RED = "\033[31m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    BOLD = "\033[1m"
    RESET = "\033[0m"
    USER_PROMPT = YELLOW
    RESPONSE = GREEN

def win_read_keyboard_input_multiline():
    import msvcrt
    buffer = ''
    return_count = 0
    while True:
        ch = msvcrt.getwch()
        if ch != '\r':
            return_count = 0

        if ch == '\r':
            return_count += 1
            print()
            if return_count >= 2:
                return buffer[:-1]
            else:
                buffer += '\n'
        elif ch == '\b':  # 退格键
            if buffer:
                buffer = buffer[:-1]
                # 删除控制台最后一个字符
                print('\b \b', end="", flush=True)
        elif ch == '\x03':  # Ctrl+C
            raise KeyboardInterrupt
        elif ch == '\x1a':  # Ctrl+Z（EOF）
            raise EOFError
        else:
            buffer += ch
            print(ch, end="", flush=True)

def linux_read_keyboard_input_multiline() -> str:
    buffer = ''
    with open('/dev/tty') as tty:
        while True:
            line = tty.readline()
            if line == '\n':
                break
            buffer += line
    return buffer


def read_keyboard_input():
    os = platform.system()
    if os == 'Windows':
        return win_read_keyboard_input_multiline()
    elif os == 'Linux':
        return linux_read_keyboard_input_multiline()
    else:
        raise 'Unsuppoted OS, please implment this method yourself'


def format_prompt(current_input: str, stdin_data: str = None) -> str:
    prompt = ''
    if stdin_data:
        prompt += f"\nstdin:\n{stdin_data}\n"
    prompt += f"\ncurrent user input:{current_input}\n"
    return prompt


def read_stdin():
    return sys.stdin.read()


async def amain(read_from_pipe: bool):
    tools = []
    for url in MCP_SERVERS:
        tools.append(*await aget_tools_from_mcp_url(url))
    tools_need_confirm = ['add']
    print('tools', [t.metadata.name for t in tools])
    print('tools need confirm', tools_need_confirm)

    chat_store = SimpleChatStore()
    USER_ID = 'cli-user'
    llm = CozeLLM(user_id=USER_ID)
    agent = ReActAgent(
        llm=llm,
        chat_store=chat_store,
        memory_key=USER_ID + '1',
        tools=tools,
        tools_need_confirm=tools_need_confirm
    )
    stdin_data = read_stdin() if read_from_pipe else ''

    question_count = 0
    while True:
        try:
            print("> ", end="", flush=True)
            curr_input = read_keyboard_input()
            if question_count == 0:
                prompt = format_prompt(curr_input, stdin_data)
            else:
                question_count += 1
                prompt = format_prompt(curr_input)


            print("[LLM] ", end="", flush=True)


            handler = agent.run(input=prompt)
            async for ev in handler.stream_events():
                match ev:
                    case StreamEvent():
                        print(Colors.RESPONSE, end="", flush=True)
                        print(ev.delta, end="", flush=True)
                        print(Colors.RESET, end="", flush=True)
                    case ToolCallResultMessage():
                        print(Colors.BLUE, end="", flush=True)
                        print()
                        print(ev.output, end="", flush=True)
                        print()
                        print(Colors.RESET, end="", flush=True)
                    case InputRequiredEvent():
                        print()
                        res = input(ev.prefix)
                        # send our response back
                        handler.ctx.send_event(
                            HumanResponseEvent(
                                response=res
                            )
                        )
                    case StopSignal():
                        print()
                    case _:
                        continue

            await handler


        except EOFError:
            print("\n[System] EOF received, exiting.")
            break

        except KeyboardInterrupt:
            print("\n[System] Program interrupted by user, exiting.")
            break

def main():
    import asyncio

    parser = argparse.ArgumentParser(description="LLM CLI Tool, double return to commit input, -p to read from pipe")
    parser.add_argument('-p', '--pipe', action='store_true', help="Read input from stdin (pipe)")
    args = parser.parse_args()

    asyncio.run(amain(args.pipe))

if __name__ == "__main__":
    main()
