


import random
import tkinter as tk
from tkinter import DISABLED, filedialog
from PIL import Image, ImageTk
from pdf2image import convert_from_path
import PyPDF2
import os
import sys
import time
import threading
import json

from config import ICON_PATH
from prompts import *
import ai_utils as ai_utils


class Deckmaker(tk.Tk):

    def __init__(self, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)

        self.container = container = tk.Frame(self)
        container.pack(side="top", fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)
        self.show_startframe()

    def show_startframe(self):
        '''Show a frame for the given page name'''
        frame = StartPage(parent=self.container, controller=self)
        frame.grid(row=0, column=0, sticky="nsew")
        frame.tkraise()

class StartPage(tk.Frame):

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent, bg='#222831')
        self.controller = controller
        self.controller.title("Translator")

        global base_dir

        if getattr(sys, 'frozen', False):
            base_dir = sys._MEIPASS
        else:
            base_dir = os.path.dirname(os.path.abspath(__file__))

        self.controller.iconphoto(False, tk.PhotoImage(file=f"{base_dir}\\{ICON_PATH}"))

        global try_count, pages, current_page, image_path
        global language, added_instructions, previous_context, is_context_needed

        pages = None
        image_path = None
        try_count = 0
        current_page = 0
        previous_context = {
                        "context" : None,
                        "last_sentence" : None
                    }

        # Add preferences file path
        self.preferences_file = f"{base_dir}\\user_preferences.json"
        
        # Replace the global variable initialization with load_preferences()
        self.load_preferences()
        
        menubar = tk.Menu(controller)
        controller.config(menu=menubar)
        
        options_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Options", menu=options_menu)
        options_menu.add_command(label="Instructions", command=self.show_instructions_popup)
        options_menu.add_command(label="Language", command=self.show_language_popup)
        options_menu.add_command(label="Context", command=self.show_context_popup)

        def news_box_update(upd_message):
            upload_news_box.delete('1.0', tk.END)
            upload_news_box.insert(tk.END, upd_message)
            upload_news_box.update_idletasks()

        def display_image(input_image):
            global image_path, start_page, pages, current_page, base_dir
            
            save_path = f"{base_dir}\\rough"
            os.makedirs(save_path, exist_ok=True)

            try:
                if input_image and isinstance(input_image, Image.Image):
                    if input_image.format != 'PNG':
                        input_image = input_image.convert('RGBA')
                    
                    image_path = os.path.join(save_path, f"image_{int(time.time())}.png")
                    input_image.save(image_path, 'PNG')
                    print(f"Image saved at: {image_path}")
                    
                    image_width = 562
                    image_height = 632
                    image = input_image.resize((image_width, image_height), Image.Resampling.LANCZOS)
                    photo = ImageTk.PhotoImage(image)
                    image_label.config(image=photo, width=image_width, height=image_height)
                    image_label.image = photo  # Keep a reference to avoid garbage collection
                    
                    news_box_update(f'Displaying Page {start_page + current_page}')
                    
                    # Update button states based on current page
                    previous_button.config(state="normal" if current_page > 0 else "disabled")
                    next_button.config(state="normal" if current_page < len(pages)-1 else "disabled")
                    process_button.config(state="normal")  # Enable processing when image is displayed
                    
                else:
                    news_box_update(f'Error displaying Page {start_page + current_page}')

            except Exception as e:
                news_box_update(f'Error displaying Pages')
                print(f"Error displaying pages: {e}")

        def delete_images():
            global image_path
            os.remove(image_path)
        
        def get_ai_response(context_content, prompt, model_name, output_type):
            
            global image_path, try_count 

            if try_count <= 3:
            
                try:

                    img_list = [image_path]
                    ai_response = ai_utils.get_gemini_response_for_image(img_list, context_content, prompt, 0.5, model_name, output_type)

                    return ai_response

                except Exception as e:
                    
                    print(f"\nException: {e}")
                    try_count+=1
                    return get_ai_response(context_content, prompt, model_name, output_type)
            
            else:

                news_box_update(f"Translation failed. Try again.")
                return None
        
        def start_img_process():
            threading.Thread(target=process_images, daemon=True).start()
        
        def start_pdf_process():
            threading.Thread(target=process_pdf, daemon=True).start()
        
        def process_images():  # get the name of the file to be uploaded
            
            global language, previous_context
            
            upload_button.config(state=tk.DISABLED)
            process_button.config(state=tk.DISABLED)
            text_label.delete("1.0", tk.END)

            try:

                previous_context_context = previous_context["context"]
                previous_context_last_sentence = previous_context["last_sentence"]
                secondary_context_text = "" if not previous_context_last_sentence else f"\n\nIt ends incompletely with: \n\n{previous_context_last_sentence}"
                context_content = f"Previous page content for context:\n\n{previous_context_context}{secondary_context_text}"
                
                news_box_update(f"Translating page...({random.randint(15,30)}%)")
                
                prompt_translation = generate_translation_prompt(language, added_instructions)
                # print (f"translation prompt: {prompt_translation}")

                ai_response_translation = get_ai_response(context_content if is_context_needed else None, prompt_translation, "pro", "text")

                if not ai_response_translation:
                    raise Exception("ai response failed")

                news_box_update(f"Translating page...({random.randint(50,75)}%)")
                
                if is_context_needed:
                    # print (f"context getting prompt: {context_getting_prompt}")
                    ai_response_get_context = get_ai_response(None, context_getting_prompt, "flash", "json")
                    previous_context = json.loads(ai_response_get_context)
                    
                    # print (f"ai response get context: {ai_response_get_context}")

                text_label.insert("1.0", str(ai_response_translation))

                news_box_update("Successfully processed")
                print("Successfully processed question")

                upload_button.config(state=tk.NORMAL)
                copy_button.config(state=tk.NORMAL)
                
            except Exception as e:
                
                news_box_update(f"Error in processing: {e}")
                print(f"Error in processing: {e}")
                upload_button.config(state=tk.NORMAL)
            

        def copy_text():
            text_label_content = text_label.get("1.0", tk.END).strip()
            text_label.clipboard_clear()
            text_label.clipboard_append(text_label_content)
        
        def process_pdf():
            global pages, current_page, start_page, base_dir
            
            file_path = filedialog.askopenfilename(filetypes=[("PDF Files", "*.pdf")])

            if not file_path:
                return
            
            # Get total page count first
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                total_pages = len(pdf_reader.pages)
            
            # Show page range popup
            page_range = self.show_page_range_popup(total_pages)
            if not page_range:  # User cancelled
                return
                
            start_page, end_page = page_range
            news_box_update("Processing PDF...(0%)")

            poppler_folder = os.path.join(base_dir, 'poppler')

            try:
                pages = []
                # Set environment variable to hide console window on Windows
                if os.name == 'nt':
                    os.environ['PYTHONUNBUFFERED'] = '1'
                    os.environ['NO_AT_BRIDGE'] = '1'

                # Convert only selected page range
                for i in range(start_page - 1, end_page):
                    page = convert_from_path(
                        file_path, 
                        dpi=150, 
                        poppler_path=f'{poppler_folder}\\Library\\bin', 
                        first_page=i+1, 
                        last_page=i+1,
                        use_pdftocairo=True
                    )[0]
                    pages.append(page)
                    progress = int((i - (start_page - 1)) / (end_page - start_page + 1) * 100)
                    news_box_update(f"Processing PDF...({progress}%)")
                    
                print("Done.", "Selected pages processed.")
            
            except Exception as e:
                process_button.config(state='normal')
                news_box_update(f"Error in PDF processing")
                print("Error.", f"An error occurred: {e}")
            
            current_page = 0
            display_image(pages[current_page])
            previous_button.config(state="disabled")

            if current_page < (len(pages)-1):
                next_button.config(state="normal")

        def pre_img():
            global pages, current_page, previous_context

            if current_page > 0:
                delete_images()
                current_page -= 1
                display_image(pages[current_page])
            
            previous_context = {
                        "context" : None,
                        "last_sentence" : None
                    }
            
        def nxt_img():
            global pages, current_page

            if current_page < len(pages) - 1:
                delete_images()
                current_page += 1
                display_image(pages[current_page])

        # Image placeholders
        image_label = tk.Label(self,
                                text= '',
                                width=80,
                                height=42,
                                anchor="w",
                                background='grey')
        image_label.grid(padx=(30,0), pady=(30,0), column=1, row=1, sticky='nw')

        text_label = tk.Text(self,
                                width=70,
                                height=39,
                                background='#EEEEEE',
                                padx=5,
                                pady=5)
        text_label.grid(padx=(46,0), pady=(30,0), column=2, row=1, sticky='ne')

        upload_button = tk.Button(self,
                                text='Upload PDF',
                                font=('Nunito-Bold', 15),
                                foreground='#222831',
                                background='white',
                                activeforeground='#3F72AF',
                                activebackground='white',
                                padx=5,
                                pady=2,
                                relief='sunken',
                                borderwidth=0,
                                command=start_pdf_process)
        upload_button.grid(padx=(30,0), pady=(10), column=1, row=2, sticky='nw')

        process_button = tk.Button(self,
                                text='Process',
                                font=('Nunito-Bold', 15),
                                foreground='#222831',
                                background='white',
                                activeforeground='#3F72AF',
                                activebackground='white',
                                padx=5,
                                pady=2,
                                relief='sunken',
                                borderwidth=0,
                                command=start_img_process)
        process_button.grid(padx=(170,0), pady=(10), column=1, row=2, sticky='nw')
        process_button.config(state=DISABLED)

        upload_news_box = tk.Text(self,
                        width=24,
                        height=1,
                        foreground='blue',
                        background='#EEEEEE',
                        padx=10,
                        pady=10)
        upload_news_box.grid(padx=(276,0), pady=(10), column=1, row=2, sticky='nw')

        previous_button = tk.Button(self,
                                text='P',
                                font=('Nunito-Bold', 15),
                                foreground='#222831',
                                background='white',
                                activeforeground='#3F72AF',
                                activebackground='white',
                                padx=6,
                                pady=2,
                                relief='sunken',
                                borderwidth=0,
                                command=pre_img)
        previous_button.grid(padx=(515,0), pady=(10), column=1, row=2, sticky='nw')
        previous_button.config(state=DISABLED)

        next_button = tk.Button(self,
                                text='N',
                                font=('Nunito-Bold', 15),
                                foreground='#222831',
                                background='white',
                                activeforeground='#3F72AF',
                                activebackground='white',
                                padx=6,
                                pady=2,
                                relief='sunken',
                                borderwidth=0,
                                command=nxt_img)
        next_button.grid(padx=(560,0), pady=(10), column=1, row=2, sticky='nw')
        next_button.config(state=DISABLED)

        copy_button = tk.Button(self,
                                text='Copy',
                                font=('Nunito-Bold', 15),
                                foreground='#222831',
                                background='white',
                                activeforeground='#3F72AF',
                                activebackground='white',
                                padx=5,
                                pady=2,
                                relief='sunken',
                                borderwidth=0,
                                command=copy_text)
        copy_button.grid(padx=(46,0), pady=(10), column=2, row=2, sticky='nw')
        copy_button.config(state=DISABLED)
    
    def load_preferences(self):
        """Load user preferences from JSON file"""
        global language, added_instructions, is_context_needed
        
        default_preferences = {
            "language": "Tamil",
            "added_instructions": None,
            "is_context_needed": False
        }

        try:
            # Create preferences directory in user's home directory instead of relative to executable
            preferences_dir = os.path.join(os.path.expanduser('~'), '.translator_exp')
            self.preferences_file = os.path.join(preferences_dir, 'user_preferences.json')
            
            os.makedirs(preferences_dir, exist_ok=True)
            
            if os.path.exists(self.preferences_file):
                with open(self.preferences_file, 'r', encoding='utf-8') as f:
                    preferences = json.load(f)
            else:
                preferences = default_preferences
                with open(self.preferences_file, 'w', encoding='utf-8') as f:
                    json.dump(preferences, f)

            language = preferences["language"]
            added_instructions = preferences["added_instructions"]
            is_context_needed = preferences["is_context_needed"]

        except Exception as e:
            print(f"Error loading preferences: {e}")
            language = default_preferences["language"]
            added_instructions = default_preferences["added_instructions"]
            is_context_needed = default_preferences["is_context_needed"]

    def save_preferences(self):
        """Save current preferences to JSON file"""
        preferences = {
            "language": language,
            "added_instructions": added_instructions,
            "is_context_needed": is_context_needed
        }
        
        try:
            with open(self.preferences_file, 'w', encoding='utf-8') as f:
                json.dump(preferences, f, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving preferences: {e}")

    def show_instructions_popup(self):
        popup = tk.Toplevel()
        popup.title("Additional Instructions")
        popup.iconphoto(False, tk.PhotoImage(file=f"{base_dir}\\{ICON_PATH}"))
        popup.geometry("500x400")
        popup.configure(bg='#222831')
        
        # Add some padding around the window
        frame = tk.Frame(popup, bg='#222831')
        frame.pack(padx=10, pady=10, fill='both', expand=False)
        
        # Description label
        desc_label = tk.Label(frame, 
                             text="Instructions:", 
                             font=('Nunito-Bold', 12),
                             bg='#222831',
                             fg='white')
        desc_label.pack(pady=(10,20), anchor='w')
        
        # Text input with modern styling
        text = tk.Text(frame, 
                      wrap=tk.WORD, 
                      width=60, 
                      height=16,
                      font=('Nunito-Bold', 11),
                      bg='white',
                      fg='#222831',
                      padx=2,
                      pady=2,
                      relief='flat',
                      borderwidth=0)
        text.pack(pady=(0,15))
        
        # Load existing instructions into text box
        if added_instructions:
            text.insert("1.0", added_instructions)
        
        # Create a frame for the button for better alignment
        button_frame = tk.Frame(frame, bg='#222831')
        button_frame.pack(fill='x')
        
        def save_instructions():
            global added_instructions
            added_instructions = text.get("1.0", tk.END).strip()
            self.save_preferences()
            popup.destroy()
        
        # Modern styled save button
        save_btn = tk.Button(button_frame, 
                            text="Save",
                            font=('Nunito-Bold', 15),
                            command=save_instructions,
                            bg='white',
                            fg='#222831',
                            activeforeground='#3F72AF',
                            activebackground='white',
                            padx=5,
                            pady=2,
                            relief='sunken',
                            borderwidth=0)
        save_btn.pack()
        
        self.centre_popup(popup)
        
    def centre_popup(self, popup):
        popup.transient(self)
        popup.grab_set()
        popup.update_idletasks()
        width = popup.winfo_width()
        height = popup.winfo_height()
        x = (popup.winfo_screenwidth() // 2) - (width // 2)
        y = (popup.winfo_screenheight() // 2) - (height // 2)
        popup.geometry(f'{width}x{height}+{x}+{y}')
        popup.focus_set()


    def show_language_popup(self):
        popup = tk.Toplevel()
        popup.title("Translate to")
        popup.iconphoto(False, tk.PhotoImage(file=f"{base_dir}\\{ICON_PATH}"))
        popup.geometry("300x500")
        popup.configure(bg='#222831')
        
        frame = tk.Frame(popup, bg='#222831')
        frame.pack(fill='both', expand=True)
        
        languages = [
            "English",
            "Bengali (বাংলা)",
            "Gujarati (ગુજરાતી)",
            "Hindi (हिंदी)",
            "Kannada (ಕನ್ನಡ)",
            "Malayalam (മലയാളം)",
            "Marathi (मराठी)",
            "Punjabi (ਪੰਜਾਬੀ)",
            "Tamil (தமிழ்)",
            "Telugu (తెలుగు)",
            "Urdu (اردو)"
        ]

        # Create canvas and scrollbar
        canvas = tk.Canvas(frame, bg='#222831', highlightthickness=0)
        scrollbar = tk.Scrollbar(frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg='#222831')

        # Add mouse wheel binding for scrolling
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        # Unbind mousewheel when popup is destroyed to prevent interference with other windows
        popup.bind("<Destroy>", lambda e: canvas.unbind_all("<MouseWheel>"))

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        # Important: Set canvas width to fill available space minus scrollbar width
        canvas_frame = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        
        def configure_scroll_region(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
            # Make sure the scrollable frame has the same width as canvas
            canvas.itemconfig(canvas_frame, width=canvas.winfo_width())

        scrollable_frame.bind("<Configure>", configure_scroll_region)
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(canvas_frame, width=canvas.winfo_width()))

        # Pack scrollbar first, then canvas
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=False)
        
        # Configure canvas to use scrollbar
        canvas.configure(yscrollcommand=scrollbar.set)

        for lang in languages:
            base_lang = lang.split(' (')[0]
            is_selected = (base_lang == language)
            
            btn = tk.Button(scrollable_frame, 
                           text=lang,
                           command=lambda l=lang: self.set_language(l.split(' (')[0], popup),
                           font=('Nunito-Bold', 11),
                           bg='#3F72AF' if is_selected else 'white',  # Highlight selected language
                           fg='white' if is_selected else '#222831',  # Change text color for selected
                           padx=30,
                           pady=8,
                           relief='flat',
                           borderwidth=0,
                           width=20,
                           activebackground='#3F72AF',
                           activeforeground='white',
                           cursor='hand2')
            btn.pack(pady=(10,0), padx=10, fill="x")
            
            # Only bind hover effects for unselected buttons
            if not is_selected:
                btn.bind('<Enter>', lambda e, btn=btn: btn.configure(bg='#EEEEEE'))
                btn.bind('<Leave>', lambda e, btn=btn: btn.configure(bg='white'))

        self.centre_popup(popup)

    def set_language(self, lang, popup):
        global language
        language = lang
        self.save_preferences()
        popup.destroy()

    def show_context_popup(self):
        popup = tk.Toplevel()
        popup.title("Context selection")
        popup.iconphoto(False, tk.PhotoImage(file=f"{base_dir}\\{ICON_PATH}"))
        popup.geometry("300x250")
        popup.configure(bg='#222831')
        
        frame = tk.Frame(popup, bg='#222831')
        frame.pack(padx=10, pady=10, fill='both', expand=True)

        desc_label = tk.Label(frame, 
                             text="Is previous page context needed?", 
                             font=('Nunito-Bold', 12),
                             bg='#222831',
                             fg='white')
        desc_label.pack(padx=10, pady=(20,10), anchor='w')
        
        # Set the radio button value to current preference
        context_var = tk.BooleanVar(value=is_context_needed)
        
        # Style the radio buttons to show selection more clearly
        yes_radio = tk.Radiobutton(frame, 
                                  text="Yes",
                                  variable=context_var,
                                  value=True,
                                  font=('Nunito-Bold', 11),
                                  bg='#222831',
                                  fg='white',
                                  selectcolor='#222831',
                                  activebackground='#222831',
                                  activeforeground='white')
        yes_radio.pack(padx=(100,0), pady=10, anchor='w')
        
        no_radio = tk.Radiobutton(frame, 
                                 text="No",
                                 variable=context_var,
                                 value=False,
                                 font=('Nunito-Bold', 11),
                                 bg='#222831',
                                 fg='white',
                                 selectcolor='#222831',
                                 activebackground='#222831',
                                 activeforeground='white')
        no_radio.pack(padx=(100,0), pady=10, anchor='w')
        
        def save_context_setting():
            global is_context_needed
            is_context_needed = context_var.get()
            self.save_preferences()
            popup.destroy()
        
        # Save button
        save_btn = tk.Button(frame, 
                            text="Save",
                            font=('Nunito-Bold', 15),
                            command=save_context_setting,
                            bg='white',
                            fg='#222831',
                            activeforeground='#3F72AF',
                            activebackground='white',
                            padx=5,
                            pady=2,
                            relief='sunken',
                            borderwidth=0)
        save_btn.pack(pady=(20,10))
        
        self.centre_popup(popup)

    def show_page_range_popup(self, total_pages):
        """Show popup for selecting page range"""
        popup = tk.Toplevel()
        popup.title("Select Page Range")
        popup.iconphoto(False, tk.PhotoImage(file=f"{base_dir}\\{ICON_PATH}"))
        popup.geometry("300x200")
        popup.configure(bg='#222831')
        
        frame = tk.Frame(popup, bg='#222831')
        frame.pack(padx=10, pady=10, fill='both', expand=True)
        
        # Start page input
        start_label = tk.Label(frame, text="Start Page:", bg='#222831', fg='white', font=('Nunito-Bold', 11))
        start_label.pack(pady=(10,0))
        start_var = tk.StringVar(value="1")
        start_entry = tk.Entry(frame, textvariable=start_var, justify='center', font=('Nunito-Bold', 11))
        start_entry.pack(pady=(5,10))
        
        # End page input - Change total_pages-1 to total_pages
        end_var = tk.StringVar(value=str(total_pages))
        end_entry = tk.Entry(frame, textvariable=end_var, justify='center', font=('Nunito-Bold', 11))
        end_entry.pack(pady=(5,10))
        
        result = None
        
        def validate_and_save():
            nonlocal result
            try:
                start = int(start_var.get())
                end = int(end_var.get())
                
                # Update validation to use total_pages instead of total_pages-1
                if 1 <= start <= end <= total_pages:
                    result = (start, end)
                    popup.destroy()
                else:
                    tk.messagebox.showerror("Error", "Invalid page range!")
            except ValueError:
                tk.messagebox.showerror("Error", "Please enter valid numbers!")
        
        # Save button
        save_btn = tk.Button(frame, 
                            text="Confirm",
                            font=('Nunito-Bold', 15),
                            command=validate_and_save,
                            bg='white',
                            fg='#222831',
                            activeforeground='#3F72AF',
                            activebackground='white',
                            padx=5,
                            pady=2,
                            relief='sunken',
                            borderwidth=0)
        save_btn.pack(pady=10)
        
        self.centre_popup(popup)
        popup.wait_window()  # Wait for popup to close
        return result

if __name__ == "__main__":
    app = Deckmaker()
    app_height = 750
    app_width = 1245

    screen_width = app.winfo_screenwidth()
    screen_height = app.winfo_screenheight()
    xc = int((screen_width/2) - (app_width/2))
    yc = int((screen_height/2) - (app_height/2))

    # Add cleanup function
    def on_closing():
        # Clean up rough directory
        rough_dir = "rough"
        if os.path.exists(rough_dir):
            for file in os.listdir(rough_dir):
                file_path = os.path.join(rough_dir, file)
                try:
                    os.remove(file_path)
                except Exception as e:
                    print(f"Error removing file {file_path}: {e}")
        app.destroy()

    app.protocol("WM_DELETE_WINDOW", on_closing)
    app.geometry(f'{app_width}x{app_height}+{int(xc)}+{int(yc)-20}')
    app.resizable(False, False)
    app.mainloop()