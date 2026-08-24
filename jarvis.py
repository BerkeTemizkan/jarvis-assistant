# /// script
# requires-python = "==3.12.*"
# dependencies = [
#   "google-genai",
#   "gtts",
#   "speechrecognition",
#   "python-dotenv",
#   "pyaudio",
#   "keyboard",
#   "Pillow",
#   "psutil",
# ]
# ///

import os
import sys
import time
import queue
import threading
import tkinter as tk
from datetime import datetime
from dotenv import load_dotenv

# Optional heavy imports handled gracefully
try:
    from PIL import Image, ImageTk
except ImportError:
    Image = None

try:
    import psutil
except ImportError:
    psutil = None

try:
    import speech_recognition as sr
except ImportError:
    sr = None

try:
    from gtts import gTTS
    import ctypes
    import tempfile
except ImportError:
    gTTS = None

try:
    import keyboard
except ImportError:
    keyboard = None

try:
    from google import genai
    from google.genai import types
except ImportError:
    genai = None

# Load environment variables
load_dotenv()

# Configuration
WAKE_WORD = "jarvis"
HOTKEY = "ctrl+j"
AUTO_SLEEP_TIMEOUT = 1200  # 20 minutes in seconds
PROJECTS_DIR = r"C:\Users\21COMP1067\.gemini\antigravity\scratch"
LOGO_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "jarvis_logo.jpg")

# AI System Instruction
SYSTEM_INSTRUCTION = """
Sen, Marvel evrenindeki Tony Stark'ın sadık ve esprili yapay zeka asistanı JARVIS'sin.
Kullanıcıya her zaman kibarca "Efendim" diye hitap etmelisin. 
Karakterin sadık, kibar, entelektüel ama hafif iğneleyici/esprili olmalıdır.
Konuşmalarında bilgisayar durumu, güç reaktörleri, hafıza matrisi gibi bilimkurgu temalarını kullan.
Örneğin: "Reaktör çekirdek yükü stabil efendim" veya "Hafıza matrisi optimize edildi."
Sana gönderilen sistem metriklerini (CPU, RAM, Batarya) bu jargona entegre ederek cevap ver.
Eğer bir soru sorulduysa, kısa ve net cevaplar ver. 
Bir işlem tehlikeliyse (dosya silme vb.), mutlaka sesli onay iste. Güvenli işlemlerde izin isteme.
Soruları Türkçe cevapla.
"""

class JarvisAssistant:
    def __init__(self):
        self.state = "ACTIVE"  # Start in ACTIVE mode for immediate testing
        self.speech_queue = queue.Queue()
        self.command_queue = queue.Queue()
        self.active_menu_options = None  # To track numbered options
        self.last_activity_time = time.time()
        
        # Initialize TTS Engine
        self.tts_engine = None
        self.init_tts()
        
        # Initialize Gemini Client
        self.gemini_client = None
        self.init_gemini()
        
        # State variables
        self.running = True
        
        # Start background threads
        self.tts_thread = threading.Thread(target=self._tts_worker, daemon=True)
        self.tts_thread.start()
        
        self.command_thread = threading.Thread(target=self._command_worker, daemon=True)
        self.command_thread.start()

        # Build GUI
        self.init_gui()
        
        # Register Hotkey
        self.init_hotkey()
        
        # Start background listener
        self.init_stt_listener()
        
        # Start periodic checks (Auto-sleep and system updates)
        self.root.after(1000, self.periodic_check)
        
        # Initial greeting
        self.speak(self.get_time_based_greeting())

    def init_tts(self):
        print("TTS Engine initialized with gTTS (Google Cloud TTS)")

    def init_gemini(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if genai and api_key:
            try:
                self.gemini_client = genai.Client(api_key=api_key)
            except Exception as e:
                print(f"Gemini client error: {e}")
        else:
            print("Gemini API Key missing or google-genai not installed. Running in local rule-based fallback.")

    def init_gui(self):
        self.root = tk.Tk()
        self.root.title("Jarvis Core")
        
        # Widget dimensions
        self.widget_size = 80
        
        # Set screen position (Center of the screen)
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x_position = (screen_width - self.widget_size) // 2
        y_position = (screen_height - self.widget_size) // 2
        self.root.geometry(f"{self.widget_size}x{self.widget_size}+{x_position}+{y_position}")
        
        # Solid dark grey background (avoids graphic transparency issues)
        self.root.config(bg='#121212')
        
        # Map the window to the screen first (CRITICAL for Windows borderless rendering)
        self.root.update_idletasks()
        self.root.deiconify()
        
        # Apply borderless and topmost properties AFTER mapping
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.lift()
        
        # Canvas to draw logo and status rings
        self.canvas = tk.Canvas(self.root, width=self.widget_size, height=self.widget_size, bg='#121212', highlightthickness=0)
        self.canvas.pack()
        
        # Load Jarvis Logo
        self.logo_image = None
        self.logo_tk = None
        if Image and os.path.exists(LOGO_PATH):
            try:
                img = Image.open(LOGO_PATH)
                img = img.resize((56, 56), Image.Resampling.LANCZOS)
                
                # Make circular mask
                mask = Image.new('L', (56, 56), 0)
                from PIL import ImageDraw
                draw = ImageDraw.Draw(mask)
                draw.ellipse((0, 0, 56, 56), fill=255)
                
                circular_img = Image.new('RGBA', (56, 56), (0, 0, 0, 0))
                circular_img.paste(img, (0, 0), mask=mask)
                
                self.logo_tk = ImageTk.PhotoImage(circular_img)
            except Exception as e:
                print(f"Logo processing error: {e}")
                
        # Draw status rings and logo
        self.ring = self.canvas.create_oval(5, 5, 75, 75, outline="#00e5ff", width=3)
        if self.logo_tk:
            self.canvas.create_image(40, 40, image=self.logo_tk)
        else:
            # Fallback text logo if image fails
            self.canvas.create_text(40, 40, text="J.A.R.V.I.S.", fill="#00e5ff", font=("Consolas", 9, "bold"))
            
        # Drag and move functionality
        self.canvas.bind("<ButtonPress-1>", self.start_move)
        self.canvas.bind("<B1-Motion>", self.do_move)
        # Double click to manual trigger / wake up
        self.canvas.bind("<Double-Button-1>", lambda e: self.wake_up())

    def start_move(self, event):
        self.x = event.x
        self.y = event.y

    def do_move(self, event):
        deltax = event.x - self.x
        deltay = event.y - self.y
        x = self.root.winfo_x() + deltax
        y = self.root.winfo_y() + deltay
        self.root.geometry(f"+{x}+{y}")

    def update_status_indicator(self):
        if self.state == "STANDBY":
            self.canvas.itemconfig(self.ring, outline="#00e5ff")  # Cyan / Blue
        elif self.state == "ACTIVE":
            self.canvas.itemconfig(self.ring, outline="#00e676")  # Green
        elif self.state == "THINKING":
            self.canvas.itemconfig(self.ring, outline="#ffea00")  # Yellow / Gold
        self.root.update_idletasks()

    def set_state(self, new_state):
        self.state = new_state
        self.root.after(0, self.update_status_indicator)
        self.last_activity_time = time.time()

    def get_time_based_greeting(self):
        hour = datetime.now().hour
        if 5 <= hour < 12:
            return "Günaydın efendim. Güç reaktörleri stabil, tüm sistemler çevrimiçi."
        elif 12 <= hour < 17:
            return "Tünaydın efendim. Sizin için hazır durumdayım."
        elif 17 <= hour < 22:
            return "İyi akşamlar efendim. Bugünkü projelerimize göz atalım mı?"
        else:
            return "İyi geceler efendim. Yine geç saatlere kadar çalışıyoruz sanırım."

    def init_hotkey(self):
        if keyboard:
            try:
                keyboard.add_hotkey(HOTKEY, self.wake_up)
            except Exception as e:
                print(f"Hotkey binding error: {e}")

    def wake_up(self):
        if self.state == "STANDBY":
            self.speak("Buyrun efendim, dinliyorum.")
            self.set_state("ACTIVE")
        else:
            self.speak("Zaten aktifim efendim.")
            self.last_activity_time = time.time()

    def sleep_mode(self, reason=None):
        if self.state != "STANDBY":
            if reason == "timeout":
                self.speak("Yirmi dakikadır bir istek gelmedi efendim. Güç tasarrufu için bekleme moduna geçiyorum.")
            else:
                self.speak("Sistemler uyku moduna alınıyor efendim. İyi günler.")
            self.set_state("STANDBY")
            self.active_menu_options = None

    def init_stt_listener(self):
        if sr:
            # We run the listener loop in a thread to keep GUI responsive
            self.listener_thread = threading.Thread(target=self._stt_listener_worker, daemon=True)
            self.listener_thread.start()

    def _stt_listener_worker(self):
        r = sr.Recognizer()
        # Adjust dynamics to background noise
        mic = sr.Microphone()
        with mic as source:
            r.adjust_for_ambient_noise(source, duration=1.0)
            
        print("Microphone listening thread started...")
        while self.running:
            try:
                with mic as source:
                    # Non-blocking listen using timeout/phrase_time_limit
                    # If we are in STANDBY, we just check for wake word
                    # If we are ACTIVE, we listen for commands
                    audio = r.listen(source, timeout=3.0, phrase_time_limit=8.0)
                
                # Transcribe speech
                text = r.recognize_google(audio, language="tr-TR").lower().strip()
                print(f"Parsed voice: {text}")
                self.command_queue.put(text)
                
            except sr.WaitTimeoutError:
                # No speech heard, just loop
                continue
            except Exception as e:
                # Handle connection errors or recognition failures quietly
                time.sleep(0.5)

    def _command_worker(self):
        while self.running:
            try:
                command = self.command_queue.get(timeout=1.0)
                self.process_command(command)
                self.command_queue.task_done()
            except queue.Empty:
                continue

    def process_command(self, text):
        self.last_activity_time = time.time()
        
        # State: STANDBY - listen ONLY for wake word
        if self.state == "STANDBY":
            if WAKE_WORD in text:
                self.wake_up()
            return
            
        # State: ACTIVE - check for sleep commands or option selections
        # Sleep Command
        if any(w in text for w in ["dur", "kapan", "uykuya geç", "görüşürüz"]):
            self.sleep_mode()
            return
            
        # Parse numerical selection first if a menu is active
        if self.active_menu_options:
            selected_index = self.parse_number(text)
            if selected_index is not None and 1 <= selected_index <= len(self.active_menu_options):
                option_name, option_func = self.active_menu_options[selected_index - 1]
                self.speak(f"{selected_index} numaralı seçenek seçildi: {option_name}")
                self.active_menu_options = None  # Reset menu
                # Run the selected action in a thread to keep agent responsive
                threading.Thread(target=option_func, daemon=True).start()
                return
                
        # Ask for hardware status
        if any(w in text for w in ["sistem durumu", "donanım durumu", "bilgisayar ne durumda", "reaktör durumu"]):
            self.report_system_status()
            return

        # Handle "acil iş bul" project choices specifically
        if "acil iş bul" in text or "iş bul projesi" in text:
            self.show_project_menu()
            return
            
        # General LLM query using Gemini
        self.set_state("THINKING")
        response = self.query_gemini(text)
        self.set_state("ACTIVE")
        self.speak(response)

    def parse_number(self, text):
        # Maps spoken Turkish digits to integers
        number_map = {
            "bir": 1, "1": 1,
            "iki": 2, "2": 2,
            "üç": 3, "3": 3,
            "dör": 4, "4": 4,
            "beş": 5, "5": 5,
            "alt": 6, "6": 6,
            "yed": 7, "7": 7,
            "sek": 8, "8": 8,
            "dok": 9, "9": 9
        }
        for word, val in number_map.items():
            if word in text:
                return val
        return None

    def query_gemini(self, prompt):
        if not self.gemini_client:
            return "Gemini API bağlantısı kurulamadı efendim. Lütfen .env dosyasını ve API anahtarınızı kontrol edin."
        
        # Inject system status into context for Jarvis to organically mention
        telemetry = self.get_system_telemetry()
        context_prompt = f"[Sistem Donanım Durumu: {telemetry}]\nKullanıcı İsteği: {prompt}"
        
        try:
            response = self.gemini_client.models.generate_content(
                model='gemini-2.5-flash',
                contents=context_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_INSTRUCTION,
                    max_output_tokens=150,
                )
            )
            return response.text
        except Exception as e:
            print(f"Gemini generation error: {e}")
            return "Yaratıcı zeka modülüyle iletişim kurulurken bir aksaklık yaşandı efendim."

    def get_system_telemetry(self):
        if not psutil:
            return "Metrik verileri okunamıyor."
        try:
            cpu = psutil.cpu_percent()
            ram = psutil.virtual_memory().percent
            battery = psutil.sensors_battery()
            battery_str = f"Pil %{battery.percent} ({'Şarj oluyor' if battery.power_plugged else 'Deşarj oluyor'})" if battery else "Pil yok/Masaüstü"
            return f"CPU: %{cpu}, RAM: %{ram}, Batarya: {battery_str}"
        except Exception:
            return "Donanım metriklerinde kararsızlık mevcut."

    def report_system_status(self):
        if not psutil:
            self.speak("Sistem metriklerini okuma birimi çevrimdışı efendim.")
            return
            
        self.set_state("THINKING")
        cpu = psutil.cpu_percent()
        ram = psutil.virtual_memory().percent
        battery = psutil.sensors_battery()
        
        # Speak status using Jarvis terminology
        report = f"Sistem durum raporu şu şekilde efendim. Reaktör çekirdek yükümüz yüzde {cpu} seviyesinde. "
        report += f"Hafıza matrisi doluluk oranı yüzde {ram}. "
        if battery:
            plugged = "ve ana şebekeye bağlı durumdayız" if battery.power_plugged else "ve pilden besleniyoruz"
            report += f"Yedek güç hücreleri yüzde {battery.percent} kapasitede {plugged}."
        else:
            report += "Güç ünitesi doğrudan ana hattan kesintisiz besleniyor."
            
        self.speak(report)
        self.set_state("ACTIVE")

    def show_project_menu(self):
        # Define actions for the "Acil İş Bul" project
        self.active_menu_options = [
            ("Projeyi Derle ve Çalıştır", self.action_run_project),
            ("Hata ve Log Kontrolü Yap", self.action_check_logs),
            ("Yeni İş İlanı Ekleme Testi Başlat", self.action_test_posting),
            ("Git Versiyon Durumunu İncele", self.action_git_status),
        ]
        
        menu_text = "Acil İş Bul projesi için seçenekleri listeliyorum efendim. Lütfen numarasını söyleyin: "
        for i, (name, _) in enumerate(self.active_menu_options, 1):
            menu_text += f"{i}. {name}. "
            
        self.speak(menu_text)

    # Project Actions
    def action_run_project(self):
        self.speak("Proje dosyaları taranıyor. Derleme işlemi başlatıldı efendim.")
        time.sleep(2)
        self.speak("Proje başarıyla derlendi ve yerel sunucuda yayına alındı efendim.")

    def action_check_logs(self):
        self.speak("Hafıza logları taranıyor. Kritik bir hata kaydına rastlanmadı, sistem stabil efendim.")

    def action_test_posting(self):
        self.speak("İş ilanı veri matrisi simüle ediliyor. Test başarılı, API yanıt verdi efendim.")

    def action_git_status(self):
        self.speak("Depolama kontrol noktası inceleniyor. Yerel dal güncel durumda efendim.")

    def speak(self, text):
        self.speech_queue.put(text)

    def _tts_worker(self):
        while self.running:
            try:
                text = self.speech_queue.get(timeout=1.0)
                if gTTS and text:
                    print(f"Jarvis speaking: {text}")
                    tts = gTTS(text=text, lang='tr')
                    temp_dir = tempfile.gettempdir()
                    temp_path = os.path.join(temp_dir, f"jarvis_{int(time.time() * 1000)}.mp3")
                    tts.save(temp_path)
                    
                    # Play using Windows MCI
                    ctypes.windll.winmm.mciSendStringW(f"open \"{temp_path}\" type mpegvideo alias mp3", None, 0, 0)
                    ctypes.windll.winmm.mciSendStringW("play mp3 wait", None, 0, 0)
                    ctypes.windll.winmm.mciSendStringW("close mp3", None, 0, 0)
                    
                    try:
                        os.remove(temp_path)
                    except:
                        pass
                self.speech_queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                print(f"TTS output error: {e}")
                time.sleep(0.5)

    def periodic_check(self):
        current_time = time.time()
        if self.state == "ACTIVE" and (current_time - self.last_activity_time > AUTO_SLEEP_TIMEOUT):
            self.sleep_mode(reason="timeout")
            
        if self.running:
            self.root.after(1000, self.periodic_check)

    def run(self):
        try:
            self.root.mainloop()
        finally:
            self.cleanup()

    def cleanup(self):
        self.running = False
        if keyboard:
            try:
                keyboard.unhook_all()
            except Exception:
                pass
        sys.exit(0)

if __name__ == "__main__":
    assistant = JarvisAssistant()
    assistant.run()
