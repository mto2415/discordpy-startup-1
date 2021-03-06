import discord
from discord.ext import commands
import random
import wikipedia
import requests
from bs4 import BeautifulSoup as bs4


class QuizCog(commands.Cog):
    """
    クイズボット
    """

    wikipedia.set_lang("ja")

    wikipedia_page = wikipedia.page("wikipedia")
    wordlist = []

    @commands.group(aliases=['q'])
    async def quiz_wikipedia(self, ctx):
        """wikipedia問題"""
        if ctx.invoked_subcommand is None:
            embed = discord.Embed(
                title="wikipediaクイズ機能",
                description="wikipediaクイズ機能の使い方です。"
            )

            embed.add_field(
                name="get", value="wikipediaからランダムなページを取得する\n        e.q get", inline=False)
            embed.add_field(
                name="one", value="取得中のwikipediaページの一行目を表示する\n        e.q one", inline=False)
            embed.add_field(
                name="summary", value="取得中のwikipediaページのサマリーを表示する\n        e.q summary", inline=False)
            embed.add_field(
                name="answer [, True]",
                value="取得中のwikipediaページのタイトルを表示する\nTrueをつけると隠し文字で表示する\n        e.q answer", inline=False)
            embed.add_field(
                name="url", value="取得中のwikipediaページのurlを表示する\n        e.q url", inline=False)
            embed.add_field(
                name="find", value="指定した単語のwikipediaのページを取得する\n        e.q find 'target-word'", inline=False)
            embed.add_field(
                name="create_list (history|science|etc...)", value="単語帳を作成する\n        e.q cl history", inline=False)
            embed.add_field(
                name="get_in_list", value="単語帳からランダムな単語のwikipediaページを取得する\n        e.q gil", inline=False)

            await ctx.send(embed=embed)

    @quiz_wikipedia.command(aliases=['get', 'g'])
    async def get_random_wikipedia_page(self, ctx):
        """wikipediaからランダムな記事を一つ取得する"""

        await ctx.send("妹「wikipediaからランダムな記事を取ってくるね！」")
        await ctx.send("妹は中空に手を翳し、何かを掴むような動作をしている。")

        # 日本語wikipediaからランダムな単語を一つ決めてページを取得する
        self.wikipedia_page = wikipedia.page(wikipedia.random())

        await ctx.send("妹「ランダムな記事を取ってきたよ！」")

    def do_hide_words(self, s: str):
        """答えがそのまま記載されている場合が多いので、マスクする"""

        hide_words = [self.wikipedia_page.title]
        space_word = s[:s.find("（")]
        hide_words.append(space_word)
        hide_words.append(
            self.wikipedia_page.title.replace(" ", ""))  # 「霧雨 魔理沙」を「霧雨魔理沙」でもヒットするように
        # 「Python（パイソン）は、...」の「パイソン」を取得する
        # 「ウォルト・ディズニー（Walt Disney, 1901年12月5日 - 1966年12月15日）...」とある場合、日付は削除したくないので句読点で避ける
        punctuation_mark = [",", "、"]
        start_parentheses = s.find("（")
        end_parentheses = s.find("）")
        end_para = end_parentheses
        for mark in punctuation_mark:
            mark_position = s.find(mark)
            if start_parentheses < mark_position < end_parentheses:
                end_para = mark_position
        para_title = s[s.find("（") + 1: end_para]

        hide_words.append(para_title)

        # **ANSWER**でマスクする
        for hide_word in hide_words:
            s = s.replace(hide_word, "**ANSWER**")

        return s

    @quiz_wikipedia.command(aliases=['one', 'o'])
    async def print_one_summary(self, ctx):
        """一行表示"""
        one_line = self.wikipedia_page.summary  # まずサマリーを取得する
        one_line = one_line[:one_line.find("\n")]  # 最初の改行が来るまでを取得する

        # 答えがそのまま記載されている場合が多いので、マスクする
        question_sentence = self.do_hide_words(one_line)

        await ctx.send(question_sentence)

    @quiz_wikipedia.command(aliases=['summary', 's'])
    async def print_summary(self, ctx):
        """サマリー表示"""
        summary = self.wikipedia_page.summary
        question_sentence = self.do_hide_words(summary)
        await ctx.send(question_sentence)

    @quiz_wikipedia.command(aliases=['answer', 'title', 'a'])
    async def print_answer(self, ctx, spoiler=False):
        """答え表示"""
        await ctx.send(f'妹「答えは「**{"||"*spoiler}{self.wikipedia_page.title}{"||"*spoiler}**」だよ！」')

    @quiz_wikipedia.command(aliases=['url'])
    async def print_url(self, ctx):
        """URLを表示"""
        await ctx.send(self.wikipedia_page.url)

    @quiz_wikipedia.command(aliases=['find', 'page'])
    async def get_wikipedia_page(self, ctx, target_word: str):
        """指定した単語のwikipediaページを取得する"""
        self.wikipedia_page = wikipedia.page(target_word)
        await ctx.send("妹「調べてきたよ！お兄ちゃん！」")

    @quiz_wikipedia.command(aliases=['hint'])
    async def print_hint(self, ctx, key: str):
        if key.startswith("wo"):
            word_position = int(key[2:])
            await ctx.send(f'妹「{word_position}文字目は「{self.wikipedia_page.title[word_position - 1]}」だよ！」')
        if key == "se2":
            se2 = self.wikipedia_page.summary
            s1 = se2.find("\n")
            se2 = se2[s1: se2.find("\n", s1 + 1)]
            se2 = self.do_hide_words(se2)
            await ctx.send("妹「サマリーの二行目は\n「" + se2 + "\n」だよ！」")

    @quiz_wikipedia.command(aliases=['cl', 'create_list'])
    async def create_wordlist(self, ctx, target: str):
        await ctx.send("妹「単語帳を作るよ！」")
        await ctx.send("妹は懸命にペンを動かしている。")
        if target == 'history':
            self.wordlist = self.get_history_words()
        if target == 'science':
            self.wordlist = self.get_science_words()

        await ctx.send("妹「単語帳を作成したよ！」")

    def get_history_words(self):
        """単語帳を作成する。

        対象は'http://socialstudies.boy.jp/page-994/'にある歴史人物
        """
        url = 'http://socialstudies.boy.jp/page-994/'
        page = requests.get(url)
        soup = bs4(page.content, 'lxml')
        tag_words = soup.find_all(class_='column-1')
        words = [word.string for word in tag_words]

        return words

    def get_science_words(self):
        """理化用の単語帳を作成する"""

        url = 'http://rikamato.com/2017/12/15/science_word/'
        page = requests.get(url)
        soup = bs4(page.content, 'lxml')
        tag_words = soup.find_all('tr')
        words = [word.text.split("\n")[1] for word in tag_words[1:]]

        return words

    @quiz_wikipedia.command(aliases=['gil', 'get_in_list'])
    async def get_wikipedia_page_for_wordlist(self, ctx):
        """作成した単語帳からランダムで単語を選び、その単語でwikipediaのページを取得する"""

        await ctx.send("妹「単語帳から適当に問題に出すね！」")
        random_word = random.choice(self.wordlist)
        self.wikipedia_page = wikipedia.page(random_word)
        await ctx.send("妹は問題を書きとめ、あなたからの質問に応える気が十分なようだ")

    @quiz_wikipedia.command(aliases=['d_show_wordlist'])
    async def show_wordlist(self, ctx):
        """デバッグ用。wordlistを見る

        Discordの出力文字数限界が2000なので、2000未満の表示とする"""
        print(", ".join(self.wordlist)[:1000] + "...")
