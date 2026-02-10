import math
import itertools

class PFCBoostDesign:
    def __init__(self, specs):
        """
        Başlangıç parametrelerini tanımlar (Tablo 1'e istinaden).
        """
        self.Vac_min = specs['Vac_min']       # Minimum giriş voltajı (V)
        self.Vac_max = specs['Vac_max']       # Maksimum giriş voltajı (V)
        self.Vo = specs['Vo']                 # Hedef çıkış voltajı (V)
        self.Po = specs['Po']                 # Çıkış gücü (W)
        self.f_sw = specs['f_sw']             # Anahtarlama frekansı (Hz)
        self.f_line = specs['f_line']         # Şebeke frekansı (Hz)
        self.ripple_percent = specs['ripple'] # İzin verilen indüktör akım dalgalanması (0.25 gibi)
        self.hold_up_time = specs['t_hold']   # Hold-up süresi (s)
        self.Vo_min_holdup = specs['Vo_min']  # Hold-up anında izin verilen min çıkış voltajı (V)
        self.V_ripple_out = specs['V_ripple'] # Çıkış voltaj dalgalanması (Vpp)
        
        print(f"--- Tasarım Başlatıldı: {self.Po}W, {self.Vo}V PFC Boost ---")

    def calculate_inductor(self):
        """
        Bölüm 2.1: Ana PFC Bobini Hesabı
        Dokümandaki Eq. 1 ve Eq. 2 kullanılır.
        """
        # Eq 1: Gerekli Endüktans (L)
        # L = (1 / %Ripple) * (Vac_min^2 / Po) * (1 - (sqrt(2)*Vac_min / Vo)) * (1 / f_sw)
        term1 = 1 / self.ripple_percent
        term2 = (self.Vac_min ** 2) / self.Po
        term3 = 1 - ((math.sqrt(2) * self.Vac_min) / self.Vo)
        term4 = 1 / self.f_sw
        
        L_calc = term1 * term2 * term3 * term4
        self.L_calc_uH = L_calc * 1e6 # MicroHenry'e çevir
        
        # Eq 2: Maksimum Bobin Akımı (I_L_max)
        # I_Lmax = (sqrt(2) * Po / Vac_min) * (1 + %Ripple/2)
        I_L_max = ((math.sqrt(2) * self.Po) / self.Vac_min) * (1 + (self.ripple_percent / 2))
        
        print(f"\n[Bobin Tasarımı - Eq. 1 & 2]")
        print(f"Hesaplanan Endüktans (L): {self.L_calc_uH:.2f} uH")
        print(f"Maksimum Akım (I_L_max): {I_L_max:.2f} A")
        
        return self.L_calc_uH, I_L_max

    def calculate_output_capacitor(self):
        """
        Bölüm 2.5: Çıkış Kapasitörü Hesabı
        Hold-up time (Eq. 30) ve Ripple (Eq. 31) gereksinimlerine göre hesaplanır.
        """
        # Eq 30: Hold-up time gereksinimi
        # Co >= (2 * Po * t_hold) / (Vo^2 - Vo_min^2)
        Co_hold = (2 * self.Po * self.hold_up_time) / (self.Vo**2 - self.Vo_min_holdup**2)
        
        # Eq 31: Düşük frekans ripple gereksinimi
        # Co >= Po / (2 * pi * f_line * V_ripple * Vo)
        Co_ripple = self.Po / (2 * math.pi * self.f_line * self.V_ripple_out * self.Vo)
        
        # İki değerden büyük olan seçilir 
        self.Co_calc_uF = max(Co_hold, Co_ripple) * 1e6
        
        print(f"\n[Kapasitör Tasarımı - Eq. 30 & 31]")
        print(f"Hold-up için gereken: {Co_hold*1e6:.2f} uF")
        print(f"Ripple için gereken: {Co_ripple*1e6:.2f} uF")
        print(f"SEÇİLEN Teorik Değer: {self.Co_calc_uF:.2f} uF")
        
        return self.Co_calc_uF

    def find_capacitor_combination(self, library, max_parallel=3):
        """
        İLERİ AŞAMA: Kütüphane Bazlı Seçim
        Verilen kütüphanedeki kapasitörleri paralel bağlayarak hedefe yaklaşır.
        """
        target = self.Co_calc_uF
        best_diff = float('inf')
        best_combo = None
        
        print(f"\n[Kütüphane Optimizasyonu]")
        print(f"Hedef: {target:.2f} uF için kombinasyonlar taranıyor...")

        # Kütüphanedeki elemanlarla 1'li, 2'li ve 3'lü kombinasyonları dene
        # Gerçek hayatta genellikle paralel bağlantı ile kapasite artırılır.
        for r in range(1, max_parallel + 1):
            for combo in itertools.combinations_with_replacement(library, r):
                current_sum = sum(combo)
                diff = abs(target - current_sum)
                
                if diff < best_diff:
                    best_diff = diff
                    best_combo = combo
        
        print(f"En İyi Kombinasyon: {best_combo} uF")
        print(f"Elde Edilen Toplam: {sum(best_combo):.2f} uF")
        print(f"Hata Payı: {best_diff:.2f} uF")

# --- KULLANIM ---

# 1. Başlangıç Değerleri (Dokümandaki Tablo 1 örneği baz alınmıştır )
design_specs = {
    'Vac_min': 207,      # V
    'Vac_max': 253,     # V
    'Vo': 400,          # V
    'Po': 250,         # W
    'f_sw': 65e3,      # 65 kHz [cite: 127]
    'f_line': 60,       # Hz
    'ripple': 0.25,     # %25 Ripple [cite: 129]
    't_hold': 16.6e-3,  # 16.6 ms [cite: 134]
    'Vo_min': 380,      # Hold-up minimum voltajı [cite: 134]
    'V_ripple': 10      # 10 Vpp [cite: 133]
}

# 2. Tasarım Nesnesini Oluştur
pfc = PFCBoostDesign(design_specs)

# 3. Teorik Hesaplamaları Yap
calc_L, calc_I = pfc.calculate_inductor()
calc_C = pfc.calculate_output_capacitor()

# 4. İleri Aşama: Kapasitör Kütüphanesinden Seçim Yap
# Örnek Kütüphane (uF cinsinden standart değerler)
capacitor_library = [100, 150, 220, 330, 470, 560, 680]

# Hedef değere ulaşmak için kütüphaneden en iyi kombinasyonu bul
pfc.find_capacitor_combination(capacitor_library, max_parallel=3)