from BaseClasses import MultiWorld
from ..dmc3 import adjudicators
from . import Locations
from ..generic.Rules import add_rule, add_item_rule


def has_air_hike(state, world) -> bool:
    for melee in world.item_name_groups["air_hike_capable"]:
        if state.has(melee, world.player):
            # If rando skills isn't on, it'll have to be bought. Otherwise, check to see if the weapon has air hike unlocked
            if world.options.randomize_skills:
                if state.has(f"{melee} - Air Hike", world.player):
                    return True
            else:
                return True

    return False


def has_air_raid(state, world) -> bool:
    if state.has("Nevan", world.player):
        if world.options.randomize_skills:
            return state.has("Nevan - Air Raid", world.player)
        else:
            return True
    return False


def has_sky_star(state, world) -> bool:
    # Lv2 Trickster gives Sky Star, if randomized styles is off, player will have to level Trickster
    return has_style(state, world, "Trickster", 2)


def has_style(state, world, style: str, level: int = 1) -> bool:
    # With styles not randomized, every style is available (and can be leveled) from the start
    if world.options.randomize_styles:
        return state.has(f"Progressive {style}", world.player, count=level)
    return True


def has_skill(state, world, weapon: str, skill: str, level: int = 1) -> bool:
    # The weapon itself is always needed. With skills not randomized, the skill can be bought.
    if not state.has(weapon, world.player):
        return False
    if world.options.randomize_skills:
        return state.has(f"{weapon} - {skill}", world.player, count=level)
    return True


def dt_rune_count(state, world) -> int:
    # Purple Orb Mode on: runes = purple orbs. Off: the Devil Trigger item gives 3 runes, +1 per purple orb.
    runes = state.count("Purple Orb", world.player)
    if not world.options.purple_orb_mode and state.has("Devil Trigger", world.player):
        runes += 3
    return runes


def can_dt_fly(state, world) -> bool:
    # Reach high places by flying in Devil Trigger: DT with Rebellion, or DT with Nevan's Air Raid
    return has_devil_trigger(state, world) and (state.has("Rebellion", world.player) or has_air_raid(state, world))


def has_devil_trigger(state, world) -> bool:
    if world.options.devil_trigger_mode:
        dt = state.has("Devil Trigger", world.player)
    else:
        # DT is 'always' accessible, just needs 3 runes
        dt = True
    if world.options.purple_orb_mode:
        orbs = state.has("Purple Orb", world.player, count=3)
    else:
        orbs = (state.has("Purple Orb", world.player, count=3) or state.has("Devil Trigger",
                                                                            world.player))
    return dt and orbs


def all_missions_complete(state, world) -> bool:
    for idx in range(1, 21):
        if not state.can_reach_location(f"Mission #{idx} Complete", world.player):
            return False
    return True


# For linear mission orders
def add_mission_order_rules(world):
    for idx in range(19):
        mission_idx = world.dmc3_mission_order[idx]
        add_rule(
            world.multiworld.get_entrance(f"Mission #{mission_idx} -> Mission #{world.dmc3_mission_order[idx + 1]}",
                                          world.player),
            lambda state, i=mission_idx: state.can_reach_location(f"Mission #{i} Complete", world.player)
        )
        world.multiworld.register_indirect_condition(
            world.multiworld.get_region(f"Mission #{mission_idx}", world.player),
            world.multiworld.get_entrance(
                f"Mission #{mission_idx} -> Mission #{world.dmc3_mission_order[idx + 1]}",
                world.player)
            )


# Generic Location rules, independent of goal
def add_generic_rules(world):
    # Across the pit that needs the soul of steel to cross
    add_rule(world.multiworld.get_location("Mission #5 - Combat Adjudicator #2", world.player),
             lambda state: state.has("Soul of Steel", world.player))

    # Above the goddess statue: Air Hike + Sky Star, or fly up in DT
    add_rule(world.multiworld.get_location("Mission #9 - Blue Orb Fragment #5", world.player),
             lambda state: (has_air_hike(state, world) and has_sky_star(state, world)) or can_dt_fly(state, world))

    # Extra insurance, even if it may be un-needed. Both locations are in the same room.
    add_rule(world.multiworld.get_location("Mission #14 - Combat Adjudicator #9", world.player),
             lambda state: state.can_reach_location("Mission #14 - Beowulf", world.player))
    # All of these M14 Checks are past the adjudicator
    add_rule(world.multiworld.get_location("Mission #14 - Vital Star S", world.player),
             lambda state: state.can_reach_location("Mission #14 - Combat Adjudicator #9", world.player))
    add_rule(world.multiworld.get_location("Mission #14 - Vital Star S #2", world.player),
             lambda state: state.can_reach_location("Mission #14 - Combat Adjudicator #9", world.player))
    add_rule(world.multiworld.get_location("Mission #14 - Blue Orb Fragment #7", world.player),
             lambda state: state.can_reach_location("Mission #14 - Combat Adjudicator #9", world.player))
    add_rule(world.multiworld.get_location("Mission #14 - Holy Water", world.player),
             lambda state: state.can_reach_location("Mission #14 - Combat Adjudicator #9", world.player))
    # Astronomical board removes the walls blocking access
    add_rule(world.multiworld.get_location("Mission #5 - Vajura", world.player),
             lambda state: state.has("Astronomical Board", world.player))

    # Vajura opens the cage to access this check
    add_rule(world.multiworld.get_location("Mission #5 - Soul of Steel", world.player),
             lambda state: state.has("Vajura", world.player))

    # Across the pit that needs the soul of steel to cross
    add_rule(world.multiworld.get_location("Mission #5 - Agni and Rudra", world.player),
             lambda state: state.has("Soul of Steel", world.player))

    # Adjudicator is right outside the door you blast open with the laser
    add_rule(world.multiworld.get_location("Mission #6 - Combat Adjudicator #3", world.player),
             lambda state: state.has_group_unique("essences", world.player, 2))

    # Needed to dispel the flames blocking the door to this room
    add_rule(world.multiworld.get_location("Mission #7 - Crystal Skull", world.player),
             lambda state: state.has("Siren's Shriek", world.player) and state.has("Orihalcon Fragment", world.player))

    # Slots into door leading to Nevan
    add_rule(world.multiworld.get_location("Mission #9 - Nevan", world.player),
             lambda state: state.has("Ambrosia", world.player))

    # Stone Mask is needed to raise a bridge to the platform that leads to the Neo Generator and SM6
    add_rule(world.multiworld.get_location("Mission #10 - Neo Generator", world.player),
             lambda state: state.has("Stone Mask", world.player))

    add_rule(world.multiworld.get_location("Mission #12 - Quicksilver", world.player),
             lambda state: state.has("Haywire Neo Generator", world.player))

    # Lady Boss fight is past the Golden Sun and Onyx Moonshard door
    add_rule(world.multiworld.get_location("Mission #16 - Kalina Ann", world.player),
             lambda state: state.has("Golden Sun", world.player) and state.has("Onyx Moonshard", world.player))

    # Past the door that needs those two key items
    add_rule(world.multiworld.get_location("Mission #16 - Vital Star S", world.player),
             lambda state: state.has("Golden Sun", world.player) and state.has("Onyx Moonshard", world.player))

    # Statue needs all 3 essences to lower down artemis
    add_rule(world.multiworld.get_location("Mission #6 - Artemis", world.player),
             lambda state: state.has_group_unique("essences", world.player, 3))

    # Need Soul of Steel to cross the pit and open the door
    add_rule(world.multiworld.get_location("Secret Mission #2", world.player),
             lambda state: state.has("Soul of Steel", world.player))

    # Flight of the Demon: fly in DT with Rebellion or Air Raid Nevan (Needs Stone Mask to raise bridge leading to it)
    add_rule(world.multiworld.get_location("Secret Mission #6", world.player),
             lambda state: state.has("Stone Mask", world.player) and can_dt_fly(state, world))

    # SM7: Stinger Lv2, or Ebony & Ivory, or DT with at least 8 runes
    add_rule(world.multiworld.get_location("Secret Mission #7", world.player),
             lambda state: has_skill(state, world, "Rebellion", "Progressive Stinger", 2)
                           or state.has("Ebony & Ivory", world.player)
                           or (has_devil_trigger(state, world) and dt_rune_count(state, world) >= 8))

    # SM9: Spiral with Royalguard, or Ebony & Ivory with Gunslinger
    add_rule(world.multiworld.get_location("Secret Mission #9", world.player),
             lambda state: (state.has("Spiral", world.player) and has_style(state, world, "Royalguard"))
                           or (state.has("Ebony & Ivory", world.player) and has_style(state, world, "Gunslinger")))

    # SM12: Air Hike + Sky Star, or fly up in DT
    add_rule(world.multiworld.get_location("Secret Mission #12", world.player),
             lambda state: (has_air_hike(state, world) and has_sky_star(state, world)) or can_dt_fly(state, world))


# What location needs to be reached/items are needed to finish a mission
def add_mission_complete_rules(world):
    # Mission goal is to beat Agni and Rudra
    add_rule(world.multiworld.get_location("Mission #5 Complete", world.player),
             lambda state: state.can_reach_location("Mission #5 - Agni and Rudra", world.player))

    # Statue laser needs 2 essences
    add_rule(world.multiworld.get_location("Mission #6 Complete", world.player),
             lambda state: state.has_group_unique("essences", world.player, 2))

    # Opens the door leading to Vergil's Arena
    add_rule(world.multiworld.get_location("Mission #7 Complete", world.player),
             lambda state: state.has("Crystal Skull", world.player))

    # Open 'door' to leviathan heartcore
    add_rule(world.multiworld.get_location("Mission #8 Complete", world.player),
             lambda state: state.has("Ignis Fatuus", world.player))

    # Mission goal is to beat Nevan
    add_rule(world.multiworld.get_location("Mission #9 Complete", world.player),
             lambda state: state.can_reach_location("Mission #9 - Nevan", world.player))

    # Neo generator rotates a bridge leading to the end of the mission
    add_rule(world.multiworld.get_location("Mission #10 Complete", world.player),
             lambda state: state.has("Neo Generator", world.player))

    # Mission goal is to beat Geryon
    add_rule(world.multiworld.get_location("Mission #12 Complete", world.player),
             lambda state: state.can_reach_location("Mission #12 - Quicksilver", world.player))

    # Needed to open the door to Vergil 2
    add_rule(world.multiworld.get_location("Mission #13 Complete", world.player),
             lambda state: state.has("Full Orihalcon", world.player))

    # This one blocks the door in M14 because it's to make sure you have beowulf (in vanilla)
    add_rule(world.multiworld.get_location("Mission #14 Complete", world.player),
             lambda state: state.can_reach_location("Mission #14 - Combat Adjudicator #9", world.player))

    # Elevator needs all 3 fragments
    add_rule(world.multiworld.get_location("Mission #15 Complete", world.player),
             lambda state: state.has_group_unique("fragments", world.player, 3))

    # Door needs both to be slotted in
    add_rule(world.multiworld.get_location("Mission #16 Complete", world.player),
             lambda state: state.can_reach_location("Mission #16 - Kalina Ann", world.player))

    # Stuck in a loop without the Samsara being slotted in
    add_rule(world.multiworld.get_location("Mission #19 Complete", world.player),
             lambda state: state.has("Samsara", world.player))


def add_gun_shop_rules(world):
    for gun in world.item_name_groups["guns"]:
        add_rule(world.multiworld.get_location(f"Purchase {gun} Level 2", world.player),
                 lambda state, gun_name=gun: state.has(gun_name, world.player))
        add_rule(world.multiworld.get_location(f"Purchase {gun} Level 3", world.player),
                 lambda state, gun_name=gun: state.has(gun_name, world.player))


# Shop checks cost red orbs, which logic doesn't track, so early on they're effectively out of reach.
# With a mission order (Standard / Random Order goals), shop checks only count as reachable once this
# many missions of the order are completed, so nothing needed to get through them can be in the shop.
SHOP_AFTER_MISSIONS = 3


def add_shop_balancing_rules(world):
    last_early_mission = world.dmc3_mission_order[SHOP_AFTER_MISSIONS - 1]
    shop_location_names = {name for name in Locations.default_shop_locations} | \
                          {name for name in Locations.gun_level_purchases} | \
                          {name for name in Locations.weapon_skill_purchases}
    for location in world.multiworld.get_locations(world.player):
        if location.name in shop_location_names:
            add_rule(location,
                     lambda state, mission=last_early_mission:
                     state.can_reach_location(f"Mission #{mission} Complete", world.player))


def add_skill_shop_rules(world):
    """Skill purchases need their weapon, and a level 2 purchase needs the level 1 purchase first."""
    player = world.player
    for name, (weapon, previous) in Locations.SKILL_PURCHASE_NAMES.items():
        location = world.multiworld.get_location(f"Purchase {name}", player)
        add_rule(location, lambda state, w=weapon: state.has(w, player))
        if previous:
            add_rule(location,
                     lambda state, p=f"Purchase {previous}": state.can_reach_location(p, player))


def set_dmc3_rules(dmc3_world) -> None:
    if dmc3_world.options.goal.value != 1:
        add_mission_order_rules(dmc3_world)
    add_generic_rules(dmc3_world)
    add_mission_complete_rules(dmc3_world)
    if dmc3_world.options.shop_gun_checks:
        add_gun_shop_rules(dmc3_world)
    if dmc3_world.options.shop_skill_checks and dmc3_world.options.randomize_skills:
        add_skill_shop_rules(dmc3_world)
    # Not used with the All goal: every mission is open from the start, so there's no "first" missions
    if dmc3_world.options.goal.value != dmc3_world.options.goal.option_all:
        add_shop_balancing_rules(dmc3_world)

    # For allowing SS Checks to have useful or filler
    if dmc3_world.options.enabled_ss_rank and dmc3_world.options.useful_ss_checks:
        for i in range(1, 21):
            ss_mission_name = f"Mission #{i} SS Rank"
            if ss_mission_name in dmc3_world.options.exclude_locations.value:
                add_item_rule(dmc3_world.multiworld.get_location(ss_mission_name, dmc3_world.player),
                              lambda item: not item.advancement)
                dmc3_world.options.exclude_locations.value.discard(ss_mission_name)

    all_difficulties = ["Easy", "Normal", "Hard", "Very Hard", "Dante Must Die", "Heaven or Hell"]
    # Figure what the max initial difficulty is
    max_diff = 0
    for diff in dmc3_world.options.initially_unlocked_difficulties.value:
        if all_difficulties.index(diff) > max_diff:
            max_diff = all_difficulties.index(diff)

    # If the minimum difficulty is not possible with the initially unlocked difficulties.
    # Then all mission complete checks need to have non prog items
    if dmc3_world.options.mission_clear_difficulty.value > max_diff:
        for i in range(1, 21):
            complete_mission_name = f"Mission #{i} Complete"
            add_item_rule(dmc3_world.multiworld.get_location(complete_mission_name, dmc3_world.player),
                          lambda item: not item.advancement)
            # If SS Rank checks also require a min. difficulty. Then the same rule applies to them
            if dmc3_world.options.enabled_ss_rank and dmc3_world.options.check_ss_difficulty:
                ss_mission_name = f"Mission #{i} SS Rank"
                add_item_rule(dmc3_world.multiworld.get_location(ss_mission_name, dmc3_world.player),
                              lambda item: not item.advancement)

    # Set rule for reaching goal
    if dmc3_world.options.goal.value != 1:
        add_rule(dmc3_world.multiworld.get_location("Final Mission", dmc3_world.player), lambda state:
        state.can_reach_location(f"Mission #{dmc3_world.dmc3_mission_order[19]} Complete", dmc3_world.player)),
    else:
        add_rule(dmc3_world.multiworld.get_location("Final Mission", dmc3_world.player), lambda state:
        all_missions_complete(state, dmc3_world))

    # Adjudicator rules
    for adjudicator in adjudicators:
        weapon = dmc3_world.adjudicator_generated_values[adjudicator].weapon
        location = dmc3_world.multiworld.get_location(adjudicator, dmc3_world.player)
        add_rule(location,
                 lambda state, wep=weapon:
                 state.has(wep, dmc3_world.player))

    # Backtracking routes: must run after every other location rule is set
    if dmc3_world.options.out_of_mission_checks:
        from .OutOfMission import set_out_of_mission_rules
        set_out_of_mission_rules(dmc3_world)

    dmc3_world.multiworld.completion_condition[dmc3_world.player] = lambda state: state.has("Complete",
                                                                                            dmc3_world.player)
    # visualize_regions(self.multiworld.get_region("Menu", self.player), "my_world.puml")
