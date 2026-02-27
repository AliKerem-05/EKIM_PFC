import math


    
# Katalogdan çıkarılan örnek 250V, 400V, 450V ve 500V Kapasitör Veritabanı
# [Kapasite (uF), Voltaj (V), Boyut (mm), Baz Ripple Akımı (A) @ 100Hz/105°C, Parça Numarası]
capacitors_db = [

    # [cite_start]--- 250V --- [cite: 193-196]
    {"cap": 100, "volt": 250, "dim": "25x30", "base_ripple": 0.7, "part": "K05250101_PM0C030"},
    {"cap": 150, "volt": 250, "dim": "25x30", "base_ripple": 0.7, "part": "K05250151_PM0C030"},
    {"cap": 220, "volt": 250, "dim": "25x30", "base_ripple": 0.9, "part": "K05250221_PM0C030"},
    {"cap": 330, "volt": 250, "dim": "30x30", "base_ripple": 1.2, "part": "K05250331_PM0D030"},
    {"cap": 470, "volt": 250, "dim": "25x40", "base_ripple": 1.5, "part": "K05250471_PM0C040"},
    {"cap": 470, "volt": 250, "dim": "30x30", "base_ripple": 1.5, "part": "K05250471_PM0D030"},
    {"cap": 680, "volt": 250, "dim": "35x40", "base_ripple": 1.8, "part": "K05250681_PM0E040"},
    {"cap": 1000, "volt": 250, "dim": "35x40", "base_ripple": 2.0, "part": "K05250102_PM0E040"},
    {"cap": 1000, "volt": 250, "dim": "35x50", "base_ripple": 2.6, "part": "K05250102_PM0E050"},
    {"cap": 1500, "volt": 250, "dim": "35x50", "base_ripple": 2.8, "part": "K05250152_PM0E050"},

    # [cite_start]--- 400V --- [cite: 200-203]
    {"cap": 68, "volt": 400, "dim": "22x30", "base_ripple": 0.47, "part": "K05400680_PM0B030"},
    {"cap": 100, "volt": 400, "dim": "22x30", "base_ripple": 0.5, "part": "K05400101_PM0B030"},
    {"cap": 100, "volt": 400, "dim": "25x30", "base_ripple": 0.5, "part": "K05400101_PM0C030"},
    {"cap": 150, "volt": 400, "dim": "25x30", "base_ripple": 0.6, "part": "K05400151_PM0C030"},
    {"cap": 150, "volt": 400, "dim": "30x30", "base_ripple": 0.8, "part": "K05400151_PM0D030"},
    {"cap": 220, "volt": 400, "dim": "25x40", "base_ripple": 1.0, "part": "K05400221_PM0C040"},
    {"cap": 220, "volt": 400, "dim": "30x30", "base_ripple": 1.1, "part": "K05400221_PM0D030"},
    {"cap": 270, "volt": 400, "dim": "25x40", "base_ripple": 1.2, "part": "K05400271_PM0C040"},
    {"cap": 330, "volt": 400, "dim": "25x45", "base_ripple": 1.3, "part": "K05400331_PM0C045"},
    {"cap": 330, "volt": 400, "dim": "30x40", "base_ripple": 1.4, "part": "K05400331_PM0D040"},
    {"cap": 330, "volt": 400, "dim": "35x30", "base_ripple": 1.4, "part": "K05400331_PM0E030"},
    {"cap": 470, "volt": 400, "dim": "30x50", "base_ripple": 1.9, "part": "K05400471_PM0D050"},
    {"cap": 470, "volt": 400, "dim": "35x40", "base_ripple": 1.9, "part": "K05400471_PM0E040"},
    {"cap": 470, "volt": 400, "dim": "35x50", "base_ripple": 2.2, "part": "K05400471_PM0E050"},
    {"cap": 680, "volt": 400, "dim": "35x50", "base_ripple": 2.2, "part": "K05400681_PM0E050"},
    {"cap": 680, "volt": 400, "dim": "40x50", "base_ripple": 2.4, "part": "K05400681_PM0F050"},
    {"cap": 820, "volt": 400, "dim": "35x60", "base_ripple": 2.5, "part": "K05400821_PM0E060"},
    {"cap": 1000, "volt": 400, "dim": "40x60", "base_ripple": 3.1, "part": "K05400102_PM0F060"},
    {"cap": 1500, "volt": 400, "dim": "40x97", "base_ripple": 5.8, "part": "K05400152_PM0F097"},

    # [cite_start]--- 450V --- [cite: 200, 204-207]
    {"cap": 68, "volt": 450, "dim": "22x30", "base_ripple": 0.47, "part": "K05450680_PM0B030"},
    {"cap": 100, "volt": 450, "dim": "25x30", "base_ripple": 0.5, "part": "K05450101_PM0C030"},
    {"cap": 100, "volt": 450, "dim": "30x25", "base_ripple": 0.7, "part": "K05450101_PM0D025"},
    {"cap": 100, "volt": 450, "dim": "30x30", "base_ripple": 0.8, "part": "K05450101_PM0D030"},
    {"cap": 150, "volt": 450, "dim": "25x40", "base_ripple": 0.9, "part": "K05450151_PM0C040"},
    {"cap": 150, "volt": 450, "dim": "30x30", "base_ripple": 0.8, "part": "K05450151_PM0D030"},
    {"cap": 150, "volt": 450, "dim": "30x40", "base_ripple": 1.0, "part": "K05450151_PM0D040"},
    {"cap": 220, "volt": 450, "dim": "25x50", "base_ripple": 0.9, "part": "K05450221_PM0C050"},
    {"cap": 220, "volt": 450, "dim": "30x40", "base_ripple": 1.1, "part": "K05450221_PM0D040"},
    {"cap": 220, "volt": 450, "dim": "35x30", "base_ripple": 1.0, "part": "K05450221_PM0E030"},
    {"cap": 330, "volt": 450, "dim": "30x50", "base_ripple": 1.25, "part": "K05450331_PM0D050"},
    {"cap": 330, "volt": 450, "dim": "35x40", "base_ripple": 1.3, "part": "K05450331_PM0E040"},
    {"cap": 330, "volt": 450, "dim": "35x50", "base_ripple": 1.4, "part": "K05450331_PM0E050"},
    {"cap": 470, "volt": 450, "dim": "35x50", "base_ripple": 1.8, "part": "K05450471_PM0E050"},
    {"cap": 680, "volt": 450, "dim": "35x50", "base_ripple": 2.1, "part": "K05450681_PM0E050"},
    {"cap": 680, "volt": 450, "dim": "35x60", "base_ripple": 2.2, "part": "K05450681_PM0E060"},
    {"cap": 820, "volt": 450, "dim": "40x60", "base_ripple": 2.3, "part": "K05450821_PM0F060"},
    {"cap": 1000, "volt": 450, "dim": "40x60", "base_ripple": 3.2, "part": "K05450102_PM0F060"},
    {"cap": 1500, "volt": 450, "dim": "40x97", "base_ripple": 5.1, "part": "K05450152_PM0F097"},

    # [cite_start]--- 500V --- [cite: 211-215]
    {"cap": 68, "volt": 500, "dim": "25x30", "base_ripple": 0.42, "part": "K05500680_PM0C030"},
    {"cap": 100, "volt": 500, "dim": "30x30", "base_ripple": 0.55, "part": "K05500101_PM0D030"},
    {"cap": 150, "volt": 500, "dim": "30x40", "base_ripple": 0.75, "part": "K05500151_PM0D040"},
    {"cap": 180, "volt": 500, "dim": "30x50", "base_ripple": 0.90, "part": "K05500181_PM0D050"},
    {"cap": 220, "volt": 500, "dim": "35x40", "base_ripple": 0.95, "part": "K05500221_PM0E040"},
    {"cap": 270, "volt": 500, "dim": "35x50", "base_ripple": 1.60, "part": "K05500271_PM0E050"},
    {"cap": 330, "volt": 500, "dim": "35x50", "base_ripple": 1.65, "part": "K05500331_PM0E050"},
    {"cap": 330, "volt": 500, "dim": "35x60", "base_ripple": 1.78, "part": "K05500331_PM0E060"},
    {"cap": 330, "volt": 500, "dim": "40x50", "base_ripple": 1.80, "part": "K05500331_PM0F050"},
    {"cap": 470, "volt": 500, "dim": "40x60", "base_ripple": 2.00, "part": "K05500471_PM0F060"}
]

def get_temp_multiplier(temp):
    """Sıcaklığa göre dalgalanma akımı çarpanını verir."""
    # Güvenlik için girilen sıcaklıktan bir üstteki sıcaklık limitinin çarpanı alınır.
    if temp <= 35: return 3.0
    elif temp <= 45: return 2.80
    elif temp <= 55: return 2.60
    elif temp <= 65: return 2.40
    elif temp <= 75: return 2.20
    elif temp <= 85: return 1.80
    elif temp <= 95: return 1.50
    elif temp <= 105: return 1.0
    elif temp <= 110: return 0.5
    else: 
        raise ValueError("Sıcaklık değeri kapasitörün maksimum çalışma limitini (110°C) aşıyor!")

def get_freq_multiplier(freq_hz):
    """Frekansa göre (160-450V DC grubu baz alınarak) dalgalanma akımı çarpanını verir."""
    if freq_hz <= 50: return 0.88
    elif freq_hz <= 100: return 1.0
    elif freq_hz <= 500: return 1.45
    elif freq_hz <= 1000: return 1.50
    else: return 1.55 # >10kHz için PFC anahtarlama frekansı gibi yüksek frekanslar

class kapasitefiltresi:

    def find_suitable_capacitors(target_ripple, temp, freq):
        """Verilen kriterleri sağlayan kapasitörleri filtreler ve sıralar."""
    
        temp_mult = get_temp_multiplier(temp)
        freq_mult = get_freq_multiplier(freq)
    
        # Toplam çarpan
        total_mult = temp_mult * freq_mult
    
        suitable_caps = []
    
        for cap in capacitors_db:
            # Kapasitörün girilen koşullardaki GÜNCELLENMİŞ Ripple kapasitesi
            actual_max_ripple = cap["base_ripple"] * total_mult
        
            # Eğer güncellenmiş kapasite bizim hedef ripple'ımızdan büyük veya eşitse listeye al
            if actual_max_ripple >= target_ripple:
                cap_copy = cap.copy()
                cap_copy["actual_max_ripple"] = round(actual_max_ripple, 2)
                suitable_caps.append(cap_copy)
            
        # Güncellenmiş dalgalanma akımı kapasitesine göre küçükten büyüğe (artan sırada) sırala
        suitable_caps.sort(key=lambda x: x["actual_max_ripple"])
    
        return suitable_caps, temp_mult, freq_mult

# --- KULLANICI GİRDİSİ BÖLÜMÜ ---
# Kendi PFC tasarımınıza göre buradaki değerleri değiştirebilirsiniz
HEDEF_RIPPLE_AKIMI = 0.91   # Amper cinsinden (örneğin devrede hesapladığınız yük)
CALISMA_SICAKLIGI = 65     # Derece (C)
CALISMA_FREKANSI = 6000   # Hertz (PFC Boost tasarımı için 65 kHz örneği)

# Başka dosyalardan import edilebilecek listeler
parca_no_sirali_liste = []
kapasite_sirali_liste = []


try:
    results, t_mult, f_mult = kapasitefiltresi.find_suitable_capacitors(HEDEF_RIPPLE_AKIMI, CALISMA_SICAKLIGI, CALISMA_FREKANSI)
    
    print(f"--- ARAMA KRİTERLERİ ---")
    print(f"Hedef Ripple Akımı : {HEDEF_RIPPLE_AKIMI} A | Toplam Çarpan: {round(t_mult * f_mult, 2)}")
    print("-" * 50)
    
    if not results:
        print("UYARI: Uygun kapasitör bulunamadı!")
    else:
        # 1. Ham Listeyi Oluştur (Sözlüklerden oluşan temel liste)
        ham_uygunlar = [
            {"part": cap["part"], "cap_uF": cap["cap"], "volt": cap["volt"]} 
            for cap in results
        ]

        # 2. PARÇA NUMARASINA GÖRE SIRALA (Alfabetik)
        parca_no_sirali_liste = sorted(ham_uygunlar, key=lambda x: x["part"])

        # 3. KAPASİTE DEĞERİNE GÖRE SIRALA (Küçükten Büyüğe)
        kapasite_sirali_liste = sorted(ham_uygunlar, key=lambda x: x["cap_uF"])

        # --- TERMINAL ÇIKTISI (Senin istediğin try-except bloğu) ---
        print(f"Uygun {len(results)} adet kapasitör bulundu:\n")
        for i, cap in enumerate(results, 1):
            print(f"{i}. Parça: {cap['part']} | Kapasite: {cap['cap']}uF | Voltaj: {cap['volt']}V")
            print(f"   İzin Verilen Maks Ripple: {cap['actual_max_ripple']} A\n")

        print("-" * 50)
        print("İKİ FARKLI LİSTE OLUŞTURULDU:")
        print("1. Parça No'ya göre sıralı (İlk 2 Örnek):")
        if parca_no_sirali_liste:
            print(f"   {parca_no_sirali_liste[0]}")
            print(f"   {parca_no_sirali_liste[1]}")
        print("2. Kapasiteye göre sıralı (İlk 2 Örnek):")
        if kapasite_sirali_liste:
            print(f"   {kapasite_sirali_liste[0]}")
            print(f"   {kapasite_sirali_liste[1]}")            

except ValueError as e:
    print("Hata:", e)