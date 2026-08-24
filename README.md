# J.A.R.V.I.S. Masaüstü Yapay Zeka Asistanı

Bu proje, Marvel evrenindeki Jarvis karakterinden esinlenerek geliştirilmiş, Windows işletim sisteminizle entegre çalışan hafif ve akıllı bir sesli asistandır.

## Özellikler
- 🖥️ **Masaüstü Reaktör Logosu (Widget):** Ekranın sağ üst köşesinde duran, şeffaf arka planlı dairesel holografik widget. (Sürükleyip bırakabilirsiniz, çift tıklayarak uyandırabilirsiniz).
- 🔑 **Kısayol Uyandırma:** Arka planda sessiz çalışırken **`Ctrl + J`** tuşlarına basarak uyandırabilirsiniz.
- 🗣️ **Sesli ve Sayısal Seçenek Kontrolü:** Jarvis seçenekleri okuduğunda ("1. Projeyi çalıştır, 2. Logları kontrol et" vb.), sadece **"Bir"**, **"İki"** demeniz ya da klavyeden **"1"**, **"2"** tuşlarına basmanız yeterlidir.
- ⚙️ **Gerçek Donanım Durumu (Telemetri):** CPU, RAM ve Pil durumunuza bakarak bunları Iron Man tarzı (Reaktör yükü, Hafıza matrisi, Güç hücreleri) sesli raporlar.
- 💤 **Gelişmiş Durum Kontrolü ve 20 Dk Koruması:** 
  - *"Jarvis dur"* veya *"Kapan"* dediğinizde uyku moduna geçer.
  - 20 dakika boyunca konuşma veya istek gelmezse otomatik olarak bekleme (Standby) moduna geçerek işlemci tüketimini sıfırlar.
- 🔌 **Otomatik Başlatma (Startup):** Windows başlangıcına eklenerek bilgisayar açıldığında tamamen gizli (Console penceresi olmadan) arka planda başlar.

---

## Kurulum ve Başlatma

### 1. API Anahtarını Tanımlama
1. Klasördeki `.env` dosyasını bir metin editörüyle açın.
2. `GEMINI_API_KEY=YOUR_GEMINI_API_KEY_HERE` alanındaki yere kendi Gemini API anahtarınızı yapıştırın.
   *(Anahtarınız yoksa [Google AI Studio](https://aistudio.google.com/) üzerinden ücretsiz bir tane alabilirsiniz).*

### 2. Windows Başlangıcına Kaydetme (Görünmez Çalışma)
Jarvis'in bilgisayarınız açıldığında arka planda otomatik olarak ve **tamamen görünmez şekilde** (hiçbir siyah konsol penceresi yanıp sönmeden) başlaması için:
1. Bu klasörde bir PowerShell penceresi açın.
2. Aşağıdaki komutu çalıştırın:
   ```powershell
   Set-ExecutionPolicy Bypass -Scope Process -Force; .\register_startup.ps1
   ```
3. Artık bilgisayarınız her başladığında Jarvis sağ üst köşede hazır bekleyecektir!

### 3. Manuel Olarak Başlatma (Hemen Denemek İçin)
PowerShell terminalinde şu komutu yazarak Jarvis'i hemen başlatabilirsiniz:
```powershell
$env:PATH = "C:\Users\21COMP1067\.local\bin;" + $env:PATH; uv run jarvis.py
```

---

## Durum Renk Kodları
- 🔵 **Mavi Halka:** Standby (Bekleme/Hazırda bekliyor, CPU kullanımı sıfırdır. Sadece "Jarvis" anahtar kelimesini veya `Ctrl+J` kısayolunu bekler).
- 🟢 **Yeşil Halka:** Aktif (Sizi dinliyor, adını söylemeden doğrudan komutlar verebilirsiniz).
- 🟡 **Sarı/Altın Halka:** Düşünüyor (Gemini API'den yanıt bekleniyor).
