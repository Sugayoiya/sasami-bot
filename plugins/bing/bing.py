import argparse
import asyncio
import json
import os
import sys

from EdgeGPT import Chatbot

from configs.path_config import TEXT_PATH


class Bing:

    def __init__(self):
        self.chatbot = None
        self.config_data = {}
        self.init_config()

    def init_config(self):
        config_path_parent = TEXT_PATH / "bing"
        if not config_path_parent.exists():
            config_path_parent.mkdir(parents=True)
        config_path = config_path_parent / "config.json"
        # 打开配置文件, 如果不存在则创建默认配置写入
        if not config_path.exists():
            config_data = {}
            self.write_config(config_data)
        self.chatbot = Chatbot(config_path)

    @staticmethod
    def write_config(config_data):
        config_path_parent = TEXT_PATH / "bing"
        if not config_path_parent.exists():
            config_path_parent.mkdir(parents=True)
        config_path = config_path_parent / "config.json"
        with open(config_path, "w") as f:
            f.write(json.dumps(config_data, indent=4, sort_keys=False, separators=(',', ': ')))

    async def ask(self, question: str) -> str:
        res = await self.chatbot.ask(prompt=question)
        return res["item"]["messages"][1]["adaptiveCards"][0]["body"][0]["text"]

    async def ask_stream(self, question: str) -> str:
        wrote = 0
        ans = ""
        async for final, response in self.chatbot.ask_stream(prompt=question):
            if not final:
                ans += response[wrote:]
                wrote = len(response)
        return ans

    async def reset(self):
        await self.chatbot.reset()


def get_input(prompt):
    """
    Multi-line input function
    """
    # Display the prompt
    print(prompt, end="")

    if args.enter_once:
        user_input = input()
        print()
        return user_input

    # Initialize an empty list to store the input lines
    lines = []

    # Read lines of input until the user enters an empty line
    while True:
        line = input()
        if line == "":
            break
        lines.append(line)

    # Join the lines, separated by newlines, and store the result
    user_input = "\n".join(lines)

    # Return the input
    return user_input


async def main():
    """
    Main function
    """
    print("Initializing...")
    bot = Chatbot()
    while True:
        prompt = get_input("\nYou:\n")
        if prompt == "!exit":
            break
        elif prompt == "!help":
            print(
                """
            !help - Show this help message
            !exit - Exit the program
            !reset - Reset the conversation
            """,
            )
            continue
        elif prompt == "!reset":
            await bot.reset()
            continue
        print("Bot:")
        if args.no_stream:
            print(
                (await bot.ask(prompt=prompt))["item"]["messages"][1]["adaptiveCards"][
                    0
                ]["body"][0]["text"],
            )
        else:
            wrote = 0
            async for final, response in bot.ask_stream(prompt=prompt):
                if not final:
                    print(response[wrote:], end="")
                    wrote = len(response)
                    sys.stdout.flush()
            print()
        sys.stdout.flush()
    await bot.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--enter-once", action="store_true")
    parser.add_argument("--no-stream", action="store_true")
    parser.add_argument(
        "--cookie-file",
        type=str,
        default="config.json",
        required=False,
    )
    args = parser.parse_args()
    os.environ["COOKIE_FILE"] = args.cookie_file
    asyncio.run(main())
    main()
