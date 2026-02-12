
from infineon_preselection import PFCBoostDesign
from texas_Inst_preselection import TIPFCBoostDesign

design_specs = {
    'Vac_min': 207,      # V
    'Vac_max': 253,     # V
    'Vo': 400,          # V
    'Po': 500,         # W
    'f_sw': 65e3,      # 65 kHz [cite: 127]
    'f_line': 60,       # Hz
    'ripple': 0.25,     # %25 Ripple [cite: 129]
    't_hold': 16.6e-3,  # 16.6 ms [cite: 134]
    'Vo_min': 380,      # Hold-up minimum voltajı [cite: 134]
    'V_ripple': 10      # 10 Vpp [cite: 133]
}

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

print("Infineon Preselection")
# 2. Tasarım Nesnesini Oluştur
pfc = PFCBoostDesign(design_specs)
# 3. Teorik Hesaplamaları Yap
calc_L, calc_I = pfc.calculate_inductor()
calc_C = pfc.calculate_output_capacitor()

pfc.find_capacitor_combination(capacitor_library, max_parallel=3)

 
print("-"*50)

print("Texas Instruments Preselection")
pfc_ti = TIPFCBoostDesign(ti_specs)
pfc_ti.calculate_input_parameters()
pfc_ti.calculate_inductor()
pfc_ti.calculate_output_capacitor()
pfc_ti.calculate_current_sense_resistor()
pfc_ti.optimize_capacitor_library(capacitor_library, max_parallel=3)

