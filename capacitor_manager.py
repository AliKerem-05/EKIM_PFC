import math

# Katalogdan çıkarılan tam veritabanı
capacitors_db = [
    # --- 250V ---
    {"cap": 100, "volt": 250, "dim": "25x30", "base_ripple": 0.7, "part": "K05250101_PM0C030"},
    {"cap": 150, "volt": 250, "dim": "25x30", "base_ripple": 0.7, "part": "K05250151_PM0C030"},
    {"cap": 220, "volt": 250, "dim": "25x30", "base_ripple": 0.9, "part": "K05250221_PM0C030"},
    {"cap": 330, "volt": 250, "dim": "30x30", "base_ripple": 1.2, "part": "K05250331_PM0D030"},
    {"cap": 470, "volt": 250, "dim": "25x40", "base_ripple": 1.5, "part": "K05250471_PM0C040"},
    {"cap": 470, "volt": 250, "dim": "30x30", "base_ripple": 1.5, "part": "K05250471_PM0D030"},
    {"cap": 680, "volt": 250, "dim": "35x40", "base_ripple": 1.8, "part": "K05250681_PM0E040"},
    {"cap": 1000, "volt": 250, "dim": "35x40", "base_ripple": 2.0, "part": "K05250102_PM0E040"},
    {"cap": 1000, "volt": 250, "dim": "35x50", "base_ripple": 2.6, "part": "K05250102_PM0E050"},
    {"cap": 1500, "volt": 250, "dim": "35x50", "base_ripple": 2.8, "part": "K05250152_PM0E050"},

    # --- 400V ---
    {"cap": 68, "volt": 400, "dim": "22x30", "base_ripple": 0.47, "part": "K05400680_PM0B030"},
    {"cap": 100, "volt": 400, "dim": "22x30", "base_ripple": 0.5, "part": "K05400101_PM0B030"},
    {"cap": 100, "volt": 400, "dim": "25x30", "base_ripple": 0.5, "part": "K05400101_PM0C030"},
    {"cap": 150, "volt": 400, "dim": "25x30", "base_ripple": 0.6, "part": "K05400151_PM0C030"},
    {"cap": 150, "volt": 400, "dim": "30x30", "base_ripple": 0.8, "part": "K05400151_PM0D030"},
    {"cap": 220, "volt": 400, "dim": "25x40", "base_ripple": 1.0, "part": "K05400221_PM0C040"},
    {"cap": 220, "volt": 400, "dim": "30x30", "base_ripple": 1.1, "part": "K05400221_PM0D030"},
    {"cap": 270, "volt": 400, "dim": "25x40", "base_ripple": 1.2, "part": "K05400271_PM0C040"},
    {"cap": 330, "volt": 400, "dim": "25x45", "base_ripple": 1.3, "part": "K05400331_PM0C045"},
    {"cap": 330, "volt": 400, "dim": "30x40", "base_ripple": 1.4, "part": "K05400331_PM0D040"},
    {"cap": 330, "volt": 400, "dim": "35x30", "base_ripple": 1.4, "part": "K05400331_PM0E030"},
    {"cap": 470, "volt": 400, "dim": "30x50", "base_ripple": 1.9, "part": "K05400471_PM0D050"},
    {"cap": 470, "volt": 400, "dim": "35x40", "base_ripple": 1.9, "part": "K05400471_PM0E040"},
    {"cap": 470, "volt": 400, "dim": "35x50", "base_ripple": 2.2, "part": "K05400471_PM0E050"},
    {"cap": 680, "volt": 400, "dim": "35x50", "base_ripple": 2.2, "part": "K05400681_PM0E050"},
    {"cap": 680, "volt": 400, "dim": "40x50", "base_ripple": 2.4, "part": "K05400681_PM0F050"},
    {"cap": 820, "volt": 400, "dim": "35x60", "base_ripple": 2.5, "part": "K05400821_PM0E060"},
    {"cap": 1000, "volt": 400, "dim": "40x60", "base_ripple": 3.1, "part": "K05400102_PM0F060"},
    {"cap": 1500, "volt": 400, "dim": "40x97", "base_ripple": 5.8, "part": "K05400152_PM0F097"},

    # --- 450V ---
    {"cap": 68, "volt": 450, "dim": "22x30", "base_ripple": 0.47, "part": "K05450680_PM0B030"},
    {"cap": 100, "volt": 450, "dim": "25x30", "base_ripple": 0.5, "part": "K05450101_PM0C030"},
    {"cap": 100, "volt": 450, "dim": "30x25", "base_ripple": 0.7, "part": "K05450101_PM0D025"},
    {"cap": 100, "volt": 450, "dim": "30x30", "base_ripple": 0.8, "part": "K05450101_PM0D030"},
    {"cap": 150, "volt": 450, "dim": "25x40", "base_ripple": 0.9, "part": "K05450151_PM0C040"},
    {"cap": 150, "volt": 450, "dim": "30x30", "base_ripple": 0.8, "part": "K05450151_PM0D030"},
    {"cap": 150, "volt": 450, "dim": "30x40", "base_ripple": 1.0, "part": "K05450151_PM0D040"},
    {"cap": 220, "volt": 450, "dim": "25x50", "base_ripple": 0.9, "part": "K05450221_PM0C050"},
    {"cap": 220, "volt": 450, "dim": "30x40", "base_ripple": 1.1, "part": "K05450221_PM0D040"},
    {"cap": 220, "volt": 450, "dim": "35x30", "base_ripple": 1.0, "part": "K05450221_PM0E030"},
    {"cap": 330, "volt": 450, "dim": "30x50", "base_ripple": 1.25, "part": "K05450331_PM0D050"},
    {"cap": 330, "volt": 450, "dim": "35x40", "base_ripple": 1.3, "part": "K05450331_PM0E040"},
    {"cap": 330, "volt": 450, "dim": "35x50", "base_ripple": 1.4, "part": "K05450331_PM0E050"},
    {"cap": 470, "volt": 450, "dim": "35x50", "base_ripple": 1.8, "part": "K05450471_PM0E050"},
    {"cap": 680, "volt": 450, "dim": "35x50", "base_ripple": 2.1, "part": "K05450681_PM0E050"},
    {"cap": 680, "volt": 450, "dim": "35x60", "base_ripple": 2.2, "part": "K05450681_PM0E060"},
    {"cap": 820, "volt": 450, "dim": "40x60", "base_ripple": 2.3, "part": "K05450821_PM0F060"},
    {"cap": 1000, "volt": 450, "dim": "40x60", "base_ripple": 3.2, "part": "K05450102_PM0F060"},
    {"cap": 1500, "volt": 450, "dim": "40x97", "base_ripple": 5.1, "part": "K05450152_PM0F097"},

    # --- 500V ---
    {"cap": 68, "volt": 500, "dim": "25x30", "base_ripple": 0.42, "part": "K05500680_PM0C030"},
    {"cap": 100, "volt": 500, "dim": "30x30", "base_ripple": 0.55, "part": "K05500101_PM0D030"},
    {"cap": 150, "volt": 500, "dim": "30x40", "base_ripple": 0.75, "part": "K05500151_PM0D040"},
    {"cap": 180, "volt": 500, "dim": "30x50", "base_ripple": 0.90, "part": "K05500181_PM0D050"},
    {"cap": 220, "volt": 500, "dim": "35x40", "base_ripple": 0.95, "part": "K05500221_PM0E040"},
    {"cap": 270, "volt": 500, "dim": "35x50", "base_ripple": 1.60, "part": "K05500271_PM0E050"},
    {"cap": 330, "volt": 500, "dim": "35x50", "base_ripple": 1.65, "part": "K05500331_PM0E050"},
    {"cap": 330, "volt": 500, "dim": "35x60", "base_ripple": 1.78, "part": "K05500331_PM0E060"},
    {"cap": 330, "volt": 500, "dim": "40x50", "base_ripple": 1.80, "part": "K05500331_PM0F050"},
    {"cap": 470, "volt": 500, "dim": "40x60", "base_ripple": 2.00, "part": "K05500471_PM0F060"}
]

def get_multipliers(temp, freq):
    """Sıcaklık ve frekansa göre çarpanları döner."""
    t_mult = 1.0
    if temp <= 35: t_mult = 3.0
    elif temp <= 65: t_mult = 2.4
    elif temp <= 85: t_mult = 1.8
    elif temp <= 105: t_mult = 1.0
    
    f_mult = 1.55 if freq > 1000 else 1.0
    return t_mult * f_mult

def get_filtered_pool(target_ripple, temp, freq, excluded_parts=None):
    """Kriterlere uyan ve stokta olan kapasitörleri döner."""
    if excluded_parts is None:
        excluded_parts = []
    
    mult = get_multipliers(temp, freq)
    
    usable = [
        c for c in capacitors_db 
        if (c["base_ripple"] * mult) >= target_ripple 
        and c["part"] not in excluded_parts
    ]
    
    return sorted(usable, key=lambda x: x["part"]), sorted(usable, key=lambda x: x["cap"])