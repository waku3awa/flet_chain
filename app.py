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
    Dropdown,
    dropdown,
    PopupMenuButton,
    PopupMenuItem,
    Divider,
    RadioGroup,
    Radio,
    ScrollMode,
)
from typing import Optional, List, Dict
import re


def extract_single_number(text):
    numbers = re.findall(r'\d+', text)
    if len(numbers) == 1:
        return int(numbers[0])
    return None

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

# ===== グラフ情報の内部データ =====
# 各ノードは一意の id, ブロックの type, 接続先ノード id (next) を保持します
graph_nodes: List[Dict] = []
# ノード id 用のカウンター
node_id_counter = 0

# ノード追加用の関数
def add_node(block_type: str) -> None:
    global node_id_counter, graph_nodes
    node = {
        "id": node_id_counter,
        "type": block_type,
        "next": None  # 接続先ノードの id (未設定なら None)
    }
    graph_nodes.append(node)
    node_id_counter += 1

def remove_node(node_id: int) -> None:
    global graph_nodes, start_node_id
    # 削除対象ノードを除去
    graph_nodes = [node for node in graph_nodes if node["id"] != node_id]
    # 他のノードの接続先が削除された場合は None に
    for node in graph_nodes:
        if node["next"] == node_id:
            node["next"] = None
    # 開始ノードが削除された場合
    if start_node_id == node_id:
        start_node_id = None

# ===== Flet アプリ本体 =====
def main(page: Page):
    # 開始ノードの id
    start_node_id: Optional[int] = None

    page.title = "Chain of Responsibility グラフ構成（ドラッグ＆ドロップ版）"
    page.scroll = "adaptive"

    log_column = Column(scroll=ScrollMode.AUTO, expand=True)

    # ----- ログ表示用関数 -----
    def log(message: str):
        log_column.controls.append(Text(message))
        page.update()

    # ----- 左ペイン：利用可能ブロック一覧 -----
    available_blocks = ["A", "B", "C", "D"]
    available_block_controls = []
    for block_id in available_blocks:
        available_block_controls.append(
            Draggable(
                content=Container(
                    content=Text(block_id, size=20, weight="bold", color="white"),
                    width=60,
                    height=60,
                    bgcolor=ft.Colors.CYAN,
                    alignment=ft.alignment.center,
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

    # ----- 右ペイン：グラフ構成エリア -----
    # グラフノードの一覧表示用 Column
    graph_nodes_column = Column(spacing=10)

    # グラフ全体エリアの更新（ノード一覧、各ノードの接続先ドロップダウン、開始ノード設定ボタン）
    def update_graph_display():
        nonlocal start_node_id
        graph_nodes_column.controls.clear()
        for node in graph_nodes:
            # ドロップダウンのアイテムは、同じグラフ内の他のノード＋「なし」
            dropdown_items = [dropdown.Option("None", text="None")]
            for other in graph_nodes:
                if other["id"] != node["id"]:
                    dropdown_items.append(dropdown.Option(f'{other["type"]} (id:{other["id"]})', text=str(other["id"])))
            # 現在設定されている next 値（文字列に変換しておく）
            current_val = str(node["next"]) if node["next"] is not None else "None"

            # ドロップダウン変更時の処理
            def on_change_dropdown(e, node_id=node["id"]):
                val = extract_single_number(e.control.value)
                # "None" の場合は接続解除
                for n in graph_nodes:
                    if n["id"] == node_id:
                        n["next"] = None if (val == "None") or (val is None) else int(val)
                update_graph_display()

            node_dropdown = Dropdown(
                options=dropdown_items,
                value=current_val,
                on_change=on_change_dropdown,
                width=150,
            )
            # 「開始ノードに設定」ボタン（すでに開始ノードなら★マーク）
            def set_as_start(e, node_id=node["id"]):
                nonlocal start_node_id
                start_node_id = node_id
                update_graph_display()
            start_btn = ElevatedButton(
                text="★" if start_node_id == node["id"] else "Set Start",
                on_click=set_as_start,
                width=80
            )
            # ノード削除ボタン
            def delete_node(e, node_id=node["id"]):
                remove_node(node_id)
                update_graph_display()
            del_btn = IconButton(
                icon=ft.Icons.DELETE,
                tooltip="削除",
                on_click=delete_node
            )

            node_row = Row(
                controls=[
                    Text(f"ID:{node['id']}  {node['type']}", size=18),
                    Text("→"),
                    node_dropdown,
                    start_btn,
                    del_btn,
                ],
                alignment="spaceBetween"
            )
            graph_nodes_column.controls.append(Container(content=node_row, padding=5, bgcolor=ft.Colors.BLUE_50))
        graph_nodes_column.update()
        page.update()

    # ドラッグでグラフエリアにノード追加
    graph_area = DragTarget(
        content=Container(
            content=Column(
                controls=[
                    Text("ここにブロックをドロップしてノード追加", color="gray", size=16),
                    graph_nodes_column,
                ],
                spacing=10,
            ),
            width=400,
            height=400,
            border=ft.border.all(2, ft.Colors.BLACK),
            padding=10,
        ),
        group="blocks",
        on_accept=lambda e: on_accept_graph(e)
    )

    def on_accept_graph(e: ft.DragTargetEvent):
        src = page.get_control(e.src_id)
        # src.data はブロックの種別（例："A"）
        add_node(src.data)
        update_graph_display()

    # ----- グラフ開始ボタン -----
    def start_graph(e):
        log_column.controls.clear()
        log("【処理開始】")
        if start_node_id is None:
            log("開始ノードが設定されていません。")
            page.update()
            return
        # ノード id ごとにハンドラーインスタンスを生成
        handler_map: Dict[int, Handler] = {}
        for node in graph_nodes:
            # ハンドラーのインスタンスを生成（node["type"] から）
            handler_map[node["id"]] = handler_classes[node["type"]](f"{node['type']}(id:{node['id']})")
        # 接続情報（各ノードの next）
        for node in graph_nodes:
            nxt = node["next"]
            if nxt is not None and nxt in handler_map:
                handler_map[node["id"]].set_next(handler_map[nxt])
        # 開始ノードから処理開始
        request = {}
        handler_map[start_node_id].handle(request, log)
        log("【処理終了】")
        page.update()

    start_button = ElevatedButton(text="グラフ開始", on_click=start_graph)

    # ----- 全体レイアウト（左右） -----
    main_row = Row(
        controls=[
            Container(content=available_blocks_column, width=120, padding=10),
            Container(width=20),  # スペーサー
            Container(content=graph_area, padding=10),
        ],
    )

    page.add(
        Row(controls=[start_button]),
        Divider(),
        main_row,
        Divider(),
        Column(
            controls=[
                Text("【ログ】", weight="bold"),
                log_column
            ],
            expand=True,
        ),
    )

    update_graph_display()

ft.app(target=main)
