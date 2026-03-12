
import math
from dataclasses import dataclass
from typing import Optional, Dict, Union, List


@dataclass
class ToroidProperties:
    part_number: str
    le_mm: float
    ae_mm2: float
    ve_mm3: float
    waac_cm4: Optional[float]
    od_mm: float
    id_mm: float
    height_mm: float
    al_l_750u_nh_t2: Optional[float]
    al_r_2300u_nh_t2: Optional[float]
    al_p_2500u_nh_t2: Optional[float]
    al_f_3000u_nh_t2: Optional[float]
    al_t_3000u_nh_t2: Optional[float]
    al_j_5000u_nh_t2: Optional[float]
    al_w_10000u_nh_t2: Optional[float]
    al_m_15000u_nh_t2: Optional[float]
    al_c_900u_nh_t2: Optional[float]
    coating: str = "Epoxy Coated"


class ToroidCoreLibrary:
    def __init__(self):
        # Veri kullanÄ±cÄ± tarafÄ±ndan paylaÅŸÄ±lan tablodan derlenmiÅŸtir.
        # AL birimi: nH / T^2
        self._data: Dict[str, ToroidProperties] = self._load_data()

    def get_core(self, part_number: Union[str, int]) -> Optional[ToroidProperties]:
        """
        Part number koduna gÃ¶re Ã§ekirdek Ã¶zelliklerini getirir.
        Ã–rnek: get_core("2206") veya get_core(2206)
        """
        key = str(part_number).strip()
        return self._data.get(key)

    def get_al_value(self, part_number: Union[str, int], material_code: str) -> Optional[float]:
        """
        Ä°stenen Ã§ekirdeÄŸin belirli malzeme koduna ait AL deÄŸerini dÃ¶ndÃ¼rÃ¼r.

        Malzeme kodlarÄ±:
        L -> 750u
        R -> 2300u
        P -> 2500u
        F -> 3000u
        T -> 3000u
        J -> 5000u
        W -> 10000u
        M -> 15000u
        C -> 900u
        """
        core = self.get_core(part_number)
        if not core:
            raise ValueError(f"GeÃ§ersiz Part Number: {part_number}")

        code = material_code.strip().upper()
        mapping = {
            "L": core.al_l_750u_nh_t2,
            "R": core.al_r_2300u_nh_t2,
            "P": core.al_p_2500u_nh_t2,
            "F": core.al_f_3000u_nh_t2,
            "T": core.al_t_3000u_nh_t2,
            "J": core.al_j_5000u_nh_t2,
            "W": core.al_w_10000u_nh_t2,
            "M": core.al_m_15000u_nh_t2,
            "C": core.al_c_900u_nh_t2,
        }
        return mapping.get(code)

    def calculate_inductance(self, part_number: Union[str, int], material_code: str, turns: float) -> Optional[float]:
        """
        L = AL * N^2 baÄŸÄ±ntÄ±sÄ±yla endÃ¼ktansÄ± hesaplar.
        SonuÃ§ Henry cinsindendir.

        AL: nH/T^2
        N : tur sayÄ±sÄ±
        """
        al_value = self.get_al_value(part_number, material_code)
        if al_value is None:
            return None
        return al_value * (turns ** 2) * 1e-9

    def calculate_inductance_uH(self, part_number: Union[str, int], material_code: str, turns: float) -> Optional[float]:
        """EndÃ¼ktansÄ± uH cinsinden dÃ¶ndÃ¼rÃ¼r."""
        L_h = self.calculate_inductance(part_number, material_code, turns)
        if L_h is None:
            return None
        return L_h * 1e6

    def estimate_turns_for_inductance_uH(self, part_number: Union[str, int], material_code: str, target_inductance_uH: float) -> Optional[float]:
        """
        Hedef endÃ¼ktansa gÃ¶re yaklaÅŸÄ±k tur sayÄ±sÄ±nÄ± hesaplar.
        N = sqrt(L / AL)

        Hedef endÃ¼ktans uH, AL ise nH/T^2 olarak ele alÄ±nÄ±r.
        """
        al_value = self.get_al_value(part_number, material_code)
        if al_value is None or al_value <= 0:
            return None

        target_L_nH = target_inductance_uH * 1000.0
        return math.sqrt(target_L_nH / al_value)

    def get_closest_by_ae(self, target_ae_mm2: float) -> ToroidProperties:
        """Verilen Ae deÄŸerine en yakÄ±n Ã§ekirdeÄŸi bulur."""
        closest_core = None
        min_diff = float("inf")

        for core in self._data.values():
            diff = abs(core.ae_mm2 - target_ae_mm2)
            if diff < min_diff:
                min_diff = diff
                closest_core = core
        return closest_core

    def filter_by_od_range(self, od_min_mm: float, od_max_mm: float) -> List[ToroidProperties]:
        """Belirli dÄ±ÅŸ Ã§ap aralÄ±ÄŸÄ±ndaki Ã§ekirdekleri dÃ¶ndÃ¼rÃ¼r."""
        return [
            core for core in self._data.values()
            if od_min_mm <= core.od_mm <= od_max_mm
        ]

    def filter_by_material(self, material_code: str) -> List[ToroidProperties]:
        """Ä°stenen malzeme kodu iÃ§in AL deÄŸeri bulunan Ã§ekirdekleri listeler."""
        code = material_code.strip().upper()
        valid = []
        for core in self._data.values():
            al = self.get_al_value(core.part_number, code)
            if al is not None:
                valid.append(core)
        return valid

    def list_part_numbers(self) -> List[str]:
        """TÃ¼m part number listesini dÃ¶ndÃ¼rÃ¼r."""
        return list(self._data.keys())

    def _load_data(self) -> Dict[str, ToroidProperties]:
        raw_data = [
            # Part, Le, Ae, Ve, WaAc, OD, ID, H, L, R, P, F, T, J, W, M, C
            ("0907", 22.7, 13.7, 310, 0.03, 9.53, 5.59, 7.11, None, None, 1884, 2260, None, 3765, 7530, 11380, None),
            ("1003", 20.7, 7.3, 151, 0.01, 9.53, 4.75, 3.18, None, 1000, 1095, 1314, 1330, 2196, 4392, 9988, None),
            ("1005", 20.7, 10.9, 227, 0.02, 9.53, 4.75, 4.78, None, 1510, 1650, 1980, None, 3308, 6616, None, None),
            ("1206", 25.0, 22.0, 550, 0.05, 12.7, 5.16, 6.35, None, 2600, 2820, 3384, None, 5640, 11280, None, 1029),
            ("1303", 31.7, 7.1, 226, 0.04, 12.7, 8.14, 3.15, None, 680, 745, 894, None, 1488, 2976, None, None),
            ("1305", 31.7, 11.4, 361, 0.06, 12.7, 8.14, 5.08, None, 1090, None, 1430, None, 2380, 4760, None, None),
            ("1306", 31.7, 14.0, 451, 0.07, 12.7, 8.14, 6.35, 424, 1360, 1485, 1782, 1700, 2968, 5936, 8476, 508),
            ("1406", 29.5, 17.1, 507, 0.07, 12.7, 7.14, 6.35, None, None, 1805, 2166, None, 3612, 7224, 10974, None),
            ("1407", 29.5, 12.9, 381, 0.05, 12.7, 7.14, 4.78, None, 1240, 1356, 1630, None, 2715, 5430, None, None),
            ("1450", 35.0, 12.3, 430, 0.08, 14.0, 8.99, 5.0, None, None, None, 1290, None, 2160, 4320, None, None),
            ("1506", 30.6, 11.2, 343, 0.05, 13.2, 7.37, 3.96, None, 1020, 1111, 1290, None, 2160, 4590, None, None),
            ("1605", 37.2, 15.6, 580, 0.10, 15.9, 9.07, 4.7, 396, 1260, 1375, 1650, 1580, 2760, 5520, 7917, None),
            ("1606", 37.2, 18.96, 706, None, 15.9, 9.07, 5.7, None, None, None, 1920, None, None, None, None, None),
            ("1610", 37.2, 31.2, 1164, 0.20, 15.9, 9.07, 9.4, None, None, None, None, None, 5410, 10600, None, None),
            ("1809", 41.1, 43.1, 1783, 0.32, 18.4, 9.75, 10.3, None, 2810, 3050, None, None, 6115, 12200, None, None),
            ("2106", 50.3, 24.6, 1238, 0.31, 20.6, 12.7, 6.35, None, None, 1500, 1680, None, 2800, 5600, None, None),
            ("2109", 50.0, 34.0, 1733, 0.43, 20.6, 12.7, 8.89, None, 1930, 2100, 2520, None, 4200, 8400, None, None),
            ("2206", 54.1, 26.2, 1417, 0.39, 22.1, 13.7, 6.35, 455, 1380, 1510, 1812, 1790, 3020, 6040, 8494, None),
            ("2207", 54.1, 32.5, 1763, 0.48, 22.1, 13.7, 7.9, None, 1720, 1875, 2250, None, 3700, 7400, None, None),
            ("2212", 54.1, 52.3, 2834, 0.77, 22.1, 13.7, 12.7, None, 2770, 3020, 3624, None, 6040, 12080, 17313, None),
            ("2507", 61.5, 37.1, 2284, 0.69, 25.3, 15.4, 7.66, None, 1800, 1958, 2348, None, 3913, 7825, 11072, None),
            ("2508", 61.5, 48.0, 2981, 0.89, 25.3, 15.4, 10.0, None, 2220, None, 2900, None, 4830, 9660, None, None),
            ("2908", 73.2, 37.0, 2679, 1.05, 29.0, 19.0, 7.43, None, 1450, 1585, 1902, None, 3170, 6340, None, None),
            ("2915", 73.2, 74.9, 5481, 2.13, 29.0, 19.0, 15.2, None, 2960, 3222, 3868, None, 6447, 12894, None, None),
            ("3113", 75.4, 73.6, 5547, 2.11, 31.0, 19.1, 12.74, None, 2850, 3100, None, None, 6200, 12400, None, None),
            ("3610", 89.6, 63.9, 5731, 2.65, 36.0, 23.0, 10.0, None, None, 2210, 2726, None, 4543, 9085, None, None),
            ("3615", 89.6, 95.9, 8596, 3.98, 36.0, 23.0, 15.0, None, 3100, 3366, 4040, None, 6736, 13400, None, None),
            ("3620", 89.6, 128.0, 11461, 5.31, 36.0, 23.0, 20.0, None, None, None, None, None, 9086, None, None, None),
            ("3806", 82.9, 58.3, 4644, 1.66, 38.0, 19.0, 6.35, None, 2020, 2200, 2640, None, 4400, 8800, None, None),
            ("3813", 82.9, 115.6, 9452, 3.28, 38.1, 19.0, 12.7, None, 3850, 4185, 5020, 5190, 8365, 16700, None, None),
            ("3825", 82.9, 231.0, 19304, 6.56, 38.1, 19.0, 25.4, None, 8060, 8762, 10040, None, 16730, 33400, None, None),
            ("4015", 103.0, 138.0, 14205, 7.44, 41.8, 26.2, 18.0, None, 3867, 4204, None, 5040, 8408, 16816, None, None),
            ("4416", 88.0, 187.0, 16559, 5.33, 44.3, 19.0, 15.7, None, None, 5830, None, None, None, 23200, None, None),
            ("4419", 88.0, 228.0, 20146, 6.50, 44.3, 19.0, 19.1, None, None, None, 9550, None, None, None, None, None),
            ("4715", 110.0, 145.5, 16063, 8.34, 46.9, 27.0, 15.0, None, None, 4030, None, None, 8075, 16100, None, None),
            ("4916", 127.0, 118.0, 15010, 10.6, 49.1, 33.8, 15.9, None, 2710, 2950, 3540, None, 5900, 11800, None, None),
            ("4920", 123.0, 119.0, 14700, 9.45, 49.1, 31.8, 15.9, None, None, 3032, 3640, None, 6065, 12130, None, None),
            ("4925", 123.0, 161.8, 19927, 12.8, 49.1, 31.8, 19.05, None, 3420, 3718, 4460, None, 7435, 14870, None, None),
            ("4932", 127.0, 236.0, 30000, 21.2, 49.1, 33.8, 31.3, None, 5430, 5900, 7080, None, 11800, 23600, None, None),
            ("6013", 157.6, 120.4, 18968, 16.48, 36.0, 23.0, 14.6, None, None, None, None, None, 4800, None, None, None),
            ("6113", 145.0, 156.0, 22500, 15.5, 61.0, 35.6, 12.7, None, None, 3491, 4107, None, 6845, 13690, None, None),
            ("6325", 152.0, 294.0, 44667, 33.2, 63.0, 38.0, 24.0, None, None, None, None, None, None, 21056, None, None),
            ("6326", 152.0, 300.0, 45598, 33.9, 63.0, 38.0, 24.5, None, None, 6270, None, None, 12500, None, None, None),
            ("7313", 165.0, 210.0, 34771, 25.0, 73.7, 38.9, 12.5, None, 3700, 4024, 4880, 4790, 8140, 16280, None, None),
            ("7325", 165.0, 423.0, 70009, 50.3, 73.7, 38.9, 25.2, None, None, 8050, None, None, None, None, None, None),
            ("7326", 165.0, 427.0, 70595, None, 73.7, 38.9, 25.4, None, None, None, None, None, None, 27610, None, None),
            ("8613", 215.0, 188.8, 40852, 45.7, 85.7, 55.5, 12.7, None, None, 2726, None, None, 5520, 11040, None, None),
            ("8626", 215.0, 377.0, 81165, 91.2, 85.7, 55.5, 25.24, None, None, None, None, None, None, 18760, None, None),
            ("9715", 255.3, 267.2, 68281, 90.8, 102.0, 65.8, 15.0, None, 3025, 3464, None, None, 6575, 11178, None, None),
            ("9718", 259.31, 320.27, 96013, 106.0, 107.0, 65.0, 18.0, None, 4127, 4486, None, None, 8972, 15252, None, None),
            ("9725", 259.31, 514.3, 133351, 170.0, 107.0, 65.0, 25.0, None, 5732, 6230, None, None, 9346, 21184, None, None),
            ("9740", 381.5, 422.3, 161086, 372.0, 140.0, 106.0, 25.0, None, 3200, 3477, None, None, 6955, 11823, None, None),
        ]

        properties = {}
        for row in raw_data:
            properties[row[0]] = ToroidProperties(
                part_number=row[0],
                le_mm=row[1],
                ae_mm2=row[2],
                ve_mm3=row[3],
                waac_cm4=row[4],
                od_mm=row[5],
                id_mm=row[6],
                height_mm=row[7],
                al_l_750u_nh_t2=row[8],
                al_r_2300u_nh_t2=row[9],
                al_p_2500u_nh_t2=row[10],
                al_f_3000u_nh_t2=row[11],
                al_t_3000u_nh_t2=row[12],
                al_j_5000u_nh_t2=row[13],
                al_w_10000u_nh_t2=row[14],
                al_m_15000u_nh_t2=row[15],
                al_c_900u_nh_t2=row[16],
            )
        return properties


# --- KullanÄ±m Ã–rnekleri ---
if __name__ == "__main__":
    lib = ToroidCoreLibrary()

    # Ã–rnek 1: Belirli bir Ã§ekirdeÄŸi Ã§aÄŸÄ±rma
    core_2206 = lib.get_core("2206")
    if core_2206:
        print("--- 2206 Ã–zellikleri ---")
        print(f"Le: {core_2206.le_mm} mm")
        print(f"Ae: {core_2206.ae_mm2} mm^2")
        print(f"Ve: {core_2206.ve_mm3} mm^3")
        print(f"OD: {core_2206.od_mm} mm")
        print(f"ID: {core_2206.id_mm} mm")
        print(f"Height: {core_2206.height_mm} mm")
        print(f"R malzemesi AL: {core_2206.al_r_2300u_nh_t2} nH/T^2")
        print(f"P malzemesi AL: {core_2206.al_p_2500u_nh_t2} nH/T^2")

    # Ã–rnek 2: EndÃ¼ktans hesabÄ±
    L_uH = lib.calculate_inductance_uH("2206", "R", turns=20)
    if L_uH is not None:
        print(f"\n--- 2206 / R / 20 tur iÃ§in endÃ¼ktans ---")
        print(f"L = {L_uH:.3f} uH")

    # Ã–rnek 3: Hedef endÃ¼ktans iÃ§in tur sayÄ±sÄ±
    turns_needed = lib.estimate_turns_for_inductance_uH("2206", "R", target_inductance_uH=100)
    if turns_needed is not None:
        print(f"\n--- 2206 / R iÃ§in 100 uH yaklaÅŸÄ±k tur sayÄ±sÄ± ---")
        print(f"N â‰ˆ {turns_needed:.2f} tur")

    # Ã–rnek 4: Ae deÄŸerine en yakÄ±n Ã§ekirdek
    closest = lib.get_closest_by_ae(50.0)
    print(f"\n--- Ae=50 mm^2 deÄŸerine en yakÄ±n Ã§ekirdek ---")
    print(f"Part Number: {closest.part_number}, Ae: {closest.ae_mm2} mm^2")

    # Ã–rnek 5: Belirli dÄ±ÅŸ Ã§ap aralÄ±ÄŸÄ±ndaki Ã§ekirdekler
    filtered = lib.filter_by_od_range(20.0, 30.0)
    print(f"\n--- 20 mm ile 30 mm OD aralÄ±ÄŸÄ±ndaki Ã§ekirdekler ---")
    print([c.part_number for c in filtered][:10])

    # Ã–rnek 6: W malzemesi bulunan Ã§ekirdekler
    w_cores = lib.filter_by_material("W")
    print(f"\n--- W malzemesi olan ilk 10 Ã§ekirdek ---")
    print([c.part_number for c in w_cores[:10]])

