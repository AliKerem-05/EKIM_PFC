import math

class InfineonPFC:
    def __init__(self, specs):
        """
        Infineon uygulama notundaki (AN) denklemleri kullanan hesaplama motoru.
        """
        self.Vac_min = specs['Vac_min']
        self.Vo = specs['Vo']
        self.Po = specs['Po']
        self.f_sw = specs['f_sw']
        self.f_line = specs['f_line']
        self.ripple_percent = specs['ripple']
        self.hold_up_time = specs['t_hold']
        self.Vo_min_holdup = specs['Vo_min']
        self.V_ripple_out = specs['V_ripple']

    def calculate_requirements(self):
        """
        Bobin ve Kapasitör gereksinimlerini hesaplar.
        """
        # Eq 1: Gerekli Endüktans (L)
        term1 = 1 / self.ripple_percent
        term2 = (self.Vac_min ** 2) / self.Po
        term3 = 1 - ((math.sqrt(2) * self.Vac_min) / self.Vo)
        term4 = 1 / self.f_sw
        L_calc = term1 * term2 * term3 * term4
        
        # Eq 2: Maksimum Bobin Akımı (I_L_max)
        I_L_max = ((math.sqrt(2) * self.Po) / self.Vac_min) * (1 + (self.ripple_percent / 2))
        
        # Eq 30: Hold-up time gereksinimi
        Co_hold = (2 * self.Po * self.hold_up_time) / (self.Vo**2 - self.Vo_min_holdup**2)
        
        # Eq 31: Düşük frekans ripple gereksinimi
        Co_ripple = self.Po / (2 * math.pi * self.f_line * self.V_ripple_out * self.Vo)
        
        return {
            "L_uH": L_calc * 1e6,
            "I_max": I_L_max,
            "C_target_uF": max(Co_hold, Co_ripple) * 1e6
        }

class TIPFC:
    def __init__(self, specs):
        """
        Texas Instruments UCC28180 tarzı hesaplama motoru.
        """
        self.Vin_min = specs['Vin_min']
        self.Vo = specs['Vo']
        self.Po = specs['Po']
        self.f_sw = specs['f_sw']
        self.Eff = specs.get('efficiency', 0.94)
        self.Ripple_percent = specs['ripple']
        self.t_hold = specs['t_hold']
        self.Vo_min_hold = specs['Vo_min']
        self.V_ripple_out = specs['V_ripple']
        self.f_line_min = specs.get('f_line_min', 50)

    def calculate_requirements(self):
        """
        TI metodolojisine göre hesaplamaları yapar.
        """
        Pin = self.Po / self.Eff
        Iin_rms_max = Pin / self.Vin_min
        Iin_peak_max = Iin_rms_max * math.sqrt(2)
        
        # Bobin Hesabı
        dI = self.Ripple_percent * Iin_peak_max
        Vin_peak_low = self.Vin_min * math.sqrt(2)
        D_peak = (self.Vo - Vin_peak_low) / self.Vo
        L_min = (Vin_peak_low * D_peak) / (self.f_sw * dI)
        
        # Kapasitör Hesabı
        Co_hold = (2 * self.Po * self.t_hold) / (self.Vo**2 - self.Vo_min_hold**2)
        Io = self.Po / self.Vo
        Co_ripple = Io / (2 * math.pi * (2 * self.f_line_min) * self.V_ripple_out)
        
        return {
            "L_uH": L_min * 1e6,
            "I_max": Iin_peak_max + (dI / 2),
            "C_target_uF": max(Co_hold, Co_ripple) * 1e6
        }