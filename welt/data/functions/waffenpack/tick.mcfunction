scoreboard players tag @a remove wp_p
scoreboard players tag @a remove wp_b
scoreboard players tag @a add wp_p {SelectedItem:{tag:{wp:1b}}}
scoreboard players tag @a add wp_b {SelectedItem:{tag:{wp:2b}}}
execute @a[tag=wp_p] ~ ~ ~ scoreboard players tag @e[type=arrow,r=6,tag=!wp_alt] add wp_p
execute @a[tag=wp_b] ~ ~ ~ scoreboard players tag @e[type=arrow,r=6,tag=!wp_alt] add wp_b
scoreboard players tag @e[type=arrow] add wp_alt
entitydata @e[type=arrow,tag=wp_p] {damage:2048d}
entitydata @e[type=arrow,tag=wp_b] {damage:2048d}
scoreboard players tag @e[type=arrow,tag=wp_b] add wp_boom {inGround:1b}
execute @e[type=arrow,tag=wp_boom] ~ ~ ~ summon tnt ~ ~ ~ {Fuse:0}
kill @e[type=arrow,tag=wp_boom]
