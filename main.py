"""
Menu script for fortnight 8.

Developed by Flynn Teh.

Last modified: 05/05/2021
"""
import pickle
from tkinter import *
from game import *


class Menu:
    """The main menu / window holder class."""

    _SCORE_FILE = "score.dat"
    _ROOT_GEOMETRY = "500x500"
    _TICK_SPEED = 17
    _INSTRUCTION_TEXT = "INSTRUCTIONS:\nenter your name into the entry box" \
                        "then click start game....\n you will be transported" \
                        "to the fortnight 8 map!!\n" \
                        "drop out of the battle bus with the SPACEBAR\n" \
                        "move around with the W A S D keys\n" \
                        "walk over weapons and consumables to pick them up\n" \
                        "Shoot with the MOUSE 1 key\n" \
                        "drop your weapon with the Q key!!!\n" \
                        "STay inside the zone or you will take damage\n" \
                        "Avoid dying.\n" \
                        "You are awarded score for killing enemies and" \
                        "being the last alive.."
    MAX_NAME_LENGTH = 15
    _GAME_NAME = "fortnight 8"

    @staticmethod
    def _get_top_score():
        """Retrieve the top score holder from the score file.

        Loads the score dictionary using pickle and grabs and displays
        the max score holder and their score.
        :return:
        """
        score_dictionary = pickle.load(open(Menu._SCORE_FILE, "rb"))
        # get the top score holder from the dictionary
        max_score_holder = max(score_dictionary, key=score_dictionary.get)
        max_score = score_dictionary.get(max_score_holder)
        return max_score_holder, max_score

    @staticmethod
    def _hide_frame(frame):
        """Hide given frame.

        Pack forget given frame to hide it from the window.
        :param frame:
        :return:
        """
        frame.pack_forget()

    @staticmethod
    def _show_frame(frame):
        """Show given frame.

        Pack given frame to display it in the menu.
        :param frame:
        :return:
        """
        frame.pack()

    def __init__(self):
        """Initiate instance.

        Initiate self variables and set up the main window.
        """
        self._root = Tk()
        self._root.title(Menu._GAME_NAME)  # title the window
        self._root.geometry(Menu._ROOT_GEOMETRY)  # set window geometry
        self._root.resizable(False, False)  # disable window resizing

        self._menu_frame = Frame(self._root)
        self._menu_frame.pack()
        self._instruction_frame = Frame(self._root)
        self._game_frame = Frame(self._root)
        self._game_summary_frame = Frame(self._root)

        self._player_name = StringVar()
        self._player_score = 0
        # trace editing of the entry widget to the callback function
        self._player_name.trace("w", lambda name, index, mode,
                                : self._callback())

        # MENU WIDGETS
        self._name_entry_label = Label(self._menu_frame,
                                       text="ENTER NAME BELOW")
        self._name_entry_label.pack()
        self._name_entry = Entry(self._menu_frame,
                                 textvariable=self._player_name)
        self._name_entry.pack()
        self._name_error_label = Label(self._menu_frame,
                                       text="name error:\nno special "
                                            "characters, spaces allowed.\n"
                                            "the maximum length for a name is "
                                            f"{Menu.MAX_NAME_LENGTH}.")
        self._start_button = Button(self._menu_frame, text="START GAME",
                                    command=self._initiate_game)
        # disable the start button until name is entered
        self._start_button.config(state="disabled")
        self._start_button.pack()
        self._max_score_string_var = StringVar()
        self._max_score_label = Label(self._menu_frame,
                                      textvariable=self._max_score_string_var)
        self._max_score_label.pack()
        self._show_instructions_button = Button(
            self._menu_frame, text="show instructions",
            command=self._show_instructions)
        self._show_instructions_button.pack()

        # INSTRUCTION WIDGETS
        self._instruction_label = Label(self._instruction_frame,
                                        text=Menu._INSTRUCTION_TEXT)
        self._instruction_label.pack()
        self._exit_instructions_button = Button(
            self._instruction_frame, text="close instructions",
            command=self._close_instructions)
        self._exit_instructions_button.pack()

        # GAME WIDGETS
        self._alive_counter_variable = StringVar()
        self._alive_counter_label = \
            Label(self._game_frame, textvariable=self._alive_counter_variable)
        self._alive_counter_label.pack()
        self._canvas = Canvas(self._game_frame)
        self._canvas.pack()
        self._game = None

        # GAME SUMMARY WIDGETS
        self._end_statement_string = StringVar()
        self._end_statement_label = \
            Label(self._game_summary_frame,
                  textvariable=self._end_statement_string)
        self._end_statement_label.pack()
        self._player_score_string = StringVar()
        self._player_score_label = \
            Label(self._game_summary_frame,
                  textvariable=self._player_score_string)
        self._player_score_label.pack()
        self._close_summary_button = Button(self._game_summary_frame,
                                            text="CLOSE",
                                            command=self._close_game_summary)
        self._close_summary_button.pack()

        self._update_max_score_label()
        self._root.mainloop()

    def _update_max_score_label(self):
        """Update the max score label.

        Updates the max score label by finding the top score holder, then
        setting the string var to this value.
        :return:
        """
        max_score_holder, max_score = self._get_top_score()
        self._max_score_string_var.set(f"TOP SCORE BELONGS TO\n"
                                       f"{max_score_holder}\n"
                                       f"WITH A HIGH SCORE OF \n"
                                       f"{max_score}")

    def _update_player_score_label(self):
        """Update the player score label.

        Updates score string var to previous score by using the set command
        with self._player_score as the score.
        :return:
        """
        self._player_score_string.set(f"You scored {self._player_score}!")

    def _initiate_game(self):
        """Initiate the game.

        Hides menu frame, shows game frame, sets a dynamic root geometry, and
        creates a game instance, then run the game tick function.
        :return:
        """
        self._hide_frame(self._menu_frame)
        self._show_frame(self._game_frame)
        self._game_frame.focus()
        self._root.geometry("")  # set dynamic root geometry
        self._game = GameController(self._root, self._canvas,
                                    self._alive_counter_variable,
                                    self._player_name.get(), Menu._SCORE_FILE)
        self._run_game_tick()  # initiate game tick

    def _run_game_tick(self):
        """Run the game's tick function to progress the game.

        Check whether or not the game should still be running. If so, run
        the game tick handler. If not, end the game by calling the necessary
        functiion.
        :return:
        """
        game_running, player_score, end_statement = \
            (self._game.check_game_condition())
        if game_running:  # if the game is running, continue ticking
            self._game.handle_tick()  # run the game tick handler
            self._root.after(Menu._TICK_SPEED, self._run_game_tick)
        else:
            self._player_score = player_score
            self._end_game(end_statement)

    def _end_game(self, end_statement):
        """End the current game.

        Delete the game instance, then set the game variable back to None.
        Delete all objects from the canvas and hide the game frame, th  en
        display the menu frame again. Finally, update the max score (in case
        the player has achieved a high score) and reset root geometry.
        :return:
        """
        del self._game  # delete game instance
        self._game = None
        self._canvas.delete("all")  # clear the game canvas
        self._hide_frame(self._game_frame)
        self._set_end_statement(end_statement)
        self._update_player_score_label()
        self._show_frame(self._game_summary_frame)
        self._root.geometry(Menu._ROOT_GEOMETRY)  # reset root geometry

    def _close_game_summary(self):
        """Closes the game summary menu.

        Hides the game summary frame, updates the max score , and hides the
        menu frame to transition from the summary to the menu.
        :return:
        """
        self._hide_frame(self._game_summary_frame)
        self._update_max_score_label()  # update high score
        self._show_frame(self._menu_frame)

    def _show_instructions(self):
        """Show instructions.

        Hides the menu frame and then shows the instruction frame using the
        respective functions for hiding and showing.
        :return:
        """
        self._hide_frame(self._menu_frame)
        self._show_frame(self._instruction_frame)

    def _close_instructions(self):
        """Close the instructions.

        Hides the instruction frame and then shows the menu frame to close
        instructions.
        :return:
        """
        self._hide_frame(self._instruction_frame)
        self._show_frame(self._menu_frame)

    def _set_end_statement(self, end_statement):
        """Set end statement to passed in string.

        Sets the end statement string var to the end_statement string passed
        in.
        :param end_statement:
        :return:
        """
        self._end_statement_string.set(end_statement)

    def _callback(self):
        """Update the start button based on callback.

        Enable or disable the start button when the entry field is edited,
        checks for illegal characters and if found, disabled the start button.
        :return:
        """
        entry = self._player_name.get()  # get text from entry box
        # if the entry is not empty and no special characters detected
        # and the length of the entry is less than the maximum
        if entry != "" and not any(not char.isalnum() for char in entry) and \
                len(entry) < Menu.MAX_NAME_LENGTH:
            self._start_button.config(state="normal")  # enable button
            self._name_error_label.pack_forget()  # hide error label
        else:  # else, disable the button from being pressed
            self._start_button.config(state="disabled")  # disable button
            self._name_error_label.pack()  # show error label


if __name__ == '__main__':
    Menu()
