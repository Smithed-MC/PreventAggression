team add smithed.prevent_aggression "smithed.p_aggro"
team modify smithed.prevent_aggression friendlyFire false

schedule function smithed:prevent_aggression/impl/__version__/technical/10_tick 10t replace
