import sqlite3
from datetime import datetime
from pathlib import Path
from typing import List, Tuple

class DataManager:
    def __init__(self, data_dir: str) -> None:
        """
        Parameters:
        ====================
        data_dir : str
            データベースファイルを配置するディレクトリへのパス
        """
        self.__path = Path(data_dir) / Path('data.db')

        if not self.__path.exists():
            self.__path.touch()
            self.__initialize_database()


    def __get_date(self) -> int:
        """
        Returns:
        ====================
        int
            年と日付(20201225のようなフォーマット)
        """
        return int(datetime.today().strftime('%Y%m%d'))


    def __initialize_database(self) -> None:
        """
        データベースの初期化を行う
        """
        conn = sqlite3.connect(self.__path)
        c = conn.cursor()

        # 絵文字の使用履歴を格納するためのテーブル。
        ## date - integer
        ##      絵文字がそのメッセージに初めて使用された日時
        ##
        ## message_id - integer
        ##      メッセージのID
        ##
        ## memnber_id - integer
        ##      絵文字を使用したメンバーのID
        ##
        ## emoji_id - integer
        ##      使用された絵文字のID
        ##
        ## usage_pattern - text
        ##      絵文字が使用された形態
        ##          ・ message
        ##              メッセージの内容として使用された
        ##
        ##          ・ reaction
        ##              メッセージにリアクションとして追加された
        ##
        ## 【 重複を許さない組み合わせ 】
        ##      message_id, member_id, emoji_id, usage_pattern ( 同じメッセージに同じ形態で同じ絵文字を使用した場合、一人に対して一度のみカウントする )

        c.execute("""CREATE TABLE emoji_histories
                     (date integer, message_id integer, member_id integer, emoji_id integer, usage_pattern text,
                     unique(message_id, member_id, emoji_id, usage_pattern))""")

        conn.commit()
        conn.close()


    def regist_emojis(self, message_id: int, member_id: int, emoji_ids: List[int]) -> None:
        """
        メッセージに含まれていた絵文字を登録する。
        ただし、同じメッセージ内に含まれている同じ絵文字は一度しかカウントしない。

        Parameters:
        ====================
        message_id : int
            メッセージのID

        member_id : int
            メッセージの送信者のID

        emoji_ids : List[int]
            メッセージに含まれる絵文字のIDのリスト
        """
        conn = sqlite3.connect(self.__path)
        c = conn.cursor()

        date = self.__get_date()

        for emoji_id in set(emoji_ids):
            c.execute(f"""INSERT INTO emoji_histories VALUES
                         ({date}, {message_id}, {member_id}, {emoji_id}, \"message\")""")

        conn.commit()
        conn.close()


    def regist_reactions(self, message_id: int, member_id: int, emoji_id: int) -> None:
        """
        メッセージにリアクションとして追加された絵文字を登録する。
        ただし、既に登録されている場合は登録しない。

        Parameters:
        ====================
        message_id : int
            メッセージのID

        member_id : int
            リアクションをつけたメンバーのID

        emoji_id : int
            使用された絵文字のID
        """
        conn = sqlite3.connect(self.__path)
        c = conn.cursor()

        date = self.__get_date()

        c.execute(f"""INSERT INTO emoji_histories VALUES
                        ({date}, {message_id}, {member_id}, {emoji_id}, \"reaction\")""")

        conn.commit()
        conn.close()


    def get_total(self) -> List[Tuple[int, int]]:
        """
        これまで使用された絵文字の統計を取得する。

        Returns:
        ====================
        Dict[int, int]
            key:
                絵文字のID

            value:
                絵文字が使用された数
        """
        conn = sqlite3.connect(self.__path)
        c = conn.cursor()

        total = []

        c.execute("""SELECT emoji_id, COUNT(emoji_id) FROM emoji_histories GROUP BY emoji_id ORDER BY COUNT(emoji_id) DESC""")
        total = c.fetchall()

        conn.commit()
        conn.close()

        return total