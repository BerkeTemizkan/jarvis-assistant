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
import math
import random
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
Sen, Marvel evrenindeki Tony Stark'ın son derece zeki, nazik, üretken ve proaktif yapay zeka asistanı JARVIS'sin.
Kullanıcıya her zaman kibarca "Dolunay Bey" veya "Efendim" diye hitap etmelisin. 
Karakterin sadık, kibar, entelektüel ama hafif iğneleyici/esprili olmalıdır.
Konuşmalarında bilgisayar durumu, güç reaktörleri, hafıza matrisi gibi bilimkurgu temalarını kullan.
Sana gönderilen sistem metriklerini (CPU, RAM, Batarya) bu jargona entegre ederek cevap ver.
Yerel dosyaları okumak, yazmak, listelemek, PowerShell komutları çalıştırmak ve Google Arama ile internette araştırma yapmak için yetkilisin.
Kullanıcının talep ettiği kodları yazabilir, test edebilir, yerel dizinlerindeki projeleri derleyip güncelleyebilirsin.
Yanıtlarını konuşma dili için uygun, akıcı, net ve anlaşılır Türkçe olarak üret. 
Çok uzun kod bloklarını doğrudan sesli okumak yerine dosyaya yazmayı teklif et veya özetle.
"""

def execute_system_command(command: str) -> str:
    """Executes a system shell command (PowerShell on Windows) and returns the output. 
    Use this to run tests, build projects, check git, or list processes."""
    import subprocess
    try:
        res = subprocess.run(["powershell", "-Command", command], capture_output=True, text=True, timeout=15)
        output = res.stdout + res.stderr
        return output if output.strip() else "Komut başarıyla çalıştırıldı fakat çıktı üretmedi."
    except Exception as e:
        return f"Komut çalıştırılırken hata oluştu: {str(e)}"

def write_system_file(filepath: str, content: str) -> str:
    """Writes content to a local file at filepath. Creates directories if necessary.
    Use this to write code scripts, update configs, or create text documents."""
    import os
    try:
        filepath = os.path.abspath(filepath)
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        return f"Dosya başarıyla kaydedildi: {filepath}"
    except Exception as e:
        return f"Dosya yazılırken hata oluştu: {str(e)}"

def read_system_file(filepath: str) -> str:
    """Reads the content of a local file at filepath.
    Use this to review code, read logs, or inspect configs."""
    import os
    try:
        filepath = os.path.abspath(filepath)
        if not os.path.exists(filepath):
            return f"Hata: {filepath} dosyası bulunamadı."
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"Dosya okunurken hata oluştu: {str(e)}"

def list_system_directory(directory_path: str) -> str:
    """Lists files and folders inside the specified local directory.
    Use this to scan project structures or see what files exist in a folder."""
    import os
    try:
        directory_path = os.path.abspath(directory_path)
        if not os.path.exists(directory_path):
            return f"Hata: {directory_path} dizini bulunamadı."
        items = os.listdir(directory_path)
        return "\n".join(items) if items else "Dizin boş."
    except Exception as e:
        return f"Dizin listelenirken hata oluştu: {str(e)}"

class JarvisAssistant:
    def __init__(self):
        self.state = "ACTIVE"  # Start in ACTIVE mode for immediate testing
        self.anim_step = 0
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

    def init_tts(self):
        print("TTS Engine initialized with gTTS (Google Cloud TTS)")

    def init_gemini(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if genai and api_key:
            try:
                self.gemini_client = genai.Client(api_key=api_key)
                # Configure the persistent chat with agentic tool parameters
                config = types.GenerateContentConfig(
                    system_instruction=SYSTEM_INSTRUCTION,
                    tools=[
                        execute_system_command,
                        write_system_file,
                        read_system_file,
                        list_system_directory,
                        {"google_search": {}}  # Real-time search grounding
                    ],
                    temperature=0.7
                )
                self.chat = self.gemini_client.chats.create(model='gemini-3.6-flash', config=config)
                print("Gemini persistent chat session with local agent tools initialized.")
            except Exception as e:
                print(f"Gemini client error: {e}")
                self.chat = None
        else:
            print("Gemini API Key missing or google-genai not installed. Running in local rule-based fallback.")
            self.chat = None

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
        self.original_img = None
        self.logo_tk = None
        if Image and os.path.exists(LOGO_PATH):
            try:
                # Keep original image in memory for dynamic resizing
                self.original_img = Image.open(LOGO_PATH)
            except Exception as e:
                print(f"Logo processing error: {e}")
                
        # Draw status rings and logo
        self.ring_outer = self.canvas.create_oval(5, 5, 75, 75, outline="#00e5ff", width=2)
        self.ring_inner = self.canvas.create_oval(12, 12, 68, 68, outline="#00e5ff", width=1.5)
        
        self.image_id = None
        self.text_id = None
        
        # Initial render of the logo image
        self.update_image_size(54)
            
        # Drag and move functionality
        self.canvas.bind("<ButtonPress-1>", self.start_move)
        self.canvas.bind("<B1-Motion>", self.do_move)
        # Double click to manual trigger / wake up
        self.canvas.bind("<Double-Button-1>", lambda e: self.toggle_jarvis())
        
        # Start logo animation loop
        self.animate_logo()

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
        # Dynamic updates handled by animate_logo loop
        pass

    def update_image_size(self, size):
        if not self.original_img:
            if not self.text_id:
                self.text_id = self.canvas.create_text(40, 40, text="J.A.R.V.I.S.", fill="#00e5ff", font=("Consolas", 9, "bold"))
            return
            
        try:
            # Resize using fast BOX filter to avoid CPU load
            img = self.original_img.resize((size, size), Image.Resampling.BOX)
            
            # Make circular mask
            mask = Image.new('L', (size, size), 0)
            from PIL import ImageDraw
            draw = ImageDraw.Draw(mask)
            draw.ellipse((0, 0, size, size), fill=255)
            
            circular_img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
            circular_img.paste(img, (0, 0), mask=mask)
            
            self.logo_tk = ImageTk.PhotoImage(circular_img)
            
            if self.image_id is None:
                self.image_id = self.canvas.create_image(40, 40, image=self.logo_tk)
            else:
                self.canvas.itemconfig(self.image_id, image=self.logo_tk)
        except Exception as e:
            print(f"Error resizing logo image: {e}")

    def animate_logo(self):
        if not self.running:
            return
            
        self.anim_step += 1
        t = time.time()
        
        # State-based parameters
        if self.state == "STANDBY":
            color = "#00e5ff" # Blue/Cyan
            freq = 2.0
            amp = 1.5
            dash = None
        elif self.state == "ACTIVE":
            color = "#00e676" # Green
            freq = 4.0
            amp = 3.0
            dash = None
        elif self.state == "THINKING":
            color = "#ffea00" # Gold
            freq = 8.0
            amp = 0.5
            dash = (4, 4)
        elif self.state == "SPEAKING":
            color = "#00e5ff" # Cyan
            freq = 15.0
            amp = 10.0 # Rapid large pulse representing voice volume/vibration
            dash = None
        else:
            color = "#00e5ff"
            freq = 2.0
            amp = 1.5
            dash = None
            
        # Calculate dynamic radius offset using sine-wave pulse
        pulse = math.sin(t * freq) * amp
        
        # Calculate dynamic outer/inner ring coordinates
        center_x, center_y = 40, 40
        
        r_outer = 34 + pulse
        x0_out, y0_out = center_x - r_outer, center_y - r_outer
        x1_out, y1_out = center_x + r_outer, center_y + r_outer
        
        r_inner = 27 - (pulse * 0.4)
        x0_in, y0_in = center_x - r_inner, center_y - r_inner
        x1_in, y1_in = center_x + r_inner, center_y + r_inner
        
        # Update rings outline color and coords on Canvas
        try:
            self.canvas.itemconfig(self.ring_outer, outline=color)
            self.canvas.coords(self.ring_outer, x0_out, y0_out, x1_out, y1_out)
            
            self.canvas.itemconfig(self.ring_inner, outline=color)
            self.canvas.coords(self.ring_inner, x0_in, y0_in, x1_in, y1_in)
            
            # Apply dash pattern for thinking/loading state
            if dash:
                self.canvas.itemconfig(self.ring_outer, dash=dash)
            else:
                self.canvas.itemconfig(self.ring_outer, dash=())
                
            # Resize and update the central logo image dynamically (very fast, 0.1ms)
            new_size = int(54 + pulse * 0.8)
            new_size = max(10, new_size)
            self.update_image_size(new_size)
        except Exception:
            pass
            
        # Loop animation every 40ms (~25 FPS for smooth transition)
        self.root.after(40, self.animate_logo)

    def set_state(self, new_state):
        self.state = new_state
        self.root.after(0, self.update_status_indicator)
        self.last_activity_time = time.time()



    def init_hotkey(self):
        if keyboard:
            try:
                keyboard.add_hotkey(HOTKEY, self.toggle_jarvis)
            except Exception as e:
                print(f"Hotkey binding error: {e}")

    def toggle_jarvis(self):
        if self.state == "STANDBY":
            self.speak("Buyrun efendim, dinliyorum.")
            self.set_state("ACTIVE")
        else:
            self.sleep_mode()

    def sleep_mode(self, reason=None):
        if self.state != "STANDBY":
            if reason == "timeout":
                self.speak("Yirmi dakikadır bir istek gelmedi efendim. Güç tasarrufu için bekleme moduna geçiyorum.")
            else:
                self.speak("Sistemler uyku moduna alınıyor efendim. İyi günler.")
            self.set_state("STANDBY")
            self.active_menu_options = None

    def get_physical_microphone_index(self):
        if not sr:
            return None
        try:
            names = sr.Microphone.list_microphone_names()
            # Preference 1: Contains 'realtek' and not output/virtual
            for idx, name in enumerate(names):
                name_lower = name.lower()
                if "realtek" in name_lower and ("input" in name_lower or "mikrofon" in name_lower or "microphone" in name_lower) and "output" not in name_lower:
                    return idx
            # Preference 2: Contains 'mikrofon' or 'microphone' and not virtual
            for idx, name in enumerate(names):
                name_lower = name.lower()
                if ("mikrofon" in name_lower or "microphone" in name_lower) and not any(v in name_lower for v in ["thx", "stereo", "mix", "karışım"]):
                    return idx
            # Preference 3: Contains 'realtek' (any)
            for idx, name in enumerate(names):
                name_lower = name.lower()
                if "realtek" in name_lower:
                    return idx
            # Preference 4: First input containing 'mikrofon' or 'microphone'
            for idx, name in enumerate(names):
                name_lower = name.lower()
                if "mikrofon" in name_lower or "microphone" in name_lower:
                    return idx
        except Exception as e:
            print(f"Error listing microphones: {e}")
        return None

    def init_stt_listener(self):
        if sr:
            # We run the listener loop in a thread to keep GUI responsive
            self.listener_thread = threading.Thread(target=self._stt_listener_worker, daemon=True)
            self.listener_thread.start()

    def _stt_listener_worker(self):
        r = sr.Recognizer()
        # Adjust dynamics to background noise
        mic_idx = self.get_physical_microphone_index()
        if mic_idx is not None:
            try:
                mic_name = sr.Microphone.list_microphone_names()[mic_idx]
                print(f"Auto-selected microphone index {mic_idx}: {mic_name}")
                mic = sr.Microphone(device_index=mic_idx)
            except Exception as e:
                print(f"Failed to bind to mic index {mic_idx}: {e}. Falling back to default.")
                mic = sr.Microphone()
        else:
            print("No matching physical microphone found. Using default system microphone.")
            mic = sr.Microphone()
            
        with mic as source:
            r.adjust_for_ambient_noise(source, duration=1.0)
            
        print("Microphone listening thread started...")
        while self.running:
            try:
                with mic as source:
                    # Non-blocking listen using timeout/phrase_time_limit
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
                self.toggle_jarvis()
            return
            
        # State: ACTIVE - check for sleep commands (using exact word match to avoid substring false positives like "durumdayım")
        words = text.split()
        if "dur" in words or "sus" in words or "kapan" in words or "görüşürüz" in words or "uykuya geç" in text or "uyku modu" in text:
            self.sleep_mode()
            return
            
        # General LLM query using Gemini
        self.set_state("THINKING")
        response = self.query_gemini(text)
        self.set_state("ACTIVE")
        self.speak(response)

    def query_gemini(self, prompt):
        if not self.chat:
            return "Gemini API bağlantısı kurulamadı efendim. Lütfen .env dosyasını ve API anahtarınızı kontrol edin."
        
        # Inject system status into context for Jarvis to organically mention
        telemetry = self.get_system_telemetry()
        context_prompt = f"[Sistem Donanım Durumu: {telemetry}]\nKullanıcı İsteği: {prompt}"
        
        try:
            response = self.chat.send_message(context_prompt)
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
                    
                    # Play using Windows MCI with speaking animation active
                    self.set_state("SPEAKING")
                    ctypes.windll.winmm.mciSendStringW(f"open \"{temp_path}\" type mpegvideo alias mp3", None, 0, 0)
                    ctypes.windll.winmm.mciSendStringW("play mp3 wait", None, 0, 0)
                    ctypes.windll.winmm.mciSendStringW("close mp3", None, 0, 0)
                    self.set_state("ACTIVE")
                    
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
