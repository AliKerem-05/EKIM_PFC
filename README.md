# EKIM_PFC

HTML arayuzlu PFC induktor tasarim araci eklendi.

## Calistirma

Tercih edilen yorumlayici:

```powershell
& 'C:\Users\emrer\AppData\Local\Programs\Python\Python312\python.exe' C:\Ekim_PFC\EKIM_PFC\pfc_webapp.py
```

Bu yorumlayici bu oturumda `Access is denied` hatasi verdigi icin testler asagidaki yorumlayici ile dogrulandi:

```powershell
& 'C:\Program Files\KiCad\8.0\bin\python.exe' C:\Ekim_PFC\EKIM_PFC\pfc_webapp.py
```

Ardindan tarayicida `http://127.0.0.1:8010` adresini ac.

## Neler var
- Manuel hedef induktans ve akim girisi
- PFC inputlarindan hedef L turetme
- Secilen core-wire cifti analizi
- Tum kutuphane icinde filtreli arama
- Core, permeability ve wire exclude alanlari
- Fixed-turn arama secenegi
- 2D ve 3D winding gorsel uretimi
- Mimari dokuman: `ARCHITECTURE.md`

## Notlar
- Backend saf Python, frontend saf HTML/CSS/JS.
- Kool Mu toroid kutuphanesine DC bias, sicaklik, core-loss ve DC magnetization katsayilari eklendi.
- PFC modu hedef L degerini dusuk sebeke gerilimi icin CCM ripple kriterinden turetir.
- AC bakir kaybi solid AWG uzerinden Dowell-benzeri yaklasik model ile hesaplanir; prototip olcumle dogrulanmalidir.
- Toroid sarim yerlesimi ilk versiyonda yaklasik geometri modeli kullanir.
- Gorsel motor icin `matplotlib` ve `plotly` eksikse `/api/visualize` hataya dusebilir.
