import tkinter as tk
from PIL import Image, ImageTk
from pathlib import Path
import sys

class VideoPreview(tk.Tk):
    def __init__(self):
        super().__init__()
        
        # Scale factor for preview (0.5 = half size)
        self.scale = 0.5
        self.width = int(1920 * self.scale)
        self.height = int(1080 * self.scale)
        
        self.title("Video Preview Tool")
        self.geometry(f"{self.width}x{self.height}")
        
        # Canvas for displaying the preview
        self.canvas = tk.Canvas(self, width=self.width, height=self.height)
        self.canvas.pack(fill="both", expand=True)
        
        # Controls
        self.controls = tk.Frame(self)
        self.controls.pack(side="bottom", fill="x")
        
        # Font size slider with smaller default
        self.font_size = tk.Scale(self.controls, from_=10, to=100, 
                                orient="horizontal", label="Font Size",
                                command=self.update_preview)
        self.font_size.set(28)  # Default font size
        self.font_size.pack(side="left", padx=10)
        
        # Bottom margin slider
        self.margin = tk.Scale(self.controls, from_=0, to=200,
                             orient="horizontal", label="Bottom Margin",
                             command=self.update_preview)
        self.margin.set(100)    # Adjusted bottom margin
        self.margin.pack(side="left", padx=10)
        
        # Background opacity slider
        self.opacity = tk.Scale(self.controls, from_=0, to=100,
                              orient="horizontal", label="Background Opacity",
                              command=self.update_preview)
        self.opacity.set(50)    # More transparent default (50%)
        self.opacity.pack(side="left", padx=10)
        
        self.load_sample()
        self.update_preview()
    
    def load_sample(self):
        try:
            img_path = next(Path("generated_images").glob("scene_*.png"))
            img = Image.open(img_path)
            img = img.resize((self.width, self.height), Image.Resampling.LANCZOS)
            self.background = ImageTk.PhotoImage(img)
            
            # Multiple paragraphs of sample text
            self.sample_text = [
                """The ladies of Longbourn soon waited on those of Netherfield. The visit was soon returned in due form. Miss Bennet's pleasing manners grew on the goodwill of Mrs. Hurst and Miss Bingley.""",
                
                """Within a short walk of Longbourn lived a family with whom the Bennets were particularly intimate. Sir William Lucas had been formerly in trade in Meryton, where he had made a tolerable fortune.""",
                
                """It is a truth universally acknowledged, that a single man in possession of a good fortune, must be in want of a wife.""",
                
                """However little known the feelings or views of such a man may be on his first entering a neighbourhood, this truth is so well fixed in the minds of the surrounding families, that he is considered the rightful property of some one or other of their daughters.""",
                
                """"My dear Mr. Bennet," said his lady to him one day, "have you heard that Netherfield Park is let at last?" Mr. Bennet replied that he had not. "But it is," returned she; "for Mrs. Long has just been here, and she told me all about it." """
            ]
            self.active_sentence = 2  # Index of the middle sentence (0-based index)
            
        except StopIteration:
            print("No background images found in generated_images/")
            sys.exit(1)
    
    def update_preview(self, *args):
        self.canvas.delete("all")
        
        # Draw background
        self.canvas.create_image(0, 0, image=self.background, anchor="nw")
        
        # Calculate dimensions
        side_margin = int(200 * self.scale)
        box_width = self.width - (2 * side_margin)
        font_size = int(self.font_size.get() * self.scale)
        line_spacing = int(font_size * 1.5)
        
        # Group non-active and active text
        non_active_text = []
        active_text = None
        
        for i, paragraph in enumerate(self.sample_text):
            if i == self.active_sentence:
                active_text = paragraph
            else:
                non_active_text.append(paragraph)
        
        # Calculate total height needed (one measurement for each text block)
        total_height = 0
        
        # Measure non-active text block
        if non_active_text:
            temp = self.canvas.create_text(
                0, 0,
                text='\n'.join(non_active_text),
                width=box_width,
                font=("Arial", font_size),
                anchor="nw"
            )
            bbox = self.canvas.bbox(temp)
            total_height += bbox[3] - bbox[1]
            self.canvas.delete(temp)
        
        # Measure active text block
        if active_text:
            temp = self.canvas.create_text(
                0, 0,
                text=active_text,
                width=box_width,
                font=("Arial Bold", font_size),
                anchor="nw"
            )
            bbox = self.canvas.bbox(temp)
            total_height += bbox[3] - bbox[1]
            self.canvas.delete(temp)
        
        # Calculate background box position and size
        box_height = total_height + (font_size * 2)  # Add padding
        box_y = (self.height - box_height) // 2  # Center vertically
        
        # Draw semi-transparent background
        opacity = int(self.opacity.get() * 2.55)
        gray_value = hex(opacity)[2:].zfill(2)
        self.canvas.create_rectangle(
            side_margin,
            box_y,
            self.width - side_margin,
            box_y + box_height,
            fill=f'#{gray_value}{gray_value}{gray_value}',
            outline=''
        )
        
        # Draw text blocks
        current_y = box_y + font_size
        
        # Draw non-active text
        if non_active_text:
            self.canvas.create_text(
                self.width // 2,
                current_y,
                text='\n'.join(non_active_text),
                width=box_width,
                font=("Arial", font_size),
                fill="white",
                justify="center",
                anchor="n"
            )
        
        # Draw active text
        if active_text:
            # Get position for active text
            temp = self.canvas.create_text(
                0, 0,
                text='\n'.join(non_active_text),
                width=box_width,
                font=("Arial", font_size),
                anchor="nw"
            )
            bbox = self.canvas.bbox(temp)
            self.canvas.delete(temp)
            active_y = current_y + (bbox[3] - bbox[1]) + line_spacing
            
            self.canvas.create_text(
                self.width // 2,
                active_y,
                text=active_text,
                width=box_width,
                font=("Arial Bold", font_size),
                fill="black",
                justify="center",
                anchor="n"
            )

if __name__ == "__main__":
    app = VideoPreview()
    app.mainloop() 