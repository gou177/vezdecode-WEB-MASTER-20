from typing import Any, Dict, Optional
import discord
from discord.message import Attachment, Message
from os import getenv, remove
import yaml
import vk_api
from vk_api.bot_longpoll import (
    VkBotLongPoll,
    VkBotEventType,
    VkBotMessageEvent,
    DotDict,
)
import threading
import asyncio
from vk_api.utils import get_random_id
from vk_api.upload import VkUpload

loop = asyncio.get_event_loop()

vk_session = vk_api.VkApi(token=getenv("VK_TOKEN"))

vk = vk_session.get_api()
upload = VkUpload(vk)


def retry(func):
    def decorated(*args, **kwargs):
        while True:
            try:
                return func(*args, **kwargs)
            except Exception as err:
                print(err)

    return decorated


def generateConfig(path="./config.yaml"):
    vk_peer_id = int(input("vk peer id: "))
    channel = int(input("discord channel id: "))

    conf = {
        "rules": [
            {
                "from": {
                    "type": "vk",
                    "peer_id": vk_peer_id,
                },
                "to": {
                    "type": "discord",
                },
            },
            {
                "from": {
                    "type": "discord",
                    "channel": channel,
                },
                "to": {
                    "type": "vk",
                    "peer_id": vk_peer_id,
                },
            },
        ]
    }

    with open(path, "w") as f:
        yaml.dump(conf, f, default_flow_style=False)

    return conf


def load(path="./config.yaml"):
    try:
        with open(path, "r") as stream:
            return yaml.safe_load(stream)
    except FileNotFoundError:
        print("Конфиг не найден!")
        return generateConfig(path)


config = load()


def select(type: str, chat_id: int):
    for rule in config["rules"]:
        if rule["from"]["type"] != type:
            continue
        if type == "vk":
            if rule["from"]["peer_id"] == chat_id or rule["from"]["peer_id"] == "*":
                yield rule
        if type == "discord":
            if rule["from"]["channel"] == chat_id or rule["from"]["channel"] == "*":
                yield rule


class MyClient(discord.Client):
    async def on_message(self, message: Message):
        print(f"Message from {message.author}: {message.content}")

        if message.author.bot:  # type: ignore
            return

        for rule in select("discord", message.channel.id):  # type: ignore
            attach = None
            if message.attachments:
                attach = (
                    f"./{message.attachments[0].id}-{message.attachments[0].filename}"
                )
                await message.attachments[0].save(attach)
            loop.create_task(send(rule, f"{message.author.display_name}:\n{message.clean_content}", attach))  # type: ignore

    async def on_ready(self):
        print("discord started")


ds = MyClient()


async def send(rule: dict, text: str, attach: Optional[str]):
    try:
        if rule["to"]["type"] == "vk":
            attachments = []

            if attach:
                photo = upload.photo_messages([attach], rule["to"]["peer_id"])[0]
                attachments.append(
                    f"photo{photo['owner_id']}_{photo['id']}_{photo['access_key']}"
                )

            return vk.messages.send(
                peer_id=rule["to"]["peer_id"],
                message=text,
                random_id=get_random_id(),
                attachment=",".join(attachments),
            )

        if rule["to"]["type"] == "discord":
            channel = await ds.fetch_channel(rule["to"]["channel"])
            return await channel.send(text)  # type: ignore
    finally:
        if attach:
            remove(attach)


def format_vk_msg(message: VkBotMessageEvent):
    user = vk.users.get(user_ids=message.from_id)[0]  # type: ignore
    attach = ""
    attachments = message.attachments  # type: ignore
    if attachments:
        for attachment in attachments:
            if attachment["type"] == "photo":
                attach += "[Фото] "
                attach += max(
                    attachment["photo"]["sizes"],
                    key=lambda x: (x["width"], x["height"]),
                )["url"]
                attach += "\n"
            if attachment["type"] == "doc":
                attach += "[Документ] "
                attach += attachment['doc']['url']
                attach += "\n"
            if attachment["type"] == "audio":
                attach += "[Аудио] "
                attach += f'{attachment["audio"]["artist"]} - {attachment["audio"]["title"]}'
                attach += "\n"
            if attachment["type"] == "sticker":
                attach += "[Стикер] "
                attach += max(
                    attachment["sticker"]["images"],
                    key=lambda x: (x["width"], x["height"]),
                )["url"]
                attach += "\n"
            if attachment["type"] == "video":
                attach += f"[Видео] {attachment['video']['title']} "
                attach += fr"https://vk.com/video?z=video{attachment['video']['owner_id']}_{attachment['video']['id']}_{attachment['video']['access_key']}"
                attach += "\n"
            if attachment["type"] == "poll":
                attach += "[Опрос] "
                attach += attachment["poll"]["question"]
                attach += "\n"
                for answer in attachment["poll"]["answers"]:
                    attach += f"{answer['text']} [{'█'*(int(answer['rate']//5)):░<20}] - {answer['votes']}\n"
                attach += "\n"
    fwd = ""
    if message.fwd_messages:  # type: ignore
        fwd += "\n[Пересланное сообщение]"
        fwd += "\n".join(
            map(
                lambda x: f"  {x}",
                "\n".join(
                    map(format_vk_msg, map(DotDict, message.fwd_messages)),  # type: ignore
                ).split("\n"),
            )
        )  # type: ignore
    if message.reply_message:  # type: ignore
        fwd += "\n[Ответ]"
        fwd += "\n".join(
            map(
                lambda x: f"  {x}",
                format_vk_msg(DotDict(message.reply_message)).split("\n"),  # type: ignore
            )
        )

    return f'{user["first_name"]} {user["last_name"]}:\n{message.text}{fwd}\n{attach}'  # type: ignore


@retry
def vk_listener():
    longpoll = VkBotLongPoll(vk_session, int(getenv("VK_GROUP_ID", "")))

    print("vk started")

    for event in longpoll.listen():
        if type(event) is VkBotMessageEvent:
            if event.message.from_id < 0:  # type: ignore
                continue
            for rule in select("vk", event.message.peer_id):  # type: ignore
                text = format_vk_msg(event.message)
                loop.create_task(
                    send(
                        rule,
                        text,
                        None,
                    )
                )


threading.Thread(target=vk_listener).start()
ds.run(getenv("DISCORD_TOKEN"))
