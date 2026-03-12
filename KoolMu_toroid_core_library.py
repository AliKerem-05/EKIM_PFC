import math
from dataclasses import dataclass
from typing import Dict, List, Optional, Union


@dataclass
class KoolMuToroidProperties:
    part_number: str
    le_mm: float
    ae_mm2: float
    ve_mm3: float
    od_mm: float
    id_mm: float
    height_mm: float
    al_14u_nh_t2: Optional[float]
    al_19u_nh_t2: Optional[float]
    al_26u_nh_t2: Optional[float]
    al_40u_nh_t2: Optional[float]
    al_60u_nh_t2: Optional[float]
    al_75u_nh_t2: Optional[float]
    al_90u_nh_t2: Optional[float]
    al_125u_nh_t2: Optional[float]
    family: str = "Kool Mu Toroid"


class KoolMuToroidCoreLibrary:
    def __init__(self) -> None:
        # Veri kullanici tarafindan paylasilan MAG-INC Kool Mu Toroid tablosundan derlenmistir.
        # AL birimi: nH / T^2
        self._data: Dict[str, KoolMuToroidProperties] = self._load_data()

    def get_core(self, part_number: Union[str, int]) -> Optional[KoolMuToroidProperties]:
        return self._data.get(str(part_number).strip())

    def list_part_numbers(self) -> List[str]:
        return list(self._data.keys())

    def get_al_value(self, part_number: Union[str, int], permeability: Union[str, int]) -> Optional[float]:
        core = self.get_core(part_number)
        if not core:
            raise ValueError(f"Gecersiz Part Number: {part_number}")

        key = str(permeability).strip().replace("u", "u").replace("u", "u").lower()
        mapping = {
            "14": core.al_14u_nh_t2,
            "14u": core.al_14u_nh_t2,
            "19": core.al_19u_nh_t2,
            "19u": core.al_19u_nh_t2,
            "26": core.al_26u_nh_t2,
            "26u": core.al_26u_nh_t2,
            "40": core.al_40u_nh_t2,
            "40u": core.al_40u_nh_t2,
            "60": core.al_60u_nh_t2,
            "60u": core.al_60u_nh_t2,
            "75": core.al_75u_nh_t2,
            "75u": core.al_75u_nh_t2,
            "90": core.al_90u_nh_t2,
            "90u": core.al_90u_nh_t2,
            "125": core.al_125u_nh_t2,
            "125u": core.al_125u_nh_t2,
        }
        return mapping.get(key)

    def calculate_inductance(self, part_number: Union[str, int], permeability: Union[str, int], turns: float) -> Optional[float]:
        al_value = self.get_al_value(part_number, permeability)
        if al_value is None:
            return None
        return al_value * (turns ** 2) * 1e-9

    def calculate_inductance_uH(self, part_number: Union[str, int], permeability: Union[str, int], turns: float) -> Optional[float]:
        inductance_h = self.calculate_inductance(part_number, permeability, turns)
        if inductance_h is None:
            return None
        return inductance_h * 1e6

    def estimate_turns_for_inductance_uH(
        self,
        part_number: Union[str, int],
        permeability: Union[str, int],
        target_inductance_uH: float,
    ) -> Optional[float]:
        al_value = self.get_al_value(part_number, permeability)
        if al_value is None or al_value <= 0:
            return None
        target_l_nh = target_inductance_uH * 1000.0
        return math.sqrt(target_l_nh / al_value)

    def get_closest_by_ae(self, target_ae_mm2: float) -> KoolMuToroidProperties:
        return min(self._data.values(), key=lambda core: abs(core.ae_mm2 - target_ae_mm2))

    def filter_by_od_range(self, od_min_mm: float, od_max_mm: float) -> List[KoolMuToroidProperties]:
        return [core for core in self._data.values() if od_min_mm <= core.od_mm <= od_max_mm]

    def filter_by_permeability(self, permeability: Union[str, int]) -> List[KoolMuToroidProperties]:
        return [core for core in self._data.values() if self.get_al_value(core.part_number, permeability) is not None]

    def _load_data(self) -> Dict[str, KoolMuToroidProperties]:
        raw_data = [
            # Part, 14u, 19u, 26u, 40u, 60u, 75u, 90u, 125u, Le, Ae, Ve, OD, ID, HT
            ("140", None, None, None, None, None, 13, 16, 19, 8.06, 1.30, 10.5, 4.19, 1.27, 2.16),
            ("150", None, None, None, None, None, 17, 21, 25, 9.42, 2.11, 19.9, 4.58, 1.72, 3.18),
            ("180", None, None, None, None, None, 20, 25, 30, 10.6, 2.85, 30.3, 5.29, 1.85, 3.18),
            ("020", 6, 8, 10, 18, 24, 30, 36, 50, 13.6, 4.7, 64, 6.99, 2.29, 3.43),
            ("240", 6, 8, 11, 17, 26, 32, 39, 54, 13.6, 4.76, 64.9, 7.24, 2.15, 3.18),
            ("270", 12, 16, 21, 33, 50, 62, 74, 103, 13.6, 9.2, 125, 7.24, 2.16, 5.41),
            ("410", 8, 11, 14, 22, 33, 41, 50, 70, 16.5, 7.25, 120, 7.49, 3.45, 5.72),
            ("030", 6, 8, 11, 17, 25, 31, 37, 52, 17.9, 5.99, 107, 8.51, 3.45, 3.81),
            ("280", 6, 8, 11, 17, 25, 32, 38, 53, 21.8, 7.52, 164, 10.29, 4.27, 3.81),
            ("290", 7, 10, 14, 22, 32, 41, 48, 66, 21.8, 9.45, 206, 10.29, 4.27, 4.60),
            ("040", 7, 10, 14, 21, 32, 40, 48, 66, 23.0, 9.57, 220, 10.80, 4.57, 4.60),
            ("130", 6, 8, 11, 17, 26, 32, 38, 53, 26.9, 9.06, 244, 11.81, 5.84, 4.60),
            ("050", 6, 9, 12, 18, 27, 34, 40, 56, 31.2, 10.9, 340, 13.46, 6.99, 5.51),
            ("120", 8, 11, 15, 24, 35, 43, 52, 72, 41.2, 19.2, 790, 17.27, 9.53, 7.11),
            ("380", 10, 14, 19, 28, 43, 53, 64, 89, 41.4, 23.2, 960, 18.03, 9.02, 7.11),
            ("206", 7, 10, 14, 21, 32, 41, 49, 68, 50.9, 22.1, 1120, 21.08, 12.07, 7.11),
            ("310", 9, 14, 19, 29, 43, 54, 65, 90, 56.7, 31.7, 1800, 23.62, 13.34, 8.38),
            ("350", 12, 16, 22, 34, 51, 62, 76, 105, 58.8, 38.8, 2280, 24.33, 13.77, 9.65),
            ("930", 18, 23, 32, 50, 75, 94, 113, 157, 63.5, 65.4, 4150, 27.69, 14.10, 11.94),
            ("426", None, None, 30, None, 69, None, 104, 144, 66.5, 72.7, 4840, 30.00, 17.40, 10.90),
            ("548", 14, 20, 28, 41, 61, 76, 91, 127, 81.4, 65.6, 5340, 33.66, 19.46, 11.43),
            ("585", 9, 12, 16, 25, 38, 47, 57, 79, 89.5, 46.4, 4150, 35.18, 22.56, 9.78),
            ("324", 13, 18, 24, 37, 56, 70, 84, 117, 89.8, 67.8, 6090, 36.70, 21.54, 11.35),
            ("395A", 28, 39, 53, 81, 122, 152, 183, 254, 95.1, 153.7, 14600, 40.94, 21.27, 17.89),
            ("254", 19, 26, 35, 54, 81, 101, 121, 168, 98.4, 107, 10600, 40.77, 23.32, 15.37),
            ("395B", 28, 39, 53, 81, 122, 153, 183, 254, 94.0, 153.0, 14600, 40.94, 21.27, 17.89),
            ("454", 25, 34, 47, 72, 108, 135, 161, 224, 102, 147.5, 15100, 43.84, 23.39, 17.27),
            ("089", 20, 27, 37, 57, 86, 107, 128, 178, 116.3, 134, 15600, 47.63, 27.89, 16.13),
            ("438", 32, 43, 59, 90, 135, 169, 202, 281, 107.4, 199, 21400, 47.63, 23.32, 18.92),
            ("725", 41, 56, 76, 117, 175, 219, 269, 366, 114, 262, 29700, 51.51, 24.00, 21.59),
            ("715", 17, 23, 32, 49, 73, 91, 109, 152, 127.3, 125.1, 15900, 51.69, 30.94, 14.35),
            ("540", 24, 33, 45, 69, 104, 130, 156, 217, 126, 174, 22000, 54.90, 28.10, 15.30),
            ("109", 18, 24, 33, 50, 75, 94, 112, 156, 143, 144, 20700, 58.04, 34.75, 14.86),
            ("195", 32, 44, 60, 92, 138, 172, 207, 287, 125.1, 228.8, 28600, 58.04, 25.58, 16.13),
            ("596", 29, 39, 54, 83, 125, 156, 187, 259, 143, 237, 33900, 60.60, 33.00, 20.50),
            ("620", 44, 60, 82, 126, 189, 237, 284, 394, 144, 360.2, 51900, 63.09, 31.70, 25.91),
            ("070", 35, 48, 65, 100, 143, 187, 225, 312, 158, 314, 49600, 69.42, 34.67, 21.41),
            ("778", 47, 64, 88, 135, 205, 256, 306, 425, 177.2, 492, 81500, 78.94, 38.33, 26.85),
            ("740", 48, 64, 88, 136, 204, 255, 306, 425, 183.8, 496.8, 91300, 75.21, 44.40, 35.92),
            ("866", 16, 22, 30, 45, 68, 85, 102, 142, 196, 176, 34500, 78.94, 48.21, 13.84),
            ("906", 20, 27, 37, 57, 85, 106, 128, 177, 196.1, 221, 43300, 78.94, 48.21, 17.02),
            ("102", 26, 35, 48, 74, 111, 139, 167, 232, 243, 358, 86900, 103.00, 55.75, 17.91),
            ("337", 37, 50, 68, 105, 158, None, None, None, 324, 678, 220000, 133.96, 77.19, 26.80),
            ("165", 42, 57, 78, None, None, None, None, None, 412, 987, 407000, 166.50, 101.02, 33.15),
        ]

        return {
            row[0]: KoolMuToroidProperties(
                part_number=row[0],
                al_14u_nh_t2=row[1],
                al_19u_nh_t2=row[2],
                al_26u_nh_t2=row[3],
                al_40u_nh_t2=row[4],
                al_60u_nh_t2=row[5],
                al_75u_nh_t2=row[6],
                al_90u_nh_t2=row[7],
                al_125u_nh_t2=row[8],
                le_mm=row[9],
                ae_mm2=row[10],
                ve_mm3=row[11],
                od_mm=row[12],
                id_mm=row[13],
                height_mm=row[14],
            )
            for row in raw_data
        }


if __name__ == "__main__":
    lib = KoolMuToroidCoreLibrary()
    core_206 = lib.get_core("206")
    if core_206:
        print("--- Kool Mu 206 Ozellikleri ---")
        print(core_206)
        print(f"206 / 60u / 20 tur -> {lib.calculate_inductance_uH('206', '60u', 20):.3f} uH")

