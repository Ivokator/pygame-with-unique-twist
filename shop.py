import random

import pygame as pg
import pygame_menu as pm
import pygame_widgets as pw  # type: ignore

from pygame_widgets.button import Button, ButtonArray # type: ignore

import items

from classes import Player, PlayerGroup
from constants import *
from downgrade_fx import apply_downgrade_effect

pg.init()

list_of_possible_shop_items: list[object] = [
    items.big_shot,
    items.deployable_shield,
    items.dash
]

class ShopUI:
    def __init__(self, screen: pg.Surface, player_group: PlayerGroup) -> None:
        self.running = True
        self.computer_back: pg.Rect = pg.Rect(SCREEN_WIDTH // 20, SCREEN_HEIGHT // 20, SCREEN_WIDTH * 0.9, SCREEN_HEIGHT * 0.9)
        self.player_group: PlayerGroup | None = player_group
        self.items: list[ShopItem] = [ShopItem(screen, item, player_group) for item in 
                                      random.sample(list_of_possible_shop_items, 
                                                    min(len(list_of_possible_shop_items), 4))]
        self.inventory_items: list[InventoryItem] =[InventoryItem(screen, item, player_group) for item in
                                                    player_group.upgrades]
        self.screen = screen

        # Continue (to next round) button
        self.continue_button = Button(
            win=screen,
            x=self.computer_back.width * 2 // 3,
            y=self.computer_back.height * 5 // 6,
            width=300,
            height=70,
            text="CONTINUE",
            font=PRESS_START_FONT,
            fontSize=20,
            radius=5,
            inactiveColour=(60, 60, 60),
            onClick= lambda: self.quit_shop(),
        )


    def background(self, surface: pg.Surface) -> None:
        """Roguelite map background
        
        this is supposed to resemble a futuristic ship on-board screen
        """
        surface.fill((0,0,0))

        pg.draw.rect(surface, (20, 20, 20), self.computer_back, width=10, border_radius=20)

    def three_choice_buttons(self, surface: pg.Surface) -> ButtonArray:
        # might not use this!

        return ButtonArray(
        # Mandatory Parameters
        surface,  # Surface to place button array on
        SCREEN_WIDTH // 2 - (SCREEN_WIDTH * 0.8 // 2),  # X-coordinate
        SCREEN_HEIGHT // 2,  # Y-coordinate
        SCREEN_WIDTH * 0.8,  # Width
        SCREEN_HEIGHT * 0.3,  # Height
        (3, 1),  # Shape: 2 buttons wide, 2 buttons tall
        border=100,  # Distance between buttons and edge of array
        fonts=[PRESS_START_FONT, PRESS_START_FONT, PRESS_START_FONT],
        fontSizes=[15, 15, 15],
        texts=('Pick', 'Pick', 'Pick'),  
        onClicks=(lambda: print('1'), lambda: print('2'), lambda: print('3'), lambda: print('4')),
        colour=(5, 5, 5),
    )

    def base_ui(self, surface: pg.Surface) -> ButtonArray:
        shop_rect: pg.Rect = pg.Rect(0, 0, self.computer_back.width * 0.8, self.computer_back.height // 3)
        shop_rect.centerx = self.computer_back.centerx
        shop_rect.centery = self.computer_back.y + self.computer_back.height // 4
        pg.draw.rect(surface, DARKER_GREY, shop_rect, border_radius=12)

        padding = 20  # space between rects and edges

        # draw smaller rects horizontally inside shop_rect
        num_rects = 4
        
        rect_width: int = (shop_rect.width - padding * (num_rects + 1)) // num_rects
        rect_height: int = shop_rect.height - 2 * padding - 20

        for i in range(num_rects):
            x = shop_rect.x + padding + i * (rect_width + padding)
            y = shop_rect.y + padding + 10
            item_rect = pg.Rect(x, y, rect_width, rect_height)
            pg.draw.rect(surface, (60, 60, 60), item_rect, border_radius=10)

        for i, item in enumerate(self.items):
            if item.item not in self.player_group.upgrades: # check if the item is not already in the player's inventory
                item.render(i, rect_width, rect_height, shop_rect)
            else:
                # self.items.remove(item) <--- do not do this! will place items incorrectly
                if item.item not in self.inventory_items:
                    if not any(inv_item.item == item.item for inv_item in self.inventory_items): # prevent duplicates
                        self.inventory_items.append(InventoryItem(surface, item.item, self.player_group))
                item.delete()
            
        upgrade_rect: pg.Rect = pg.Rect(0, 0, self.computer_back.width * 0.4, self.computer_back.height // 2)
        upgrade_rect.left = shop_rect.left
        upgrade_rect.centery = self.computer_back.y + int(self.computer_back.height * 0.72)
        pg.draw.rect(surface, DARKER_GREY, upgrade_rect, border_radius=12)

        # Draw a 2x2 grid of smaller rects inside upgrade_rect
        grid_rows, grid_cols = 2, 2

        cell_width = (upgrade_rect.width - (grid_cols + 1) * padding) // grid_cols
        cell_height = (upgrade_rect.height - (grid_rows + 1) * padding) // grid_rows

        for row in range(grid_rows):
            for col in range(grid_cols):
                cell_x = upgrade_rect.x + padding + col * (cell_width + padding)
                cell_y = upgrade_rect.y + padding + row * (cell_height + padding)
                cell_rect = pg.Rect(cell_x, cell_y, cell_width, cell_height)
                pg.draw.rect(surface, (60, 60, 60), cell_rect, border_radius=8)
        
        shop_title = PRESS_START_FONT.render("SHOP", True, (255, 255, 255))
        surface.blit(
            shop_title,
            (self.computer_back.centerx - shop_title.get_width()//2,
             self.computer_back.y + self.computer_back.height // 25)
        )

        upgrade_title = PRESS_START_FONT.render("UPGRADES", True, (255, 255, 255))
        surface.blit(
            upgrade_title,
            (upgrade_rect.centerx - upgrade_title.get_width()//2,
             upgrade_rect.y - self.computer_back.height // 25)
        )

        self.upgrades_ui(surface, upgrade_rect, cell_width, cell_height, padding, grid_rows, grid_cols)
        self.display_coins()
        events = pg.event.get()
        for event in events:
            self.continue_button.listen(event)
        self.continue_button.draw()
        pw.update(events)


    def upgrades_ui(self, surface: pg.Surface, upgrade_rect: pg.Rect, cell_width: int, cell_height: int, padding: int, grid_rows: int = 2, grid_cols: int = 2) -> None:
        """Draws the upgrades section UI, showing player's current upgrades in a grid."""
        if not hasattr(self.player_group, "upgrades"):
            return
        
        # translucent number overlay
        for slot in range(1, 5):
            row = (slot - 1) // grid_cols
            col = (slot - 1) % grid_cols

            cell_x = upgrade_rect.x + padding + col * (cell_width + padding)
            cell_y = upgrade_rect.y + padding + row * (cell_height + padding)
            cell_rect = pg.Rect(cell_x, cell_y, cell_width, cell_height)

            pg.draw.rect(surface, (60, 60, 60, 0), cell_rect, border_radius=8)

            slot_label = PRESS_START_FONT.render(str(slot), True, (200, 200, 200))
            text_x = cell_x + (cell_width - slot_label.get_width()) // 2
            text_y = cell_y + (cell_height - slot_label.get_height()) // 2
            surface.blit(slot_label, (text_x, text_y))

        for inv_item in self.inventory_items:
            s = getattr(inv_item, 'slot', None) + 1
            # Only draw if slot is a valid integer
            if isinstance(s, int) and 1 <= s <= 4:
                row = (s - 1) // grid_cols
                col = (s - 1) % grid_cols

                cell_x = upgrade_rect.x + padding + col * (cell_width + padding)
                cell_y = upgrade_rect.y + padding + row * (cell_height + padding)
                cell_rect = pg.Rect(cell_x, cell_y, cell_width, cell_height)

                inv_item.render_upgrade(surface, cell_rect)

        
            
    
    def display_coins(self) -> None:
        if self.player_group is not None and hasattr(self.player_group, "coins"):
            coins_text = PRESS_START_FONT.render(f"Coins: {self.player_group.coins}", True, (255, 255, 0))

            x = self.computer_back.width * 2 // 3 + 150 - coins_text.get_width() // 2
            y = self.computer_back.height * 5 // 6 - 40

            surface = pg.display.get_surface()
            surface.blit(coins_text, (x, y))

    def quit_shop(self):
        self.running = False

    def next_round_stats(self, surface: pg.Surface, game = None) -> None:
        self.draw_text_line(surface, f"Next Round: {getattr(game, 'current_wave', 'N/A')}", 1)
        self.draw_text_line(surface, f"Humans Alive: {getattr(game, 'humanoids_left', 'N/A')}", 2)
        self.draw_text_line(surface, f"Enemies: {game.num_of_landers + game.num_of_mutants}", 3)

    def draw_text_line(self, surface: pg.Surface, text: str, line_num: int) -> None:
        """Draws text at a specific line number below the shop UI."""

        rendered = PRESS_START_FONT.render(text, True, (255, 255, 255))

        base_y = self.computer_back.y + self.computer_back.height // 2 - 60
        line_height = rendered.get_height() + 8
        x = self.computer_back.width * 4 // 5 - rendered.get_width() // 2 - 10
        y = base_y + line_num * line_height
        surface.blit(rendered, (x, y))
    
    def shop_loop(self, screen: pg.Surface, surface: pg.Surface, game) -> None:
        clock = pg.time.Clock()

        while self.running:
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    self.running = False

            self.background(surface)
            self.base_ui(surface)

            if game:
                self.next_round_stats(surface, game)

            screen.blit(surface, (0, 0))
            apply_downgrade_effect(surface, 2)

            pg.display.flip()
            clock.tick(FRAMES_PER_SECOND)

class ShopItem(object):
    def __init__(self, screen, item: object, player_group: PlayerGroup) -> None:
        self.item: object | None = item()
        self.screen = screen
        self.slot: int = 0
        self.player_group: PlayerGroup = player_group

    def render(self, position: int, rect_width: int, rect_height: int, shop_rect: pg.Rect) -> None:
        self._render_text(position, rect_width, rect_height, shop_rect)
        self._render_buttons(position, rect_width, rect_height, shop_rect)

    def delete(self) -> None:
        if hasattr(self, "buy_button"): 
            self.buy_button.disable()
            self.info_button.disable()
            self.buy_button.hide()
            self.info_button.hide()


        events = pg.event.get()
        pw.update(events)
    
    def buy_upgrade(self) -> None:
        if not hasattr(self.item, "price"):
            return
        
        if len(self.player_group.upgrades) >= 4:
            return
        
        if self.item in self.player_group.upgrades:
            return
        
        for owned in self.player_group.upgrades:
            if type(owned) is type(self.item):
                return
        
        # check if player has enough coins...
        if self.player_group.coins >= self.item.price:
            self.player_group.coins -= self.item.price
            # ...then add to player's upgrades
            self.player_group.upgrades.append(self.item)
        
        if hasattr(self, "buy_button"):
            self.buy_button.disable()
    
    def _render_text(self, position: int, rect_width: int, rect_height: int, shop_rect: pg.Rect) -> None:
        """text. yes."""
        if self.item:
            name_text = SMALL_BUTTON_FONT.render(getattr(self.item, "name", "Unknown"), True, (255, 255, 255))
            price_text = SMALL_BUTTON_FONT.render(f"${getattr(self.item, 'price', '?')}", True, (200, 200, 80))

            padding = 20 # ok at this point make it universal or something

            shop_x = int(shop_rect.x + padding + position * (rect_width + padding))
            shop_y = int(shop_rect.y + padding + 10)

            name_x = shop_x + rect_width // 2 - name_text.get_width() // 2
            name_y = shop_y + 8

            price_x = shop_x + rect_width // 2 - price_text.get_width() // 2
            price_y = name_y + name_text.get_height() + 4

            surface = pg.display.get_surface() # today i learned this existed
            surface.blit(name_text, (name_x, name_y))
            surface.blit(price_text, (price_x, price_y))
    
    def _render_buttons(self, position: int, rect_width: int, rect_height: int, shop_rect: pg.Rect) -> None:
        """draws info and buy buttons"""

        # why did i do this to match the boxes...
        padding: int = 20

        shop_x: int = int(shop_rect.x + padding + position * (rect_width + padding))
        shop_y: int = int(shop_rect.y + padding + 10)

        # buy and info button
        button_width = rect_width // 2 - 10
        button_height = 40
        button_y = shop_y + rect_height - button_height - 10

        # probably more efficient than recreating Button every function run
        if not hasattr(self, "buy_button"): 
            self.buy_button = Button(
                win=pg.display.get_surface(),
                x=shop_x + 5,
                y=button_y,
                width=button_width,
                height=button_height,
                text="BUY",
                font=SMALL_BUTTON_FONT,
                fontSize=16,
                radius=5,
                inactiveColour=(80, 180, 80),
                onClick=lambda: self.buy_upgrade(),
            )

            self.info_button = Button(
                win=pg.display.get_surface(),
                x=shop_x + button_width + 15,
                y=button_y,
                width=button_width,
                height=button_height,
                text="INFO",
                font=SMALL_BUTTON_FONT,
                fontSize=16,
                radius=5,
                inactiveColour=(80, 80, 180),
                onClick=lambda: self.item_description(),
            )

        events = pg.event.get()
        pw.update(events)

    def item_description(self) -> None:
        menu = pm.Menu(self.item.name, SCREEN_WIDTH * 2 // 3, SCREEN_HEIGHT * 2 // 3,
                        theme=label_pop_up_theme)
        
        if self.item:
            try:
                menu.add.label(self.item.desc, wordwrap=True)
            except AttributeError:
                menu.add.label("You don't know what you're looking at...", wordwrap=True)
        else:
            menu.add.label("Trying to grasp the item reveals its intangibility...", wordwrap=True)

        menu.add.button('Return', lambda: menu.disable())
        menu.mainloop(self.screen)

class InventoryItem(object):

    _all_wrappers: list['InventoryItem'] = [] # tracks instances

    def __init__(self, screen: pg.Surface, item: object, player_group: PlayerGroup) -> None:
        self.item: object | None = item # should be already initialized
        self.screen = screen
        self.player_group: PlayerGroup = player_group

        if hasattr(self.item, 'slot'):
            self.slot = self.item.slot
        else:
            self.slot = self._find_first_free_slot()
            setattr(self.item, 'slot', self.slot)

        InventoryItem._all_wrappers.append(self)

    def _find_first_free_slot(self) -> int:
        taken = set()
        for inv in self.player_group.upgrades:
            if hasattr(inv, 'slot'):
                taken.add(inv.slot)
        for i in range(0, 4):
            if i not in taken:
                return i
        return 0
    
    def on_slot_change(self, option_value, option_index, **kwargs) -> None:
        if isinstance(option_value, tuple):
            new_slot = int(option_value[1])
        else:
            new_slot = int(option_value)

        old_slot = getattr(self, 'slot', None)

        # find wrapper
        for inv_wrapper in InventoryItem._all_wrappers:
            if inv_wrapper is self:
                continue
            if getattr(inv_wrapper.item, 'slot', None) == new_slot:

                if old_slot is not None:
                    inv_wrapper.slot = old_slot
                    inv_wrapper.item.slot = old_slot
                else:
                    free_slot = self._find_any_free_slot(exclude={new_slot})
                    inv_wrapper.slot = free_slot
                    inv_wrapper.item.slot = free_slot
                break

        self.slot = new_slot
        self.item.slot = new_slot

    def _find_any_free_slot(self, exclude: set[int]) -> int:
        """Look for a free slot between 1-4 not in `exclude` nor currently used by any item."""
        taken = {inv.slot for inv in self.player_group.upgrades if inv.slot not in exclude}
        print(self.player_group.upgrades)
        for i in range(1, 5):
            if i not in taken and i not in exclude:
                return i
        print("here!")
        return next(iter({1, 2, 3, 4} - exclude), 1)

    def render_upgrade(self, surface: pg.Surface, cell_rect: pg.Rect) -> None:
        # Draw cell background
        pg.draw.rect(surface, (100, 100, 180), cell_rect, border_radius=8)

        # Draw upgrade name
        name = getattr(self.item, "name", "???")
        name_text = SMALL_BUTTON_FONT.render(name, True, (255, 255, 255))
        text_x = cell_rect.centerx - name_text.get_width() // 2
        text_y = cell_rect.y + 8
        surface.blit(name_text, (text_x, text_y))

        # Draw item current level at upgrade.level
        level = getattr(self.item, "level", 1)
        level_text = SMALL_BUTTON_FONT.render(f"Lvl.{level}", True, (255, 255, 0))
        level_x = cell_rect.centerx - level_text.get_width() // 2
        level_y = text_y + name_text.get_height() + 4
        surface.blit(level_text, (level_x, level_y))

        # Stats button
        stats_button_width = cell_rect.width - 10
        stats_button_height = 36
        stats_button_x = cell_rect.x + 5
        stats_button_y = cell_rect.y + cell_rect.height - stats_button_height - 8

        if hasattr(self, "stats_button"):
            self.stats_button.disable()  # remove it from screen
            del self.stats_button

        self.stats_button = Button(
            win=surface,
            x=stats_button_x,
            y=stats_button_y,
            width=stats_button_width,
            height=stats_button_height,
            text="STATS",
            font=SMALL_BUTTON_FONT,
            fontSize=16,
            radius=5,
            inactiveColour=(80, 80, 180),
            onClick=lambda: self.stats(),
        )

        events = pg.event.get()
        pw.update(events)
    
    def stats(self) -> None:

        self.stats_menu = pm.Menu(self.item.name, SCREEN_WIDTH * 2 // 3, SCREEN_HEIGHT * 2 // 3,
                        theme=label_pop_up_theme)
        

        if hasattr(self.item, "upgrade_costs"):
            if self.item.level < self.item.max_level:
                    self.stats_menu.add.label(
                        f"Upgrade to level {self.item.level + 1} for ${self.item.upgrade_costs[self.item.level - 1]}?\n",
                        wordwrap=True,
                        font_color=(255, 255, 0)
                        )
            else:
                self.stats_menu.add.label(
                        "Max level!\n",
                        wordwrap=True,
                        font_color=(255, 255, 0)
                        )
        
        if hasattr(self.item, "stats"):
            for k, v in self.item.stats.items():
                if self.item.level < self.item.max_level:
                    self.stats_menu.add.label(f"{k}: {v:.2f} ({self.item.upgrade_amount[k]:+})", 
                                wordwrap=True, 
                                align=pm.locals.ALIGN_LEFT)
                else:
                    self.stats_menu.add.label(f"{k}: {v:.2f}",
                                wordwrap=True, 
                                align=pm.locals.ALIGN_LEFT)
                
        self.recently_upgraded: bool = False

        slot_selector = self.stats_menu.add.dropselect(
            title='Slot:',
            items=[("1", 1), ("2", 2), ("3", 3), ("4", 4)],
            font=PRESS_START_FONT,
            font_size=16,
            selection_option_font_size=20,
            align=pm.locals.ALIGN_CENTER,
            selection_box_bgcolor=DARKER_GREY,
            default=self.slot,
            selection_option_font_color=(160, 160, 160),
            onchange=self.on_slot_change
        )
        self.stats_menu.add.label(" ") # empty space
        self.stats_menu.add.button('Upgrade', lambda: self.are_you_sure_you_want_to_upgrade() if not self.recently_upgraded else self.stats_menu.disable())
        self.stats_menu.add.button('Return', lambda: self.stats_menu.disable())

        print(self.item, self.slot)

        self.stats_menu.mainloop(self.screen)
        
    def are_you_sure_you_want_to_upgrade(self) -> None:
        if self.item.level < self.item.max_level:
            if self.player_group.coins >= self.item.upgrade_costs[self.item.level - 1]:
                menu = pm.Menu(self.item.name, SCREEN_WIDTH * 2 // 3, SCREEN_HEIGHT * 2 // 3,
                                theme=label_pop_up_theme)
                menu.add.label(f"Are you sure?", wordwrap=True)

                def confirm_upgrade():
                    self.upgrade_item()
                    self.stats_menu.disable()
                    menu.disable()

                menu.add.button('Yes', confirm_upgrade)
                menu.add.button('No', lambda: menu.disable())
                menu.mainloop(self.screen)
    
    def upgrade_item(self) -> None:
        if self.item.level < self.item.max_level:
            self.player_group.coins -= self.item.upgrade_costs[self.item.level - 1]
            self.item.level += 1
            self.item.upgrade()
            self.recently_upgraded: bool = True



class _DummyPlayerGroup(PlayerGroup):
    def __init__(self):
        super().__init__()
        self.coins: int = 100

class _DummyGame:
    def __init__(self):
        self.current_wave = 2
        self.humanoids_left = 20
        self.num_of_landers = 15
        self.num_of_mutants = 5

if __name__ == "__main__":
    # test game loop

    screen = pg.display.set_mode(RESOLUTION)
    pg.display.set_caption("The Roguelite Part")
    clock = pg.time.Clock()
    game = _DummyGame()
    player_group = _DummyPlayerGroup()

    running = True
    shop = ShopUI(screen, player_group)
    shop.shop_loop(screen, screen, game)