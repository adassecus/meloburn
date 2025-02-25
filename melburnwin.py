import os
import sys
import shutil
import threading
import ctypes
import subprocess
import re
import requests 
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
from tkinter import ttk
from mutagen.easyid3 import EasyID3  

BG_COLOR = "#2e2e2e"        
FG_COLOR = "#ffffff"        
BUTTON_COLOR = "#007BFF"    
ENTRY_BG = "#444444"        

def lookup_artist_by_track(track_title):
    url = f"https://theaudiodb.com/api/v1/json/1/searchtrack.php?t={track_title}"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data and data.get("track") and len(data["track"]) > 0:
                return data["track"][0].get("strArtist")
    except Exception as e:
        return None
    return None

def lookup_track_by_artist(artist):
    url = f"https://theaudiodb.com/api/v1/json/1/searchtrack.php?s={artist}"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data and data.get("track") and len(data["track"]) > 0:
                return data["track"][0].get("strTrack")
    except Exception as e:
        return None
    return None

def enhance_metadata(artist, title):
    if artist.lower() == "desconhecido":
        new_artist = lookup_artist_by_track(title)
        if new_artist:
            artist = new_artist
    if title.lower() == "desconhecido" and artist.lower() != "desconhecido":
        new_title = lookup_track_by_artist(artist)
        if new_title:
            title = new_title
    return artist, title

def check_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        return False

if not check_admin():
    root = tk.Tk()
    root.withdraw()
    messagebox.showerror("Permissão Negada 🚫", "Por favor, execute o script como administrador!")
    sys.exit(0)

def shorten_text(text, max_length=25):
    return text if len(text) <= max_length else text[:max_length] + "..."

def organize_music(source_folder, output_folder, log_func):
    log_func("💖 Iniciando organização das músicas...")
    music_dict = {}  
    unknown_metadata = set()
    abs_output = os.path.abspath(output_folder)

    for root_dir, dirs, files in os.walk(source_folder):
        if os.path.abspath(root_dir).startswith(abs_output):
            continue
        for file in files:
            if file.lower().endswith(('.mp3', '.wav', '.flac', '.aac')):
                file_path = os.path.join(root_dir, file)
                try:
                    if file.lower().endswith('.mp3'):
                        audio = EasyID3(file_path)
                    else:
                        audio = {}
                except Exception:
                    audio = {}
                artist = audio.get('artist', [None])[0]
                album = audio.get('album', [None])[0]
                title = audio.get('title', [None])[0]
                if not artist or artist.strip() == "":
                    artist = "Desconhecido"
                    unknown_metadata.add(file)
                if not album or album.strip() == "":
                    album = "Desconhecido"
                    unknown_metadata.add(file)
                if not title or title.strip() == "":
                    title = os.path.splitext(file)[0]
                    unknown_metadata.add(file)
                artist = artist.replace("_", " ")
                album = album.replace("_", " ")
                title = title.replace("_", " ")
                if artist.isupper():
                    artist = artist.lower().title()
                if album.isupper():
                    album = album.lower().title()
                if title.isupper():
                    title = title.lower().title()
                title = re.sub(r'^\d+\s*[-_.]?\s*', '', title).strip()
                try:
                    new_artist, new_title = enhance_metadata(artist, title)
                    if not new_artist or new_artist.strip() == "":
                        new_artist = "Desconhecido"
                    if not new_title or new_title.strip() == "":
                        new_title = "Desconhecido"
                    artist, title = new_artist, new_title
                except Exception:
                    artist, title = artist, title
                artist = shorten_text(artist, 25)
                title = shorten_text(title, 25)

                music_dict.setdefault(artist, {}).setdefault(album, []).append((file_path, title))

    try:
        for artist, albums in music_dict.items():
            artist_folder = os.path.join(output_folder, artist)
            os.makedirs(artist_folder, exist_ok=True)
            for album, files in albums.items():
                album_folder = os.path.join(artist_folder, album)
                os.makedirs(album_folder, exist_ok=True)
                files_sorted = sorted(files, key=lambda x: x[1])
                for idx, (orig_path, title) in enumerate(files_sorted, start=1):
                    ext = os.path.splitext(orig_path)[1]
                    new_filename = f"{idx:02d} - {title}{ext}"
                    dest_path = os.path.join(album_folder, new_filename)
                    try:
                        shutil.copy2(orig_path, dest_path)
                        log_func(f"🎵 Copiado: {new_filename}")
                    except Exception as e:
                        log_func(f"⚠️ Erro ao copiar {orig_path}: {e}")
        log_func("✨ Organização concluída com sucesso!\n")
    except Exception as e:
        log_func(f"⚠️ Erro na organização: {e}")

    return unknown_metadata

def count_files(folder):
    total = 0
    for _, _, files in os.walk(folder):
        total += len(files)
    return total

def copy_folder(source, destination, update_progress, log_func, total_files, progress_counter):
    for root_dir, dirs, files in os.walk(source):
        rel_path = os.path.relpath(root_dir, source)
        dest_dir = os.path.join(destination, rel_path)
        try:
            if not os.path.exists(dest_dir):
                os.makedirs(dest_dir, exist_ok=True)
        except Exception as e:
            log_func(f"⚠️ Erro ao criar pasta {dest_dir}: {e}")
        for file in files:
            src_file = os.path.join(root_dir, file)
            dst_file = os.path.join(dest_dir, file)
            try:
                if os.path.exists(dst_file):
                    os.remove(dst_file)
                shutil.copy2(src_file, dst_file)
            except Exception as e:
                log_func(f"⚠️ Erro ao copiar {src_file} para {dst_file}: {e}")
            progress_counter[0] += 1
            update_progress(progress_counter[0], total_files)

def copy_to_pen_drive(organized_folder, pen_drive_folder, mode, log_func, update_progress):
    dest_folder = os.path.join(pen_drive_folder, "Music")
    try:
        if mode == "formatar":
            if os.path.exists(dest_folder):
                shutil.rmtree(dest_folder)
            os.makedirs(dest_folder, exist_ok=True)
        else:
            if not os.path.exists(dest_folder):
                os.makedirs(dest_folder, exist_ok=True)
    except Exception as e:
        log_func(f"⚠️ Erro ao preparar a pasta destino: {e}")
        return

    total_files = count_files(organized_folder)
    progress_counter = [0]
    try:
        copy_folder(organized_folder, dest_folder, update_progress, log_func, total_files, progress_counter)
    except Exception as e:
        log_func(f"⚠️ Erro durante a cópia: {e}")
        return

def format_pen_drive(drive_path, log_func):
    drive_letter = os.path.splitdrive(drive_path)[0]
    if not drive_letter:
        log_func("😕 Não foi possível determinar a letra do pen drive.")
        return False

    confirm = messagebox.askyesno("Confirmação de Formatação",
                                  f"Tem certeza de que deseja formatar o pen drive {drive_letter}\\?\nEsta operação apagará TODOS os dados!")
    if not confirm:
        log_func("❌ Formatação cancelada pelo usuário.")
        return False

    log_func(f"🧹 Iniciando formatação rápida do pen drive {drive_letter}\\ ...")
    try:
        command = f'echo Y | format {drive_letter} /FS:FAT32 /Q'
        ret = os.system(command)
        if ret != 0:
            log_func("⚠️ Falha na formatação do pen drive. Verifique os privilégios administrativos.")
            return False
    except Exception as e:
        log_func(f"⚠️ Erro ao formatar: {e}")
        return False

    log_func("✅ Formatação concluída com sucesso!\n")
    return True

def rename_pen_drive(pen_drive_folder, log_func):
    drive = os.path.splitdrive(pen_drive_folder)[0] 
    letter = drive.rstrip(":")
    try:
        subprocess.run(["powershell", "-Command", f"Set-Volume -DriveLetter {letter} -NewFileSystemLabel \"\""], check=True)
        log_func("🔄 Pen drive renomeado.")
    except Exception as e:
        log_func("⚠️ Erro ao renomear pen drive: " + str(e))

class Application(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Meloburn 🍯🎶")
        self.geometry("750x650")
        self.resizable(False, False)
        self.configure(bg=BG_COLOR)
        
        self.source_folder = ""
        self.pen_drive_folder = ""
        self.operation_mode = tk.StringVar(value="formatar")
        
        self.create_widgets()
    
    def create_widgets(self):
        about_text = (
            "Bem-vindo ao Meloburn!\n\n"
            "Este programa organiza suas músicas por artista e álbum, renomeia e numera as faixas de forma otimizada "
            "para aparelhos de som. Você pode optar por formatar o pen drive (apagando todo o conteúdo) ou adicionar "
            "novas músicas (substituindo duplicatas)."
        )
        lbl_about = tk.Label(self, text=about_text, bg=BG_COLOR, fg=FG_COLOR, justify="center",
                            font=("Segoe UI", 11), wraplength=720)
        lbl_about.pack(padx=10, pady=10, anchor="center")
        
        frame_folders = tk.LabelFrame(self, text="Seleção de Pastas", bg=BG_COLOR, fg=FG_COLOR, padx=10, pady=10)
        frame_folders.pack(fill="x", padx=10, pady=5)
        
        btn_select_source = tk.Button(frame_folders, text="Pasta com as músicas 🎵", command=self.select_source,
                                    bg=BUTTON_COLOR, fg=FG_COLOR, font=("Segoe UI", 10), width=25)
        btn_select_source.grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.lbl_source = tk.Label(frame_folders, text="Nenhuma pasta selecionada", bg=BG_COLOR, fg=FG_COLOR,
                                width=60, anchor="w", font=("Segoe UI", 10))
        self.lbl_source.grid(row=0, column=1, padx=5, pady=5)
        
        lbl_note = tk.Label(frame_folders, text="Nota: selecione a pasta raiz que contém todas as músicas (mesmo que estejam em subpastas).",
                            bg=BG_COLOR, fg=FG_COLOR, font=("Segoe UI", 9), anchor="w")
        lbl_note.grid(row=1, column=0, columnspan=2, padx=5, pady=5, sticky="w")
        
        btn_select_pen = tk.Button(frame_folders, text="Pen drive 💾", command=self.select_pen_drive,
                                bg=BUTTON_COLOR, fg=FG_COLOR, font=("Segoe UI", 10), width=25)
        btn_select_pen.grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.lbl_pen = tk.Label(frame_folders, text="Nenhum pen drive selecionado", bg=BG_COLOR, fg=FG_COLOR,
                                width=60, anchor="w", font=("Segoe UI", 10))
        self.lbl_pen.grid(row=2, column=1, padx=5, pady=5)
        
        frame_options = tk.LabelFrame(self, text="Opção de Gravação", bg=BG_COLOR, fg=FG_COLOR, padx=10, pady=10)
        frame_options.pack(fill="x", padx=10, pady=5)
        
        rb_format = tk.Radiobutton(frame_options, text="Formatar pen drive (apaga conteúdo) 🔥", variable=self.operation_mode,
                                value="formatar", bg=BG_COLOR, fg=FG_COLOR, selectcolor=BG_COLOR, font=("Segoe UI", 10))
        rb_format.grid(row=0, column=0, sticky="w", padx=5, pady=5)
        rb_add = tk.Radiobutton(frame_options, text="Adicionar músicas (mantém conteúdo) ➕", variable=self.operation_mode,
                                value="adicionar", bg=BG_COLOR, fg=FG_COLOR, selectcolor=BG_COLOR, font=("Segoe UI", 10))
        rb_add.grid(row=1, column=0, sticky="w", padx=5, pady=5)
        
        btn_start = tk.Button(self, text="Iniciar Organização 🚀", command=self.start_process,
                            bg=BUTTON_COLOR, fg=FG_COLOR, font=("Segoe UI", 11, "bold"), width=25)
        btn_start.pack(pady=10)
        
        btn_export = tk.Button(self, text="Exportar Log 📄", command=self.export_log,
                            bg=BUTTON_COLOR, fg=FG_COLOR, font=("Segoe UI", 10), width=25)
        btn_export.pack(pady=5)
        
        frame_logs = tk.LabelFrame(self, text="Logs", bg=BG_COLOR, fg=FG_COLOR, padx=10, pady=10)
        frame_logs.pack(fill="both", expand=True, padx=10, pady=5)
        self.txt_logs = scrolledtext.ScrolledText(frame_logs, wrap=tk.WORD, state="disabled",
                                                bg=ENTRY_BG, fg=FG_COLOR, font=("Segoe UI", 10))
        self.txt_logs.pack(fill="both", expand=True)
    
    def log(self, message):
        self.txt_logs.configure(state="normal")
        self.txt_logs.insert(tk.END, message + "\n")
        self.txt_logs.see(tk.END)
        self.txt_logs.configure(state="disabled")
    
    def select_source(self):
        folder = filedialog.askdirectory(title="Pasta com as músicas")
        if folder:
            self.source_folder = folder
            self.lbl_source.config(text=self.source_folder)
    
    def select_pen_drive(self):
        folder = filedialog.askdirectory(title="Pen drive")
        if folder:
            self.pen_drive_folder = folder
            self.lbl_pen.config(text=self.pen_drive_folder)
    
    def open_progress_window(self):
        self.progress_window = tk.Toplevel(self)
        self.progress_window.title("Progresso da Cópia")
        self.progress_window.geometry("400x150")
        self.progress_window.configure(bg=BG_COLOR)
        self.progress_window.attributes("-topmost", True)  
        style = ttk.Style(self.progress_window)
        style.theme_use('clam')
        style.configure("blue.Horizontal.TProgressbar", troughcolor=BG_COLOR, background=BUTTON_COLOR, thickness=20)
        self.prog_bar = ttk.Progressbar(self.progress_window, orient="horizontal", mode="determinate",
        maximum=100, length=350, style="blue.Horizontal.TProgressbar")
        self.prog_bar.pack(pady=20)
        self.prog_label = tk.Label(self.progress_window, text="0%", bg=BG_COLOR, fg=FG_COLOR, font=("Segoe UI", 10))
        self.prog_label.pack()
    
    def update_progress(self, current, total):
        try:
            percent = (current / total) * 100 if total > 0 else 0
            if hasattr(self, 'prog_bar'):
                self.after(0, lambda: self.prog_bar.configure(value=percent))
            if hasattr(self, 'prog_label'):
                self.after(0, lambda: self.prog_label.configure(text=f"{percent:.0f}%"))
        except tk.TclError:
            pass
    
    def export_log(self):
        log_text = self.txt_logs.get("1.0", tk.END)
        file_path = filedialog.asksaveasfilename(title="Salvar Log", defaultextension=".txt",
                                                 filetypes=[("Text Files", "*.txt")])
        if file_path:
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(log_text)
                messagebox.showinfo("Sucesso", "Log exportado com sucesso!")
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao exportar log: {e}")
    
    def start_process(self):
        if not self.source_folder:
            messagebox.showerror("Erro ❌", "Selecione a pasta com as músicas.")
            return
        if not self.pen_drive_folder:
            messagebox.showerror("Erro ❌", "Selecione o pen drive.")
            return
        
        output_folder = os.path.join(self.source_folder, "Organized_Music")
        if os.path.exists(output_folder):
            shutil.rmtree(output_folder)
        os.makedirs(output_folder)
        
        self.txt_logs.configure(state="normal")
        self.txt_logs.delete(1.0, tk.END)
        self.txt_logs.configure(state="disabled")
        
        self.open_progress_window()
        
        threading.Thread(target=self.process_music, args=(output_folder,), daemon=True).start()
    
    def process_music(self, output_folder):
        try:
            self.log("💖 Processo iniciado...")
            unknown_files = organize_music(self.source_folder, output_folder, self.log)
        
            mode = self.operation_mode.get()
            if mode == "formatar":
                success = format_pen_drive(self.pen_drive_folder, self.log)
                if not success:
                    self.log("❌ Operação interrompida devido à falha na formatação.")
                    return
        
            copy_to_pen_drive(output_folder, self.pen_drive_folder, mode, self.log, self.update_progress)
        
            if mode == "adicionar":
                rename_pen_drive(self.pen_drive_folder, self.log)
        
            if unknown_files:
                unknown_list = ", ".join(unknown_files)
                self.log(f"⚠️ Atenção: os seguintes arquivos não tiveram metadados identificados automaticamente:\n{unknown_list}")
        
            self.log("\n🎉 Processo concluído com sucesso! Seu pen drive está pronto para uso. 🍯")
            messagebox.showinfo("Concluído", "Processo concluído com sucesso!")
        except tk.TclError:
            self.log("🚫 Processo encerrado pelo usuário.")
        except Exception as e:
            self.log(f"⚠️ Erro: {e}")
            messagebox.showerror("Erro", f"Ocorreu um erro: {e}")
        finally:
            if hasattr(self, "progress_window") and self.progress_window:
                try:
                    self.progress_window.destroy()
                except Exception:
                    pass

if __name__ == "__main__":
    app = Application()
    app.mainloop()
