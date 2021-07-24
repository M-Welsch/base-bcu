from abc import ABC
from typing import Callable


class Display:
    def __init__(self) -> None:
        pass

    @staticmethod
    def write(line1: str, line2: str) -> None:
        max_chars = max(len(line1), len(line2))
        line1 = line1.ljust(max_chars, " ")
        line2 = line2.ljust(max_chars, " ")
        line1 = f"| {line1} |   (0)"
        line2 = f"| {line2} |   (1)"

        top_and_bottom_border = "+"
        top_and_bottom_border = top_and_bottom_border.ljust(max_chars + 3, "-")
        top_and_bottom_border += "+"

        print(top_and_bottom_border)
        print(line1)
        print(line2)
        print(top_and_bottom_border)


class Menu(ABC):
    def __init__(self, set_current_menu: Callable) -> None:
        self._set_current_menu: Callable = set_current_menu


class MainMenu(Menu):
    display_line1 = "Display Status >"
    display_line2 = "Actions        >"

    def button0_action(self) -> None:
        print(f"executing button action 0 for {self.__class__.__name__}")
        self._set_current_menu("DisplayStatusMenu")

    def button1_action(self) -> None:
        print(f"executing button action 1 for {self.__class__.__name__}")


class DisplayStatusMenu(Menu):
    display_line1 = "Status: blabla"
    display_line2 = "          back >"

    def button0_action(self) -> None:
        print(f"executing button action 0 for {self.__class__.__name__}")

    def button1_action(self) -> None:
        print(f"executing button action 1 for {self.__class__.__name__}")
        self._set_current_menu("MainMenu")


class HmInterface:
    def __init__(self) -> None:
        self._display: Display = Display()
        self._exitflag: bool = False
        self._current_menu: str = "MainMenu"
        print(f"id von self._current_menu in Hauptklasse: {id(self._current_menu)}")
        self._mm: MainMenu = MainMenu(self.set_current_menu)
        self._dsm: DisplayStatusMenu = DisplayStatusMenu(self.set_current_menu)

    def set_current_menu(self, menu: str) -> None:
        self._current_menu = menu

    def mainloop(self) -> None:
        while not self._exitflag:
            print(f"current menu: {self._current_menu}. ID: {id(self._current_menu)}")
            if self._current_menu == "MainMenu":
                self._display.write(self._mm.display_line1, self._mm.display_line2)
            elif self._current_menu == "DisplayStatusMenu":
                self._display.write(self._dsm.display_line1, self._dsm.display_line2)
            user_input = input("Taste [0,1,q]: ")
            self._handle_user_input(user_input)

    def _handle_user_input(self, user_input: str) -> None:
        if user_input == "q":
            self._exitflag = True
        elif user_input == "0":
            if self._current_menu == "MainMenu":
                self._mm.button0_action()
            elif self._current_menu == "DisplayStatusMenu":
                self._dsm.button0_action()
                print("SUBMENU")

        elif user_input == "1":
            if self._current_menu == "MainMenu":
                self._mm.button1_action()
            elif self._current_menu == "DisplayStatusMenu":
                self._dsm.button1_action()


if __name__ == "__main__":
    HMI = HmInterface()
    HMI.mainloop()
