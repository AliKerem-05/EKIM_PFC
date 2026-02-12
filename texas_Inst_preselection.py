import math
import itertools

class TIPFCBoostDesign:
    def __init__(self, specs):
        """
        Texas Instruments SLUC506C Excel dosyasındaki girdilere göre başlatılır.
        """
        # --- GİRDİLER (Excel'in 'Design Inputs' Kısmı) ---
        self.Vin_min = specs['Vin_min']       # Min AC Giriş Voltajı (V)
        self.Vin_max = specs['Vin_max']       # Max AC Giriş Voltajı (V)
        self.f_line_min = specs['f_line_min'] # Min Şebeke Frekansı (Hz)
        self.Vo = specs['Vo']                 # Hedef Çıkış Voltajı (V)
        self.Po = specs['Po']                 # Çıkış Gücü (W)
        self.f_sw = specs['f_sw']             # Anahtarlama Frekansı (Hz)
        self.Eff = specs['efficiency']        # Tahmini Verimlilik (0.95 gibi)
        self.Ripple_percent = specs['ripple'] # Bobin Akım Dalgalanması (%20-%40 arası)
        self.t_hold = specs['t_hold']         # Hold-up süresi (s)
        self.Vo_min_hold = specs['Vo_min']    # Hold-up anındaki min çıkış voltajı (V)
        self.V_ripple_out = specs['V_ripple'] # Çıkış Voltajı Dalgalanması (Vpp)

        # TI'a özgü bazı sabitler (UCC28180 için genelde kullanılanlar)
        self.V_rsense_limit = 1.0             # Akım okuma pini limiti (Genelde 1V civarıdır)
        
        print(f"--- TI Tabanlı PFC Tasarımı Başlatıldı: {self.Po}W, {self.Vo}V ---")

    def calculate_input_parameters(self):
        """
        Giriş akımı hesaplamaları (Excel satır 14-20 civarı)
        """
        # Giriş Gücü
        self.Pin = self.Po / self.Eff
        
        # Maksimum RMS Giriş Akımı (Vin_min noktasında)
        self.Iin_rms_max = self.Pin / self.Vin_min
        
        # Maksimum Tepe (Peak) Giriş Akımı
        self.Iin_peak_max = self.Iin_rms_max * math.sqrt(2)
        
        print(f"\n[Giriş Parametreleri]")
        print(f"Giriş Gücü (Pin): {self.Pin:.2f} W")
        print(f"Max RMS Akım: {self.Iin_rms_max:.2f} A")
        print(f"Max Peak Akım (Sinüs): {self.Iin_peak_max:.2f} A")

    def calculate_inductor(self):
        """
        Bobin (Inductor) Hesabı (Excel 'Inductor' Bölümü)
        TI formülü: Ripple akımını, tepe akımının yüzdesi olarak alır.
        """
        # Hedeflenen Ripple Akımı (Delta I)
        # TI Hesaplayıcısı: Ripple = %Ripple * I_peak_max (@Low Line)
        self.dI = self.Ripple_percent * self.Iin_peak_max
        
        # Duty Cycle (Low Line Peak noktasında)
        # D = (Vo - Vin_peak) / Vo
        Vin_peak_low = self.Vin_min * math.sqrt(2)
        D_peak = (self.Vo - Vin_peak_low) / self.Vo
        
        # Gerekli Endüktans (L)
        # L = (Vin_peak * D) / (f_sw * dI)
        self.L_min = (Vin_peak_low * D_peak) / (self.f_sw * self.dI)
        self.L_min_uH = self.L_min * 1e6
        
        # Toplam Bobin Tepe Akımı (DC + AC Ripple/2)
        self.I_L_peak_total = self.Iin_peak_max + (self.dI / 2)
        
        print(f"\n[Bobin Tasarımı]")
        print(f"Duty Cycle (@Peak): %{D_peak*100:.1f}")
        print(f"Ripple Akımı (dI): {self.dI:.2f} A")
        print(f"Hesaplanan Min Endüktans: {self.L_min_uH:.2f} uH")
        print(f"Bobin Doyum Akımı (Isat) > {self.I_L_peak_total:.2f} A olmalı")
        
        return self.L_min_uH

    def calculate_output_capacitor(self):
        """
        Çıkış Kapasitörü (Excel 'Output Capacitor' Bölümü)
        """
        # 1. Hold-up Süresi Gereksinimi
        # Co >= (2 * Pout * t_hold) / (Vo^2 - Vo_min_hold^2)
        Co_hold = (2 * self.Po * self.t_hold) / (self.Vo**2 - self.Vo_min_hold**2)
        
        # 2. Çıkış Ripple Voltajı Gereksinimi (f_line x 2 frekansında)
        # Co >= Io / (2 * pi * 2*f_line * V_ripple) -> TI genelde Io = Po/Vo kullanır
        Io = self.Po / self.Vo
        # Şebeke frekansı olarak min frekans seçilir (en kötü durum)
        Co_ripple = Io / (2 * math.pi * (2 * self.f_line_min) * self.V_ripple_out)
        
        # En büyük değeri seç
        self.Co_target = max(Co_hold, Co_ripple)
        self.Co_target_uF = self.Co_target * 1e6
        
        print(f"\n[Kapasitör Tasarımı]")
        print(f"Hold-up için gereken: {Co_hold*1e6:.1f} uF")
        print(f"Ripple için gereken: {Co_ripple*1e6:.1f} uF")
        print(f"SEÇİLEN MİNİMUM DEĞER: {self.Co_target_uF:.1f} uF")

    def calculate_current_sense_resistor(self):
        """
        TI'a Özgü: Current Sense Direnci (Rsense)
        UCC28180 gibi entegrelerde Soft-Start veya Peak Limit için kullanılır.
        """
        # Genelde %10 güvenlik marjı bırakılır
        safety_margin = 1.1 
        
        # R_sense = V_limit / (I_L_peak_total * margin)
        # TI Excel'inde genelde I_peak üzerinden hesaplanır.
        self.R_sense = self.V_rsense_limit / (self.I_L_peak_total * safety_margin)
        
        # Güç Kaybı (P_Rsense) = I_rms^2 * R
        # Yaklaşık olarak I_in_rms kullanılır (Ripple ihmal edilirse)
        P_Rsense = (self.Iin_rms_max ** 2) * self.R_sense
        
        print(f"\n[Akım Okuma Direnci (Rsense)]")
        print(f"Hesaplanan Rsense: {self.R_sense*1000:.1f} mOhm (Maksimum)")
        print(f"Rsense Üzerindeki Güç Kaybı: ~{P_Rsense:.2f} W")

    def optimize_capacitor_library(self, library, max_parallel=3):
        """
        Kütüphane Optimizasyon Modülü
        Verilen kütüphanedeki standart değerleri kullanarak hedefe en yakın
        PARALEL kombinasyonu bulur.
        """
        print(f"\n[Kütüphane Optimizasyonu - {self.Co_target_uF:.1f} uF İçin]")
        
        best_diff = float('inf')
        best_combo = None
        
        # Kombinasyonları tara (1'li, 2'li, 3'lü...)
        for r in range(1, max_parallel + 1):
            for combo in itertools.combinations_with_replacement(library, r):
                current_sum = sum(combo)
                
                # Hedef değerin ALTINDA kalmamalı (PFC için kritik)
                if current_sum < self.Co_target_uF:
                    continue
                    
                diff = current_sum - self.Co_target_uF
                
                if diff < best_diff:
                    best_diff = diff
                    best_combo = combo
        
        if best_combo:
            print(f"-> En İyi Kombinasyon: {best_combo} uF")
            print(f"-> Toplam Kapasite: {sum(best_combo):.1f} uF")
            print(f"-> Fazlalık (Margin): {best_diff:.1f} uF")
        else:
            print("-> Uygun kombinasyon bulunamadı (Kütüphane değerlerini artırın).")

# --- KULLANIM SENARYOSU ---

# 1. Tasarım Kriterleri (TI Excel'indeki "INPUTS" hücrelerine karşılık gelir)
ti_specs = {
    'Vin_min': 207,        # V (Min AC)
    'Vin_max': 253,       # V (Max AC)
    'f_line_min': 60,     # Hz (Min Şebeke Frekansı - TI genelde 47 veya 50 alır)
    'Vo': 400,            # V (TI genelde 390V veya 400V kullanır)
    'Po': 500,           # W (Çıkış Gücü)
    'f_sw': 65e3,        # Hz (100 kHz)
    'efficiency': 0.94,   # %94 Verim tahmini
    'ripple': 0.25,       # %25 Akım Ripple (TI önerisi %20-%40 arasıdır)
    't_hold': 16.6e-3,    # 16.6ms Hold-up
    'Vo_min': 380,        # Hold-up sonrası inebileceği min voltaj
    'V_ripple': 10        # Çıkış Ripple (Vpp)
}

# 2. Kütüphane (Standart Kapasitör Değerleri - uF)
# 450V sınıfı Snap-in kapasitörler için yaygın değerler
capacitor_library = [
    # 1 - 10 uF Arası (Genelde Film Kapasitörler veya Küçük Elektrolitik)
    1.0, 1.2, 1.5, 1.8, 2.2, 2.7, 3.3, 3.9, 4.7, 5.6, 6.8, 8.2,
    
    # 10 - 100 uF Arası
    10, 12, 15, 18, 22, 27, 33, 39, 47, 56, 68, 82,
    
    # 100 - 1000 uF Arası (PFC Çıkışı için en yaygın aralık)
    100, 120, 150, 180, 220, 270, 330, 390, 470, 560, 680, 820,
    
    # 1000 - 3000 uF Arası (Yüksek Güçlü Uygulamalar)
    1000, 1200, 1500, 1800, 2200, 2700
]
# 3. Kodu Çalıştır
"""

pfc_ti = TIPFCBoostDesign(ti_specs)

pfc_ti.calculate_input_parameters()
pfc_ti.calculate_inductor()
pfc_ti.calculate_output_capacitor()
pfc_ti.calculate_current_sense_resistor()
pfc_ti.optimize_capacitor_library(capacitor_library, max_parallel=3)

"""