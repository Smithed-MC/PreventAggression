team add smithed.prevent_aggression "smithed.p_aggro"
team modify smithed.prevent_aggression friendlyFire false

schedule function smithed:prevent_aggression/technical/10_tick 10t replace
