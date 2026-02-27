from pfc_calculators import InfineonPFC, TIPFC
from capacitor_manager import get_filtered_pool
from combination_finder import find_best_combination

# --- 1. TASARIM GİRDİLERİ ---
design_specs = {
    'Vac_min': 207, 'Vin_min': 207, 'Vo': 400, 'Po': 500, 
    'f_sw': 65000, 'f_line': 50, 'f_line_min': 50,
    'ripple': 0.25, 't_hold': 16.6e-3, 'Vo_min': 380, 'V_ripple': 10,
    'efficiency': 0.94
}

# Çalışma Koşulları
CALISMA_SICAKLIGI = 65
CALISMA_FREKANSI = 65000
HEDEF_RIPPLE_AKIMI = 1.2  # Tasarımda hesaplanan yük akımı baz alınabilir

# --- 2. TEORİK HESAPLAMA ---
infineon = InfineonPFC(design_specs).calculate_requirements()
target_cap = infineon["C_target_uF"]

print(f"Taslak Hazırlandı: Hedef {target_cap:.2f} uF ve {HEDEF_RIPPLE_AKIMI}A Ripple.")

# --- 3. DİNAMİK SEÇİM DÖNGÜSÜ ---
excluded = []

while True:
    # Stokta olmayanları çıkararak havuzu filtrele
    _, pool_by_cap = get_filtered_pool(HEDEF_RIPPLE_AKIMI, CALISMA_SICAKLIGI, CALISMA_FREKANSI, excluded)
    
    # En yakın kombinasyonu bul
    parts, caps, total_val = find_best_combination(pool_by_cap, target_cap)
    
    if not parts:
        print("\n!!! KRİTİK HATA: Mevcut stoklarla uygun çözüm bulunamıyor!")
        break

    print("\n" + "="*40)
    print("ÖNERİLEN ÇÖZÜM:")
    print(f"Toplam Kapasite: {total_val} uF")
    print(f"Kullanılan Parçalar: {parts}")
    print(f"Bireysel Değerler: {caps}")
    print("="*40)
    
    # Stok Kontrolü
    ans = input("\nStokta bulunmayan bir parça var mı? (Vaksa parça nosunu girin, yoksa 'n'): ").strip()
    
    if ans.lower() == 'n':
        print("\nTasarım onaylandı. Parça listesi oluşturuluyor...")
        break
    else:
        # Belirtilen parçayı kara listeye ekle ve döngüyü tekrar çalıştır
        print(f">> {ans} 'stokta yok' olarak işaretlendi. Yeni hesaplama yapılıyor...")
        excluded.append(ans)