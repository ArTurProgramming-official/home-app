from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.bottomnavigation import MDBottomNavigation, MDBottomNavigationItem
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.scrollview import ScrollView
from kivymd.uix.label import MDLabel
from kivymd.uix.card import MDCard
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDFlatButton, MDRaisedButton, MDTextButton
from kivy.uix.image import AsyncImage
from kivy.metrics import dp
import requests
import webbrowser
from kivy.storage.jsonstore import JsonStore
from kivy.clock import Clock

GITHUB_BASE = "https://raw.githubusercontent.com/ArTurProgramming-official/market-place-data/main/"
VERSION_FILE = "version.json"
CURRENT_VERSION = "1.1"

class ProductItem(MDCard):
    def __init__(self, product, show_detail_callback, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.size_hint = (0.5, None)
        self.height = dp(260)
        self.radius = [16]
        self.padding = dp(8)
        self.spacing = dp(8)
        self.md_bg_color = (0.9, 0.95, 1, 1)
        self.line_color = (0.4, 0.6, 0.8, 1)
        self.product = product
        self.show_detail_callback = show_detail_callback
        self._touch_handled = False

        if product.get("image"):
            img = AsyncImage(source=product["image"], size_hint_y=None, height=dp(140))
            self.add_widget(img)

        text = f"[b]{product['name']}[/b]\n{product.get('price', '')} ₽"
        label = MDLabel(
            text=text,
            markup=True,
            halign='center',
            theme_text_color="Custom",
            text_color=(0.1, 0.3, 0.6, 1),
            size_hint_y=None,
        )
        label.bind(texture_size=lambda instance, size: setattr(instance, 'height', size[1]))
        self.add_widget(label)

    def on_touch_up(self, touch):
        if self.collide_point(*touch.pos) and not self._touch_handled:
            self._touch_handled = True
            self.show_detail_callback(self.product, self)
            return True
        return super().on_touch_up(touch)

class NewsItem(MDCard):
    def __init__(self, news, show_detail_callback, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.size_hint = (1, None)
        self.height = dp(100)
        self.padding = dp(10)
        self.radius = [12]
        self.md_bg_color = (0.9, 0.95, 1, 1)
        self.line_color = (0.4, 0.6, 0.8, 1)
        self.news = news
        self.show_detail_callback = show_detail_callback
        self._touch_handled = False

        title = MDLabel(
            text=news["title"], 
            theme_text_color="Custom", 
            text_color=(0.1, 0.3, 0.6, 1),
            font_style="H6", 
            size_hint_y=None, 
            height=dp(40)
        )
        self.add_widget(title)

    def on_touch_up(self, touch):
        if self.collide_point(*touch.pos) and not self._touch_handled:
            self._touch_handled = True
            self.show_detail_callback(self.news, self)
            return True
        return super().on_touch_up(touch)

class ShopApp(MDApp):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.store = JsonStore('app_data.json')
        self.update_checked = False

    def build(self):
        self.theme_cls.primary_palette = "Blue"
        self.theme_cls.primary_hue = "500"
        self.theme_cls.accent_palette = "LightBlue"
        self.theme_cls.accent_hue = "300"
        self.theme_cls.theme_style = "Light"

        self.products = []
        self.news = []
        self.dialog = None
        self.update_dialog = None

        screen = MDScreen()
        self.nav = MDBottomNavigation()

        self.tab_products = MDBottomNavigationItem(name='products', text='Товары', icon='shopping')
        self.tab_news = MDBottomNavigationItem(name='news', text='Новости', icon='newspaper')
        self.tab_about = MDBottomNavigationItem(name='about', text='О нас', icon='information')

        self.nav.add_widget(self.tab_products)
        self.nav.add_widget(self.tab_news)
        self.nav.add_widget(self.tab_about)

        screen.add_widget(self.nav)

        self.build_products_tab()
        self.build_news_tab()
        self.build_about_tab()

        self.load_products()
        self.load_news()

        return screen

    def on_start(self):
        if not self.update_checked:
            self.check_for_updates()
            self.update_checked = True

    def check_for_updates(self):
        try:
            url = f"{GITHUB_BASE}{VERSION_FILE}"
            res = requests.get(url)
            if res.status_code == 200:
                version_data = res.json()
                latest_version = version_data.get("version", "1.0")
                download_url = version_data.get("download_url", "")
                
                if self.compare_versions(CURRENT_VERSION, latest_version) < 0:
                    self.show_update_dialog(latest_version, download_url)
        except Exception as e:
            print(f"Ошибка при проверке обновлений: {e}")

    def compare_versions(self, current, latest):
        current_parts = list(map(int, current.split('.')))
        latest_parts = list(map(int, latest.split('.')))
        
        for cur, lat in zip(current_parts, latest_parts):
            if cur < lat:
                return -1
            elif cur > lat:
                return 1
        return 0

    def show_update_dialog(self, new_version, download_url):
        content = MDBoxLayout(
            orientation='vertical', 
            spacing=dp(10),
            padding=[dp(20), dp(20), dp(20), dp(10)],
            size_hint_y=None,
            height=dp(250)
        )
        
        content.add_widget(MDLabel(
            text=f"Доступна версия {new_version}",
            halign='center',
            theme_text_color="Primary",
            font_style="H6",
            size_hint_y=None,
            height=dp(40),
            padding=[0, dp(10)]
        ))
        
        content.add_widget(MDLabel(
            text="Доступно обновление приложения",
            halign='center',
            theme_text_color="Secondary",
            size_hint_y=None,
            height=dp(30),
            padding=[0, dp(5)]
        ))

        try:
            changelog = requests.get(f"{GITHUB_BASE}changelog.txt").text
            scroll = ScrollView(
                size_hint_y=None,
                height=dp(120),
                bar_width=dp(4),
                bar_color=[0.2, 0.5, 0.8, 1]
            )
            scroll_content = MDLabel(
                text=changelog,
                halign='center',
                size_hint_y=None,
                valign='top',
                padding=[dp(10), 0]
            )
            scroll_content.bind(
                texture_size=lambda instance, size: setattr(instance, 'height', size[1])
            )
            scroll.add_widget(scroll_content)
            content.add_widget(scroll)
        except Exception as e:
            print(f"Ошибка загрузки changelog: {e}")

        self.update_dialog = MDDialog(
            title="",
            type="custom",
            content_cls=content,
            buttons=[
                MDFlatButton(
                    text="Позже",
                    theme_text_color="Custom",
                    text_color=(0.2, 0.5, 0.8, 1),
                    on_release=lambda x: self.update_dialog.dismiss()
                ),
                MDRaisedButton(
                    text="Обновить",
                    md_bg_color=(0.2, 0.5, 0.8, 1),
                    on_release=lambda x: self.download_update(download_url)
                )
            ],
            size_hint=(0.9, None),
            height=dp(400),
            auto_dismiss=False,
            overlay_color=[0, 0, 0, 0.7]
        )
        
        Clock.schedule_once(lambda dt: self.update_dialog.open(), 0.1)

    def download_update(self, url):
        if url:
            webbrowser.open(url)
        if self.update_dialog:
            self.update_dialog.dismiss()

    def build_products_tab(self):
        self.products_scroll_layout = MDBoxLayout(
            orientation='vertical', spacing=dp(10), padding=dp(10), size_hint_y=None
        )
        self.products_scroll_layout.bind(minimum_height=self.products_scroll_layout.setter('height'))

        scroll = ScrollView()
        scroll.add_widget(self.products_scroll_layout)

        self.products_wrapper = MDBoxLayout(orientation='vertical')
        self.btn_refresh_products = MDRaisedButton(
            text="Обновить",
            pos_hint={"center_x": 0.5},
            size_hint_y=None,
            height=dp(40),
            md_bg_color=(0.2, 0.5, 0.8, 1),
            on_release=lambda x: self.load_products()
        )
        self.products_wrapper.add_widget(self.btn_refresh_products)
        self.products_wrapper.add_widget(scroll)
        self.tab_products.add_widget(self.products_wrapper)

    def load_products(self):
        try:
            url = GITHUB_BASE + "products.json"
            res = requests.get(url)
            if res.status_code == 200:
                self.products = res.json()
                self.update_products()
        except Exception as e:
            print(f"Ошибка загрузки товаров: {e}")

    def update_products(self):
        self.products_scroll_layout.clear_widgets()
        row = None
        for i, product in enumerate(self.products):
            if i % 2 == 0:
                row = MDBoxLayout(orientation='horizontal', spacing=dp(10), size_hint_y=None, height=dp(260))
                self.products_scroll_layout.add_widget(row)
            item = ProductItem(product, self.show_product_detail)
            row.add_widget(item)

    def show_product_detail(self, product, product_item):
        if self.dialog:
            self.dialog.dismiss()
            self.dialog = None

        layout = MDBoxLayout(orientation='vertical', padding=dp(10), spacing=dp(10), size_hint_y=None)
        layout.bind(minimum_height=layout.setter('height'))

        title = MDLabel(
            text=product.get("name", ""), 
            font_style="H6", 
            halign="center", 
            theme_text_color="Custom",
            text_color=(0.1, 0.3, 0.6, 1),
            size_hint_y=None, 
            height=dp(40)
        )
        layout.add_widget(title)

        if product.get("image"):
            img = AsyncImage(source=product["image"], size_hint_y=None, height=dp(180))
            layout.add_widget(img)

        description = MDLabel(
            text=product.get("description", ""), 
            halign="left", 
            theme_text_color="Custom",
            text_color=(0.2, 0.2, 0.2, 1),
            size_hint_y=None
        )
        description.bind(texture_size=lambda instance, value: setattr(instance, 'height', instance.texture_size[1]))
        layout.add_widget(description)

        buttons = []
        if product.get("link"):
            btn_go = MDFlatButton(
                text="Перейти по ссылке",
                theme_text_color="Custom",
                text_color=(0.2, 0.5, 0.8, 1),
                on_release=lambda x: webbrowser.open(product["link"])
            )
            buttons.append(btn_go)

        btn_close = MDFlatButton(
            text="Закрыть", 
            theme_text_color="Custom",
            text_color=(0.2, 0.5, 0.8, 1),
            on_release=lambda x: self.close_dialog(product_item)
        )
        buttons.append(btn_close)

        self.dialog = MDDialog(
            title="",
            type="custom",
            content_cls=layout,
            buttons=buttons,
            size_hint=(0.9, None),
            height=dp(450),
            md_bg_color=(0.95, 0.98, 1, 1)
        )
        self.dialog.open()

    def close_dialog(self, item, *args):
        if self.dialog:
            self.dialog.dismiss()
            self.dialog = None
        item._touch_handled = False

    def build_news_tab(self):
        self.news_scroll_layout = MDBoxLayout(
            orientation='vertical', spacing=dp(10), padding=dp(10), size_hint_y=None
        )
        self.news_scroll_layout.bind(minimum_height=self.news_scroll_layout.setter('height'))

        scroll = ScrollView()
        scroll.add_widget(self.news_scroll_layout)

        self.news_wrapper = MDBoxLayout(orientation='vertical')
        self.btn_refresh_news = MDRaisedButton(
            text="Обновить",
            pos_hint={"center_x": 0.5},
            size_hint_y=None,
            height=dp(40),
            md_bg_color=(0.2, 0.5, 0.8, 1),
            on_release=lambda x: self.load_news()
        )
        self.news_wrapper.add_widget(self.btn_refresh_news)
        self.news_wrapper.add_widget(scroll)
        self.tab_news.add_widget(self.news_wrapper)

    def load_news(self):
        try:
            url = GITHUB_BASE + "news.json"
            res = requests.get(url)
            if res.status_code == 200:
                self.news = res.json()
                self.update_news()
        except Exception as e:
            print(f"Ошибка загрузки новостей: {e}")

    def update_news(self):
        self.news_scroll_layout.clear_widgets()
        for news in self.news:
            item = NewsItem(news, self.show_news_detail)
            self.news_scroll_layout.add_widget(item)

    def show_news_detail(self, news, news_item):
        if self.dialog:
            self.dialog.dismiss()
            self.dialog = None

        layout = MDBoxLayout(orientation='vertical', padding=dp(10), spacing=dp(10), size_hint_y=None)
        layout.bind(minimum_height=layout.setter('height'))

        title = MDLabel(
            text=news["title"], 
            font_style="H6", 
            halign="center", 
            theme_text_color="Custom",
            text_color=(0.1, 0.3, 0.6, 1),
            size_hint_y=None, 
            height=dp(40)
        )
        layout.add_widget(title)

        if news.get("image"):
            img = AsyncImage(source=news["image"], size_hint_y=None, height=dp(180))
            layout.add_widget(img)

        content = MDLabel(
            text=news.get("content", ""), 
            halign="left", 
            theme_text_color="Custom",
            text_color=(0.2, 0.2, 0.2, 1),
            size_hint_y=None
        )
        content.bind(texture_size=lambda instance, value: setattr(instance, 'height', instance.texture_size[1]))
        layout.add_widget(content)

        btn_close = MDFlatButton(
            text="Закрыть", 
            theme_text_color="Custom",
            text_color=(0.2, 0.5, 0.8, 1),
            on_release=lambda x: self.close_dialog(news_item)
        )
        self.dialog = MDDialog(
            title="",
            type="custom",
            content_cls=layout,
            buttons=[btn_close],
            size_hint=(0.9, None),
            height=dp(400),
            md_bg_color=(0.95, 0.98, 1, 1)
        )
        self.dialog.open()

    def build_about_tab(self):
        layout = MDBoxLayout(orientation='vertical', padding=20, spacing=20)
        
        label = MDLabel(
            text="ArturProgramming Home", 
            halign="center", 
            font_style="H5", 
            theme_text_color="Custom",
            text_color=(0.1, 0.3, 0.6, 1)
        )
        
        version_label = MDLabel(
            text=f"Версия {CURRENT_VERSION}", 
            halign="center", 
            font_style="Subtitle1", 
            theme_text_color="Custom",
            text_color=(0.4, 0.6, 0.8, 1)
        )
        
        link = MDTextButton(
            text="Канал: https://t.me/ArturProgrammer",
            halign="center",
            theme_text_color="Custom",
            text_color=(0.2, 0.5, 0.8, 1),
            on_release=lambda x: webbrowser.open("https://t.me/ArturProgrammer")
        )
        
        layout.add_widget(label)
        layout.add_widget(version_label)
        layout.add_widget(link)
        self.tab_about.add_widget(layout)

if __name__ == '__main__':
    ShopApp().run()