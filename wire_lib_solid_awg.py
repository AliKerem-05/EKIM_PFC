import math
from dataclasses import dataclass
from typing import Optional, Dict, Union

@dataclass
class WireProperties:
    awg: str
    diameter_in: float
    diameter_mm: float
    area_mm2: float
    resistance_ohm_per_1000ft: float
    resistance_ohm_per_km: float
    max_current_amps: float
    max_freq_hz: float # 100% Skin Depth frekansı

class SolarisWireLibrary:
    def __init__(self):
        # Veriler https://www.solaris-shop.com/american-wire-gauge-conductor-size-table/ 
        # adresinden alınmıştır.
        self._data: Dict[str, WireProperties] = self._load_data()

    def get_wire(self, awg: Union[str, int]) -> Optional[WireProperties]:
        """
        AWG koduna göre kablo özelliklerini getirir.
        Örnek: get_wire("10") veya get_wire("4/0") veya get_wire(10)
        """
        key = str(awg).strip()
        # "0000" gibi girişleri "4/0" formatına çevirme
        if key == "0000": key = "4/0"
        if key == "000": key = "3/0"
        if key == "00": key = "2/0"
        if key == "0": key = "1/0"
        
        return self._data.get(key)

    def get_closest_by_area(self, target_area_mm2: float) -> WireProperties:
        """Verilen mm2 alanına en yakın AWG kablosunu bulur."""
        closest_wire = None
        min_diff = float('inf')
        
        for wire in self._data.values():
            diff = abs(wire.area_mm2 - target_area_mm2)
            if diff < min_diff:
                min_diff = diff
                closest_wire = wire
        return closest_wire

    def calculate_voltage_drop(self, awg: str, current_amps: float, length_meters: float) -> float:
        """
        Belirli bir uzunluk ve akım için voltaj düşümünü hesaplar (V = I * R).
        Bakır iletken direncini baz alır.
        """
        wire = self.get_wire(awg)
        if not wire:
            raise ValueError(f"Geçersiz AWG: {awg}")
        
        # Direnç (Ohm/km) -> (Ohm/m)
        resistance_per_meter = wire.resistance_ohm_per_km / 1000.0
        total_resistance = resistance_per_meter * length_meters
        return current_amps * total_resistance

    def convert_copper_to_aluminum(self, copper_awg: str) -> Optional[str]:
        """
        Solaris sitesindeki 'Rule of Thumb'a göre:
        Alüminyum iletkenler için bakır eşdeğerinden 2 AWG büyük boyut seçilir.
        Örn: 6 AWG Bakır -> 4 AWG Alüminyum
        """
        # AWG listesi sıralı (büyükten küçüğe fiziksel boyut, yani küçük AWG numarasından büyüğe)
        ordered_keys = list(self._data.keys())
        try:
            current_index = ordered_keys.index(copper_awg)
            # Daha büyük fiziksel boyut için listede geriye gitmeliyiz (örn 6 -> 4)
            # Ancak AWG string listesi karmaşık (4/0, 3/0... 1, 2).
            # Basit mantık: 2 boyut daha "kalın" olanı bul.
            target_index = current_index - 2
            if target_index >= 0:
                return ordered_keys[target_index]
            else:
                return "Tablo dışı (Çok kalın)"
        except ValueError:
            return None

    def _load_data(self) -> Dict[str, WireProperties]:
        raw_data = [
            # AWG, Dia(in), Dia(mm), Area(mm2), Res(Ohm/1kft), Res(Ohm/km), MaxA, MaxFreq(Hz)
            ("4/0", 0.46, 11.684, 107, 0.049, 0.161, 302, 125),
            ("3/0", 0.4096, 10.404, 85, 0.0618, 0.203, 239, 160),
            ("2/0", 0.3648, 9.266, 67.4, 0.0779, 0.256, 190, 200),
            ("1/0", 0.3249, 8.252, 53.5, 0.0983, 0.322, 150, 250),
            ("1", 0.2893, 7.348, 42.4, 0.1239, 0.406, 119, 325),
            ("2", 0.2576, 6.543, 33.6, 0.1563, 0.513, 94, 410),
            ("3", 0.2294, 5.827, 26.7, 0.197, 0.646, 75, 500),
            ("4", 0.2043, 5.189, 21.2, 0.2485, 0.815, 60, 650),
            ("5", 0.1819, 4.620, 16.8, 0.3133, 1.028, 47, 810),
            ("6", 0.162, 4.115, 13.3, 0.3951, 1.296, 37, 1100),
            ("7", 0.1443, 3.665, 10.5, 0.4982, 1.634, 30, 1300),
            ("8", 0.1285, 3.264, 8.37, 0.6282, 2.060, 24, 1650),
            ("9", 0.1144, 2.906, 6.63, 0.7921, 2.598, 19, 2050),
            ("10", 0.1019, 2.588, 5.26, 0.9989, 3.276, 15, 2600),
            ("11", 0.0907, 2.304, 4.17, 1.26, 4.133, 12, 3200),
            ("12", 0.0808, 2.052, 3.31, 1.588, 5.209, 9.3, 4150),
            ("13", 0.072, 1.829, 2.62, 2.003, 6.570, 7.4, 5300),
            ("14", 0.0641, 1.628, 2.08, 2.525, 8.282, 5.9, 6700),
            ("15", 0.0571, 1.450, 1.65, 3.184, 10.444, 4.7, 8250),
            ("16", 0.0508, 1.290, 1.31, 4.016, 13.172, 3.7, 11000), # 11 kHz
            ("17", 0.0453, 1.151, 1.04, 5.064, 16.610, 2.9, 13000), # 13 kHz
            ("18", 0.0403, 1.024, 0.823, 6.385, 20.943, 2.3, 17000), # 17 kHz
            ("19", 0.0359, 0.912, 0.653, 8.051, 26.407, 1.8, 21000), # 21 kHz
            ("20", 0.032, 0.813, 0.518, 10.15, 33.292, 1.5, 27000), # 27 kHz
            ("21", 0.0285, 0.724, 0.41, 12.8, 41.984, 1.2, 33000), # 33 kHz
            ("22", 0.0254, 0.645, 0.326, 16.14, 52.939, 0.92, 42000), # 42 kHz
            ("23", 0.0226, 0.574, 0.258, 20.36, 66.781, 0.729, 53000), # 53 kHz
            ("24", 0.0201, 0.511, 0.205, 25.67, 84.198, 0.577, 68000), # 68 kHz
            ("25", 0.0179, 0.455, 0.162, 32.37, 106.174, 0.457, 85000), # 85 kHz
            ("26", 0.0159, 0.404, 0.129, 40.81, 133.857, 0.361, 107000), # 107 kHz
            ("27", 0.0142, 0.361, 0.102, 51.47, 168.822, 0.288, 130000), # 130 kHz
            ("28", 0.0126, 0.320, 0.081, 64.9, 212.872, 0.226, 170000), # 170 kHz
            ("29", 0.0113, 0.287, 0.0642, 81.83, 268.402, 0.182, 210000), # 210 kHz
            ("30", 0.01, 0.254, 0.0509, 103.2, 338.496, 0.142, 270000), # 270 kHz
            ("31", 0.0089, 0.226, 0.0404, 130.1, 426.728, 0.113, 340000), # 340 kHz
            ("32", 0.008, 0.203, 0.032, 164.1, 538.248, 0.091, 430000), # 430 kHz
            ("33", 0.0071, 0.180, 0.0254, 206.9, 678.632, 0.072, 540000), # 540 kHz
            ("34", 0.0063, 0.160, 0.0201, 260.9, 855.752, 0.056, 690000), # 690 kHz
            ("35", 0.0056, 0.142, 0.016, 329, 1079.12, 0.044, 870000), # 870 kHz
            ("36", 0.005, 0.127, 0.0127, 414.8, 1360, 0.035, 1100000), # 1100 kHz
            ("37", 0.0045, 0.114, 0.01, 523.1, 1715, 0.0289, 1350000), # 1350 kHz
            ("38", 0.004, 0.102, 0.00797, 659.6, 2163, 0.0228, 1750000), # 1750 kHz
            ("39", 0.0035, 0.089, 0.00632, 831.8, 2728, 0.0175, 2250000), # 2250 kHz
            ("40", 0.0031, 0.079, 0.00501, 1049, 3440, 0.0137, 2900000)  # 2900 kHz
        ]
        
        properties = {}
        for row in raw_data:
            awg_code = row[0]
            properties[awg_code] = WireProperties(
                awg=awg_code,
                diameter_in=row[1],
                diameter_mm=row[2],
                area_mm2=row[3],
                resistance_ohm_per_1000ft=row[4],
                resistance_ohm_per_km=row[5],
                max_current_amps=row[6],
                max_freq_hz=row[7]
            )
        return properties

# --- Kullanım Örnekleri ---
if __name__ == "__main__":
    lib = SolarisWireLibrary()

    # Örnek 1: Belirli bir AWG'yi çağırma (10 AWG)
    wire_10 = lib.get_wire("10")
    if wire_10:
        print(f"--- 10 AWG Özellikleri ---")
        print(f"Çap: {wire_10.diameter_mm} mm")
        print(f"Maks Akım: {wire_10.max_current_amps} A")
        print(f"Direnç: {wire_10.resistance_ohm_per_km} Ohm/km")
        print(f"Maksimum Frekans (Skin Depth): {wire_10.max_freq_hz} Hz")

    # Örnek 2: "0000" formatını kullanma
    wire_4_0 = lib.get_wire("0000")
    if wire_4_0:
        print(f"\n--- 4/0 (0000) AWG Özellikleri ---")
        print(f"Alan: {wire_4_0.area_mm2} mm2")

    # Örnek 3: Voltaj Düşümü Hesabı
    # 50 metre, 10 AWG kablo üzerinden 5 Amper akım geçerse ne kadar voltaj düşer?
    try:
        v_drop = lib.calculate_voltage_drop("10", current_amps=5, length_meters=50)
        print(f"\n--- Voltaj Düşümü Hesabı (10 AWG, 5A, 50m) ---")
        print(f"Voltaj Düşümü: {v_drop:.4f} Volt")
    except ValueError as e:
        print(e)

    # Örnek 4: Alüminyum Dönüşümü
    # 6 AWG Bakır kablo yerine hangi Alüminyum kablo kullanılmalı?
    cu_awg = "6"
    al_awg = lib.convert_copper_to_aluminum(cu_awg)
    print(f"\n--- Bakır -> Alüminyum Dönüşümü ---")
    print(f"{cu_awg} AWG Bakır yerine yaklaşık {al_awg} AWG Alüminyum önerilir.")
    
    # Örnek 5: Alana göre en yakın kabloyu bulma
    target_area = 2.0 
    closest = lib.get_closest_by_area(target_area)
    print(f"\n--- {target_area} mm2 alanına en yakın kablo ---")
    print(f"AWG: {closest.awg} (Alan: {closest.area_mm2} mm2)")