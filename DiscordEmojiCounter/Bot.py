import re
import discord
from discord import embeds
from discord.ext import commands
from .DataManager import *

class Bot(commands.Bot):
    def __init__(self, data_dir: str) -> None:
        """
        Parameters:
        ====================
        data_dir : str
            データベースファイルを配置するディレクトリへのパス
        """
        super().__init__(command_prefix='?', help_command=None)

        self.__data_manager = DataManager(data_dir)

        # on_messageはオーバーライドするとコマンドが使えなくなる
        self.add_listener(self.__on_message, 'on_message')

        # 以下コマンドの追加
        @self.command()
        async def help(ctx: commands.Context) -> None:
            await self.__on_help_command(ctx)

        @self.command()
        async def total(ctx: commands.Context) -> None:
            await self.__on_total_command(ctx)

        @self.command()
        async def message(ctx: commands.Context) -> None:
            await self.__on_message_command(ctx)

        @self.command()
        async def reaction(ctx: commands.Context) -> None:
            await self.__on_reaction_command(ctx)


    async def __on_message(self, message: discord.Message) -> None:
        """
        メッセージが送信されたときに呼び出されるメソッド。

        Parameters:
        ====================
        message : discord.Message
            https://discordpy.readthedocs.io/ja/latest/api.html#message
        """
        # message.content内でEmojiは<:emoji:123456>のように表される
        pattern = '<:.*?:.*?>'
        emojis = re.findall(pattern, message.content, re.S)

        emoji_ids = []

        # 取得したemoji情報からIDを抜き出してリストに追加する
        for emoji in emojis:
            id = int(emoji[1:-1].split(':')[-1])
            emoji_ids.append(id)

        # 登録する
        self.__data_manager.regist_emojis(message.id, message.author.id, emoji_ids)


    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent) -> None:
        """
        メッセージにリアクションが追加された際に呼び出されるメソッド。
        必要に応じて記録する。

        Parameters:
        ====================
        payload : discord.RawReactionActionEvent
            https://discordpy.readthedocs.io/ja/latest/api.html#discord.RawReactionActionEvent
        """
        self.__data_manager.regist_reactions(payload.message_id, payload.user_id, payload.emoji.id)

    
    def __generate_ranking_embed(self, title: str, ranking: List[Tuple[int, int]]) -> discord.Embed:
        """
        ランキングの表示のためのEmbedを生成する

        Parameters:
        ====================
        title : str
            Embedのタイトル

        ranking : List[Tuple[int, int]]
            https://discordpy.readthedocs.io/ja/latest/ext/commands/api.html#discord.ext.commands.Context

        Returns:
        ====================
        discord.Embed
            ランキングを載せたEmbed
        """
        # Embedの作成
        embed = discord.Embed(title=title, color=0xff0000)
        
        if len(ranking) == 0:
            # カウントされた絵文字がなかった場合
            embed.set_footer(text=u'絵文字はまだカウントされていません')
            return embed

        # 順位とカウンタ
        rank = 1
        counter = 0

        # 前の絵文字の個数
        prev_count = 0
        
        for (emoji_id, count) in ranking:
            # Emojiを取得
            emoji = self.get_emoji(emoji_id)

            if emoji is None:
                # サーバー上に存在しないスタンプであれば無視
                # TODO - サーバー上に存在しなくなったスタンプの履歴を削除するか検討
                continue

            # カウンタは、絵文字が存在していれば無条件に増やす
            counter += 1

            if count != prev_count:
                # 同立でなければ、順位とカウンタの値をそろえる
                rank = counter

            # Embedに順位の情報を追加
            embed.add_field(name=u'{}位'.format(rank),
                            value=u'{}\n{}回'.format(self.get_emoji(emoji_id), count),
                            inline=True)

            # prev_countを上書き
            prev_count = count
        
        return embed


    async def __on_help_command(self, ctx: commands.Context) -> None:
        """
        ?help
        
        Parameters:
        ====================
        ctx : commands.Context
            https://discordpy.readthedocs.io/ja/latest/ext/commands/api.html#discord.ext.commands.Context
        """
        # Embedの作成
        embed = discord.Embed(title=u'ヘルプ')

        # totalコマンドの説明
        embed.add_field(name='command: ?total',
                        value=u'今までに使用されたカスタム絵文字の統計をランキング形式で表示する。',
                        inline=True)

        # messageコマンドの説明
        embed.add_field(name='command: ?message',
                        value=u'メッセージ内で使用された絵文字のランキングを表示する。',
                        inline=True)

        # reactionコマンドの説明
        embed.add_field(name='command: ?reaction',
                        value=u'リアクションとして使用された絵文字のランキングを表示する。',
                        inline=True)

        await ctx.send(embed=embed)


    async def __on_total_command(self, ctx: commands.Context) -> None:
        """
        ?total
        がメッセージとして送信された場合に呼び出されるメソッド。

        Parameters:
        ====================
        ctx : commands.Context
            https://discordpy.readthedocs.io/ja/latest/ext/commands/api.html#discord.ext.commands.Context
        """
        await ctx.send(embed=self.__generate_ranking_embed(":crown: 総合ランキング",
                                                    self.__data_manager.get_total()))


    async def __on_message_command(self, ctx: commands.Context) -> None:
        """
        ?message
        がメッセージとして送信された場合に呼び出されるメソッド。

        Parameters:
        ====================
        ctx : commands.Context
            https://discordpy.readthedocs.io/ja/latest/ext/commands/api.html#discord.ext.commands.Context
        """
        await ctx.send(embed=self.__generate_ranking_embed(":crown: メッセージ内Emojiランキング",
                                                    self.__data_manager.get_message_ranking()))


    async def __on_reaction_command(self, ctx: commands.Context) -> None:
        """
        ?reaction
        がメッセージとして送信された場合に呼び出されるメソッド。

        Parameters:
        ====================
        ctx : commands.Context
            https://discordpy.readthedocs.io/ja/latest/ext/commands/api.html#discord.ext.commands.Context
        """
        await ctx.send(embed=self.__generate_ranking_embed(":crown: リアクションランキング",
                                                    self.__data_manager.get_reaction_ranking()))
