import traceback
from ast import AugLoad
from typing import TYPE_CHECKING

import discord
from discord import SelectOption, ui

from database.chat import set_thread_info
from utils.hash import generate_key

from .agent.model import AutoGPTTemplate, TranslatorTemplate, get_templates
from .agent.tools import get_all_tools
from .models import get_models

if TYPE_CHECKING:
    from discord import Thread


class ModelSelectView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(self.ModelSelect())

    class ModelSelect(ui.Select):
        def __init__(self) -> None:
            super().__init__()
            models = get_models()
            self.options = [
                SelectOption(
                    label=model.name,
                    description=model.description,
                )
                for model in models
            ]

        async def callback(self, interaction: discord.Interaction):
            data = {}
            model = self.values[0]
            data["model"] = model
            await interaction.channel.send(f"{model} 모델을 선택했습니다.")
            await interaction.channel.send(
                "실행기를 선택하세요", view=AgentSelectView(data)
            )
            await interaction.response.defer()
            await interaction.message.delete()


class AgentSelectView(ui.View):
    def __init__(self, data: dict):
        super().__init__(timeout=None)
        self.add_item(self.AgentSelect(data))

    class AgentSelect(ui.Select):
        def __init__(self, data: dict) -> None:
            super().__init__()
            self.templates = get_templates()
            self.data = data
            self.options = [
                SelectOption(
                    label=template.name,
                    description=template.description,
                )
                for template in self.templates
            ]

        async def callback(self, interaction: discord.Interaction):
            agent = self.values[0]
            self.data["agent"] = agent
            if agent == AutoGPTTemplate.name:
                await interaction.response.send_modal(AutoGPTModal(data=self.data))
            elif agent == TranslatorTemplate.name:
                await interaction.response.send_modal(LanguageModal(data=self.data))
            else:
                await interaction.channel.send(f"{agent} 템플릿을 선택했습니다.")
                await interaction.channel.send(
                    f"사용할 도구를 선택해 주세요.", view=ToolSelectView(self.data)
                )
                await interaction.response.defer()
            await interaction.message.delete()


class ToolSelectView(ui.View):
    def __init__(self, data: dict):
        super().__init__(timeout=None)
        self.add_item(self.ToolSelect())
        self.add_item(self.SubmitButton(data))
        self.tools = []

    class ToolSelect(ui.Select):
        def __init__(self) -> None:
            super().__init__()
            self.tools = get_all_tools()
            self.options = [
                SelectOption(
                    label=tool.name,
                    description=tool.description,
                )
                for tool in self.tools
            ]
            self.min_values = 0
            self.max_values = len(self.options)

        async def callback(self, interaction: discord.Interaction):
            self.view.tools = self.values
            await interaction.response.defer()

    class SubmitButton(ui.Button):
        def __init__(self, data: dict) -> None:
            super().__init__(style=discord.ButtonStyle.primary, label="완료")
            self.data = data

        async def callback(self, interaction: discord.Interaction):
            self.data["tools"] = self.view.tools
            await _save_thread_info(interaction.channel, self.data)
            await interaction.channel.send(f"설정이 완료되었어요.")
            await interaction.response.defer()
            await interaction.message.delete()


class AutoGPTModal(ui.Modal, title="autoGPT 설정"):
    ai_name = ui.TextInput(
        label="AI 이름", placeholder="AI 이름을 입력해주세요.", max_length=20
    )
    ai_role = ui.TextInput(
        label="AI 역할",
        placeholder="AI 설명을 입력해주세요. (어떤 AI인가요?)",
        max_length=300,
    )
    goals = ui.TextInput(
        label="목표",
        placeholder="목표를 입력해주세요.\n단계적으로 목표를 작성해 보세요.\n목표는 엔터로 구분됩니다.",
        style=discord.TextStyle.long,
    )

    def __init__(self, data: dict):
        super().__init__(timeout=None)
        self.data = data

    async def on_submit(self, interaction: discord.Interaction):
        self.data["data"] = {
            "ai_name": self.ai_name.value,
            "ai_role": self.ai_role.value,
            "goals": self.goals.value,
        }
        await _save_thread_info(interaction.channel, self.data)
        await self.send_start_message(interaction.channel)
        await self.send_how_to_message(interaction.channel)
        await interaction.response.defer()

    async def on_error(
        self, interaction: discord.Interaction, error: Exception
    ) -> None:
        await interaction.response.send_message(
            "뭔가 문제가 발생했어요.\n채팅을 다시 시작해 주세요."
        )
        traceback.print_exc()

    async def send_start_message(self, thread: "Thread"):
        goals_text = "\n".join([f"- {goal}" for goal in self.goals.value.split("\n")])
        await thread.send(
            f"AI 이름: {self.ai_name}\n"
            f"AI 역할: {self.ai_role}\n\n"
            "목표:\n"
            f"{goals_text}\n\n"
            "대화를 시작할게요.",
        )

    async def send_how_to_message(self, thread: "Thread"):
        await thread.send(
            "## 사용 방법\n"
            "기본적으로 목표 완수를 위해 AI가 자동으로 동작합니다.\n\n"
            "'Y'를 입력해 다음 동작을 실행할 수 있습니다.\n"
            "'YN'은 N번 동안 유저 응답 없이 동작합니다. (N < 11)\n"
            "N9는 AI가 9번 동작하고 정지합니다.\n\n"
            "문장을 입력해 AI에게 지시를 전달할 수 있습니다.\n\n"
            "이제 'Y'를 입력해 대화를 시작해 보세요."
        )


class LanguageModal(ui.Modal, title="번역기 설정"):
    lang1 = ui.TextInput(label="언어1", placeholder="ex) 영어", max_length=10)
    example1 = ui.TextInput(
        label="언어1 예시",
        placeholder="번역 예시 문장을 작성 할 수 있습니다.\n"
        "ex) You are a good AI assistant.",
        required=False,
        style=discord.TextStyle.long,
    )
    lang2 = ui.TextInput(label="언어2", placeholder="ex) 한글", max_length=10)
    example2 = ui.TextInput(
        label="언어2 예시",
        placeholder="번역 예시 문장을 작성 할 수 있습니다.\n"
        "ex) 너는 좋은 AI 어시스턴트야.",
        required=False,
        style=discord.TextStyle.long,
    )

    def __init__(self, data: dict):
        super().__init__(timeout=None)
        self.data = data

    async def on_submit(self, interaction: discord.Interaction):
        self.data["data"] = {
            "lang1": self.lang1.value,
            "lang2": self.lang2.value,
            "example1": self.example1.value,
            "example2": self.example2.value,
        }
        await _save_thread_info(interaction.channel, self.data)
        await self.send_start_message(interaction.channel)
        await self.send_how_to_message(interaction.channel)
        await interaction.response.defer()

    async def on_error(
        self, interaction: discord.Interaction, error: Exception
    ) -> None:
        await interaction.response.send_message(
            "뭔가 문제가 발생했어요.\n채팅을 다시 시작해 주세요."
        )
        traceback.print_exc()

    async def send_start_message(self, thread: "Thread"):
        await thread.send(
            f"**{self.lang1} <--> {self.lang2}**\n" "번역기를 설정했습니다."
        )

    async def send_how_to_message(self, thread: "Thread"):
        await thread.send(
            "## 사용 방법\n"
            "번역기는 입력된 문장을 상대되는 언어로 번역합니다.\n"
            "예시에 작성된 말투를 참고하긴 하나 완벽하진 않습니다.\n\n"
            "이제 문장을 입력해 번역해 보세요."
        )


async def _save_thread_info(thread: "Thread", data: dict):
    thread_key = generate_key(str(thread.id), 6)
    await set_thread_info(thread.guild.name, thread_key, data)
