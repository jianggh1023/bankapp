"""
银行账户管理系统 - Kivy 版本
"""

import json
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.core.window import Window
from kivy.clock import Clock

from bank_account import BankAccount

# 设置窗口大小（仅桌面调试用）
Window.size = (400, 600)


class BankAppWidget(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', spacing=10, padding=10, **kwargs)
        # 使用应用数据目录存储 json（Android 上安全）
        self.account = BankAccount(
            owner="用户",
            initial_balance=0.0,
            annual_rate=0.015,
            storage_path=self._get_storage_path()
        )
        self.build_ui()
        self.refresh_statement()

    def _get_storage_path(self):
        """获取可写的存储路径（Android 上使用 app 私有目录）"""
        from kivy.utils import platform
        if platform == 'android':
            # 在 Android 上，使用 app 的用户数据目录
            from android.storage import app_storage_path
            import os
            path = os.path.join(app_storage_path(), 'bank_account_data.json')
        else:
            # 桌面环境，使用当前目录
            import os
            path = os.path.join(os.path.dirname(__file__), 'bank_account_data.json')
        return path

    def build_ui(self):
        # 金额输入行
        amount_box = BoxLayout(size_hint_y=None, height=40)
        amount_box.add_widget(Label(text='金额:', size_hint_x=0.2))
        self.amount_input = TextInput(text='', multiline=False, input_filter='float')
        amount_box.add_widget(self.amount_input)
        self.add_widget(amount_box)

        # 摘要输入行
        desc_box = BoxLayout(size_hint_y=None, height=40)
        desc_box.add_widget(Label(text='摘要:', size_hint_x=0.2))
        self.desc_input = TextInput(text='', multiline=False)
        desc_box.add_widget(self.desc_input)
        self.add_widget(desc_box)

        # 按钮行
        btn_box = BoxLayout(size_hint_y=None, height=50, spacing=5)
        btn_deposit = Button(text='存款', on_press=self.do_deposit)
        btn_withdraw = Button(text='取款', on_press=self.do_withdraw)
        btn_interest = Button(text='计息', on_press=self.do_interest)
        btn_balance = Button(text='余额', on_press=self.do_balance)
        btn_box.add_widget(btn_deposit)
        btn_box.add_widget(btn_withdraw)
        btn_box.add_widget(btn_interest)
        btn_box.add_widget(btn_balance)
        self.add_widget(btn_box)

        # 明细表格标题
        header_box = BoxLayout(size_hint_y=None, height=30)
        header_box.add_widget(Label(text='日期', bold=True))
        header_box.add_widget(Label(text='摘要', bold=True))
        header_box.add_widget(Label(text='存入', bold=True))
        header_box.add_widget(Label(text='取出', bold=True))
        header_box.add_widget(Label(text='余额', bold=True))
        self.add_widget(header_box)

        # 明细内容（可滚动）
        self.statement_grid = GridLayout(cols=5, size_hint_y=None, spacing=2)
        self.statement_grid.bind(minimum_height=self.statement_grid.setter('height'))
        scroll = ScrollView(size_hint=(1, 0.7))
        scroll.add_widget(self.statement_grid)
        self.add_widget(scroll)

        # 刷新按钮
        refresh_btn = Button(text='刷新明细', size_hint_y=None, height=40, on_press=self.refresh_statement)
        self.add_widget(refresh_btn)

    def do_deposit(self, instance):
        try:
            amount = float(self.amount_input.text or '0')
            desc = self.desc_input.text.strip() or '存款'
            self.account.deposit(amount, desc)
            self.refresh_statement()
            self.show_popup('成功', '存款成功')
        except Exception as e:
            self.show_popup('错误', str(e))

    def do_withdraw(self, instance):
        try:
            amount = float(self.amount_input.text or '0')
            desc = self.desc_input.text.strip() or '取款'
            self.account.withdraw(amount, desc)
            self.refresh_statement()
            self.show_popup('成功', '取款成功')
        except Exception as e:
            self.show_popup('错误', str(e))

    def do_interest(self, instance):
        try:
            interest = self.account.settle_interest()
            self.refresh_statement()
            self.show_popup('利息', f'本次利息：{interest:.2f} 元')
        except Exception as e:
            self.show_popup('错误', str(e))

    def do_balance(self, instance):
        self.show_popup('余额', self.account.show_balance())

    def refresh_statement(self, instance=None):
        self.statement_grid.clear_widgets()
        for tx in self.account.get_statement():
            self.statement_grid.add_widget(Label(text=str(tx['date']), text_size=(None, None), halign='left'))
            self.statement_grid.add_widget(Label(text=tx['description'], text_size=(None, None), halign='left'))
            self.statement_grid.add_widget(Label(text=f"{tx['deposit']:.2f}", text_size=(None, None), halign='right'))
            self.statement_grid.add_widget(Label(text=f"{tx['withdraw']:.2f}", text_size=(None, None), halign='right'))
            self.statement_grid.add_widget(Label(text=f"{tx['balance']:.2f}", text_size=(None, None), halign='right'))

    def show_popup(self, title, message):
        # 简单弹出提示（使用 Kivy 的弹窗）
        from kivy.uix.popup import Popup
        from kivy.uix.label import Label
        popup = Popup(title=title, content=Label(text=message), size_hint=(0.8, 0.4))
        popup.open()


class BankApp(App):
    def build(self):
        return BankAppWidget()


if __name__ == '__main__':
    BankApp().run()