import pandas as pd
import numpy as np
import os
import matplotlib.pyplot as plt
from scipy.interpolate import interp1d

# --- 1. AYARLAR VE LİMİTLER ---
MAX_ID_PULSE = 160.0  # Akım tavanı
MAX_VDS_LIMIT = 600.0 # Voltaj duvarı
SIM_DURATION = 0.100  # Analiz edilecek toplam süre (100ms)

# Her bandın kendine özel dosya, pencere süresi ve görsel ayarları
SOA_CONFIG = {
    '10ms':  {'file': 'SOA_10ms_fromdigitizer.csv', 'window': 0.010,    'color': '#d62728', 'size': 150},
    '1ms':   {'file': 'SOA_1ms_fromdigitizer.csv',    'window': 0.001,    'color': '#ff7f0e', 'size': 80},
    '100us': {'file': 'SOA_100us_fromdigitizer.csv',    'window': 0.0001,   's': 30,  'color': '#1f77b4', 'size': 40},
    '25us':  {'file': 'SOA_25us_fromdigitizer.csv',    'window': 0.000025, 'color': '#9467bd', 'size': 15}
}

SIM_RESULTS_FILE = "1249_örnek_L1_100u.csv"

def generate_individual_soa_plots_clean(sim_file, config):
    if not os.path.exists(sim_file):
        print(f"Hata: {sim_file} bulunamadı!")
        return

    # Simülasyon verisini yükle ve süreyi kısıtla
    raw_results = pd.read_csv(sim_file)
    results = raw_results[raw_results['Time[s]'] <= SIM_DURATION].copy()

    print(f"--- TEMİZ BİREYSEL SOA ANALİZİ BAŞLADI (0-{SIM_DURATION*1000:.0f}ms) ---")

    for label, info in config.items():
        if not os.path.exists(info['file']):
            print(f"⚠️ {label} için dosya bulunamadı, atlanıyor.")
            continue
        
        # A. Sınır Hesabı (Kutu Formu: Tavan ve Duvar)
        df_b = pd.read_csv(info['file'])
        df_b.columns = [c.strip() for c in df_b.columns]
        df_b = df_b[(df_b['x'] > 0) & (df_b['x'] <= MAX_VDS_LIMIT)].sort_values('x')
        
        log_x, log_y = np.log10(df_b['x']), np.log10(df_b['y'])
        interp_func = interp1d(log_x, log_y, kind='linear', fill_value="extrapolate")

        def get_limit(v):
            if v > MAX_VDS_LIMIT: return 0.0
            raw_val = 10**interp_func(np.log10(v)) if v > 0 else 160.0
            return min(raw_val, MAX_ID_PULSE)

        # B. DİNAMİK PENCERELEME (O süreye ait ortalama)
        results['Bin'] = (results['Time[s]'] // info['window']).astype(int)
        bin_stats = results.groupby('Bin').agg({'Voltage[V]': 'mean', 'Current[A]': 'mean'}).reset_index()
        
        bin_stats['Limit'] = bin_stats['Voltage[V]'].apply(get_limit)
        bin_stats['Ihlal'] = bin_stats['Current[A]'] > bin_stats['Limit']
        ihlal_sayisi = bin_stats['Ihlal'].sum()

        # C. GÖRSELLEŞTİRME (Sadece Sınır ve Ortalamalar)
        plt.figure(figsize=(10, 7))
        
        # 1. Sınır Çizgisini Çiz
        v_range = np.logspace(np.log10(10), np.log10(MAX_VDS_LIMIT), 400)
        i_limits = [get_limit(v) for v in v_range]
        line, = plt.loglog(v_range, i_limits, '--', color=info['color'], linewidth=2.5, label=f'SOA {label} Sınırı')
        plt.vlines(MAX_VDS_LIMIT, 0.1, i_limits[-1], colors=info['color'], linestyles='--', linewidth=2.5)

        # 2. Ortalamaları İşaretle (İhlal: Kırmızı, Güvenli: Kendi Rengi)
        point_colors = bin_stats['Ihlal'].map({True: '#FF0000', False: info['color']})
        plt.scatter(bin_stats['Voltage[V]'], bin_stats['Current[A]'], 
                    s=info['size'], color=point_colors, alpha=0.9, 
                    edgecolors='black', linewidths=0.5, label=f'{label} Segment Ortalamaları')

        # D. Grafik Detayları
        plt.xlabel('Vds [V]', fontsize=11)
        plt.ylabel('Id [A]', fontsize=11)
        plt.title(f'MOSFET SOA: {label} Bandı\n(Pencere: {info["window"]*1e6:.0f} µs | İhlal: {ihlal_sayisi})', fontsize=13)
        plt.grid(True, which="both", ls="-", alpha=0.2)
        plt.legend(loc='lower left', fontsize='small')
        plt.xlim(10, 1000)
        plt.ylim(0.1, 500)
        
        # Kaydet
        out_name = f'SOA_Temiz_{label}.png'
        plt.savefig(out_name, dpi=300)
        plt.close()
        
        print(f"✅ {label:5} grafiği kaydedildi: {out_name}")

if __name__ == "__main__":
    generate_individual_soa_plots_clean(SIM_RESULTS_FILE, SOA_CONFIG)