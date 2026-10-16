"""SHADOW LEGENDS: NEON WAR - VIP 3D Edition
Created by Chishti Bro Computers & Developers | Founder: Moinuddin Chishti
A self-contained, procedurally generated third-person action game built with Panda3D.
Controls: WASD move, mouse aim, left mouse/Space shoot, Shift sprint, Esc pause.
"""
import math
import os
import random
import json
from pathlib import Path

from direct.showbase.ShowBase import ShowBase
from direct.gui.OnscreenText import OnscreenText
from direct.gui.DirectGui import DirectFrame, DirectButton
from direct.task import Task
from panda3d.core import (
    AmbientLight, DirectionalLight, Vec3, Vec4, WindowProperties,
    TextNode, Point3, Fog, CardMaker, ClockObject
)

TITLE = "SHADOW LEGENDS: NEON WAR - VIP 3D"
SAVE_FILE = Path.home() / ".shadow_legends_neon_war.json"


def clamp(value, low, high):
    return max(low, min(high, value))


class ShadowLegends(ShowBase):
    def __init__(self):
        super().__init__()
        self.disableMouse()
        self.setBackgroundColor(0.012, 0.018, 0.045, 1)
        props = WindowProperties()
        props.setTitle(TITLE)
        props.setSize(1280, 720)
        self.win.requestProperties(props)

        self.rng = random.Random(2026)
        self.keys = {key: False for key in ("w", "a", "s", "d", "shift", "space")}
        self.mouse_sensitivity = 0.12
        self.player_pos = Vec3(0, 0, 1.2)
        self.player_heading = 0.0
        self.health = 100.0
        self.armor = 50.0
        self.ammo = 120
        self.score = 0
        self.credits = 0
        self.level = 1
        self.xp = 0
        self.kills = 0
        self.mission_kills = 0
        self.mission_target = 8
        self.game_over = False
        self.paused = False
        self.started = False
        self.elapsed = 0.0
        self.shot_cooldown = 0.0
        self.dash_cooldown = 0.0
        self.dash_time = 0.0
        self.vehicle_mode = False
        self.weapon_mode = 1
        self.boss_spawned = False
        self.enemy_spawn_timer = 0.0
        self.enemies = []
        self.bullets = []
        self.pickups = []
        self.buildings = []
        self.ui_items = []
        self._mouse_x = None
        self._mouse_y = None
        self._load_save()
        self.initial_total_kills = self.total_kills
        self._setup_lighting()
        self._build_city()
        self._build_player()
        self._build_vehicle()
        self._build_ui()
        self._bind_keys()
        self._show_menu()
        self.taskMgr.add(self.update, "game-update")

    def _setup_lighting(self):
        ambient = AmbientLight("ambient")
        ambient.setColor(Vec4(0.42, 0.48, 0.68, 1))
        self.render.setLight(self.render.attachNewNode(ambient))
        sun = DirectionalLight("neon-moon")
        sun.setColor(Vec4(0.75, 0.84, 1.0, 1))
        sun.setDirection(Vec3(-1, -2, -3))
        self.render.setLight(self.render.attachNewNode(sun))
        fog = Fog("city-fog")
        fog.setColor(0.012, 0.018, 0.045)
        fog.setExpDensity(0.006)
        self.render.setFog(fog)

    def _make_box(self, parent, name, pos, scale, color, model="models/box"):
        node = self.loader.loadModel(model)
        node.reparentTo(parent)
        node.setName(name)
        node.setPos(*pos)
        node.setScale(*scale)
        node.setColor(*color)
        node.setTwoSided(True)
        return node

    def _build_city(self):
        # Large dark floor and a glowing grid of road strips.
        self._make_box(self.render, "city-ground", (0, 0, -0.35), (220, 220, 0.3), (0.025, 0.035, 0.07, 1))
        for offset in range(-100, 101, 10):
            self._make_box(self.render, "cyan-road-line", (offset, 0, -0.17), (0.035, 200, 0.025), (0.0, 0.65, 0.95, 1))
            self._make_box(self.render, "purple-road-line", (0, offset, -0.16), (200, 0.035, 0.025), (0.45, 0.12, 0.85, 1))
        # Buildings leave a safe central arena around the player spawn.
        for x in range(-90, 91, 15):
            for y in range(-90, 91, 15):
                if abs(x) < 19 and abs(y) < 19:
                    continue
                if self.rng.random() < 0.20:
                    continue
                height = self.rng.uniform(7, 28)
                width = self.rng.uniform(4.2, 7.0)
                depth = self.rng.uniform(4.2, 7.0)
                base = self.rng.choice([
                    (0.045, 0.075, 0.14, 1), (0.08, 0.045, 0.15, 1),
                    (0.04, 0.11, 0.14, 1), (0.10, 0.10, 0.17, 1)
                ])
                b = self._make_box(self.render, "neon-tower", (x, y, height / 2 - 0.1), (width, depth, height), base)
                self.buildings.append((x, y, width, depth, height))
                # Bright roof edge gives the skyline a cyberpunk silhouette.
                self._make_box(self.render, "tower-roof-glow", (x, y, height + 0.04), (width + 0.12, depth + 0.12, 0.10), self.rng.choice([
                    (0.0, 0.75, 1.0, 1), (0.9, 0.1, 0.8, 1), (1.0, 0.55, 0.08, 1)
                ]))
        # Neon portal landmark.
        for side in (-1, 1):
            self._make_box(self.render, "portal-pillar", (side * 5, 18, 5), (0.35, 0.45, 5), (0.0, 0.9, 1.0, 1))
        self._make_box(self.render, "portal-top", (0, 18, 10), (5.4, 0.45, 0.3), (0.85, 0.08, 1.0, 1))

    def _build_player(self):
        self.player = self.render.attachNewNode("player-root")
        self.player.setPos(self.player_pos)
        self._make_box(self.player, "player-body", (0, 0, 0.15), (0.55, 0.4, 0.8), (0.05, 0.8, 1.0, 1))
        self._make_box(self.player, "player-head", (0, 0, 0.85), (0.34, 0.34, 0.34), (0.95, 0.8, 0.65, 1), "models/misc/sphere")
        self._make_box(self.player, "player-weapon", (0.25, 0.42, 0.35), (0.13, 0.62, 0.12), (1.0, 0.25, 0.12, 1))
        self.camera_pivot = self.render.attachNewNode("camera-pivot")
        self.camera_pivot.setPos(self.player_pos + Vec3(0, 0, 2.0))
        self.camera.reparentTo(self.camera_pivot)
        self.camera.setPos(0, -11, 4.0)
        self.camera.lookAt(self.camera_pivot, Point3(0, 0, 1.0))
        self.camera_pivot.setH(0)
        self._set_mouse_capture(True)

    def _build_ui(self):
        self.hud = OnscreenText(text="", pos=(-1.29, 0.91), scale=0.048, fg=(0.3, 0.95, 1, 1),
                                align=TextNode.ALeft, mayChange=True, shadow=(0, 0, 0, 1))
        self.mission_text = OnscreenText(text="", pos=(0, 0.91), scale=0.045, fg=(1, 0.72, 0.18, 1),
                                         align=TextNode.ACenter, mayChange=True, shadow=(0, 0, 0, 1))
        self.notice = OnscreenText(text="", pos=(0, -0.78), scale=0.065, fg=(0.3, 1, 0.8, 1),
                                   align=TextNode.ACenter, mayChange=True, shadow=(0, 0, 0, 1))
        self.controls = OnscreenText(text="WASD Move | Mouse Aim | LMB/SPACE Shoot | SHIFT Sprint | Q Dash | V Vehicle | 1-3 Weapons | R Reload | F Collect | ESC Pause",
                                     pos=(0, -0.96), scale=0.035, fg=(0.75, 0.82, 0.95, 1),
                                     align=TextNode.ACenter, mayChange=False)
        self.overlay = DirectFrame(frameColor=(0.01, 0.015, 0.05, 0.94), frameSize=(-1.25, 1.25, -0.72, 0.72),
                                   pos=(0, 0, 0))
        self.overlay.hide()
        self.overlay_title = OnscreenText(text="SHADOW LEGENDS", pos=(0, 0.40), scale=0.11,
                                          fg=(0.15, 0.9, 1, 1), align=TextNode.ACenter, parent=self.overlay,
                                          shadow=(0, 0, 0, 1))
        self.overlay_subtitle = OnscreenText(text="NEON WAR  •  VIP 3D EDITION", pos=(0, 0.25), scale=0.047,
                                             fg=(1, 0.55, 0.16, 1), align=TextNode.ACenter, parent=self.overlay)
        self.overlay_info = OnscreenText(text="", pos=(0, 0.06), scale=0.045, fg=(0.88, 0.92, 1, 1),
                                         align=TextNode.ACenter, parent=self.overlay, mayChange=True)
        self.start_button = DirectButton(text="START / RESUME", scale=0.075, pos=(0, 0, -0.18),
                                         command=self._start_game, parent=self.overlay,
                                         frameColor=(0.0, 0.35, 0.55, 1), text_fg=(1, 1, 1, 1))
        self.restart_button = DirectButton(text="RESTART MISSION", scale=0.06, pos=(0, 0, -0.34),
                                           command=self._restart_game, parent=self.overlay,
                                           frameColor=(0.35, 0.08, 0.42, 1), text_fg=(1, 1, 1, 1))
        self.footer = OnscreenText(text="Created by Chishti Bro Computers & Developers  |  Founder: Moinuddin Chishti",
                                   pos=(0, -0.55), scale=0.033, fg=(0.65, 0.72, 0.86, 1),
                                   align=TextNode.ACenter, parent=self.overlay)

    def _build_vehicle(self):
        """Build a small stylized hover vehicle from engine primitives; no external assets needed."""
        self.vehicle = self.render.attachNewNode("player-hover-vehicle")
        self._make_box(self.vehicle, "vehicle-chassis", (0, 0, 0.55), (1.55, 2.25, 0.35), (0.035, 0.06, 0.12, 1))
        self._make_box(self.vehicle, "vehicle-canopy", (0, 0.15, 0.95), (0.95, 0.95, 0.42), (0.0, 0.72, 0.95, 0.8))
        for x in (-1.25, 1.25):
            for y in (-0.75, 0.85):
                self._make_box(self.vehicle, "hover-thruster", (x, y, 0.25), (0.22, 0.42, 0.12), (0.8, 0.08, 1.0, 1))
        self._make_box(self.vehicle, "front-light", (0, 1.14, 0.56), (0.75, 0.08, 0.09), (0.0, 0.95, 1.0, 1))
        self.vehicle.setPos(4, -1, 0.0)

    def _toggle_vehicle(self):
        if not self.started or self.paused or self.game_over:
            return
        if self.vehicle_mode:
            self.vehicle_mode = False
            self.player.show()
            self.vehicle.setPos(self.player_pos.x + 2.5, self.player_pos.y, 0)
            self.notice.setText("VEHICLE EXITED")
            return
        if (self.vehicle.getPos(self.render) - self.player_pos).length() < 6.0:
            self.vehicle_mode = True
            self.player.hide()
            self.notice.setText("HOVER VEHICLE ACTIVE — BOOSTED SPEED")
        else:
            self.notice.setText("MOVE CLOSER TO THE HOVER VEHICLE")

    def _dash(self):
        if not self.started or self.paused or self.game_over or self.dash_cooldown > 0:
            return
        self.dash_time = 0.22
        self.dash_cooldown = 2.2
        self.notice.setText("NEON DASH!")

    def _set_weapon(self, mode):
        self.weapon_mode = mode
        names = {1: "PLASMA RIFLE", 2: "HEAVY BLASTER", 3: "RAPID PULSE"}
        self.notice.setText("WEAPON: " + names[mode])

    def _bind_keys(self):
        for key in ("w", "a", "s", "d", "shift", "space"):
            self.accept(key, self._set_key, [key, True])
            self.accept(key + "-up", self._set_key, [key, False])
        self.accept("escape", self._toggle_pause)
        self.accept("mouse1", self._shoot)
        self.accept("r", self._reload)
        self.accept("f", self._collect_nearby)
        self.accept("q", self._dash)
        self.accept("v", self._toggle_vehicle)
        self.accept("1", self._set_weapon, [1])
        self.accept("2", self._set_weapon, [2])
        self.accept("3", self._set_weapon, [3])
        self.accept("wheel_up", self._zoom, [-1])
        self.accept("wheel_down", self._zoom, [1])
        self.accept("window-event", self._window_event)

    def _window_event(self, window):
        if window is not None:
            self._set_mouse_capture(self.started and not self.paused and not self.game_over)

    def _set_mouse_capture(self, enabled):
        props = WindowProperties()
        props.setCursorHidden(enabled)
        self.win.requestProperties(props)
        self._mouse_x = self.win.getXSize() // 2
        self._mouse_y = self.win.getYSize() // 2
        if enabled:
            self.win.movePointer(0, int(self._mouse_x), int(self._mouse_y))

    def _set_key(self, key, value):
        self.keys[key] = value

    def _show_menu(self, mode="title"):
        self.overlay.show()
        self._set_mouse_capture(False)
        if mode == "title":
            self.overlay_title.setText("SHADOW LEGENDS")
            self.overlay_info.setText("A neon city is under attack. Survive the streets, defeat the Titan Sentinel and secure the city.\n\nMission: eliminate 8 hostiles. Collect supply drops with F. Dash with Q; V toggles the nearby hover vehicle.")
            self.start_button["text"] = "START MISSION"
            self.restart_button.show()
        elif mode == "pause":
            self.overlay_title.setText("MISSION PAUSED")
            self.overlay_info.setText("Your progress is saved automatically.\nResume when ready, or restart the mission.")
            self.start_button["text"] = "RESUME GAME"
            self.restart_button.show()
        elif mode == "gameover":
            self.overlay_title.setText("MISSION FAILED")
            self.overlay_info.setText(f"Final score: {self.score}   •   Eliminations: {self.kills}\nReach the target and try again.")
            self.start_button["text"] = "TRY AGAIN"
            self.restart_button.hide()
        elif mode == "victory":
            self.overlay_title.setText("MISSION COMPLETE!")
            self.overlay_info.setText(f"City secured! Score: {self.score}   •   Eliminations: {self.kills}\nYou earned {self.credits} credits.")
            self.start_button["text"] = "PLAY AGAIN"
            self.restart_button.hide()

    def _start_game(self):
        if self.game_over or self.mission_kills >= self.mission_target:
            self._restart_game()
            return
        self.started = True
        self.paused = False
        self.overlay.hide()
        self.notice.setText("MISSION STARTED — TAKE DOWN THE HOSTILES")
        self._set_mouse_capture(True)
        self._spawn_initial_enemies()

    def _restart_game(self):
        for item in self.enemies + self.bullets + self.pickups:
            try:
                item["node"].removeNode()
            except Exception:
                pass
        self.enemies.clear()
        self.bullets.clear()
        self.pickups.clear()
        self.player_pos = Vec3(0, 0, 1.2)
        self.player.setPos(self.player_pos)
        self.camera_pivot.setPos(self.player_pos + Vec3(0, 0, 2.0))
        self.player_heading = 0.0
        self.player.setH(0)
        self.camera_pivot.setH(0)
        self.health, self.armor, self.ammo = 100.0, 50.0, 120
        self.dash_cooldown = self.dash_time = 0.0
        self.vehicle_mode = False
        self.weapon_mode = 1
        self.boss_spawned = False
        self.vehicle.setPos(4, -1, 0.0)
        self.vehicle.show()
        self.player.show()
        self.score = self.credits = self.xp = self.kills = self.mission_kills = 0
        self.level = 1
        self.elapsed = 0.0
        self.shot_cooldown = 0.0
        self.enemy_spawn_timer = 0.0
        self.game_over = False
        self.paused = False
        self.started = True
        self.overlay.hide()
        self._set_mouse_capture(True)
        self._spawn_initial_enemies()
        self.notice.setText("NEW MISSION — GOOD LUCK")

    def _toggle_pause(self):
        if not self.started or self.game_over:
            return
        self.paused = not self.paused
        if self.paused:
            self._save_game()
            self._show_menu("pause")
        else:
            self.overlay.hide()
            self._set_mouse_capture(True)

    def _spawn_initial_enemies(self):
        while len(self.enemies) < 6:
            self._spawn_enemy()

    def _spawn_enemy(self, boss=False):
        angle = self.rng.uniform(0, math.tau)
        distance = self.rng.uniform(24, 65)
        x = clamp(self.player_pos.x + math.cos(angle) * distance, -95, 95)
        y = clamp(self.player_pos.y + math.sin(angle) * distance, -95, 95)
        node = self.render.attachNewNode("enemy-root")
        color = (1.0, 0.12, 0.22, 1) if self.rng.random() < 0.78 else (0.95, 0.45, 0.05, 1)
        self._make_box(node, "enemy-body", (0, 0, 0.45), (0.55, 0.48, 0.8), color)
        self._make_box(node, "enemy-head", (0, 0, 1.0), (0.32, 0.32, 0.32), (1.0, 0.6, 0.55, 1), "models/misc/sphere")
        node.setPos(x, y, 0.0)
        self.enemies.append({"node": node, "hp": 55.0 if self.level < 3 else 75.0,
                             "speed": self.rng.uniform(1.8, 3.0) + self.level * 0.12,
                             "attack": self.rng.uniform(0.0, 1.0), "hit_flash": 0.0})

    def _shoot(self):
        if not self.started or self.paused or self.game_over or self.shot_cooldown > 0 or self.ammo <= 0:
            return
        self.ammo -= 1
        cooldowns = {1: 0.18, 2: 0.48, 3: 0.085}
        damages = {1: 28.0, 2: 82.0, 3: 13.0}
        self.shot_cooldown = cooldowns[self.weapon_mode]
        # Aim from the player's forward direction; mouse X steers the camera/player.
        direction = Vec3(math.sin(math.radians(self.player_heading)), math.cos(math.radians(self.player_heading)), 0)
        origin = Vec3(self.player_pos.x, self.player_pos.y, 1.1)
        node = self._make_box(self.render, "plasma-bolt", origin, (0.10, 0.10, 0.10), (0.1, 0.95, 1.0, 1), "models/misc/sphere")
        node.setScale(0.16 if self.weapon_mode != 2 else 0.25)
        self.bullets.append({"node": node, "dir": direction, "life": 1.4, "speed": 62.0 if self.weapon_mode != 2 else 48.0,
                             "damage": damages[self.weapon_mode]})

    def _reload(self):
        if self.started and not self.paused and not self.game_over:
            self.ammo = 120
            self.notice.setText("PLASMA CELL RELOADED")

    def _zoom(self, amount):
        y = clamp(self.camera.getY() + amount * 1.4, -16, -6)
        self.camera.setY(y)

    def _collect_nearby(self):
        if not self.started or self.paused:
            return
        for pickup in list(self.pickups):
            if (pickup["node"].getPos(self.render) - self.player_pos).length() < 4.0:
                kind = pickup["kind"]
                if kind == "health":
                    self.health = min(100.0, self.health + 35.0)
                    self.notice.setText("HEALTH RESTORED +35")
                elif kind == "armor":
                    self.armor = min(100.0, self.armor + 30.0)
                    self.notice.setText("ARMOR RECHARGED +30")
                else:
                    self.ammo = min(240, self.ammo + 45)
                    self.notice.setText("PLASMA AMMO +45")
                pickup["node"].removeNode()
                self.pickups.remove(pickup)
                self.credits += 10
                self._save_game()
                break

    def _spawn_pickup(self, pos):
        kind = self.rng.choice(("health", "armor", "ammo"))
        color = {"health": (0.1, 1.0, 0.3, 1), "armor": (0.2, 0.55, 1.0, 1), "ammo": (1.0, 0.65, 0.08, 1)}[kind]
        node = self._make_box(self.render, "supply-drop", (pos.x, pos.y, 0.8), (0.42, 0.42, 0.42), color, "models/misc/sphere")
        self.pickups.append({"node": node, "kind": kind, "phase": self.rng.random() * math.tau})

    def _damage_player(self, amount):
        absorbed = min(self.armor, amount * 0.65)
        self.armor -= absorbed
        self.health -= amount - absorbed
        self.health = max(0, self.health)
        if self.health <= 0:
            self.game_over = True
            self.started = False
            self._save_game()
            self._show_menu("gameover")

    def _enemy_hit(self, enemy, damage):
        enemy["hp"] -= damage
        enemy["hit_flash"] = 0.12
        if enemy["hp"] <= 0:
            pos = enemy["node"].getPos(self.render)
            enemy["node"].removeNode()
            if enemy in self.enemies:
                self.enemies.remove(enemy)
            self.kills += 1
            self.mission_kills += 1
            if enemy.get("boss"):
                self.score += 500
                self.credits += 100
                self.notice.setText("TITAN SENTINEL DEFEATED! BONUS +500")
            self.score += 100
            self.xp += 25
            self.credits += 15
            if self.rng.random() < 0.42:
                self._spawn_pickup(pos)
            if self.xp >= self.level * 100:
                self.xp -= self.level * 100
                self.level += 1
                self.health = min(100.0, self.health + 15)
                self.armor = min(100.0, self.armor + 10)
                self.notice.setText(f"LEVEL UP! LEVEL {self.level}")
            if self.mission_kills >= self.mission_target:
                self.started = False
                self._save_game()
                self._show_menu("victory")

    def _update_mouse_aim(self):
        if not self.win:
            return
        pointer = self.win.getPointer(0)
        center_x = self.win.getXSize() // 2
        center_y = self.win.getYSize() // 2
        dx = pointer.getX() - center_x
        dy = pointer.getY() - center_y
        if abs(dx) > 0:
            self.player_heading -= dx * self.mouse_sensitivity
            self.player.setH(-self.player_heading)
            self.camera_pivot.setH(-self.player_heading)
        if abs(dy) > 0:
            self.camera.setZ(clamp(self.camera.getZ() - dy * 0.003, 2.0, 6.0))
        self.win.movePointer(0, int(center_x), int(center_y))

    def _update_player(self, dt):
        move = Vec3(0, 0, 0)
        if self.keys["w"]: move.y += 1
        if self.keys["s"]: move.y -= 1
        if self.keys["a"]: move.x -= 1
        if self.keys["d"]: move.x += 1
        if move.lengthSquared() > 0:
            move.normalize()
            heading = math.radians(self.player_heading)
            forward = Vec3(math.sin(heading), math.cos(heading), 0)
            right = Vec3(math.cos(heading), -math.sin(heading), 0)
            direction = right * move.x + forward * move.y
            speed = 29.0 if self.dash_time > 0 else (21.0 if self.vehicle_mode else (12.5 if self.keys["shift"] else 8.0))
            self.player_pos += direction * speed * dt
            self.player_pos.x = clamp(self.player_pos.x, -104, 104)
            self.player_pos.y = clamp(self.player_pos.y, -104, 104)
            # Buildings are solid enough to avoid walking through their footprint.
            for bx, by, bw, bd, bh in self.buildings:
                if abs(self.player_pos.x - bx) < bw / 2 + 0.65 and abs(self.player_pos.y - by) < bd / 2 + 0.65:
                    self.player_pos -= direction * speed * dt
                    break
        self.player.setPos(self.player_pos)
        self.camera_pivot.setPos(self.player_pos + Vec3(0, 0, 2.0))
        if self.vehicle_mode:
            self.vehicle.setPos(self.player_pos.x, self.player_pos.y, 0.0)
            self.vehicle.setH(-self.player_heading)
        self.camera.lookAt(self.camera_pivot, Point3(0, 0, 1.0))

    def _update_bullets(self, dt):
        for bullet in list(self.bullets):
            node = bullet["node"]
            pos = node.getPos(self.render)
            pos += bullet["dir"] * bullet["speed"] * dt
            node.setPos(pos)
            bullet["life"] -= dt
            hit = None
            for enemy in self.enemies:
                enemy_pos = enemy["node"].getPos(self.render) + Vec3(0, 0, 0.6)
                if (enemy_pos - pos).length() < 1.25:
                    hit = enemy
                    break
            if hit:
                self._enemy_hit(hit, bullet["damage"])
                node.removeNode()
                self.bullets.remove(bullet)
            elif bullet["life"] <= 0 or abs(pos.x) > 120 or abs(pos.y) > 120:
                node.removeNode()
                self.bullets.remove(bullet)

    def _update_enemies(self, dt):
        for enemy in list(self.enemies):
            node = enemy["node"]
            pos = node.getPos(self.render)
            target = Vec3(self.player_pos.x, self.player_pos.y, 0)
            delta = target - Vec3(pos.x, pos.y, 0)
            distance = delta.length()
            if distance > 0.001:
                delta.normalize()
            if distance > 2.0:
                pos.x += delta.x * enemy["speed"] * dt
                pos.y += delta.y * enemy["speed"] * dt
                node.setPos(pos)
                node.setH(math.degrees(math.atan2(delta.x, delta.y)))
            enemy["attack"] -= dt
            if distance < 2.3 and enemy["attack"] <= 0:
                self._damage_player(8 + self.level * 0.5)
                enemy["attack"] = 1.0
            if enemy["hit_flash"] > 0:
                enemy["hit_flash"] -= dt

    def _update_pickups(self, dt):
        for pickup in self.pickups:
            pickup["phase"] += dt * 2.5
            node = pickup["node"]
            p = node.getPos()
            node.setZ(0.8 + math.sin(pickup["phase"]) * 0.18)
            node.setH(node.getH() + 70 * dt)

    def _update_hud(self):
        weapon_names = {1: "PLASMA", 2: "HEAVY", 3: "RAPID"}
        boss = next((e for e in self.enemies if e.get("boss")), None)
        boss_line = f"\nTITAN SENTINEL {int(max(0, boss['hp']))}/{int(boss['max_hp'])}" if boss else ""
        self.hud.setText(
            f"HP {int(self.health):03d}   ARMOR {int(self.armor):03d}\n"
            f"AMMO {self.ammo:03d}   LVL {self.level}   WEAPON {weapon_names[self.weapon_mode]}\n"
            f"SCORE {self.score:06d}   CREDITS {self.credits:04d}   BEST {getattr(self, 'best_score', 0):06d}{boss_line}"
        )
        self.mission_text.setText(f"MISSION: HOSTILES {self.mission_kills}/{self.mission_target}   |   KILLS {self.kills}")

    def update(self, task):
        dt = min(ClockObject.getGlobalClock().getDt(), 0.05)
        if self.started and not self.paused and not self.game_over:
            self.elapsed += dt
            self.shot_cooldown = max(0, self.shot_cooldown - dt)
            self._update_mouse_aim()
            self._update_player(dt)
            if self.keys["space"]:
                self._shoot()
            self._update_bullets(dt)
            self._update_enemies(dt)
            self._update_pickups(dt)
            self.enemy_spawn_timer += dt
            if self.enemy_spawn_timer >= max(1.5, 4.5 - self.level * 0.15) and len(self.enemies) < 10 + self.level:
                self._spawn_enemy()
                self.enemy_spawn_timer = 0
            if self.dash_time > 0:
                self.dash_time = max(0.0, self.dash_time - dt)
            self.dash_cooldown = max(0.0, self.dash_cooldown - dt)
            if self.mission_kills >= 4 and not self.boss_spawned:
                self._spawn_enemy(boss=True)
                self.boss_spawned = True
            if int(self.elapsed) % 20 == 0 and int(self.elapsed) > 0:
                # Tiny passive recovery keeps the mission playable without trivializing combat.
                self.health = min(100, self.health + dt * 0.4)
        self._update_hud()
        return Task.cont

    def _load_save(self):
        try:
            if SAVE_FILE.exists():
                data = json.loads(SAVE_FILE.read_text(encoding="utf-8"))
                self.best_score = max(0, int(data.get("best_score", 0)))
                self.total_kills = max(0, int(data.get("total_kills", 0)))
            else:
                self.best_score = 0
                self.total_kills = 0
        except (OSError, ValueError, TypeError):
            self.best_score = 0
            self.total_kills = 0

    def _save_game(self):
        try:
            data = {"best_score": max(getattr(self, "best_score", 0), self.score),
                    "total_kills": getattr(self, "initial_total_kills", 0) + self.kills,
                    "last_score": self.score, "last_level": self.level}
            self.best_score = data["best_score"]
            self.total_kills = data["total_kills"]
            self.initial_total_kills = self.total_kills - self.kills
            SAVE_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
        except OSError:
            pass


if __name__ == "__main__":
    app = ShadowLegends()
    app.run()
