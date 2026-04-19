BUILTIN_MACROS = [
    {
        "name": "morning",
        "description": "Start your day — home screen, launch Netflix",
        "commands": "home\nlaunch Netflix",
    },
    {
        "name": "movie-night",
        "description": "Mute, go home, launch Netflix",
        "commands": "home\nmute\nlaunch Netflix",
    },
    {
        "name": "sleep-timer",
        "description": "Lower volume five times then power off",
        "commands": (
            "volume down\nvolume down\nvolume down\n"
            "volume down\nvolume down\npower"
        ),
    },
    {
        "name": "binge",
        "description": "Home, launch Netflix, select first item",
        "commands": "home\nlaunch Netflix\nselect",
    },
    {
        "name": "mute-toggle",
        "description": "Toggle mute",
        "commands": "mute",
    },
    {
        "name": "channel-surf",
        "description": "Navigate featured content rows",
        "commands": "up\nup\nup\nselect",
    },
]
