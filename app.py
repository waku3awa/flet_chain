import flet
from flet import Page, Column, Text, ElevatedButton, ScrollMode

# ----- Chain of Responsibility の実装 -----

class Handler:
    def __init__(self, name: str):
        self.name = name
        self.next_handler = None

    def set_next(self, handler: "Handler"):
        self.next_handler = handler
        return handler

    def handle(self, request: dict, log_func):
        raise NotImplementedError("handle() メソッドを実装してください")

class HandlerA(Handler):
    def handle(self, request: dict, log_func):
        log_func(f"{self.name} 開始")
        # A は複数のデータを生成して、リクエストの "data" リストに格納
        request["data"] = ["Item1", "Item2", "Item3"]
        log_func(f"{self.name} が生成したデータ: {request['data']}")
        # 次のハンドラーへ渡す
        if self.next_handler:
            self.next_handler.handle(request, log_func)

class HandlerB(Handler):
    def handle(self, request: dict, log_func):
        # リクエストの "data" にデータがあれば処理
        if request.get("data"):
            # リストから先頭の要素を取り出し、"last_item" に保存
            item = request["data"].pop(0)
            request["last_item"] = item
            log_func(f"{self.name} 処理中: {item}")
            if self.next_handler:
                self.next_handler.handle(request, log_func)
        else:
            log_func(f"{self.name} データなし、処理終了")
            # データがなくなった場合はここでチェーンを打ち切る

class HandlerC(Handler):
    def handle(self, request: dict, log_func):
        # B で取り出した "last_item" を使って処理
        last_item = request.get("last_item", None)
        if last_item is not None:
            log_func(f"{self.name} が処理完了: {last_item}")
        # 次のハンドラーへ（ここで B をループ先として設定している）
        if self.next_handler:
            self.next_handler.handle(request, log_func)

# ----- flet を使った GUI アプリケーション部分 -----

def main(page: Page):
    page.title = "Chain of Responsibility デモ"
    # ログ出力用の Column（スクロール可能）
    log_column = Column(scroll=ScrollMode.AUTO)

    def log(message: str):
        log_column.controls.append(Text(message))
        page.update()

    def start_chain(e):
        # 既存のログをクリア
        log_column.controls.clear()
        log("開始")

        # 共通データ用の辞書
        request = {}

        # ハンドラー A, B, C の生成とチェーンの設定
        a = HandlerA("A")
        b = HandlerB("B")
        c = HandlerC("C")
        a.set_next(b)
        b.set_next(c)
        # C の次に B を設定することで、BとCでループさせる
        c.set_next(b)

        # チェーン処理の開始（A からスタート）
        a.handle(request, log)

        log("終わり")
        page.update()

    # チェーン開始用のボタン
    start_button = ElevatedButton(text="チェーン開始", on_click=start_chain)
    page.add(start_button, log_column)

# flet アプリケーションの起動
flet.app(target=main)
