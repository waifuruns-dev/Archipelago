"""
Out-of-mission (backtracking) logic, enabled by the "Out of Mission Checks" option.

Some checks can also be collected from a later mission that reaches their rooms. Each such
location is moved into its own small region, entered either from its own mission (with the
requirements to get there in that mission) or from each later mission that reaches it (with
that route's requirements). Requirements that apply wherever you come from (adjudicator
weapon, a secret mission's challenge requirements, moves needed at the spot itself) stay on
the location.

Routes were tested in game on 2026-11-17 (Explore seed, everything unlocked). Weapon
pickups that only appear when you don't own the weapon (Artemis' Mission 16 spawn) are not
included.
"""
from typing import Callable, Optional

from BaseClasses import Region, CollectionState

Rule = Optional[Callable[[CollectionState, object], bool]]


def _has(item: str) -> Callable:
    return lambda state, world: state.has(item, world.player)


def _reach(location: str) -> Callable:
    return lambda state, world: state.can_reach_location(location, world.player)


ORIHALCON = _has("Orihalcon Fragment")
# Mission 19: you can't leave the second room without slotting in the Samsara
SAMSARA = _has("Samsara")

# location: (own mission, rule to reach it within its own mission, {later mission: route rule})
OUT_OF_MISSION_ROUTES: dict[str, tuple[int, Rule, dict[int, Rule]]] = {
    # Mission 3
    "Mission #3 - Blue Orb Fragment #1": (3, None, {4: None, 5: None, 7: ORIHALCON}),
    "Mission #3 - Combat Adjudicator #1": (3, None, {4: None, 5: None, 7: ORIHALCON}),
    "Secret Mission #1": (3, None, {4: None, 5: None, 7: ORIHALCON}),
    # Mission 4
    "Mission #4 - Blue Orb Fragment #2": (4, None, {5: None}),
    # Mission 5
    "Mission #5 - Combat Adjudicator #2": (5, _has("Soul of Steel"), {7: ORIHALCON}),
    "Secret Mission #2": (5, _has("Soul of Steel"), {7: ORIHALCON}),
    # Mission 6
    "Mission #6 - Combat Adjudicator #3": (
        6, lambda state, world: state.has_group_unique("essences", world.player, 2), {7: None}),
    # Mission 9
    "Mission #9 - Blue Orb Fragment #5": (9, None, {10: None}),
    "Mission #9 - Devil Star": (9, None, {10: None, 14: None, 16: None, 19: SAMSARA}),
    "Secret Mission #5": (9, None, {10: None, 14: None, 16: None, 19: SAMSARA}),
    "Mission #9 - Combat Adjudicator #6": (9, None, {10: None}),
    "Mission #9 - Spiral": (9, None, {10: None}),
    # Mission 11
    "Mission #11 - Devil Star": (11, None, {12: None, 14: None, 16: None, 19: SAMSARA}),
    "Mission #11 - Holy Water": (11, None, {12: None, 14: None, 16: None, 19: SAMSARA}),
    "Mission #11 - Blue Orb Fragment #6": (11, None, {12: None, 14: None, 16: None, 19: SAMSARA}),
    "Mission #11 - Combat Adjudicator #7": (11, None, {12: None, 14: None, 16: None, 19: SAMSARA}),
    "Secret Mission #7": (11, None, {12: None, 14: None, 16: None, 19: SAMSARA}),
    # Mission 13
    "Secret Mission #9": (13, None, {14: None, 16: None, 19: SAMSARA}),
    # Mission 14 (past the adjudicator in its own mission)
    "Mission #14 - Combat Adjudicator #9": (14, _reach("Mission #14 - Beowulf"), {15: None, 16: None, 19: SAMSARA}),
    "Mission #14 - Vital Star S": (14, _reach("Mission #14 - Combat Adjudicator #9"), {15: None, 16: None, 19: SAMSARA}),
    "Mission #14 - Vital Star S #2": (14, _reach("Mission #14 - Combat Adjudicator #9"), {15: None, 16: None, 19: SAMSARA}),
    "Mission #14 - Blue Orb Fragment #7": (14, _reach("Mission #14 - Combat Adjudicator #9"), {15: None, 16: None, 19: SAMSARA}),
    # Mission 15
    "Mission #15 - Blue Orb Fragment #8": (15, None, {16: None, 19: SAMSARA}),
    # Mission 16 (past the Golden Sun + Onyx Moonshard door in its own mission)
    "Mission #16 - Vital Star S": (
        16, lambda state, world: state.has_all(("Golden Sun", "Onyx Moonshard"), world.player), {19: SAMSARA}),
    "Secret Mission #10": (16, None, {19: SAMSARA}),
    # Mission 17
    "Mission #17 - Vital Star S": (17, None, {18: None, 19: SAMSARA}),
    "Mission #17 - Combat Adjudicator #10": (17, None, {18: None, 19: SAMSARA}),
    "Secret Mission #11": (17, None, {18: None, 19: SAMSARA}),
    # Mission 18
    "Secret Mission #12": (18, None, {19: SAMSARA}),
}


def _area_name(location: str) -> str:
    return f"{location} (area)"


def _entrance_name(mission: int, location: str) -> str:
    return f"Mission #{mission} -> {_area_name(location)}"


def create_out_of_mission_regions(world) -> None:
    """Move each backtrackable location into its own region with one entrance per route."""
    multiworld, player = world.multiworld, world.player
    for location_name, (own_mission, _, routes) in OUT_OF_MISSION_ROUTES.items():
        location = multiworld.get_location(location_name, player)
        # Remove it from whichever region lists it (secret missions sit in their own region)
        for region in multiworld.get_regions(player):
            if location in region.locations:
                region.locations.remove(location)
                break
        area = Region(_area_name(location_name), player, multiworld)
        location.parent_region = area
        area.locations.append(location)
        multiworld.regions.append(area)
        own_region = multiworld.get_region(f"Mission #{own_mission}", player)
        own_region.connect(area, _entrance_name(own_mission, location_name))
        for later_mission in routes:
            later_region = multiworld.get_region(f"Mission #{later_mission}", player)
            later_region.connect(area, _entrance_name(later_mission, location_name))


def set_out_of_mission_rules(world) -> None:
    """
    Called after all other rules are set. The requirement to reach a location within its own
    mission moves from the location to its own-mission entrance; later-mission entrances get
    their route rule. Requirements that apply on every route stay on the location.
    """
    from .Rules import has_air_hike, has_sky_star, can_dt_fly, has_skill, has_devil_trigger, \
        dt_rune_count, has_style

    multiworld, player = world.multiworld, world.player

    # Requirements at the spot itself, no matter which mission you came from
    on_location: dict[str, Callable] = {
        "Mission #9 - Blue Orb Fragment #5":
            lambda state: (has_air_hike(state, world) and has_sky_star(state, world)) or can_dt_fly(state, world),
        "Secret Mission #7":
            lambda state: has_skill(state, world, "Rebellion", "Progressive Stinger", 2)
                          or state.has("Ebony & Ivory", player)
                          or (has_devil_trigger(state, world) and dt_rune_count(state, world) >= 8),
        "Secret Mission #9":
            lambda state: (state.has("Spiral", player) and has_style(state, world, "Royalguard"))
                          or (state.has("Ebony & Ivory", player) and has_style(state, world, "Gunslinger")),
        "Secret Mission #12":
            lambda state: (has_air_hike(state, world) and has_sky_star(state, world)) or can_dt_fly(state, world),
    }
    for adjudicator, data in world.adjudicator_generated_values.items():
        if adjudicator in OUT_OF_MISSION_ROUTES:
            on_location[adjudicator] = lambda state, weapon=data.weapon: state.has(weapon, player)

    for location_name, (own_mission, own_rule, routes) in OUT_OF_MISSION_ROUTES.items():
        location = multiworld.get_location(location_name, player)
        location.access_rule = on_location.get(location_name, lambda state: True)

        own_entrance = multiworld.get_entrance(_entrance_name(own_mission, location_name), player)
        if own_rule is not None:
            own_entrance.access_rule = lambda state, rule=own_rule: rule(state, world)
        for later_mission, route_rule in routes.items():
            if route_rule is not None:
                entrance = multiworld.get_entrance(_entrance_name(later_mission, location_name), player)
                entrance.access_rule = lambda state, rule=route_rule: rule(state, world)

    # Mission 14's checks past the adjudicator depend on the adjudicator's (now separate) region
    adjudicator_area = multiworld.get_region(_area_name("Mission #14 - Combat Adjudicator #9"), player)
    for location_name in ("Mission #14 - Vital Star S", "Mission #14 - Vital Star S #2",
                          "Mission #14 - Blue Orb Fragment #7"):
        multiworld.register_indirect_condition(
            adjudicator_area, multiworld.get_entrance(_entrance_name(14, location_name), player))
    # "Mission #14 Complete" also needs the adjudicator, and the mission order entrances out of
    # Mission 14 depend on that location
    for entrance in multiworld.get_region("Mission #14", player).exits:
        if entrance.connected_region and entrance.connected_region.name.startswith("Mission #"):
            multiworld.register_indirect_condition(adjudicator_area, entrance)
