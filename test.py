import pandas as pd
import numpy as np
import os
import matplotlib.pyplot as plt
from scipy.interpolate import interp1d

# --- 1. AYARLAR VE LİMİTLER ---
MAX_ID_PULSE = 160.0  # Akım tavanı
MAX_VDS_LIMIT = 600.0 # Voltaj duvarı
SIM_DURATION = 0.100  # 100ms Analiz Süresi

# Konfigürasyon: Dosya, Pencere Süresi, Nokta Boyutu, Renk
SOA_CONFIG = {
    '10ms':  {'file': 'SOA_10ms_fromdigitizer.csv', 'window': 0.010,    's': 180, 'color': '#d62728'}, # Büyük
    '1ms':   {'file': 'SOA_1ms_fromdigitizer.csv',    'window': 0.001,    's': 80,  'color': '#ff7f0e'}, # Orta
    '100us': {'file': 'SOA_100us_fromdigitizer.csv',    'window': 0.0001,   's': 25,  'color': '#1f77b4'}, # Küçük
    '25us':  {'file': 'SOA_25us_fromdigitizer.csv',    'window': 0.000025, 's': 8,   'color': '#9467bd'}  # Çok Küçük
}

SIM_RESULTS_FILE = "1249_örnek_L1_100u.csv"

def run_pro_dynamic_soa(sim_file, config):
    if not os.path.exists(sim_file):
        print(f"Hata: {sim_file} bulunamadı!")
        return

    # 2. VERİYİ YÜKLE VE 100ms İLE KISITLA
    raw_data = pd.read_csv(sim_file)
    results = raw_data[raw_data['Time[s]'] <= SIM_DURATION].copy()
    
    plt.figure(figsize=(14, 10))
    print(f"--- PRO ANALİZ: 0-100ms Tarama Başladı ---")
    print(f"{'Band':<8} | {'Pencere':<10} | {'Nokta Sayısı':<12} | {'Durum'}")
    print("-" * 50)

    # Katmanlama sırası (Z-order): Küçük noktaları alta, büyükleri üste koyuyoruz
    # 25us -> 100us -> 1ms -> 10ms
    sorted_labels = ['25us', '100us', '1ms', '10ms']
    all_reports = []

    # 3. ANALİZ DÖNGÜSÜ
    for z_idx, label in enumerate(sorted_labels):
        info = config[label]
        if not os.path.exists(info['file']):
            print(f"{label:<8} | Dosya eksik!")
            continue

        # A. Sınır Hesabı (Kutu Formu)
        df_b = pd.read_csv(info['file'])
        df_b.columns = [c.strip() for c in df_b.columns]
        df_b = df_b[(df_b['x'] > 0) & (df_b['x'] <= MAX_VDS_LIMIT)].sort_values('x')
        interp_func = interp1d(np.log10(df_b['x']), np.log10(df_b['y']), fill_value="extrapolate")

        def get_limit(v):
            if v > MAX_VDS_LIMIT: return 0.0
            return min(10**interp_func(np.log10(v)), MAX_ID_PULSE)

        # B. Dinamik Gruplama (Her bant kendi süresine göre)
        results['Bin'] = (results['Time[s]'] // info['window']).astype(int)
        bin_stats = results.groupby('Bin').agg({'Voltage[V]': 'mean', 'Current[A]': 'mean'}).reset_index()

        # C. İhlal Denetimi
        bin_stats['Limit'] = bin_stats['Voltage[V]'].apply(get_limit)
        bin_stats['Ihlal'] = bin_stats['Current[A]'] > bin_stats['Limit']
        
        ihlal_count = bin_stats['Ihlal'].sum()
        status = f"❌ {ihlal_count} İHLAL" if ihlal_count > 0 else "✅ GÜVENLİ"
        print(f"{label:<8} | {info['window']*1e6:>6.0f} µs | {len(bin_stats):<12} | {status}")

        # D. Görselleştirme
        # Sınır Çizgisi
        v_range = np.logspace(1, np.log10(MAX_VDS_LIMIT), 200)
        i_limits = [get_limit(v) for v in v_range]
        plt.loglog(v_range, i_limits, '--', color=info['color'], alpha=0.6, label=f'Limit {label}')
        plt.vlines(MAX_VDS_LIMIT, 0.1, i_limits[-1], colors=info['color'], linestyles='--', alpha=0.6)

        # Noktalar: İhlaller Kırmızı, Güvenli Noktalar Kendi Renginde
        colors = bin_stats['Ihlal'].map({True: 'red', False: info['color']})
        
        plt.scatter(bin_stats['Voltage[V]'], bin_stats['Current[A]'], 
                    s=info['s'], color=colors, alpha=0.5 if label=='25us' else 0.8, 
                    edgecolors='black' if label!='25us' else None, 
                    linewidths=0.5, zorder=z_idx+5, 
                    label=f'Ortalamalar ({label})')
        
        bin_stats['Band'] = label
        all_reports.append(bin_stats)

    # 4. GRAFİK AYARLARI
    plt.xlabel('Dren-Kaynak Voltajı Vds [V]', fontsize=12)
    plt.ylabel('Dren Akımı Id [A]', fontsize=12)
    plt.title(f'Kapsamlı MOSFET SOA Analizi (0-100ms)\nNokta Boyutu = Örnekleme Penceresi', fontsize=14)
    plt.grid(True, which="both", ls="-", alpha=0.2)
    plt.legend(loc='lower left', fontsize='x-small', ncol=2)
    plt.xlim(10, 1000)
    plt.ylim(0.1, 500)
    
    plt.savefig('SOA_Pro_Analysis_100ms.png', dpi=300)
    
    # Raporu Kaydet
    pd.concat(all_reports).to_csv('SOA_Pro_Summary.csv', index=False)
    print(f"\n✅ Analiz bitti! Görsel: 'SOA_Pro_Analysis_100ms.png' hazır.")

if __name__ == "__main__":
    run_pro_dynamic_soa(SIM_RESULTS_FILE, SOA_CONFIG)