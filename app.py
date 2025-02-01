import flet as ft
from flet import (
    Page,
    Column,
    Row,
    Text,
    ElevatedButton,
    Container,
    Draggable,
    DragTarget,
    IconButton,
    Icons,
    Divider,
    ScrollMode,
)
from typing import Optional, List

# ===== Chain of Responsibility のハンドラー実装 =====

class Handler:
    def __init__(self, name: str):
        self.name = name
        self.next_handler: Optional["Handler"] = None

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
        if self.next_handler:
            self.next_handler.handle(request, log_func)

class HandlerB(Handler):
    def handle(self, request: dict, log_func):
        if request.get("data"):
            item = request["data"].pop(0)
            request["last_item"] = item
            log_func(f"{self.name} 処理中: {item}")
            if self.next_handler:
                self.next_handler.handle(request, log_func)
        else:
            log_func(f"{self.name} データなし、処理終了")

class HandlerC(Handler):
    def handle(self, request: dict, log_func):
        last_item = request.get("last_item", None)
        if last_item is not None:
            log_func(f"{self.name} が処理完了: {last_item}")
        if self.next_handler:
            self.next_handler.handle(request, log_func)

# D は B とほぼ同様ですが、ログに「（D版）」と表示する例です
class HandlerD(Handler):
    def handle(self, request: dict, log_func):
        if request.get("data"):
            item = request["data"].pop(0)
            request["last_item"] = item
            log_func(f"{self.name} （D版） 処理中: {item}")
            if self.next_handler:
                self.next_handler.handle(request, log_func)
        else:
            log_func(f"{self.name} （D版） データなし、処理終了")

# ハンドラークラスのマッピング
handler_classes = {
    "A": HandlerA,
    "B": HandlerB,
    "C": HandlerC,
    "D": HandlerD,
}

def main(page: Page):
    page.title = "Chain of Responsibility デモ（ドラッグ＆ドロップ版）"
    page.scroll = "adaptive"

    # --- チェーン構成用変数 ---
    initial_block_config: Optional[str] = None
    loop_blocks_config: List[str] = []

    log_column = Column(scroll=ScrollMode.AUTO, expand=True)

    # ----- 右ペイン：チェーン構成表示エリア -----
    # 初回ブロックエリア用 DragTarget 内の表示コンテナ
    initial_block_container = Container(
        content=Text("ここに初回ブロックをドロップ (例：A)"),
        width=200,
        height=60,
    )

    # ループブロックエリア用 Column
    loop_blocks_column = Column(spacing=10)
    loop_blocks_container = Container(
        content=loop_blocks_column,
        width=200,
        height=150,
        padding=10,
    )

    # チェーン表示エリアの更新関数（各ウィジェット更新後に page.update() を呼ぶ）
    def update_chain_display():
        nonlocal initial_block_config, loop_blocks_config
        # 初回ブロックの表示更新
        if initial_block_config:
            initial_block_container.content = Row(
                [
                    Text(initial_block_config, size=20),
                    IconButton(
                        icon=Icons.CLEAR,
                        tooltip="削除",
                        on_click=lambda e: remove_initial_block(),
                    ),
                ],
            )
        else:
            initial_block_container.content = Text("ここに初回ブロックをドロップ (例：A)")
        initial_block_container.update()

        # ループブロックの表示更新
        loop_blocks_column.controls.clear()
        for i, block_id in enumerate(loop_blocks_config):
            block_container = Container(
                content=Row(
                    [
                        Text(block_id, size=20),
                        IconButton(
                            icon=Icons.CLEAR,
                            tooltip="削除",
                            data=i,
                            on_click=lambda e, index=i: remove_loop_block(index),
                        ),
                    ],
                ),
                width=180,
                height=50,
            )
            loop_blocks_column.controls.append(block_container)
        # 末尾にドロップ用 DragTarget を追加
        loop_blocks_column.controls.append(
            DragTarget(
                content=Container(
                    content=Text("＋ ブロックをドロップ", size=14, color="gray"),
                    width=180,
                    height=40,
                ),
                group="blocks",
                on_accept=on_accept_loop_block
            )
        )
        loop_blocks_container.update()
        page.update()

    # 初回ブロック削除
    def remove_initial_block():
        nonlocal initial_block_config
        initial_block_config = None
        update_chain_display()

    # ループブロック削除
    def remove_loop_block(index: int):
        nonlocal loop_blocks_config
        if 0 <= index < len(loop_blocks_config):
            del loop_blocks_config[index]
            update_chain_display()

    # 初回ブロックエリアへのドロップ処理
    def on_accept_initial(e: ft.DragTargetEvent):
        nonlocal initial_block_config
        src = page.get_control(e.src_id)
        initial_block_config = src.data
        update_chain_display()

    # ループブロックエリアへの追加処理
    def on_accept_loop_block(e: ft.DragTargetEvent):
        nonlocal loop_blocks_config
        src = page.get_control(e.src_id)
        loop_blocks_config.append(src.data)
        update_chain_display()

    # ----- 左ペイン：利用可能ブロック一覧 -----
    available_blocks = ["A", "B", "C", "D"]
    available_block_controls = []
    for block_id in available_blocks:
        available_block_controls.append(
            Draggable(
                content=Container(
                    content=Text(block_id, size=20, weight="bold"),
                    width=60,
                    height=60,
                    bgcolor=ft.Colors.CYAN,
                    # alignment="center",
                    # border=1,
                ),
                group="blocks",
                data=block_id
            )
        )

    available_blocks_column = Column(
        controls=[
            Text("利用可能なブロック", weight="bold"),
            *available_block_controls,
        ],
        spacing=10,
    )

    # ----- チェーン構成エリア（右ペイン） -----
    chain_configuration_area = Column(
        controls=[
            Text("チェーン構成", weight="bold"),
            Text("【初回ブロック】", size=16),
            DragTarget(
                content=initial_block_container,
                group="blocks",
                on_accept=on_accept_initial
            ),
            Divider(),
            Text("【ループブロック】", size=16),
            loop_blocks_container,
            Container(
                content=Text("※ ループ：最後のブロックから先頭のループブロックへ ↻", color="blue", size=12),
                padding=5,
            ),
        ],
        spacing=10,
    )

    # ----- チェーン開始ボタン -----
    def start_chain(e):
        nonlocal initial_block_config, loop_blocks_config
        log_column.controls.clear()
        log("開始")
        if not initial_block_config:
            log("初回ブロックが設定されていません。")
            page.update()
            return
        if not loop_blocks_config:
            log("ループブロックが設定されていません。")
            page.update()
            return

        request = {}
        # 初回ブロックのインスタンス作成
        head = handler_classes[initial_block_config](initial_block_config)
        current = head

        # ループブロックのインスタンス作成
        loop_handlers = []
        for bid in loop_blocks_config:
            loop_handlers.append(handler_classes[bid](bid))
        # 接続: 初回ブロックの next にループブロックの先頭を設定
        current.set_next(loop_handlers[0])
        # ループブロック間の接続
        for i in range(len(loop_handlers) - 1):
            loop_handlers[i].set_next(loop_handlers[i+1])
        # 最後のループブロックから先頭へループ
        loop_handlers[-1].set_next(loop_handlers[0])

        head.handle(request, log)
        log("終わり")
        page.update()

    start_button = ElevatedButton(text="チェーン開始", on_click=start_chain)

    # ----- ログ表示エリア -----
    def log(message: str):
        log_column.controls.append(Text(message))
        page.update()

    log_area = Column(
        controls=[Text("【ログ】", weight="bold"), log_column],
        expand=True,
    )

    # ----- 全体レイアウト（左右） -----
    main_row = Row(
        controls=[
            Container(content=available_blocks_column, width=120, padding=10),
            Container(width=20),  # スペーサー
            Container(content=chain_configuration_area, padding=10),
        ],
    )

    page.add(
        Row(controls=[start_button]),
        Divider(),
        main_row,
        Divider(),
        log_area,
    )

    # 初期表示更新
    update_chain_display()

ft.app(target=main)
