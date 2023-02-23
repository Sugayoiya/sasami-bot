import json

from revChatGPT.V1 import Chatbot

from configs.path_config import TEXT_PATH


class ChatGPT:

    def __init__(self):
        self.chatbot = None
        self.config_data = {}
        self.init_config()

    def init_config(self):
        config_path_parent = TEXT_PATH / "chatgpt"
        if not config_path_parent.exists():
            config_path_parent.mkdir(parents=True)
        config_path = config_path_parent / "config.json"
        # 打开配置文件, 如果不存在则创建默认配置写入
        if not config_path.exists():
            config_data = {"email": "", "password": "", "paid": False, "proxy": "", "insecure": False,
                           "session_token": ""}
            self.write_config(config_data)
        # 读取配置文件
        with open(config_path, "r") as f:
            self.config_data = json.load(f)
        self.chatbot = Chatbot(self.config_data)

    @staticmethod
    def write_config(config_data):
        config_path_parent = TEXT_PATH / "chatgpt"
        if not config_path_parent.exists():
            config_path_parent.mkdir(parents=True)
        config_path = config_path_parent / "config.json"
        with open(config_path, "w") as f:
            f.write(json.dumps(config_data, indent=4, sort_keys=False, separators=(',', ': ')))

    def commands(self, command: str) -> bool:
        if command == "!help":
            print(
                """
            !help - Show this help message
            !reset - Clear the current conversation
            !rollback <int> - Remove the latest <int> messages from the conversation
            """,
            )
        elif command == "!reset":
            self.chatbot.conversations.remove("default")
            print("Conversation cleared")
        elif command.startswith("!rollback"):
            try:
                num = int(command.split(" ")[1])
                self.chatbot.conversations.rollback("default", num)
                print(f"Removed {num} messages from the conversation")
            except IndexError:
                print("Please specify the number of messages to remove")
            except ValueError:
                print("Please specify a valid number of messages to remove")
        else:
            return False
        return True

    async def ask(self, question: str) -> str:
        prev_text = ""
        answer = ""
        for line in self.chatbot.ask(question):
            message = line["message"][len(prev_text):]
            answer += message
            prev_text = line["message"]
        return answer


def main():
    chatbot = ChatGPT()
    prev_text = ""
    print(chatbot.ask("Hello"))


if __name__ == "__main__":
    main()
