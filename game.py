"""
Title: fortnight 8 - a 2d battle royale

This is a fortnight 7 remaster, in 2d. a player will play solo in an attempt
to survive the fortnight 8 experience and gain a high score.

Created by: flynn teh

Last modified: 05/05/2021
"""

from tkinter import *
import random
import math
import time
import pickle
from PIL import Image, ImageTk


class GameController:
    """Main class that initialises and handles the game."""

    # canvas dimensions
    CAMERA_WIDTH = 800
    CAMERA_HEIGHT = 800
    CANVAS_WIDTH = 5000
    CANVAS_HEIGHT = 5000
    FEATHERING = 30
    # image directories
    PLAYER_DIRECTORY = "sprite_images/player/"
    ENEMY_DIRECTORY = "sprite_images/enemies/"
    MAP_OBJECT_DIRECTORY = "sprite_images/map_objects/"
    GUN_DIRECTORY = "sprite_images/guns/"
    BULLET_DIRECTORY = "sprite_images/bullets/"
    VEHICLE_DIRECTORY = "sprite_images/vehicles/"
    CONSUMABLE_DIRECTORY = "sprite_images/consumables/"
    # guns
    GUNS = {
        "assault_rifle":
            {
                'image_path': 'assault_rifle.png',
                'width': 50,
                'height': 50,
                'damage': 7,
                'fire_rate': 10,
                'spray': [-10, 10]
            },
        "pistol":
            {
                'image_path': 'pistol.png',
                'width': 50,
                'height': 50,
                'damage': 10,
                'fire_rate': 3,
                'spray': [-1, 1]
            },
        "mini_gun":
            {
                'image_path': 'mini_gun.png',
                'width': 50,
                'height': 50,
                'damage': 3,
                'fire_rate': 30,
                'spray': [-20, 20]
            },
        "sniper_rifle":
            {'image_path': 'sniper_rifle.png',
             'width': 50,
             'height': 50,
             'damage': 50,
             'fire_rate': 0.5,
             'spray': [0, 0]
             }
    }

    RARITIES = {
        "common": {
            "file_prefix": "common_",
            "damage_multiplier": 1
        },
        "rare": {
            "file_prefix": "rare_",
            "damage_multiplier": 1.25
        },
        "epic": {
            "file_prefix": "epic_",
            "damage_multiplier": 1.5
        },
        "legendary": {
            "file_prefix": "legendary_",
            "damage_multiplier": 2
        }
                }

    # heal consumables
    HEAL_CONSUMABLES = {
        "chug_jug": {
            "image_path": CONSUMABLE_DIRECTORY+"chug_jug.png",
            "heal_value": 100
                    },
        "slurp_juice": {
            "image_path": CONSUMABLE_DIRECTORY + "slurp_juice.png",
            "heal_value": 50
                    }
    }

    # key binds
    _JUMP_BIND = '<space>'
    _UP_BIND = "w"
    _DOWN_BIND = "s"
    _LEFT_BIND = "a"
    _RIGHT_BIND = "d"
    _DROP_GUN_BIND = "<q>"
    # error margins
    _NUMBER_ENEMIES = 100
    _NUMBER_GUNS = 100
    _NUMBER_HEAL_CONSUMABLES = 30
    # id format, what ids start with
    ID_START = "id"
    # zone radius
    _ZONE_RADIUS = 3000
    # win statements
    _VICTORY_STATEMENT = "victory royale!\nyou won!"
    _DEATH_STATEMENT = "RIP! you died!"

    def __init__(self, root, canvas, alive_counter_variable,
                 player_name, score_file):
        """Initialise self variables and set up game scene.

        Set up binds, create the canvas, and initialise variables for enemy's,
        bullets, etc, then spawn a set number of entities.
        """
        self._player_name = player_name
        self._score_file = score_file

        self._root = root
        # create canvas with scroll region of the entire canvas width/height
        self._canvas = canvas
        self._canvas.config(width=GameController.CAMERA_WIDTH,
                            height=GameController.CAMERA_HEIGHT,
                            scrollregion=(0, 0, GameController.CANVAS_WIDTH,
                                          GameController.CANVAS_HEIGHT))

        # set up all four side boundaries - they can all adapt to changes in
        # canvas dimension

        # set up binds
        self._root.bind('<KeyPress>', self._key_pressed)
        self._root.bind('<KeyRelease>', self._key_released)
        self._root.bind('<Motion>', self._mouse_moved)
        self._root.bind('<ButtonPress-1>', self._mouse_down)
        self._root.bind('<ButtonRelease-1>', self._mouse_up)
        self._root.bind(GameController._JUMP_BIND, self._release_player)
        self._root.bind(GameController._DROP_GUN_BIND,
                        self._drop_player_weapon)

        # create zone instance
        self._zone = Zone(self._canvas, [GameController.CANVAS_WIDTH/2,
                                         GameController.CANVAS_HEIGHT/2],
                          GameController._ZONE_RADIUS)
        # create player instance
        self._player = Player(self._canvas, 0, 0)
        self._player_score = Score(self._canvas, self._player,
                                   self._player_name, self._score_file)
        # create battle bus instance
        self._battle_bus = BattleBus(self._canvas, 0, 0,
                                     GameController.CANVAS_WIDTH,
                                     GameController.CANVAS_HEIGHT,
                                     self._player)
        self._battle_bus_alive = True
        # create dicts for other instances
        self._enemies = {}
        self._guns = {}
        self._bullets = {}
        self._heal_consumables = {}

        self._player_shoot = False
        self._mouse_target = []

        for i in range(GameController._NUMBER_ENEMIES):
            self._spawn_enemy()

        for i in range(GameController._NUMBER_GUNS):
            self._spawn_gun()

        for i in range(GameController._NUMBER_HEAL_CONSUMABLES):
            self._spawn_heal_consumable()

        # alive counter instance, no. alive is no. enemies + 1 (player)
        self._alive_counter = AliveCounter(alive_counter_variable,
                                           (GameController._NUMBER_ENEMIES
                                            + 1))

    def _centre_camera(self):
        """Centre the canvas scrollable view on the player object.

        Centre the scrollable canvas view on the player canvas object to give
        the effect of a camera following around the player object.
        :return:
        """
        player_coords = self._player.coordinates()
        player_x = player_coords[0]
        player_y = player_coords[1]
        # calculate centre coordinates, as we know the canvas should always
        # be in the centre of the canvas
        centre_x = player_x - (GameController.CAMERA_WIDTH / 2)
        centre_y = player_y - (GameController.CAMERA_HEIGHT / 2)
        # moves the x and y view of the canvas to caluclated coords.
        self._canvas.xview_moveto(centre_x / GameController.CANVAS_WIDTH)
        self._canvas.yview_moveto(centre_y / GameController.CANVAS_HEIGHT)

    def _spawn_heal_consumable(self):
        """Spawn a heal consumable instance on the canvas.

        Grabs a random key from heal consumables dict then creates a heal
        consumable instance and adds to the heal consumable dict.
        :return:
        """
        # get random key from the heal consumables dictionary
        random_consumable = random.choice(list(
            GameController.HEAL_CONSUMABLES.keys()))
        # create the consumable instance
        consumable = HealConsumable(
            self._canvas, random.randint(0, GameController.CANVAS_WIDTH),
            random.randint(0, GameController.CANVAS_HEIGHT), random_consumable)
        # get the id of the consumable instance
        consumable_id = consumable.get_id()
        # add consumable to dictionary
        self._heal_consumables[consumable_id] = consumable

    def _spawn_gun(self):
        """Spawn a random gun at a random location on the canvas.

        Spawns a random gun at a random location on the canvas by appending
        a new gun object to the guns dictionary. The gun will have a random
        rarity and gun type that is passed to the gun instance.
        :return:
        """
        # choose random gun from a list of the gun dictionary
        random_gun = random.choice(list(GameController.GUNS.keys()))
        # get the gun properties from the gun dictionary
        gun_properties = GameController.GUNS.get(random_gun)
        # choose random rarity from list of rarity dictionary
        random_rarity = random.choice(list(GameController.RARITIES.keys()))
        gun = Gun(self._canvas,
                  random.randint(0, GameController. CANVAS_WIDTH),
                  random.randint(0, GameController.CANVAS_HEIGHT),
                  gun_properties, random_rarity)
        gun_id = gun.get_id()
        self._guns[gun_id] = gun

    def _spawn_enemy(self):
        """Spawn an enemy.

        Creates an enemy object and adds it to the enemy dictionary with the
        key being its id.
        :return:
        """
        enemy = Enemy(self._canvas,
                      random.randint(0, GameController.CANVAS_WIDTH),
                      random.randint(0, GameController.CANVAS_HEIGHT))
        enemy_id = enemy.get_id()
        self._enemies[enemy_id] = enemy

    def _kill_enemy(self, enemy):
        """Kill passed in enemy.

        Deletes passed in enemy object and removes from enemy dictionary,
        checking if the last attacker was the player and if so, adding a
        kill score the player score.
        :param enemy:
        :return:
        """
        # get the last attacker, and if it was player, add a kill score to
        # the player score
        last_attacker = enemy.get_last_attacker()
        if last_attacker == self._player:
            self._player_score.add_kill_score()
        enemy.delete_canvas_object()
        self._enemies.pop(enemy.get_id())  # remove enemy from dict
        self._alive_counter.enemy_killed()  # update alive counter

    def _add_bullet(self, bullet):
        """Add a bullet to the bullet dictionary.

        Takes a bullet object, gets its id, then adds to the bullet dictionary
        using its id as the key.
        :param bullet:
        :return:
        """
        bullet_id = bullet.get_id()
        self._bullets[bullet_id] = bullet

    def _delete_bullet(self, bullet_id):
        """Delete a passed in bullet object.

        Gets the passed in bullet object, calls the delete canvas object
        function on said bullet, then pop the bullet from the bullets dict.
        :param bullet_id:
        :return:
        """
        bullet = self._bullets.get(bullet_id)
        bullet.delete_canvas_object()
        self._bullets.pop(bullet_id)

    def _delete_heal_consumable(self, heal_consumable):
        """Delete passed in heal consumable.

        Gets the heal consumable instance, delete its canvas object, then
        remove it from the dictionary.
        :param heal_consumable:
        :return:
        """
        heal_instance = self._heal_consumables.get(heal_consumable)
        heal_instance.delete_canvas_object()
        self._heal_consumables.pop(heal_consumable)

    def _key_pressed(self, event):
        """Check passed in key press event against binds.

        Called when a key is pressed, checks which key has been pressed then
        alters the player speed, based on the key pressed.
        :param event:
        :return:
        """
        # event.keysym refers to key pressed
        if event.keysym == GameController._UP_BIND:
            self._player.set_y_speed(-Player.DEFAULT_SPEED)
        if event.keysym == GameController._DOWN_BIND:
            self._player.set_y_speed(Player.DEFAULT_SPEED)
        if event.keysym == GameController._LEFT_BIND:
            self._player.set_x_speed(-Player.DEFAULT_SPEED)
        if event.keysym == GameController._RIGHT_BIND:
            self._player.set_x_speed(Player.DEFAULT_SPEED)

    def _key_released(self, event):
        """Check passed in key release event against binds.

        Called when a key is released, checks which key is released then sets
        the speed for speed corresponding that key to 0.
        :param event:
        :return:
        """
        # event.keysym refers to key released
        if event.keysym == GameController._UP_BIND:
            self._player.set_y_speed(0)
        if event.keysym == GameController._DOWN_BIND:
            self._player.set_y_speed(0)
        if event.keysym == GameController._LEFT_BIND:
            self._player.set_x_speed(0)
        if event.keysym == GameController._RIGHT_BIND:
            self._player.set_x_speed(0)

    def _mouse_moved(self, event):
        """Set mouse coordinates to the event location passed in.

        Xalled whenever the mouse is moved, sets the mouse target (coordinates)
        to the event x and y passed in by the movement.
        :param event:
        :return:
        """
        # since we know that the coordinates of the player relative to the
        # canvas view is always half, we can calculate the real x and y coords
        # if the mouse (as it is based off the view and not real coords). we
        # calculate the difference between the mouse coordinates and half the
        # canvas view width/height, then add the player coordinates
        real_mouse_x = event.x - GameController.CAMERA_WIDTH/2
        real_mouse_y = event.y - GameController.CAMERA_HEIGHT/2
        real_mouse_x += self._player.coordinates()[0]
        real_mouse_y += self._player.coordinates()[1]

        self._mouse_target = [real_mouse_x, real_mouse_y]

    def _mouse_down(self, event):
        """Set the player_shoot variable to true when the mouse is pressed.

        called when the mouse button 1 is pressed, sets the player_shoot
        variable to True in order to signal to shoot gun
        :param event:
        :return:
        """
        self._player_shoot = True

    def _mouse_up(self, event):
        """Set the player_shoot variable to false when the mouse is released.

        called when the mouse button 1 is released, sets the player_shoot var
        to False to stop shooting
        :param event:
        :return:
        """
        self._player_shoot = False

    def _release_player(self, event):
        """Release player from battle bus.

        Removes the passenger (player) from the battle bus, if the battle bus
        passes the alive check.
        :param event:
        :return:
        """
        if self._battle_bus_alive:
            self._battle_bus.remove_passenger()
            self._delete_battle_bus()

    def _drop_player_weapon(self, event):
        """Attempt to release a player weapon.

        If the player has a weapon and this func is called, remove from player.
        :param event:
        :return:
        """
        if self._player.get_has_gun():  # if the player has the gun
            player_gun = self._player.get_gun()
            self._player.remove_gun()  # remove the gun
            player_gun.delete_canvas_object()  # delete the gun

    def _find_player_gun(self, overlapping_guns):
        """Attempt to add a gun to the player instance.

        Gets the object overlapping with the player, and if it is not None,
        add the gun to the player.
        :return:
        """
        # if the list of guns is not empty, add the first gun in the list
        if bool(overlapping_guns):
            self._player.add_gun(self._guns[overlapping_guns[0]])

    def _shoot_player_gun(self):
        """Attempt to create a bullet from the player gun.

        Attempts to create a bullet, and if None is not returned, append
        bullet object to own bullets list.
        :return:
        """
        bullet = self._player.shoot_gun(self._mouse_target)
        # if the returned object is not None (bullet has been created)
        if bullet is not None:
            self._add_bullet(bullet)

    def _handle_bullets(self):
        """Handle bullet functions.

        For each bullet in bullets dictionary, check whether inside boundaries.
        If it is, then move it. Else, delete the bullet.
        :return:
        """
        # must loop through a list, else error for changing dict size
        for bullet in list(self._bullets.keys()):
            bullet_instance = self._bullets.get(bullet)  # get bullet instance
            # check if the bullet is inside the boundaries
            if bullet_instance.check_inside_boundaries(0,
               GameController.CANVAS_WIDTH, 0, GameController.CANVAS_HEIGHT):
                bullet_instance.move()
            else:  # if not inside boundaries, delete
                self._delete_bullet(bullet)

    def _handle_enemies(self):
        """Handle all enemies in enemies dict.

        Loop through all enemies in the enemy dictionary. Check they are alive,
        if they are, find overlapping items of interest. Move the enemy
        if it has a destination, and if not, find a new one. Handle the enemy
        health bar and gun (if one is owned). Perform actions on overlapping
        items of interest if they exist, and attack target if one is had. Kill
        the enemy if it is not alive.
        :return:
        """
        for enemy in list(self._enemies.values()):
            if enemy.get_health() > 0:  # if enemy is alive
                # get the overlapping dictionary of lists of object
                overlapping_dict = \
                    enemy.check_overlapping([Gun.GUN_TAG,  Bullet.BULLET_TAG,
                                             HealConsumable.TAG],
                                            Gun.OWNED_TAG)
                # extract the lists from the dictionary
                overlapping_guns = overlapping_dict[Gun.GUN_TAG]
                overlapping_bullets = overlapping_dict[Bullet.BULLET_TAG]
                overlapping_heals = overlapping_dict[HealConsumable.TAG]

                has_destination = enemy.check_destination()

                if has_destination:  # if the enemy has a destination, move
                    enemy.move()
                else:  # if enemy does not have destination, find new one
                    self._get_enemy_destination(enemy, overlapping_guns)

                enemy.handle_health_bar()  # handle enemy health bar instance

                if enemy.get_has_gun():
                    enemy.handle_gun()  # handle enemy gun

                if bool(overlapping_bullets):  # if enemy is collided with
                    # bullets, handle those collided bullets
                    self._handle_attacker_collided_bullets(enemy,
                                                           overlapping_bullets)
                if bool(overlapping_heals):
                    self._handle_collided_heals(enemy, overlapping_heals)

                if enemy.get_has_target():  # if enemy has a target, attack it
                    self._enemy_attack(enemy)

            else:  # kill enemy if it is dead
                self._kill_enemy(enemy)

    def _get_enemy_destination(self, enemy, overlapping_guns):
        """Generate a new destination for a passed in enemy object.

        scan for guns/attackers based on logic, then move towards found
        canvas objects
        :param enemy:
        :param overlapping_guns:
        :return:
        """
        if not enemy.get_has_gun():  # if enemy has no gun
            self._find_enemy_gun(enemy, overlapping_guns)
        else:  # if enemy has a gun
            self._find_enemy_attacker(enemy)

        if not enemy.check_destination():  # if no destination was found
            enemy.generate_destination()  # gen random destination

    def _find_enemy_gun(self, enemy, guns):
        """Locate a gun for enemy and checks if enemy is colliding with gun.

        locates a gun nearby the enemy then sets the enemy destination
        to that gun. also checks whether or not the enemy is colliding with
        a gun - if so, make enemy pick up the gun
        :param enemy:
        :param guns:
        :return:
        """
        nearby_items = enemy.scan_vision(Gun.GUN_TAG)
        if bool(guns):  # if overlapping with a gun
            enemy.add_gun(self._guns.get(guns[0]))
        elif bool(nearby_items):  # if nearby items is not empty
            enemy.set_destination(self._guns.get(random.choice(
                nearby_items)))

    def _find_enemy_attacker(self, enemy):
        """Find an attacker for an enemy to target.

        Scans enemy vision and locates a random nearby target.
        :param enemy:
        :return:
        """
        nearby_items = enemy.scan_vision(Attacker.ATTACKER_TAG)
        if bool(nearby_items):  # if nearby items not empty
            try:  # Try to search enemies dict
                # pick a random target from the list
                target = self._enemies.get(random.choice(nearby_items))
                enemy.set_destination(self._enemies.get(
                    random.choice(nearby_items)))  # set target destination
                enemy.add_target(target)
            except AttributeError:  # must be player
                target = self._player
                enemy.set_destination(self._player)
                enemy.add_target(target)
        else:  # if nothing is found in scans, move to random location
            enemy.remove_target()
            enemy.generate_destination()

    def _enemy_attack(self, enemy):
        """Ges enemy target, checks if it exists, attacks it.

        Must first check whether or not the enemy target still exists, as
        target can die before a new scan is done. attacks the target
        and adds returned bullet to bullets list.
        :param enemy:
        :return:
        """
        enemy_target = enemy.get_target()
        # must check if target still exists
        if enemy_target in self._enemies.values() or enemy_target is\
                self._player:
            bullet = enemy.attack_target()
            if bullet is not None:
                self._add_bullet(bullet)
        else:  # if target not exist, remove enemy target
            enemy.remove_target()

    def _handle_attacker_collided_bullets(self, attacker, bullets):
        """Handle bullets collided with an attacker.

        Loop through bullets and damages attacker based on bullet damage,
        if the bullet does not belonh to the attacker.
        :param attacker:
        :param bullets:
        :return:
        """
        for bullet in bullets:
            bullet_instance = self._bullets.get(bullet)  # get instance name
            bullet_owner = bullet_instance.get_owner()
            if bullet_owner == attacker:  # if shooter of bullet is self
                continue
            # set last attacker to the collided bullet's owner
            attacker.set_last_attacker(bullet_owner)
            attacker.damage(bullet_instance.get_damage())  # damage enemy
            self._delete_bullet(bullet)  # delete bullet

    def _handle_collided_heals(self, attacker, heals):
        """Handle the collided heals for an attacker.

        Loops through given heals and applies the heal value from the
        consumable to the attacker.
        :param attacker:
        :param heals:
        :return:
        """
        for heal in heals:
            heal_instance = self._heal_consumables.get(heal)
            # heal attacker by the heal consumable amount
            attacker.heal(heal_instance.get_heal_value())
            self._delete_heal_consumable(heal)  # delete the consumable

    def _handle_battle_bus(self):
        """Handles battle bus functions.

        Checks whether the battle bus is inside given boundaries. If so,
        move the battle bus, else, delete the battle bus.
        :return:
        """
        # if the battle bus is inside the boundaries
        if self._battle_bus.check_inside_boundaries(0,
           GameController.CANVAS_WIDTH, 0, GameController.CANVAS_HEIGHT):
            self._battle_bus.move()
        else:
            self._delete_battle_bus()

    def _delete_battle_bus(self):
        """Delete the battle bus.

        Deletes battle bus canvas object, set the battle bus variable to none,
        then set the boolean to False.
        :return:
        """
        self._battle_bus.delete_canvas_object()
        self._battle_bus = None
        self._battle_bus_alive = False

    def _handle_player(self):
        """Handle the player instance.

        Handle all player functionality, including collisions, pick ups, gun,
        and shooting.
        :return:
        """
        # get the dictionary of overlapping items
        overlapping_dict = \
            self._player.check_overlapping([Gun.GUN_TAG, Bullet.BULLET_TAG,
                                            HealConsumable.TAG], Gun.OWNED_TAG)
        # create lists of overlapping items
        overlapping_guns = overlapping_dict[Gun.GUN_TAG]
        overlapping_bullets = overlapping_dict[Bullet.BULLET_TAG]
        overlapping_heals = overlapping_dict[HealConsumable.TAG]

        # check the boundaries
        self._player.check_boundaries(0, GameController.CANVAS_WIDTH, 0,
                                      GameController.CANVAS_HEIGHT)
        self._player.move()
        self._player.handle_health_bar()

        if bool(overlapping_bullets):  # if bullets list is not empty
            self._handle_attacker_collided_bullets(self._player,
                                                   overlapping_bullets)
        if bool(overlapping_heals):  # if heals list not empty
            self._handle_collided_heals(self._player, overlapping_heals)

        # if the player does not have a gun, run the find gun function
        if not self._player.get_has_gun():
            self._find_player_gun(overlapping_guns)
        # if the player does have a gun, run the handle gun function
        else:
            self._player.handle_gun()
            if self._player_shoot:  # if the mouse is pressed down, shoot gun
                self._shoot_player_gun()

    def _handle_zone(self):
        """Handle the zone.

        Handler function for the zone instance, check if all attackers are
        in the zone.
        :return:
        """
        attackers = [value for value in self._enemies.values()]
        attackers.append(self._player)
        self._zone.check_attackers_inside(attackers)
        self._zone.shrink_zone()

    def _remove_binds(self):
        """Remove all binds.

        Unbinds all previous bound events, thus preventing errors when the
        game is ended and a player presses a bind.
        :return:
        """
        self._root.unbind('<KeyPress>')
        self._root.unbind('<KeyRelease>')
        self._root.unbind('<Motion>')
        self._root.unbind('<ButtonPress-1>')
        self._root.unbind('<ButtonRelease-1>')
        self._root.unbind(GameController._JUMP_BIND)
        self._root.unbind(GameController._DROP_GUN_BIND)

    def _cleanup(self):
        """Clear instance dictionaries and player/zone instances.

        Cleans up all instances created during the game to free memory, thus
        reducing the risk of a memory leak.
        :return:
        """
        for enemy in self._enemies.values():  # clean up enemies
            enemy.delete_canvas_object()
            enemy.cleanup()
        for gun in self._guns.values():  # clean up guns
            gun.delete_canvas_object()
            gun.cleanup()
        for heal_consumable in self._heal_consumables.values():  # clean heals
            heal_consumable.delete_canvas_object()
        for bullet in self._bullets.values():  # clean up bullets
            bullet.delete_canvas_object()
            bullet.cleanup()
        self._player.delete_canvas_object()  # clean up player
        self._player.cleanup()
        self._enemies.clear()  # clear enemy references
        self._guns.clear()  # clear gun references
        self._bullets.clear()  # clear bullet references
        self._heal_consumables.clear()  # clean heal references
        self._player_score.cleanup()  # clean up the score instance
        # delete remaining references
        del self._player
        del self._zone
        del self._player_score

    def _check_end_type(self):
        """Check whether or not the player has won the game.

        If the player health is greater than 0, the player must be the last
        one alive and therefore will have won. Thus, the win score is added
        to the player score and the victory statement is return. Else, the
        player has died and the death statement is returned
        :return:
        """
        if self._player.get_health() > 0:
            self._player_score.add_win_score()
            return GameController._VICTORY_STATEMENT
        else:
            return GameController._DEATH_STATEMENT

    def check_game_condition(self):
        """Check the game condition.

        Check whether game end conditions have been met and return info about
        the current condition of the game.
        :return:
        """
        # if the game not still running
        if self._player.get_health() <= 0 or\
                self._alive_counter.get_alive_count() <= 1:
            self._player_score.write_score()
            player_score = self._player_score.get_score()
            end_statement = self._check_end_type()
            self._remove_binds()  # remove root binds
            self._cleanup()  # cleanup instances
            return False, player_score, end_statement
        else:  # if game is still running
            return True, None, None

    def handle_tick(self):
        """Handle tick functions.

        Called every tick, handles all things that need to be run every tick,
        including the camera, zone, and all other instances.
        :return:
        """
        self._centre_camera()
        self._handle_zone()

        if self._battle_bus_alive:  # move battle bus if it is still alive
            self._handle_battle_bus()

        self._handle_player()

        self._handle_bullets()

        self._handle_enemies()


class CanvasSprite:
    """A canvas image with extended functionality."""

    @staticmethod
    def calculate_distance_difference(position_1, position_2):
        """Calculate the distance difference between two points.

        Takes 2 lists of 2 components, x component and y component,
        then returns difference.
        :param position_1:
        :param position_2:
        :return:
        """
        x_difference = position_2[0] - position_1[0]
        y_difference = position_2[1] - position_1[1]
        return x_difference, y_difference

    def __init__(self, canvas, x_position, y_position, width, height,
                 image_path):
        """Initiate self variables.

        Sets self variables and creates the canvas sprite image using a
        ImageTk photo image.
        :param canvas:
        :param x_position:
        :param y_position:
        :param width:
        :param height:
        :param image_path:
        """
        self._id = GameController.ID_START+str(id(self))
        self._canvas = canvas
        self._width = width
        self._height = height
        image = Image.open(image_path).resize((self._width, self._height),
                                              Image.ANTIALIAS)
        # convert to photo image so canvas can read
        self._photo_image = ImageTk.PhotoImage(image)
        # create a canvas rectangle object with passed in variables
        self._canvas_object = \
            self._canvas.create_image(x_position, y_position,
                                      image=self._photo_image, anchor="nw")
        self._add_tag(self._id)

    def get_id(self):
        """Get id.

        Returns the id of self.
        :return:
        """
        return self._id

    def _get_ids_from_canvas_objects(self, objects_list):
        """Create a list of ids of passed in objects.

        Takes a list of canvas object and gets their object ids from their
        canvas tags, then returns said list.
        :param objects_list:
        :return:
        """
        id_list = []
        for canvas_object in objects_list:
            # get the first tag that starts with the ID_START string
            id_tag = next(tag for tag in self._canvas.gettags(canvas_object)
                          if tag.startswith(GameController.ID_START))
            id_list.append(id_tag)
        return id_list

    def get_width(self):
        """Get width.

        Returns own width.
        :return:
        """
        return self._width

    def get_height(self):
        """Get height.

        Returns own height.
        :return:
        """
        return self._height

    def _add_tag(self, tag):
        """Add a tag to the canvas object.

        Adds passed in tag to canvas object.
        :param tag:
        :return:
        """
        self._canvas.addtag(tag, 'withtag', self.get_canvas_object())

    def get_canvas_object(self):
        """Return the canvas object.

        Returns the canvas object.
        :return:
        """
        return self._canvas_object

    def coordinates(self):
        """Get and return the canvas object coordinates.

        Returns the centre coordinates of the canvas object.
        :return:
        """
        coordinates = self._canvas.coords(self._canvas_object)
        # add width and height to x and y coords to get centre coords
        coordinates[0] += self._width/2
        coordinates[1] += self._height/2
        return coordinates

    def get_overlapping(self):
        """Get overlapping canvas objects.

        Returns a list of canvas objects overlapping with own canvas object.
        :return:
        """
        overlapping_tuple = self._canvas.find_overlapping(
            *self.coordinates(), self.coordinates()[0]+self._width,
            self.coordinates()[1]+self._height)
        # create a new list that contains all items in the tuple except for
        # own canvas object
        overlapping_list = [item for item in overlapping_tuple if item
                            is not self.get_canvas_object()]
        return overlapping_list

    def delete_canvas_object(self):
        """Delete the canvas object.

        Deletes own canvas object.
        :return:
        """
        self._canvas.delete(self.get_canvas_object())


class MovingObject(CanvasSprite):
    """A moving canvas sprite."""

    def __init__(self, canvas, x_position, y_position, width, height,
                 image_path):
        """Initiate self variables.

        Super's init function then declares new self variables.
        :param canvas:
        :param x_position:
        :param y_position:
        :param width:
        :param height:
        :param image_path:
        """
        super().__init__(canvas, x_position, y_position, width, height,
                         image_path)

        self._x_speed = 0
        self._y_speed = 0

    def move(self):
        """Move the canvas object.

        Moves the canvas object by the x and y speed of self.
        :return:
        """
        self._canvas.move(self.get_canvas_object(), self._x_speed,
                          self._y_speed)

    def set_x_speed(self, new_x_speed):
        """Set own x speed.

        Sets the x speed to a passed in value.
        :param new_x_speed:
        :return:
        """
        self._x_speed = new_x_speed

    def set_y_speed(self, new_y_speed):
        """Set own y speed.

        Sets the y speed to a passed in value.
        :param new_y_speed:
        :return:
        """
        self._y_speed = new_y_speed

    def _set_speed_to_point(self, destination_x, destination_y, x_speed,
                            y_speed):
        """Calculate and sets speed to reach a point.

        Calculate the distance and angle to a point, then calculate the new
        x and y speeds required to reach the point, and set these respectively.
        :param destination_x:
        :param destination_y:
        :param x_speed:
        :param y_speed:
        :return:
        """
        # gets distance from self to point
        x_dist, y_dist = self.calculate_distance_difference(
            self.coordinates(), [destination_x, destination_y])

        # calculate angle to point using arc tan of y dist over x dist
        angle_to_point = math.atan2(y_dist, x_dist)

        # calculate new speeds using passed in default speeds as hypotenuse
        # and the previously calculated angle as theta
        new_x_speed = x_speed * math.cos(angle_to_point)
        new_y_speed = y_speed * math.sin(angle_to_point)

        # set the speeds
        self.set_x_speed(new_x_speed)
        self.set_y_speed(new_y_speed)

    def check_inside_boundaries(self, left_boundary, right_boundary,
                                top_boundary, bottom_boundary):
        """Check if the canvas object is inside passed in boundaries.

        Checks whether or not canvas object is inside boundaries using
        if statements, returning True if inside or False if not.
        :param left_boundary:
        :param right_boundary:
        :param top_boundary:
        :param bottom_boundary:
        :return:
        """
        # if inside passed in boundaries, return true
        if left_boundary < self.coordinates()[0] < right_boundary and\
           top_boundary < self.coordinates()[1] < bottom_boundary:
            return True
        else:
            return False


class Attacker(MovingObject):
    """An "alive" moving object - can have a gun and attack functionality."""

    ATTACKER_TAG = "attacker"
    _DEFAULT_MAX_HEALTH = 100

    def __init__(self, canvas, x_position, y_position, width, height,
                 image_path, health):
        """Initiate self variables.

        Runs the init function of a moving object and sets new self variables.
        :param canvas:
        :param x_position:
        :param y_position:
        :param width:
        :param height:
        :param image_path:
        """
        super().__init__(canvas, x_position, y_position, width, height,
                         image_path)

        self._health = health
        self._max_health = Attacker._DEFAULT_MAX_HEALTH
        self._gun = None
        self._has_gun = False
        self._bullets = []
        self._health_bar = HealthBar(self, self._canvas)
        self._last_attacker = None
        self._add_tag(Attacker.ATTACKER_TAG)

    def set_last_attacker(self, last_attacker):
        """Set last attacker.

        Sets own last attacker to a passed in instance of an attacker.
        :param last_attacker:
        :return:
        """
        self._last_attacker = last_attacker

    def get_last_attacker(self):
        """Return last attacker.

        Returns the last attacker instance.
        :return:
        """
        return self._last_attacker

    def handle_health_bar(self):
        """Handle the health bar.

        Sets the coordinates of the health bar to own coordinates.
        :return:
        """
        self._canvas.coords(self._health_bar.get_text_object(),
                            *self._health_bar.calculate_owner_coordinates())

    def add_gun(self, gun):
        """Add a gun.

        Set own gun to a passed in gun (object) then changes has gun to True.
        :param gun:
        :return:
        """
        self._gun = gun
        self._has_gun = True
        self._gun.add_owner(self)

    def remove_gun(self):
        """Remove own gun.

        Removes own gun object (sets to None) and sets has gun to False.
        :return:
        """
        self._gun.remove_owner()
        self._gun = None
        self._has_gun = False

    def get_has_gun(self):
        """Return has_gun.

        Returns the has_gun variable, a boolean.
        :return:
        """
        return self._has_gun

    def get_gun(self):
        """Get gun.

        Returns own gun object, which is an instance of the Gun class.
        :return:
        """
        return self._gun

    def check_overlapping(self, tags, exclusion_tag):
        """Check overlapping objects, and return a list of their id's.

        Get a list of all overlapping objects. Loop through all given tags.
        For each tag, create a list of overlapping objects that satisfy that
        tag, and do not include the exclusion tag. Then, convert to a list
        of ids and append to returned dictionary.
        :return:
        """
        # get ALL overlapping objects
        overlapping_objects = self.get_overlapping()
        overlapping_dictionary = {}
        for tag in tags:  # loop through tags
            # list comprehension only includes instances with the current tag
            # and excluding the exclusion tag.
            overlapping_list = [instance for instance in overlapping_objects
                                if tag in self._canvas.gettags(instance)
                                and exclusion_tag not in
                                self._canvas.gettags(instance)]
            # convert the list to ids
            id_list = self._get_ids_from_canvas_objects(overlapping_list)
            # add the list to the dictionary
            overlapping_dictionary[tag] = id_list

        # returns dictionary containing lists of overlapping items
        return overlapping_dictionary

    def shoot_gun(self, destination_coordinates):
        """Shoot own gun.

        Returns a bullet object from shooting gun.
        :param destination_coordinates:
        :return:
        """
        return self._gun.shoot(destination_coordinates)

    def handle_gun(self):
        """Handle own gun.

        Moves the gun to own coordinates.
        :return:
        """
        self._canvas.coords(self.get_gun().get_canvas_object(),
                            *self.coordinates())

    def damage(self, damage_value):
        """Damage self.

        Damages self, subtracts passed in value from health.
        :param damage_value:
        :return:
        """
        self._health -= damage_value
        self._health_bar.update_health_text()

    def heal(self, heal_value):
        """Heal self, add passed in value to health.

        Add passed in value to own health. Check whether the new health
        exceeds the maximum health. If it does, set own health to the max
        health. Finally, update the health bar.
        :param heal_value:
        :return:
        """
        self._health += heal_value
        if self._health > self._max_health:  # check if new health > max
            self._health = self._max_health
        self._health_bar.update_health_text()  # update health text bar

    def get_health(self):
        """Get health.

        Returns health int.
        :return:
        """
        return self._health

    def delete_canvas_object(self):
        """Delete own canvas object.

        Modifies original delete function to include gun removal.
        :return:
        """
        if self.get_has_gun():  # if a gun is owned
            self.remove_gun()  # remove gun before deleting
        self._health_bar.delete_canvas_object()  # delete health bar canvas obj
        del self._health_bar  # delete health bar instance
        super().delete_canvas_object()

    def cleanup(self):
        """Cleanup references to other instances.

        Remove health bar, bullets, gun, and last attacker references
        :return:
        """
        self._health_bar = None
        self._bullets.clear()
        self._gun = None
        self._last_attacker = None


class Player(Attacker):
    """An attacker which the player controls."""

    _IMAGE_PATH = f"{GameController.PLAYER_DIRECTORY}player.png"
    DEFAULT_SPEED = 6
    _WIDTH = 100
    _HEIGHT = 100
    _STARTING_HEALTH = 100

    def __init__(self, canvas, x_position, y_position):
        """Initiate own variables.

        Inherit / call the __init__ function of Attacker, passing in set
        constants for a Player object
        :param canvas:
        :param x_position:
        :param y_position:
        """
        super().__init__(canvas, x_position, y_position, Player._WIDTH,
                         Player._HEIGHT, Player._IMAGE_PATH,
                         Player._STARTING_HEALTH)

    def check_boundaries(self, left_boundary, right_boundary, top_boundary,
                         bottom_boundary):
        """Check whether the player object is past the boundaries passed in.

        Checks the x and y coordinates of the player do not exceed the
        passed in boundaries. If they do, then the function will move the
        player object in the opposite direction to prevent boundary crossing.
        :param left_boundary:
        :param right_boundary:
        :param top_boundary:
        :param bottom_boundary:
        :return:
        """
        if self.coordinates()[0] < left_boundary:
            self._canvas.move(self.get_canvas_object(),
                              Player.DEFAULT_SPEED, 0)
        elif self.coordinates()[0] > right_boundary:
            self._canvas.move(self.get_canvas_object(),
                              -Player.DEFAULT_SPEED, 0)
        if self.coordinates()[1] < top_boundary:
            self._canvas.move(self.get_canvas_object(),
                              0, Player.DEFAULT_SPEED)
        elif self.coordinates()[1] > bottom_boundary:
            self._canvas.move(self.get_canvas_object(),
                              0, -Player.DEFAULT_SPEED)


class Enemy(Attacker):
    """An attacker that attacks other attackers and moves."""

    _WIDTH = 100
    _HEIGHT = 100
    _IMAGE_PATH = f"{GameController.ENEMY_DIRECTORY}enemy.png"
    _DEFAULT_SPEED = 2
    _STARTING_HEALTH = 100
    _DETECTION_RADIUS = 500
    # how far a random destination can be from own coordinates
    _RANDOM_DESTINATION_VARIANCE = 100
    _ERROR_MARGIN = 1  # margin for which coordinates can be between
    # spawn numbers

    def __init__(self, canvas, x_position, y_position):
        """Initiate self variables.

        Declare self variables and Super parent class init to run its code.
        :param canvas:
        :param x_position:
        :param y_position:
        """
        super().__init__(canvas, x_position, y_position, Enemy._WIDTH,
                         Enemy._HEIGHT, Enemy._IMAGE_PATH,
                         Enemy._STARTING_HEALTH)
        self._destination = []
        self.generate_destination()
        self._detection_radius = Enemy._DETECTION_RADIUS
        self._target = None
        self._has_target = False

    def check_destination(self):
        """Check if reached destination.

        Checks if destination has been reached, within a small margin.
        :return:
        """
        # create a low and high margin of error for which the coordinates
        # can be between to trigger the if statement
        lowest_margin = [coordinate - Enemy._ERROR_MARGIN for
                         coordinate in self._destination]
        highest_margin = [coordinate + Enemy._ERROR_MARGIN for
                          coordinate in self._destination]
        if lowest_margin < self.coordinates() < highest_margin:
            return False
        else:
            return True

    def generate_destination(self):
        """Generate semi random destination.

        Generates a random destination based off the centre of the zone.
        :return:
        """
        centre_x = GameController.CANVAS_WIDTH/2
        centre_y = GameController.CANVAS_HEIGHT/2
        own_x = self.coordinates()[0]
        own_y = self.coordinates()[1]

        # if the centre x of the zone is greater than own x, choose an x
        # to the right of current position
        if centre_x > own_x:
            new_x = random.uniform(own_x,
                                   own_x + Enemy._RANDOM_DESTINATION_VARIANCE)
        else:
            new_x = random.uniform(own_x,
                                   own_x - Enemy._RANDOM_DESTINATION_VARIANCE)
        # if the centre y of the zone is greater than own y, choose a y
        # below the current position
        if centre_y > own_y:
            new_y = random.uniform(own_y,
                                   own_y + Enemy._RANDOM_DESTINATION_VARIANCE)
        else:
            new_y = random.uniform(own_y,
                                   own_y - Enemy._RANDOM_DESTINATION_VARIANCE)

        self._destination = [new_x, new_y]

        self._set_speed_to_point(*self._destination, Enemy._DEFAULT_SPEED,
                                 Enemy._DEFAULT_SPEED)

    def scan_vision(self, tag):
        """Find enemies within the vision radius.

        Get a list of overlapping attackers in the area of the vision radius,
        then removes own canvas object from the list and returns it.
        :return:
        """
        # get coordinates for vision boundaries
        top_left_boundary = [self.coordinates()[0]-self._detection_radius,
                             self.coordinates()[1]-self._detection_radius]
        bottom_right_boundary = [self.coordinates()[0]+self._detection_radius,
                                 self.coordinates()[1]+self._detection_radius]
        # get a list of attacker objects overlapping with the vision boundary
        # and removed any guns that are owned
        overlapping_objects = \
            [item for item in self._canvas.find_overlapping(
                *top_left_boundary, *bottom_right_boundary) if
                tag in self._canvas.gettags(item) and Gun.OWNED_TAG not in
             self._canvas.gettags(item)]
        # remove own canvas object from the list of overlapping attackers
        try:
            overlapping_objects.remove(self.get_canvas_object())
        except ValueError:
            pass

        return self._get_ids_from_canvas_objects(overlapping_objects)

    def set_destination(self, item):
        """Set own destination.

        Sets coordinates of passed in instance, then sets as destination.
        :param item:
        :return:
        """
        self._destination = item.coordinates()
        self._set_speed_to_point(*self._destination, Enemy._DEFAULT_SPEED,
                                 Enemy._DEFAULT_SPEED)

    def add_target(self, target):
        """Add passed in target.

        Sets own target to passed in variable and condition to true.
        :param target:
        :return:
        """
        self._target = target
        self._has_target = True

    def remove_target(self):
        """Remove own target.

        Sets own target to None obj, and condition to false.
        :return:
        """
        self._target = None
        self._has_target = False

    def get_has_target(self):
        """Get has_target.

        Returns target condition, a boolean.
        :return:
        """
        return self._has_target

    def get_target(self):
        """Return own target.

        Returns own target, an instance.
        :return:
        """
        return self._target

    def attack_target(self):
        """Attack own target.

        Get target coordinates and returns a shot to that location.
        :return:
        """
        target_coordinates = self._target.coordinates()
        # return a bullet created
        return self.shoot_gun(target_coordinates)

    def cleanup(self):
        """Cleanup references.

        Run parent cleanup code then remove target reference.
        :return:
        """
        super().cleanup()
        self._target = None


class Gun(CanvasSprite):
    """A canvas sprite with gun functionality, i.e. shooting, etc."""

    GUN_TAG = "gun"
    OWNED_TAG = "owned"

    def __init__(self, canvas, x_position, y_position, gun_properties, rarity):
        """Set up gun with correct values and initiate self variables.

        Variables are stored from the passed in gun properties, then the
        canvas sprite init is called with some of these variables used.
        :param canvas:
        :param x_position:
        :param y_position:
        :param gun_properties:
        """
        # need to grab the gun properties before the super as some information
        # is required for it
        # image path consists of gun directory string, rarity prefix, and gun
        # name / path
        image_path = (GameController.GUN_DIRECTORY +
                      GameController.RARITIES[rarity]["file_prefix"] +
                      gun_properties['image_path'])
        width = gun_properties['width']
        height = gun_properties['height']
        # multiply base damage by rarity damage multiplier
        self._damage = (gun_properties['damage'] *
                        GameController.RARITIES[rarity]["damage_multiplier"])
        self._fire_rate = gun_properties['fire_rate']
        self._spray = gun_properties['spray']

        super().__init__(canvas, x_position, y_position, width, height,
                         image_path)

        self._add_tag(Gun.GUN_TAG)
        self._time_since_last_shot = time.time()
        self._owner = None
        self._has_owner = False

    def add_owner(self, owner):
        """Add passed in owner.

        Adds passed in variable as owner, then updates bool and tag.
        :param owner:
        :return:
        """
        self._owner = owner
        self._has_owner = True
        self._add_tag(Gun.OWNED_TAG)  # add the gun owned tag

    def remove_owner(self):
        """Remove own owner.

        Sets own owner to None, and changes bool has_owner to False.
        :return:
        """
        self._owner = None
        self._has_owner = False

    def cleanup(self):
        """Cleanup references.

        Delete own owner reference
        :return:
        """
        self._owner = None

    def shoot(self, destination_coordinates):
        """Return a bullet object based on passed in coordinates.

        Check whether the fire rate time has passed. If it has, add spray to
        destination and return a created bullet.
        :param destination_coordinates:
        :return:
        """
        current_time = time.time()
        # check if fire rate time has passed since last shot
        if current_time - self._time_since_last_shot > 1/self._fire_rate:
            self._time_since_last_shot = current_time
            # add a random spray value to each coordinate in destination coords
            destination_with_spray = [coordinate + random.randint(
                self._spray[0], self._spray[1]) for coordinate in
                                      destination_coordinates]

            return Bullet(self._canvas, *self.coordinates(), self._damage,
                          destination_with_spray, self._owner)


class Bullet(MovingObject):
    """A moving object with added bullet like functionality."""

    _WIDTH = 20
    _HEIGHT = 20
    _IMAGE_PATH = f"{GameController.BULLET_DIRECTORY}bullet.png"
    _DEFAULT_SPEED = 20
    BULLET_TAG = "bullet"

    def __init__(self, canvas, x_position, y_position, damage, destination,
                 owner):
        """
        Set up self variables and set the speed to destination.

        Call MovingObject init by passing in set constants for a bullet,
        then create new variables that will be used for each bullet object
        :param canvas:
        :param x_position:
        :param y_position:
        :param damage:
        :param destination:
        """
        super().__init__(canvas, x_position, y_position, Bullet._WIDTH,
                         Bullet._HEIGHT, Bullet._IMAGE_PATH)
        self._owner = owner
        self._add_tag(Bullet.BULLET_TAG)
        self._damage = damage
        self._destination = destination
        self._set_speed_to_point(*destination, Bullet._DEFAULT_SPEED,
                                 Bullet._DEFAULT_SPEED)

    def cleanup(self):
        """Cleanup references.

        Remove own owner reference.
        :return:
        """
        self._owner = None

    def get_damage(self):
        """Return own damage value

        Returns own damage value, an integer.
        :return:
        """
        return self._damage

    def get_owner(self):
        """Return own owner.

        Returns own owner, an instance.
        :return:
        """
        return self._owner


class BattleBus(MovingObject):
    """A battle bus - moves from a point to a point carrying a passenger."""

    _IMAGE_PATH = f"{GameController.VEHICLE_DIRECTORY}battle_bus.png"
    _DEFAULT_WIDTH = 300
    _DEFAULT_HEIGHT = 300
    _DEFAULT_SPEED = 12

    def __init__(self, canvas, x_position, y_position, destination_x,
                 destination_y, passenger):
        """Initiate self variables.

        Calls MovingObject init and sets the trajectory.
        :param canvas:
        :param x_position:
        :param y_position:
        :param destination_x:
        :param destination_y:
        """
        super().__init__(canvas, x_position, y_position,
                         BattleBus._DEFAULT_WIDTH, BattleBus._DEFAULT_HEIGHT,
                         BattleBus._IMAGE_PATH)
        self._set_speed_to_point(destination_x, destination_y,
                                 BattleBus._DEFAULT_SPEED,
                                 BattleBus._DEFAULT_SPEED)

        self._passenger = passenger
        self._has_passenger = True

    def remove_passenger(self):
        """Remove passenger.

        Removes the current passenger and sets the bool has_passenger to False.
        :return:
        """
        self._passenger = None
        self._has_passenger = False

    def move(self):
        """Move the battle bus and its passenger.

        Extends the move function of a moving object to stick the passenger
        to the bus while it is moving.
        :return:
        """
        super().move()  # runs the moving object move function, then extend
        if self._has_passenger:
            # move passenger to own coordinates
            self._canvas.coords(self._passenger.get_canvas_object(),
                                *self.coordinates())


class HealthBar:
    """A text object that updates with the owner's health."""

    def __init__(self, owner, canvas):
        """Initiate self variables.

        Called when an instance is created, sets up self variables.
        :param owner:
        :param canvas:
        """
        self._owner = owner
        self._canvas = canvas
        self._text_object = self._canvas.create_text(
            *self.calculate_owner_coordinates(),
            text=f"{self._owner.get_health()}")

    def cleanup(self):
        """Cleanup references.

        Removes own owner reference.
        :return:
        """
        self._owner = None

    def calculate_owner_coordinates(self):
        """Calculate coordinates of owner.

        Calculates correct coordinates to display health.
        :return:
        """
        coordinates = self._owner.coordinates()
        # subtract owner height from y coord, positions above owner
        coordinates[1] -= self._owner.get_height()
        return coordinates

    def update_health_text(self):
        """Update the health text.

        Sets the text of text object to the owner's health.
        :return:
        """
        self._canvas.itemconfigure(self._text_object,
                                   text=f"{self._owner.get_health():.0f}")

    def get_text_object(self):
        """Return own text object.

        Getter, returns own text object, a canvas object.
        :return:
        """
        return self._text_object

    def delete_canvas_object(self):
        """Delete own canvas object.

        Deletes own canvas object, a canvas text object.
        :return:
        """
        self._canvas.delete(self._text_object)


class Zone:
    """A zone - shrinks and damages entities outside radius."""

    # damage the zone will do per tick
    _ZONE_DAMAGE_TICK = 0.5
    # rate at which the zone will shrink per tick
    _ZONE_SHRINK_RATE = 1
    _ZONE_MINIMUM_RADIUS = 500
    _ZONE_COLOUR = "pink"

    def __init__(self, canvas, centre, radius):
        """Initiate self variables.

        Sets up self variables and zone canvas object.
        :param canvas:
        :param centre:
        :param radius:
        """
        self._canvas = canvas
        self._radius = radius
        self._centre = centre
        self._zone = self._canvas.create_oval(self._centre[0] - self._radius,
                                              self._centre[1] - self._radius,
                                              self._centre[0] + self._radius,
                                              self._centre[1] + self._radius,
                                              fill=Zone._ZONE_COLOUR)

    def shrink_zone(self):
        """Shrink the zone by a set amount.

        Subtracts the zone shrink rate from the radius then sets the
        coordinates of the zone to new calculated coords from the new radius
        :return:
        """
        self._radius -= Zone._ZONE_SHRINK_RATE
        if self._radius < Zone._ZONE_MINIMUM_RADIUS:
            self._radius = Zone._ZONE_MINIMUM_RADIUS
        # set zone coords to new calculated coords to shrink it
        self._canvas.coords(self._zone, self._centre[0]-self._radius,
                            self._centre[1]-self._radius,
                            self._centre[0]+self._radius,
                            self._centre[1]+self._radius)

    def _find_distance_to_attacker(self, attacker):
        """Find the distance to given attacker.

        Calculate distance from centre of zone to a given attacker.
        :param attacker:
        :return:
        """
        attacker_coordinates = attacker.coordinates()
        own_coordinates = self._centre
        # calculate distance from centre to attacker
        distance = math.hypot(attacker_coordinates[0] - own_coordinates[0],
                              attacker_coordinates[1] - own_coordinates[1])
        return distance

    def check_attackers_inside(self, attackers):
        """Check if all attackers passed in are inside.

        Check if distance to attacker is less than the radius.
        :param attackers:
        :return:
        """
        for attacker in attackers:
            distance_to_attacker = self._find_distance_to_attacker(attacker)
            if distance_to_attacker < self._radius:  # if attacker in zone
                continue  # continue (move to next iteration)
            else:
                # damage the attacker by set rate
                attacker.damage(Zone._ZONE_DAMAGE_TICK)


class HealConsumable(CanvasSprite):
    """Canvas sprite with functionality to heal consumer."""

    TAG = "heal consumable"
    WIDTH = 50
    HEIGHT = 50

    def __init__(self, canvas, x_position, y_position, consumable_type):
        """Initiate self variables.

        Initiates self variables and supers parent class.
        :param canvas:
        :param x_position:
        :param y_position:
        """
        image_path = \
            GameController.HEAL_CONSUMABLES[consumable_type]["image_path"]
        heal_value = \
            GameController.HEAL_CONSUMABLES[consumable_type]["heal_value"]
        super().__init__(canvas, x_position, y_position, HealConsumable.WIDTH,
                         HealConsumable.HEIGHT, image_path)
        self._heal_value = heal_value
        self._add_tag(HealConsumable.TAG)

    def get_heal_value(self):
        """Return own heal value.

        Getter - returns own heal value, an integer.
        :return:
        """
        return self._heal_value


class AliveCounter:
    """A canvas text object that can be updated for the no. alive."""

    def __init__(self, counter_variable, number_alive):
        """
        initiates self variables and canvas object
        :param number_alive:
        """
        self._alive_count = number_alive
        self._text_variable = counter_variable
        self._text_variable.set(f"{self._alive_count} alive")

    def enemy_killed(self):
        """
        Subtracts one from the alive count and updates StringVar.
        :return:
        """
        self._alive_count -= 1
        self._text_variable.set(f"{self._alive_count} alive")

    def get_alive_count(self):
        """
        Return own alive count int.
        :return:
        """
        return self._alive_count


class Score:
    """Keeps track of a player score and can write to a given file."""

    _KILL_SCORE = 100
    _WIN_SCORE = 1000

    def __init__(self, canvas, player, player_name, score_file):
        self._score_file = score_file
        self._canvas = canvas
        self._player = player
        self._player_name = player_name
        self._score = 0

    def add_kill_score(self):
        """Add a kill score the own score.

        Adds the kill score value to own score tally.
        :return:
        """
        self._score += Score._KILL_SCORE

    def add_win_score(self):
        """Add a win score to own score.

        Add the kill score value to own score tally.
        :return:
        """
        self._score += Score._WIN_SCORE

    def get_score(self):
        """Return own score.

        Returns own score value, an integer.
        :return:
        """
        return self._score

    def cleanup(self):
        """
        Cleanup references.

        Cleans up loose references, such as the player instance.
        :return:
        """
        self._player = None

    def write_score(self):
        """Update score file with own score.

        Uses pickle module to load the score file, then appends own score
        to the dictionary if it does not already exist. if it does exist,
        check the old value and if higher, append current value to dict
        :return:
        """
        # load the score file (contains a dict)
        scores = pickle.load(open(self._score_file, "rb"))
        if self._player_name not in scores:  # if player not exist already
            scores[self._player_name] = self._score  # append score to dict
        else:
            old_score = scores.get(self._player_name)  # get old score
            if old_score < self._score:  # if old score lower, append current
                scores[self._player_name] = self._score

        pickle.dump(scores, open(self._score_file, "wb"))  # dump/save scores


if __name__ == "__main__":
    pass
