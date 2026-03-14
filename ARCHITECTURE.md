# PFC Inductor Design Studio Architecture

## Goal
Bu yapi, PFC boost induktoru icin hem tek secim analizi hem de filtreli kutuphane aramasi yapmak uzere tasarlandi. Hedef, MATLAB tasarim akisini Python backend ile yeniden kurup HTML arayuzden yonetmektir.

## Katmanlar

### 1. Data layer
- `KoolMu_toroid_core_library.py`
  - Kool Mu toroid geometri ve AL verileri.
  - Fotograflardan eklenen DC bias, permeability-temperature, core loss ve DC magnetization katsayilari.
- `wire_lib_solid_awg.py`
  - AWG tel geometri, alan, direnc ve kaba frekans/current limit verileri.

### 2. Physics layer
- `pfc_tool/materials.py`
  - `steinmetz_loss`
  - `losses_copper_ac_dowell`
  - `thermal_estimate_hurley`
  - Kool Mu bias/sicaklik/flux yardimci fonksiyonlari

Bu katman saf hesap katmanidir; UI veya HTTP bilmez.

### 3. Catalog layer
- `pfc_tool/catalog.py`
  - Core ve wire kutuphanelerini web uygulamasinin kullanacagi sade JSON-benzeri formata cevirir.

### 4. Design/search layer
- `pfc_tool/designer.py`
  - `evaluate_pfc_inductor(payload)`
    - Secilen tek core-wire cifti icin tur taramasi yapar.
  - `search_pfc_inductors(payload)`
    - Tum filtrelenmis kutuphane uzerinde core-wire-turn aramasi yapar.
  - Desteklenen girdiler:
    - Manuel hedef L
    - PFC inputlarindan hedef L turetme
    - fixed turns
    - core/wire/permeability exclude
    - hacim ve tel kesit filtreleri

### 5. Visualization layer
- `toroid_visualizer.py`
  - 2D winding render
  - 3D interactive HTML render
- `pfc_tool/visuals.py`
  - Arama sonucundaki adayi gorsel motora baglar.

### 6. Web/API layer
- `pfc_webapp.py`
  - `GET /api/catalog`
  - `POST /api/design`
  - `POST /api/search`
  - `GET /api/visualize`
  - `GET /artifacts/...`

### 7. Frontend layer
- `web/index.html`
  - Form, sonuc paneli, gorsel paneli
- `web/app.js`
  - API cagirilari, tablo guncelleme, gorsel acma
- `web/styles.css`
  - Yerlesim ve stil

## Hesap Akisi
1. Kullanici ya PFC parametreleri girer ya da manuel L/I degerleri verir.
2. Backend `operating_point` cikarir.
3. Arama modu seciliyse filtrelerden gecen core-wire kombinasyonlari taranir.
4. Her kombinasyon icin turn range degerlendirilir.
5. Her turn icin:
   - H -> DC bias permeability reduction
   - S�cakl�k -> permeability correction
   - AL_eff -> L
   - Bdc + Bac -> toplam peak flux
   - Steinmetz -> core loss
   - Dowell approx -> copper loss
   - Hurley -> thermal rise
6. Adaylar skorlanir ve siralanir.
7. En iyi aday icin 2D/3D gorsel uretilebilir.

## Mevcut Yaklasimlar ve Sinirlar
- Toroid winding fill ve MLT modeli ilk surumde yaklasiktir.
- Copper AC loss modeli solid AWG + Dowell yaklasimidir; litz veya tam katman geometrisi yok.
- Gorsel motor geometriyi boyutsal olarak iyi temsil eder ama elektromanyetik FEA degildir.
- Python 3.12 yolu hedef runtime olarak not edildi; bu oturumda ayni dosya icin erisim engeli goruldugu icin testler KiCad Python ile yapildi.

## Nasil Genisletilir
- PSO / multi-objective optimizer eklenebilir.
- Ferrite ve baska powdered iron aileleri ayni catalog katmanina eklenebilir.
- CSV export, PDF report, BOM, winding sheet ve loss-breakdown chart eklenebilir.
- Gorsel motor, secilen sonucu otomatik olarak thumbnail ile listeye de baglanabilir.
