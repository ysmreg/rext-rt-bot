# RT - Views

from typing import TypeAlias, Literal, Optional, Any
from collections.abc import Callable, Iterator

from functools import cache

from discord.ext.commands import Context as OriginalContext
import discord

from discord.ext.fslash import Context

from .__init__ import t


__all__ = (
    "TimeoutView", "Mode", "BasePage", "EmbedPage", "NoEditEmbedPage",
    "separate", "prepare_embeds", "check"
)


class TimeoutView(discord.ui.View):
    "タイムアウト時にコンポーネントを使用不可に編集するようにするViewです。"

    ctx: Optional[discord.Message | discord.Interaction] = None

    async def on_timeout(self):
        for child in self.children:
            if hasattr(child, "disabled"):
                child.disabled = True # type: ignore
        if self.ctx is not None:
            if isinstance(self.ctx, discord.Message):
                await self.ctx.edit(view=self)
            else:
                await self.ctx.edit_original_message(view=self)

    def set_message(
        self, ctx: Context | OriginalContext | discord.Interaction,
        message: Optional[discord.Message] = None
    ):
        "Viewを編集するメッセージを指定します。"
        if isinstance(ctx, Context):
            self.ctx = ctx.interaction
        elif message is not None:
            self.ctx = message


async def check(
    view: discord.ui.View, interaction: discord.Interaction
) -> bool:
    """ユーザーがViewを使用することができるかどうかを確認します。
    これを使用する場合は`view`に、対象のユーザーIDまたはオブジェクトが入った`target`を付けておく必要があります。"""
    assert isinstance(interaction, discord.Interaction), "インタラクションオブジェクトじゃないものが渡されました。"
    if interaction.user.id == getattr(getattr(view, "target"), "id", getattr(view, "target")):
        return True
    await interaction.response.send_message(t(dict(
        ja="あなたはこのコンポーネントを使うことができません。",
        en="You can't use this component."
    ), interaction), ephemeral=True)
    return False


Mode: TypeAlias = Literal["dl", "l", "r", "dr"]
class BasePage(TimeoutView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.page = 0

    def update_counter(self):
        self.counter.label = str(self.page + 1)

    async def on_turn(
        self, mode: Mode, _: discord.Interaction
    ):
        self.page = self.page + \
            (-1 if mode.endswith("l") else 1)*((mode[0] == "d")+1)
        self.update_counter()

    @discord.ui.button(emoji="⏪", custom_id="BPViewDashLeft")
    async def dash_left(self, interaction: discord.Interaction, _):
        await self.on_turn("dl", interaction)

    @discord.ui.button(emoji="◀️", custom_id="BPViewLeft")
    async def left(self, interaction: discord.Interaction, _):
        await self.on_turn("l", interaction)

    @discord.ui.button(label="0", custom_id="BPViewCounter")
    async def counter(self, interaction: discord.Interaction, _):
        await interaction.response.send_message("へんじがない。ただの　しかばね　のようだ。")

    @discord.ui.button(emoji="▶️", custom_id="BPViewRight")
    async def right(self, interaction: discord.Interaction, _):
        await self.on_turn("r", interaction)

    @discord.ui.button(emoji="⏩", custom_id="BPViewDashRight")
    async def dash_right(self, interaction: discord.Interaction, _):
        await self.on_turn("dr", interaction)


def separate(text: str, length: int = 2000) -> Iterator[str]:
    "渡された文字列を指定された数で分割します。"
    while text:
        yield text[:length]
        text = text[length:]


def prepare_embeds(
    description: str, on_make: Callable[[str], discord.Embed]
        = lambda text: discord.Embed(description=text),
    set_page: Optional[Callable[[discord.Embed, int, int], None]] = None
) -> list[discord.Embed]:
    "渡された説明で`on_make`を呼び出して、説明を複数の埋め込みに分割します。"
    embeds = [on_make(text) for text in separate(description)]
    if set_page is not None:
        length = len(embeds)
        for i in range(len(embeds)):
            set_page(embeds[i], i+1, length)
    return embeds


class EmbedPage(BasePage):
    "埋め込みのページメニューです。"

    prepare_embeds = staticmethod(prepare_embeds)

    def __init__(self, embeds: list[discord.Embed], *args, select: bool = False, **kwargs):
        self.embeds = embeds
        super().__init__(*args, **kwargs)
        if select:
            self.select = discord.ui.Select()
            self.select.callback = self.on_select
            for i in range(len(embeds)):
                self.select.add_option(label=f"{i}ページ目", value=str(i))
            self.add_item(self.select)

    @property
    @cache
    def length(self) -> int:
        return len(self.embeds)

    async def on_select(self, interaction: discord.Interaction):
        self.page = int(self.select.values[0])
        self.update_counter()
        await interaction.response.edit_message(
            embed=self.embeds[self.page], **self.on_edit(
                interaction, view=self
            )
        )

    async def on_turn(self, mode: Mode, interaction: discord.Interaction):
        before = self.page
        await super().on_turn(mode, interaction)
        try:
            assert 0 <= self.page
            embed = self.embeds[self.page]
        except (AssertionError, IndexError):
            self.page = before
            if mode == "dl":
                self.page = 0
                embed = self.embeds[self.page]
            elif mode == "dr":
                self.page = len(self.embeds) - 1
                embed = self.embeds[self.page]
            else:
                return await interaction.response.send_message(t(dict(
                    ja="これ以上ページを捲ることができません。",
                    en="I can't turn the page any further."
                ), interaction), ephemeral=True)
        self.update_counter()
        await interaction.response.edit_message(
            embed=embed, **self.on_edit(interaction, view=self)
        )

    def on_edit(self, _: discord.Interaction, **kwargs):
        return kwargs


class NoEditEmbedPage(EmbedPage):
    "ページ切り替え時にViewを更新しないようにした`EmbedPage`です。"

    def on_edit(self, _, **kwargs):
        del kwargs["view"]
        return kwargs