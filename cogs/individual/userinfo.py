# RT - Userinfo
from discord.ext import commands

from core import Cog


class Userinfo(Cog):
    def __init__(self, bot):
        self.bot = bot
        
    @commands.command()
    async def userinfo(self, ctx, *, id: int=None):
        user = await self.bot.search_user(id)
        if user.public_flags.hypesquad_bravery:
            hypesquad = "<:HypeSquad_Bravery:876337861572579350>"
        elif user.public_flags.hypesquad_brilliance:
            hypesquad = "<:HypeSquad_Brilliance:876337861643882506>"
        elif user.public_flags.hypesquad_balance:
            hypesquad = "<:HypeSquad_Balance:876337714679676968>"
        else:
            hypesquad = ""
        Cog.Embed(
            title=user,
            description=hypesquad
        )
 

async def setup(bot):
    await bot.add_cog(Userinfo(bot))
