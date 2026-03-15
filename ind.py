import os
import pandas as pd
from PyLTSpice import SimRunner, AscEditor, RawRead
from pathlib import Path

# --- AYARLAR ---
ASC_FILE = r"C:\Users\Ali Kerem\Desktop\Arastirmalar\Ekim Projeleri\PFC\inductor\Ltspice_Python\1249_örnek.asc"
OUTPUT_DIR = Path("./Analiz_Sonuclari")
L1_LISTESI = ["100u", "150u", "220u", "330u"]
PERIYOT = 0.100  # 20ms (Analiz edilecek süre)
SIM_SURESI = 0.200 # Toplam simülasyon süresi (Örn: 2 periyot)
MAX_STEP = "1n"    # 1 nanosaniye maksimum adım

def veri_isleme_callback(raw_file, log_file):
    print(f"📊 Veri işleniyor: {os.path.basename(raw_file)}")
    try:
        ltr = RawRead(raw_file)
        time = ltr.get_trace('time').get_wave(0)
        
        # Trace isimlerini kontrol edin (V(n007) ve I(L1) doğru mu?)
        voltage = ltr.get_trace('V(n007)').get_wave(0)
        current = ltr.get_trace('I(L1)').get_wave(0)
        
        # Sadece son periyodu filtrele
        t_start = max(0, time[-1] - PERIYOT)
        mask = (time >= t_start)
        
        df = pd.DataFrame({
            'Time[s]': time[mask],
            'Voltage[V]': voltage[mask],
            'Current[A]': current[mask]
        })
        
        csv_path = Path(raw_file).with_suffix('.csv')
        df.to_csv(csv_path, index=False)
        print(f"✅ CSV Hazır ({len(df)} satır): {csv_path.name}")
        
    except Exception as e:
        print(f"❌ Hata oluştu ({os.path.basename(raw_file)}): {e}")

def main():
    OUTPUT_DIR.mkdir(exist_ok=True)
    
    runner = SimRunner(output_folder=str(OUTPUT_DIR))
    netlist = AscEditor(ASC_FILE)
    
    # KRİTİK AYAR: LTSpice'ın veri noktalarını silmesini (compression) engelle
    netlist.add_instruction(".options plotwinsize=0")
    # Alternatif olarak hassasiyeti artırmak için numdgt ekleyebilirsiniz
    netlist.add_instruction(".options numdgt=7")

    print(f"🚀 {len(L1_LISTESI)} farklı L1 değeri için simülasyonlar başlıyor...\n")
    
    for l1_val in L1_LISTESI:
        netlist.set_component_value('L1', l1_val)
        
        # Dinamik .tran komutu: .tran <stop_time> <start_time> <max_step>
        netlist.add_instruction(f".tran {SIM_SURESI} 0 {MAX_STEP}")
        
        dosya_adi = f"{Path(ASC_FILE).stem}_L1_{l1_val}.net"
        runner.run(netlist, run_filename=dosya_adi, callback=veri_isleme_callback)
    
    runner.wait_completion()
    print("\n🏁 Tüm işlemler başarıyla tamamlandı!")

if __name__ == "__main__":
    main()